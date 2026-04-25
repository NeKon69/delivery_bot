from __future__ import annotations

import json
from typing import Any, Callable

from pi.protocol import decode_message, encode_message


class SerialLinkDisconnected(RuntimeError):
    pass


class SerialJsonLink:
    def __init__(
        self,
        port: str,
        baudrate: int,
        timeout: float = 0.05,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._serial: Any | None = None
        self._logger = logger

    def open(self) -> None:
        if self._serial is not None:
            return
        try:
            import serial  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "pyserial is required; install with 'pip install pyserial'"
            ) from exc
        try:
            self._serial = serial.Serial(
                self._port, self._baudrate, timeout=self._timeout
            )
        except Exception as exc:
            self._raise_disconnected("open", exc)

    def close(self) -> None:
        if self._serial is None:
            return
        self._serial.close()
        self._serial = None

    def send(self, message: dict[str, Any]) -> None:
        if self._serial is None:
            raise RuntimeError("Serial link is not open")
        self._log("tx", message)
        try:
            self._serial.write(encode_message(message))
        except Exception as exc:
            self._raise_disconnected("write", exc)

    def send_raw_line(self, payload: bytes, debug_label: str) -> None:
        if self._serial is None:
            raise RuntimeError("Serial link is not open")
        if self._logger is not None:
            self._logger(f"[serial tx] {debug_label}")
        try:
            self._serial.write(payload)
            self._serial.flush()
        except Exception as exc:
            self._raise_disconnected("write", exc)

    def read_message(self) -> dict[str, Any] | None:
        if self._serial is None:
            raise RuntimeError("Serial link is not open")
        try:
            raw = self._serial.readline()
        except Exception as exc:
            self._raise_disconnected("read", exc)
        if not raw:
            return None
        line = raw.decode("utf-8", errors="ignore").strip()
        if not line:
            return None
        message = decode_message(line)
        self._log("rx", message)
        return message

    def _log(self, direction: str, message: dict[str, Any]) -> None:
        if self._logger is None:
            return
        rendered = json.dumps(message, separators=(",", ":"), ensure_ascii=True)
        self._logger(f"[serial {direction}] {rendered}")

    def _raise_disconnected(self, operation: str, exc: Exception) -> None:
        detail = f"Serial {operation} failed on {self._port}: {exc}"
        if self._logger is not None:
            self._logger(f"[serial error] {detail}")
        self.close()
        raise SerialLinkDisconnected(detail) from exc
