from __future__ import annotations

import argparse
import json
import threading
import time

from pi.protocol import decode_message, encode_compact_command
from pi.serial_link import SerialJsonLink


HELP_TEXT = """Commands:
  ping
  state
  lcd-demo
  lcd-clear
  lcd <line> <text>
  move <forward_cell|reverse_cell|turn_left|turn_right|stop> [duration_ms]
  servo-open <box>
  servo-close <box>
  raw <opcode> [field1] [field2] ...
  quit
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive hardware debug console")
    parser.add_argument("--port", default="/dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=115200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    def log(line: str) -> None:
        print(line, flush=True)

    link = SerialJsonLink(args.port, args.baud, logger=log)
    link.open()
    stop_flag = False

    def reader() -> None:
        nonlocal stop_flag
        while not stop_flag:
            try:
                message = link.read_message()
            except Exception as exc:  # noqa: BLE001
                print(f"[console] read error: {exc}", flush=True)
                time.sleep(0.1)
                continue
            if message is None:
                continue
            print(
                f"[console event] {json.dumps(message, ensure_ascii=True)}", flush=True
            )

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()

    print(HELP_TEXT, flush=True)
    try:
        while True:
            line = input("hw> ").strip()
            if not line:
                continue
            if line in {"quit", "exit"}:
                break
            if line == "help":
                print(HELP_TEXT, flush=True)
                continue

            parts = line.split(" ", 2)
            cmd = parts[0]

            if cmd == "ping":
                link.send_raw_line(encode_compact_command("ping"), "@P")
            elif cmd == "state":
                link.send_raw_line(encode_compact_command("get_state"), "@G")
            elif cmd == "lcd-demo":
                link.send_raw_line(encode_compact_command("lcd_demo"), "@D")
            elif cmd == "lcd-clear":
                link.send_raw_line(encode_compact_command("lcd_clear"), "@C")
            elif cmd == "lcd":
                lcd_parts = line.split(" ", 2)
                if len(lcd_parts) < 3:
                    print("usage: lcd <line> <text>", flush=True)
                    continue
                line_index = int(lcd_parts[1])
                text = lcd_parts[2]
                link.send_raw_line(
                    encode_compact_command("lcd_set_line", line_index, text),
                    f"@L|{line_index}|{text}",
                )
            elif cmd == "move":
                move_parts = line.split()
                if len(move_parts) not in {2, 3}:
                    print("usage: move <action> [duration_ms]", flush=True)
                    continue
                action = move_parts[1]
                if len(move_parts) == 3:
                    link.send_raw_line(
                        encode_compact_command("move", action, move_parts[2]),
                        f"@M|{action}|{move_parts[2]}",
                    )
                else:
                    link.send_raw_line(
                        encode_compact_command("move", action), f"@M|{action}"
                    )
            elif cmd == "servo-open":
                box = int(parts[1])
                link.send_raw_line(
                    encode_compact_command("servo_open", box), f"@O|{box}"
                )
            elif cmd == "servo-close":
                box = int(parts[1])
                link.send_raw_line(
                    encode_compact_command("servo_close", box), f"@X|{box}"
                )
            elif cmd == "raw":
                raw_parts = line.split()[1:]
                if not raw_parts:
                    print("usage: raw <opcode> [field ...]", flush=True)
                    continue
                payload = ("@" + "|".join(raw_parts) + "\n").encode("utf-8")
                link.send_raw_line(payload, "@" + "|".join(raw_parts))
            else:
                try:
                    message = decode_message(line)
                except Exception:  # noqa: BLE001
                    print("unknown command; type help", flush=True)
                    continue
                link.send(message)
    finally:
        stop_flag = True
        link.close()


if __name__ == "__main__":
    main()
