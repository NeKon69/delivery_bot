from __future__ import annotations

import pytest

from pi.arduino_client import ArduinoClient
from pi.main import ensure_arduino_connection
from pi.protocol import encode_message
from pi.serial_link import SerialJsonLink, SerialLinkDisconnected


class FakeBrokenSerial:
    def __init__(self) -> None:
        self.closed = False

    def readline(self) -> bytes:
        raise OSError("device disconnected")

    def close(self) -> None:
        self.closed = True


class FakeWorkingSerial:
    def __init__(self) -> None:
        self.writes: list[bytes] = []
        self.closed = False

    def readline(self) -> bytes:
        return encode_message({"type": "event", "event": "ready"})

    def write(self, payload: bytes) -> None:
        self.writes.append(payload)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class FakeLink:
    def __init__(self, failures_before_success: int) -> None:
        self.failures_before_success = failures_before_success
        self.open_calls = 0

    def open(self) -> None:
        self.open_calls += 1
        if self.open_calls <= self.failures_before_success:
            raise SerialLinkDisconnected("port unavailable")

    def close(self) -> None:
        return None


def test_serial_link_wraps_read_disconnect_and_closes_port() -> None:
    link = SerialJsonLink("/dev/ttyUSB0", 115200)
    broken = FakeBrokenSerial()
    link._serial = broken

    with pytest.raises(SerialLinkDisconnected):
        link.read_message()

    assert broken.closed is True
    assert link._serial is None


def test_ensure_arduino_connection_retries_until_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    link = FakeLink(failures_before_success=2)
    arduino = ArduinoClient(link)  # type: ignore[arg-type]
    logs: list[str] = []

    monkeypatch.setattr("pi.main.time.sleep", lambda _: None)

    ensure_arduino_connection(arduino, logs.append, retry_delay_s=0.01)

    assert link.open_calls == 3
    assert len(logs) == 2


def test_serial_link_reads_message_after_recovery_ready_payload() -> None:
    link = SerialJsonLink("/dev/ttyUSB0", 115200)
    link._serial = FakeWorkingSerial()

    message = link.read_message()

    assert message == {"type": "event", "event": "ready"}
