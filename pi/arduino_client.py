from __future__ import annotations

import time
from collections import deque
from typing import Any

from pi.protocol import encode_compact_command
from pi.serial_link import SerialJsonLink


class ArduinoClient:
    def __init__(self, link: SerialJsonLink) -> None:
        self._link = link
        self._last_lcd_lines = ["", "", "", ""]
        self._pending_lcd_acks = 0
        self._buffered_messages: deque[dict[str, Any]] = deque()

    def open(self) -> None:
        self._link.open()

    def close(self) -> None:
        self._link.close()

    def read_message(self) -> dict[str, Any] | None:
        if self._buffered_messages:
            return self._buffered_messages.popleft()
        message = self._link.read_message()
        if message is not None:
            self.handle_message(message)
        return message

    def handle_message(self, message: dict[str, Any]) -> None:
        if message.get("type") != "ack":
            return
        if message.get("command") == "lcd_set_line" and self._pending_lcd_acks > 0:
            self._pending_lcd_acks -= 1

    def lcd_busy(self) -> bool:
        return self._pending_lcd_acks > 0

    def ping(self) -> None:
        self._link.send_raw_line(encode_compact_command("ping"), "@P")

    def rfid_reset(self) -> None:
        self._link.send_raw_line(encode_compact_command("rfid_reset"), "@R")

    def get_state(self) -> None:
        self._link.send_raw_line(encode_compact_command("get_state"), "@G")

    def lcd_set(self, lines: list[str]) -> None:
        padded = list(lines[:4])
        while len(padded) < 4:
            padded.append("")
        for index, text in enumerate(padded):
            if self._last_lcd_lines[index] == text:
                continue
            debug_label = f"@L|{index}|{text}"
            self._link.send_raw_line(
                encode_compact_command("lcd_set_line", index, text), debug_label
            )
            self._last_lcd_lines[index] = text
            self._pending_lcd_acks += 1
            self._wait_for_lcd_ack(index)

    def lcd_clear(self) -> None:
        self._link.send_raw_line(encode_compact_command("lcd_clear"), "@C")
        self._last_lcd_lines = ["", "", "", ""]
        self._pending_lcd_acks = 0

    def lcd_demo(self) -> None:
        self._link.send_raw_line(encode_compact_command("lcd_demo"), "@D")

    def servo_open(self, box: int) -> None:
        self._link.send_raw_line(encode_compact_command("servo_open", box), f"@O|{box}")

    def servo_close(self, box: int) -> None:
        self._link.send_raw_line(
            encode_compact_command("servo_close", box), f"@X|{box}"
        )

    def move(self, action: str, duration_ms: int | None = None) -> None:
        if duration_ms is None:
            self._link.send_raw_line(
                encode_compact_command("move", action), f"@M|{action}"
            )
            return
        self._link.send_raw_line(
            encode_compact_command("move", action, duration_ms),
            f"@M|{action}|{duration_ms}",
        )

    def stop(self) -> None:
        self._link.send_raw_line(encode_compact_command("stop"), "@T")

    def _wait_for_lcd_ack(self, line_index: int, timeout_s: float = 0.25) -> bool:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            message = self._link.read_message()
            if message is None:
                time.sleep(0.005)
                continue
            self.handle_message(message)
            if (
                message.get("type") == "ack"
                and message.get("command") == "lcd_set_line"
                and message.get("line") == line_index
            ):
                return True
            self._buffered_messages.append(message)

        if self._pending_lcd_acks > 0:
            self._pending_lcd_acks -= 1
        return False
