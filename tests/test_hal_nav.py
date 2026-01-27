import unittest
import sys
import os

# Path Setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.hal import RobotHAL
from brain.navigator import Navigator
from tests.test_utils import MockSerial


# --- Mock Objects ---
class MockPathfinder:
    """Simulates A* so we can test Navigator logic in isolation."""

    def __init__(self, fixed_path):
        self.fixed_path = fixed_path  # e.g. [(0,0), (1,0)]

    def find_path(self, start, end):
        return self.fixed_path


# --- Tests ---


class TestHAL(unittest.TestCase):
    def setUp(self):
        self.mock_serial = MockSerial()
        self.config = {
            "calibration": {
                "time_move_1_grid_ms": 1000,
                "time_turn_90_ms": 500,
                "voltage_scalar": 1.5,  # Huge scalar to verify math
            }
        }
        self.hal = RobotHAL(self.mock_serial, self.config)

    def test_voltage_scaling_math(self):
        """
        Verify that base_time * scalar = output_time.
        1000ms * 1.5 = 1500ms.
        """
        duration = self.hal.drive_forward()

        # Check return value
        self.assertEqual(duration, 1500)

        # Check Serial Command
        last_cmd = self.mock_serial.get_last_sent()
        # Expecting: ("MOV", "FWD", "1500")
        self.assertEqual(last_cmd, ("MOV", "FWD", "1500"))

    def test_turn_scaling(self):
        """Verify turns are also scaled"""
        # 500ms * 1.5 = 750ms
        duration = self.hal.turn("LEFT")
        self.assertEqual(duration, 750)
        self.assertEqual(self.mock_serial.get_last_sent(), ("MOV", "LFT", "750"))

    def test_lcd_truncation(self):
        """
        LCD is 16x2. Sending >16 chars breaks layout/protocol.
        HAL must truncate.
        """
        long_string = "ThisIsWayTooLongForTheScreen"
        self.hal.lcd_write(long_string)

        # history will contain [CLS, Row0, Row1]
        # We want the 2nd command (Row 0 write)
        # Format: (LCD, 0, Text)
        lcd_cmd = self.mock_serial.history[1]
        sent_text = lcd_cmd[2]

        self.assertEqual(len(sent_text), 16)
        self.assertEqual(sent_text, "ThisIsWayTooLong")


class TestNavigator(unittest.TestCase):
    def setUp(self):
        self.mock_serial = MockSerial()
        # Normal Scalar for nav tests
        config = {"calibration": {"time_move_1_grid_ms": 100, "voltage_scalar": 1.0}}
        self.hal = RobotHAL(self.mock_serial, config)

        # Mock Pathfinder: Path is (0,0) -> (1,0) (One step East)
        self.pf = MockPathfinder([(0, 0), (1, 0)])

        # Inject dummy sleeper to skip delays
        self.dummy_sleep = lambda x: None

    def test_move_east_no_turn(self):
        """
        Start: (0,0) Facing East (1).
        Target: (1,0).
        Action: Forward 1.
        """
        # start_pos=(0,0), start_facing=1 (East)
        nav = Navigator(self.hal, self.pf, (0, 0), 1, sleeper_func=self.dummy_sleep)

        success = nav.goto((1, 0))
        self.assertTrue(success)

        # Final Position should be updated
        self.assertEqual(nav.get_position(), (1, 0))
        self.assertEqual(nav.facing, 1)  # Still East

        # Serial History: Should contain 1 FWD command
        # History: [MOV:FWD:100]
        cmd = self.mock_serial.get_last_sent()
        self.assertEqual(cmd[1], "FWD")

    def test_move_north_with_turn(self):
        """
        Start: (0,0) Facing East (1).
        Target: (0,-1) (North).
        Path: [(0,0), (0,-1)]
        Action: Turn Left (to N), Forward 1.
        """
        self.pf.fixed_path = [(0, 0), (0, -1)]
        nav = Navigator(self.hal, self.pf, (0, 0), 1, sleeper_func=self.dummy_sleep)

        nav.goto((0, -1))

        # Final State
        self.assertEqual(nav.get_position(), (0, -1))
        self.assertEqual(nav.facing, 0)  # North

        # Serial History Check
        # 1. Turn Left (East -> North)
        # 2. Move Fwd
        history = self.mock_serial.history
        self.assertEqual(history[0][1], "LFT")
        self.assertEqual(history[1][1], "FWD")

    def test_u_turn_logic(self):
        """
        Start: (0,0) Facing North (0).
        Target: (0,1) (South).
        Path: [(0,0), (0,1)]
        Action: Turn Right, Turn Right (to S), Forward.
        """
        self.pf.fixed_path = [(0, 0), (0, 1)]
        nav = Navigator(self.hal, self.pf, (0, 0), 0, sleeper_func=self.dummy_sleep)

        nav.goto((0, 1))

        self.assertEqual(nav.facing, 2)  # South

        # Expect: RGT, RGT, FWD
        cmds = [cmd[1] for cmd in self.mock_serial.history]
        self.assertEqual(cmds, ["RGT", "RGT", "FWD"])


if __name__ == "__main__":
    unittest.main()
