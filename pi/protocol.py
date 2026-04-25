from __future__ import annotations

import json
from typing import Any


COMMAND_CODES: dict[str, str] = {
    "ping": "P",
    "rfid_reset": "R",
    "get_state": "G",
    "lcd_clear": "C",
    "lcd_demo": "D",
    "lcd_set_line": "L",
    "servo_open": "O",
    "servo_close": "X",
    "servo_set_angle": "A",
    "move": "M",
    "stop": "T",
}


def encode_message(message: dict[str, Any]) -> bytes:
    return (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")


def decode_message(line: str) -> dict[str, Any]:
    message = json.loads(line)
    if not isinstance(message, dict):
        raise ValueError("Protocol message must be a JSON object")
    return message


def command(message_type: str, **fields: Any) -> dict[str, Any]:
    return {"type": message_type, **fields}


def encode_compact_command(name: str, *fields: Any) -> bytes:
    opcode = COMMAND_CODES[name]
    payload = [opcode, *(_escape_compact_field(str(field)) for field in fields)]
    return ("@" + "|".join(payload) + "\n").encode("utf-8")


def _escape_compact_field(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
