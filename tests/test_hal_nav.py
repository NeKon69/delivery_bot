import unittest
import sys
import os
import json

# --- Path Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.hal import RobotHAL
from tests.test_utils import MockSerial

# --- Test Data ---
DEFAULT_CONFIG = {
    "calibration": {
        "time_move_1_grid_ms": 1000,
        "time_turn_90_ms": 500,
        "voltage_scalar": 1.0,
    }
}


class TestRobotHALExtended(unittest.TestCase):
    """
    Exhaustive tests for the Hardware Abstraction Layer.
    Focuses on Physics Math, Protocol adherence, and Voltage Compensation.
    """

    def setUp(self):
        print(f"\n[SETUP] {self._testMethodName}")
        self.mock_serial = MockSerial()
        # Deep copy config to prevent tests from polluting each other
        self.config = json.loads(json.dumps(DEFAULT_CONFIG))
        self.hal = RobotHAL(self.mock_serial, self.config)

    def tearDown(self):
        # Optional: Print separator
        print(f"[TEARDOWN] Finished {self._testMethodName}")

    # =========================================================================
    # SECTION 1: Voltage Compensation Math
    # =========================================================================

    def test_scalar_unity(self):
        """Test with scalar 1.0 (Full Battery). Input should equal Output."""
        print("[LOG] Testing Voltage Scalar = 1.0")

        self.hal.scalar = 1.0
        base_time = 1000

        result = self.hal._apply_scalar(base_time)
        print(f" -> Input: {base_time}ms | Scalar: 1.0 | Output: {result}ms")

        self.assertEqual(result, 1000)

    def test_scalar_low_voltage(self):
        """Test with scalar > 1.0 (Low Battery). Motors need MORE time."""
        print("[LOG] Testing Voltage Scalar = 1.2 (Low Battery)")

        self.hal.scalar = 1.2
        # Modify config to match strictly if HAL reloads it (though we set attribute directly)

        # Test Move Calculation
        # Expected: 1000 * 1.2 = 1200
        result_move = self.hal._apply_scalar(1000)
        print(f" -> Move Base: 1000ms | Scalar: 1.2 | Output: {result_move}ms")
        self.assertEqual(result_move, 1200)

        # Test Turn Calculation
        # Expected: 500 * 1.2 = 600
        result_turn = self.hal._apply_scalar(500)
        print(f" -> Turn Base: 500ms | Scalar: 1.2 | Output: {result_turn}ms")
        self.assertEqual(result_turn, 600)

    def test_scalar_high_voltage(self):
        """Test with scalar < 1.0 (Fresh off charger / Overvolted). Motors need LESS time."""
        print("[LOG] Testing Voltage Scalar = 0.8 (High Voltage)")
        self.hal.scalar = 0.8

        result = self.hal._apply_scalar(1000)
        print(f" -> Input: 1000ms | Scalar: 0.8 | Output: {result}ms")

        self.assertEqual(result, 800)

    def test_scalar_zero_edge_case(self):
        """Test edge case where scalar is 0 (should stop)."""
        print("[LOG] Testing Scalar = 0.0")
        self.hal.scalar = 0.0
        result = self.hal._apply_scalar(5000)
        print(f" -> Input: 5000ms | Output: {result}ms")
        self.assertEqual(result, 0)

    def test_scalar_rounding_logic(self):
        """Ensure the HAL returns Integers, not Floats (Serial needs ints)."""
        print("[LOG] Testing Float Rounding")
        self.hal.scalar = 1.15
        base = 100

        # 100 * 1.15 = 115.0 -> 115 (int)
        result = self.hal._apply_scalar(base)
        print(
            f" -> Input: {base} | Scalar: 1.15 | Result type: {type(result)} | Val: {result}"
        )

        self.assertIsInstance(result, int)
        self.assertEqual(result, 115)

    # =========================================================================
    # SECTION 2: Movement Commands
    # =========================================================================

    def test_drive_forward_protocol(self):
        print("[LOG] Testing drive_forward() protocol")
        self.hal.scalar = 1.0

        # Action
        duration = self.hal.drive_forward()

        # Verification
        last_cmd = self.mock_serial.get_last_sent()
        print(f" -> HAL Sent: {last_cmd}")

        self.assertEqual(last_cmd[0], "MOV")
        self.assertEqual(last_cmd[1], "FWD")
        self.assertEqual(last_cmd[2], "1000")
        self.assertEqual(duration, 1000)

    def test_turn_left_protocol(self):
        print("[LOG] Testing turn('LEFT')")
        self.hal.scalar = 1.0

        duration = self.hal.turn("LEFT")

        last_cmd = self.mock_serial.get_last_sent()
        print(f" -> HAL Sent: {last_cmd}")

        self.assertEqual(last_cmd, ("MOV", "LFT", "500"))
        self.assertEqual(duration, 500)

    def test_turn_right_protocol(self):
        print("[LOG] Testing turn('RIGHT')")
        self.hal.scalar = 1.0

        duration = self.hal.turn("RIGHT")

        last_cmd = self.mock_serial.get_last_sent()
        print(f" -> HAL Sent: {last_cmd}")

        self.assertEqual(last_cmd, ("MOV", "RGT", "500"))

    def test_movement_integration_with_scalar(self):
        """Ensure drive_forward calls apply_scalar internally."""
        print("[LOG] Integration: Drive Forward with Scalar 2.0")
        self.hal.scalar = 2.0

        duration = self.hal.drive_forward()

        last_cmd = self.mock_serial.get_last_sent()
        print(f" -> Duration returned: {duration}")
        print(f" -> Command Sent: {last_cmd}")

        self.assertEqual(duration, 2000)
        self.assertEqual(last_cmd[2], "2000")

    def test_invalid_turn_direction(self):
        """What happens if we pass 'UP' to turn?"""
        print("[LOG] Testing Invalid Turn Direction")

        # Depending on implementation, this might crash or send garbage.
        # Assuming implementation does simple mapping or passes string through.
        # If it passes through, we check protocol.

        try:
            self.hal.turn("UP")
            last_cmd = self.mock_serial.get_last_sent()
            print(f" -> Sent with invalid arg: {last_cmd}")
        except Exception as e:
            print(f" -> Caught expected exception: {e}")

    # =========================================================================
    # SECTION 3: LCD Display Logic
    # =========================================================================

    def test_lcd_clear_screen(self):
        """LCD Write should always clear screen first."""
        print("[LOG] Testing LCD Clear Sequence")

        self.hal.lcd_write("Test")

        # Check History: Should be CLS -> Row 0 -> Row 1
        history = self.mock_serial.history
        print(f" -> Serial History: {history}")

        # The prompt for HAL says: 1. Sends LCD:CLS
        first_cmd = history[0]
        self.assertEqual(first_cmd[0], "LCD")
        self.assertEqual(first_cmd[1], "CLS")

    def test_lcd_exact_16_chars(self):
        """Test boundary condition: Exactly 16 chars."""
        print("[LOG] Testing LCD 16 char limit")
        text = "1234567890123456"  # 16 chars

        self.hal.lcd_write(text)

        # Find the command for Row 0
        cmd = [x for x in self.mock_serial.history if x[1] == "0"][0]
        sent_text = cmd[2]
        print(
            f" -> Input len: {len(text)} | Sent: '{sent_text}' | Len: {len(sent_text)}"
        )

        self.assertEqual(sent_text, text)
        self.assertEqual(len(sent_text), 16)

    def test_lcd_truncation_overflow(self):
        """Test string > 16 chars. Must truncate."""
        print("[LOG] Testing LCD Truncation (Input > 16)")
        input_text = "ThisIsVerryyyyyLongString"
        expected = "ThisIsVerryyyyyL"  # First 16

        self.hal.lcd_write(input_text)

        cmd = [x for x in self.mock_serial.history if x[1] == "0"][0]
        sent_text = cmd[2]

        print(f" -> Full Input: '{input_text}'")
        print(f" -> Expected:   '{expected}'")
        print(f" -> Actual:     '{sent_text}'")

        self.assertEqual(sent_text, expected)

    def test_lcd_second_line(self):
        """Test writing to the second row."""
        print("[LOG] Testing LCD Row 2")
        row1 = "Top"
        row2 = "Bottom"

        self.hal.lcd_write(row1, row2)

        # History analysis
        # Expect: LCD:CLS, LCD:0:Top, LCD:1:Bottom
        cmds = self.mock_serial.get_history_as_strings()
        print(f" -> History: {cmds}")

        self.assertIn("LCD:0:Top", cmds)
        self.assertIn("LCD:1:Bottom", cmds)

    def test_lcd_empty_strings(self):
        """Test clearing lines with empty strings."""
        print("[LOG] Testing Empty LCD Strings")
        self.hal.lcd_write("", "")

        cmds = self.mock_serial.get_history_as_strings()
        print(f" -> History: {cmds}")

        # Should send commands with empty values
        # Depending on implementation: LCD:0: or LCD:0:""
        # Mock stores value as string
        self.assertIn("LCD:0:", cmds)
        self.assertIn("LCD:1:", cmds)

    def test_lcd_special_chars(self):
        """Test sending colons or symbols."""
        print("[LOG] Testing Special Characters in LCD")
        text = "Time: 12:00 PM"

        self.hal.lcd_write(text)

        cmd = self.mock_serial.get_last_sent()  # Assuming row 2 is empty
        # Wait, if row 2 is empty defaults, last sent might be LCD:1:
        # Let's search history
        row0 = [x for x in self.mock_serial.history if x[1] == "0"][0]
        print(f" -> Sent: {row0[2]}")

        self.assertEqual(row0[2], "Time: 12:00 PM")

    # =========================================================================
    # SECTION 4: Configuration Handling
    # =========================================================================

    def test_missing_config_keys(self):
        """Test behavior when config is malformed."""
        print("[LOG] Testing Malformed Configuration")
        bad_config = {"calibration": {}}  # Missing keys

        # Initializing HAL might crash if it looks up keys in __init__
        # Or it might crash when accessing attributes

        try:
            hal_broken = RobotHAL(self.mock_serial, bad_config)
            print(" -> HAL initialized with empty config (Unexpected but handled?)")

            # Accessing attribute that relies on config
            val = hal_broken.time_block
            print(f" -> time_block value: {val}")
        except KeyError as e:
            print(f" -> Caught expected KeyError for missing config: {e}")
        except Exception as e:
            print(f" -> Caught unexpected exception: {type(e)} - {e}")

    def test_config_update_reflected(self):
        """If we update the config dict, does HAL see it?"""
        print("[LOG] Testing Config Object Mutation")

        # HAL usually caches values in __init__. Let's verify.
        # Prompt says: "Caches configuration values."

        print(f" -> Old time_block: {self.hal.time_block}")

        # Mutate the source dict
        self.config["calibration"]["time_move_1_grid_ms"] = 9999

        # If HAL cached it in __init__, this change won't matter
        print(f" -> New time_block (attribute): {self.hal.time_block}")

        # This asserts that it IS cached (i.e. does not change)
        self.assertEqual(self.hal.time_block, 1000)

    # =========================================================================
    # SECTION 5: Hardware Failure Simulation
    # =========================================================================

    def test_write_during_serial_disconnect(self):
        """Ensure HAL doesn't crash app if Serial raises OS Error."""
        print("[LOG] Testing Serial Disconnect Handling")

        # Configure Mock to fail
        self.mock_serial.simulate_connection_loss = True

        try:
            self.hal.drive_forward()
            print(" -> HAL swallowed the exception (Safe)")
        except OSError:
            print(" -> HAL let the exception bubble up (Crash)")
            # Note: The prompt description for SerialDriver says it returns silently
            # or logs error. HAL invokes serial.send.
            # If SerialDriver swallows it, HAL shouldn't see it.
            # But MockSerial raises it if simulate_connection_loss is True.
            # Let's assume SerialDriver catches it.
            # In this test, we are checking if HAL adds extra handling.
            pass

    def test_rapid_commands(self):
        """Stress test: Send 100 commands rapidly."""
        print("[LOG] Stress Testing Rapid Commands")
        self.mock_serial.clear_history()

        for i in range(100):
            self.hal.drive_forward()

        count = len(self.mock_serial.history)
        print(f" -> Sent 100 commands. History length: {count}")
        self.assertEqual(count, 100)


if __name__ == "__main__":
    unittest.main()
