#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time

try:
    import serial
except ImportError:
    print("Missing dependency: pyserial")
    print("Install with: pip install pyserial")
    sys.exit(1)


def normalize_uid(raw: str) -> str:
    return "".join(ch for ch in raw.upper() if ch in "0123456789ABCDEF")


def load_db(path: str):
    if not os.path.exists(path):
        return {"cards": []}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if "cards" not in data or not isinstance(data["cards"], list):
        data = {"cards": []}
    return data


def save_db(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Capture RC522 cards into cards.json")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port (default: /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("--count", type=int, default=3, help="How many NEW cards to add (default: 3)")
    parser.add_argument("--file", default="cards.json", help="Output JSON file (default: cards.json)")
    args = parser.parse_args()

    db = load_db(args.file)
    cards = db["cards"]
    existing = {str(item.get("pass", "")).upper(): item.get("id") for item in cards}
    next_id = max([int(item.get("id", 0)) for item in cards], default=0) + 1

    print(f"Opening serial: {args.port} @ {args.baud}")
    print(f"Need {args.count} new unique card(s).")
    print("Tap cards now...")

    added = 0
    with serial.Serial(args.port, args.baud, timeout=1) as ser:
        time.sleep(2.0)
        while added < args.count:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                continue
            if not line.startswith("CARD_UID:"):
                continue

            uid = normalize_uid(line.split(":", 1)[1])
            if not uid:
                continue

            if uid in existing:
                print(f"Duplicate ignored: {uid} (id={existing[uid]})")
                continue

            record = {"id": next_id, "pass": uid}
            cards.append(record)
            existing[uid] = next_id
            print(f"Added: {record}")
            next_id += 1
            added += 1

            save_db(args.file, db)

    print(f"Done. Saved to {args.file}")


if __name__ == "__main__":
    main()
