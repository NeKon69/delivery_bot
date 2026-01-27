import json
import sys
import os

from serial_driver import SerialDriver
from hal import RobotHAL
from pathfinder import Pathfinder
from navigator import Navigator
from controller import RobotController

# Constants
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_ROOMS_FILE = "rooms.json"
DEFAULT_MAP_FILE = "map_grid.json"


def load_json_file(path):
    """
    Helper to safely load JSON data.
    Exits the program if the file is missing or invalid.
    """
    if not os.path.exists(path):
        print(f"[BOOT] CRITICAL ERROR: File not found: {path}")
        sys.exit(1)

    try:
        with open(path, "r") as f:
            data = json.load(f)
            print(f"[BOOT] Loaded {path}")
            return data
    except json.JSONDecodeError as e:
        print(f"[BOOT] CRITICAL ERROR: Invalid JSON in {path}")
        print(f"       Reason: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[BOOT] CRITICAL ERROR: Could not read {path}")
        print(f"       Reason: {e}")
        sys.exit(1)


def assemble_system(config_path, rooms_path, map_path):
    """
    Dependency Injection Wiring.
    Instantiates all classes and injects dependencies.

    :return: A fully constructed RobotController instance.
    """
    print("-" * 40)
    print("      DELIVERY ROBOT BOOT SEQUENCE      ")
    print("-" * 40)

    # 1. Load Data
    config = load_json_file(config_path)
    rooms = load_json_file(rooms_path)
    # Map is loaded by Pathfinder directly, but we check existence here?
    # Pathfinder loads it internally, so we just pass path.
    if not os.path.exists(map_path):
        print(f"[BOOT] CRITICAL ERROR: Map file missing: {map_path}")
        sys.exit(1)

    # 2. Initialize Hardware Layer
    # SerialDriver handles the physical connection
    serial = SerialDriver(config)

    # HAL handles the logic/calibration
    hal = RobotHAL(serial, config)

    # 3. Initialize Navigation Layer
    pf = Pathfinder(map_path)

    # Extract Home Position from Config
    home_node = config.get("map_settings", {}).get("home_node", [0, 0])

    # Default facing East (1) as specificied in Navigator
    nav = Navigator(hal, pf, start_pos=home_node, start_facing=1)

    # 4. Initialize Brain (Controller)
    # This ties everything together
    controller = RobotController(serial, hal, nav, rooms, config)

    print("[BOOT] System Assembly Complete.")
    print("-" * 40)
    return controller


if __name__ == "__main__":
    try:
        bot = assemble_system(DEFAULT_CONFIG_FILE, DEFAULT_ROOMS_FILE, DEFAULT_MAP_FILE)

        bot.run()

    except KeyboardInterrupt:
        print("\n[MAIN] Keyboard Interrupt detected.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[MAIN] Unhandled Exception: {e}")
        sys.exit(1)
