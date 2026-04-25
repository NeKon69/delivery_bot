from __future__ import annotations

from dataclasses import dataclass, field

from pi.models import DeliveryJob


@dataclass
class KeypadParseResult:
    display_text: str
    completed_jobs: list[DeliveryJob] = field(default_factory=list)
    error: str | None = None
    reset_requested: bool = False


class KeypadParser:
    def __init__(self) -> None:
        self._buffer = ""

    @property
    def buffer(self) -> str:
        return self._buffer

    def reset(self) -> None:
        self._buffer = ""

    def handle_key(self, key: str) -> KeypadParseResult:
        if len(key) != 1:
            return KeypadParseResult(
                display_text=self._buffer, error="Invalid key length"
            )

        if key == "0":
            self.reset()
            return KeypadParseResult(display_text="", reset_requested=True)

        if key == "*":
            self._buffer = self._buffer[:-1]
            return KeypadParseResult(display_text=self._buffer)

        if key == "D":
            self.reset()
            return KeypadParseResult(display_text=self._buffer)

        allowed = "123456789ABCD#"
        if key not in allowed:
            return KeypadParseResult(
                display_text=self._buffer, error=f"Unsupported key: {key}"
            )

        self._buffer += key
        if not self._buffer.endswith("##"):
            return KeypadParseResult(display_text=self._buffer)

        payload = self._buffer[:-2]
        self.reset()
        try:
            jobs = self.parse_payload(payload)
        except ValueError as exc:
            return KeypadParseResult(display_text="", error=str(exc))
        return KeypadParseResult(display_text="", completed_jobs=jobs)

    def parse_payload(self, payload: str) -> list[DeliveryJob]:
        if not payload:
            raise ValueError("Empty request")
        if payload.startswith("#") or payload.endswith("#"):
            raise ValueError("Malformed request separators")

        parts = payload.split("#")
        if len(parts) % 2 != 0:
            raise ValueError("Each request must be cabinet#box")

        jobs: list[DeliveryJob] = []
        for index in range(0, len(parts), 2):
            cabinet_id = parts[index].strip()
            box_raw = parts[index + 1].strip()
            if not cabinet_id.isdigit():
                raise ValueError(f"Invalid cabinet id: {cabinet_id}")
            if box_raw not in {"1", "2"}:
                raise ValueError(f"Invalid box id: {box_raw}")
            jobs.append(DeliveryJob(cabinet_id=cabinet_id, box_id=int(box_raw)))
        return jobs
