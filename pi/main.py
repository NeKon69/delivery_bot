from __future__ import annotations

import argparse
import subprocess
import time
from pathlib import Path

from pi.arduino_client import ArduinoClient
from pi.cabinet_index import CabinetIndex
from pi.card_registry import CardRegistry
from pi.config import load_project_config
from pi.map_loader import load_grid_map
from pi.serial_link import SerialJsonLink, SerialLinkDisconnected
from pi.state_machine import RobotStateMachine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transport robot Raspberry Pi controller"
    )
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Arduino serial port")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload Arduino firmware with PlatformIO before starting",
    )
    parser.add_argument(
        "--pio-env",
        default="megaatmega2560",
        help="PlatformIO environment to upload before starting",
    )
    parser.add_argument(
        "--verbose-rpc",
        action="store_true",
        help="Print every JSON message sent to and received from Arduino",
    )
    parser.add_argument(
        "--verbose-state",
        action="store_true",
        help="Print keypad, routing, RFID, and state-machine debug logs",
    )
    parser.add_argument(
        "--lcd-demo-on-start",
        action="store_true",
        help="Ask Arduino to draw a built-in LCD demo screen after startup",
    )
    return parser.parse_args()


def maybe_upload_firmware(port: str, env_name: str) -> None:
    project_root = Path(__file__).resolve().parent.parent
    command = [
        "pio",
        "run",
        "-e",
        env_name,
        "-t",
        "upload",
        "--upload-port",
        port,
    ]
    print(f"[pi.main] Uploading Arduino firmware via: {' '.join(command)}")
    subprocess.run(command, cwd=project_root, check=True)


def ensure_arduino_connection(
    arduino: ArduinoClient,
    log: callable,
    retry_delay_s: float = 1.0,
) -> None:
    while True:
        try:
            arduino.open()
            return
        except SerialLinkDisconnected as exc:
            log(f"[main] Waiting for Arduino serial port: {exc}")
            time.sleep(retry_delay_s)


def main() -> None:
    args = parse_args()
    config = load_project_config()

    def log(line: str) -> None:
        print(line, flush=True)

    if args.upload:
        maybe_upload_firmware(port=args.port, env_name=args.pio_env)
        time.sleep(2.0)

    link = SerialJsonLink(
        port=args.port,
        baudrate=args.baud,
        logger=log if args.verbose_rpc else None,
    )
    arduino = ArduinoClient(link)
    grid_map = load_grid_map(config.map_config)
    cabinets = CabinetIndex(config.cabinets_config)
    cards = CardRegistry(config.cards_config)
    machine = RobotStateMachine(
        arduino=arduino,
        grid_map=grid_map,
        cabinet_index=cabinets,
        card_registry=cards,
        logger=log if args.verbose_state else None,
    )

    ensure_arduino_connection(arduino, log)
    ready_seen = False
    started = False

    try:
        while True:
            try:
                message = arduino.read_message()
                if message is not None:
                    if (
                        message.get("type") == "event"
                        and message.get("event") == "ready"
                        and not ready_seen
                    ):
                        ready_seen = True
                        log("[main] Arduino ready; sending startup commands")
                        arduino.ping()
                        arduino.get_state()
                        if args.lcd_demo_on_start:
                            arduino.lcd_demo()
                        if not started:
                            machine.start()
                            started = True
                    machine.process_message(message)
            except SerialLinkDisconnected as exc:
                ready_seen = False
                log(f"[main] Serial link lost; reconnecting: {exc}")
                arduino.close()
                ensure_arduino_connection(arduino, log)
                continue
            machine.tick()
            time.sleep(0.01)
    finally:
        arduino.close()


if __name__ == "__main__":
    main()
