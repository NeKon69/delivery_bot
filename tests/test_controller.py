import unittest
import sys
import os

# Path hack to include 'brain' directory
brain_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../brain"))
if brain_path not in sys.path:
    sys.path.append(brain_path)

from controller import (
    RobotController,
    STATE_IDLE,
    STATE_LOADING,
    STATE_INPUT,
    STATE_DELIVERY,
)
from hal import RobotHAL
from tests.test_utils import MockSerial

# --- Mocks ---


class MockNavigator:
    def __init__(self):
        self.last_destination = None

    def goto(self, coords):
        self.last_destination = coords
        return True


# --- Integration Test ---


class TestRobotController(unittest.TestCase):

    def setUp(self):
        self.mock_serial = MockSerial()
        self.config = {
            "calibration": {"voltage_scalar": 1.0},
            "map_settings": {"home_node": [0, 0]},
        }
        self.rooms_db = {
            "101": {"owner_name": "Alice", "rfid_uid": "USER_101", "coords": [5, 5]},
            "ADMIN": {"owner_name": "Admin", "rfid_uid": "ADMIN_KEY", "role": "admin"},
        }
        self.hal = RobotHAL(self.mock_serial, self.config)
        self.nav = MockNavigator()
        self.bot = RobotController(
            self.mock_serial, self.hal, self.nav, self.rooms_db, self.config
        )

    def test_initial_state(self):
        self.assertEqual(self.bot.state, STATE_IDLE)
        found_lock = any(
            "SRV:1:LOCK" in f"{cmd[0]}:{cmd[1]}:{cmd[2]}"
            for cmd in self.mock_serial.history
        )
        self.assertTrue(found_lock)

    def test_auth_success(self):
        self.bot.handle_event("RFD", "ADMIN_KEY")
        self.assertEqual(self.bot.state, STATE_LOADING)
        cmds = [c[1] + ":" + c[2] for c in self.mock_serial.history]
        self.assertIn("1:OPEN", cmds)
        self.assertIn("2:OPEN", cmds)

    def test_auth_fail(self):
        """Invalid RFID should deny access and stay IDLE"""
        self.bot.handle_event("RFD", "UNKNOWN_CARD")
        self.assertEqual(self.bot.state, STATE_IDLE)

        # --- FIX: Scan FULL history, not just the last element ---
        # The controller writes "Unknown ID", waits, then writes "Scan ID to Load".
        # We must ensure "Unknown ID" appeared at some point.

        # Extract all text sent to LCD rows
        lcd_texts = [c[2] for c in self.mock_serial.history if c[0] == "LCD"]

        # Check if the error message is in ANY of the sent texts
        error_found = any("Unknown ID" in text for text in lcd_texts)
        self.assertTrue(error_found, f"Error message not found in history: {lcd_texts}")

    def test_full_workflow(self):
        # 1. IDLE -> LOADING
        self.bot.handle_event("RFD", "USER_101")
        self.assertEqual(self.bot.state, STATE_LOADING)

        # 2. LOADING -> INPUT
        self.bot.handle_event("LMT", "1:1")
        self.assertEqual(self.bot.state, STATE_INPUT)

        # 3. INPUT -> DELIVERY
        for char in "1D101DD":
            self.bot.handle_event("KEY", char)

        self.assertEqual(self.bot.state, STATE_DELIVERY)
        self.assertEqual(self.bot.target_room_code, "101")
        self.assertEqual(self.nav.last_destination, [5, 5])

    def test_delivery_verification(self):
        self.bot.state = STATE_DELIVERY
        self.bot.target_room_code = "101"
        self.bot.active_box_id = 1

        # Wrong Card
        self.mock_serial.clear_history()
        self.bot.handle_event("RFD", "RANDOM_HACKER")
        servo_cmds = [c for c in self.mock_serial.history if c[0] == "SRV"]
        self.assertEqual(len(servo_cmds), 0)

        # Correct Card
        self.bot.handle_event("RFD", "USER_101")
        last_cmd = self.mock_serial.get_last_sent()
        self.assertEqual(last_cmd, ("SRV", "1", "OPEN"))


if __name__ == "__main__":
    unittest.main()
