import unittest
import sys
import os
import time

brain_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../brain"))
if brain_path not in sys.path:
    sys.path.append(brain_path)

from controller import (
    RobotController,
    STATE_IDLE,
    STATE_LOADING,
    STATE_INPUT,
    STATE_MOVING,
    STATE_DELIVERY,
    STATE_RETURNING,
)
from hal import RobotHAL
from tests.test_utils import MockSerial, MockNavigator, MockSleeper

# --- Constants for Testing ---
ADMIN_UID = "ADMIN_007"
USER_UID = "USER_101"
HACKER_UID = "UNKNOWN_999"
ROOM_CODE_VALID = "101"
ROOM_COORDS_VALID = [5, 5]
HOME_COORDS = [0, 0]


class TestRobotControllerExtended(unittest.TestCase):
    """
    Extensive Integration Tests for the RobotController.
    Covers State Machine transitions, Hardware interactions, and Edge Cases.
    """

    def setUp(self):
        """
        Bootstrap the test environment with high-fidelity mocks.
        """
        # 1. Setup Mock Hardware
        self.mock_serial = MockSerial()
        self.mock_sleeper = MockSleeper()

        # 2. Setup Configuration
        self.config = {
            "calibration": {
                "voltage_scalar": 1.0,
                "time_move_1_grid_ms": 1000,
                "time_turn_90_ms": 500,
            },
            "map_settings": {"home_node": HOME_COORDS},
        }

        self.rooms_db = {
            "101": {
                "owner_name": "Alice",
                "rfid_uid": USER_UID,
                "coords": ROOM_COORDS_VALID,
            },
            "ADMIN": {"owner_name": "SysAdmin", "rfid_uid": ADMIN_UID, "role": "admin"},
            "102": {"owner_name": "Bob", "rfid_uid": "USER_102", "coords": [10, 10]},
        }

        # 3. Setup Dependencies
        self.hal = RobotHAL(self.mock_serial, self.config)
        self.nav = MockNavigator()

        # 4. Instantiate Controller
        # Note: We are injecting dependencies to bypass hardware requirements
        self.bot = RobotController(
            self.mock_serial, self.hal, self.nav, self.rooms_db, self.config
        )

        # Clear startup noise from history (like initial locking/clearing)
        self.mock_serial.clear_history()

    # =========================================================================
    # GROUP 1: Initialization & IDLE State Logic
    # =========================================================================

    def test_initialization_state(self):
        """
        Verify the robot starts in a safe, known state.
        """
        self.assertEqual(self.bot.state, STATE_IDLE)
        self.assertEqual(self.bot.active_box_id, None)
        self.assertEqual(self.bot.target_room_code, None)

    def test_idle_unauthorized_rfid(self):
        """
        Scenario: An unknown RFID tag is scanned while IDLE.
        Expected: Error message on LCD, Remain IDLE, Servo logic untouched.
        """
        self.bot.handle_event("RFD", HACKER_UID)

        # 1. Check State
        self.assertEqual(self.bot.state, STATE_IDLE)

        # 2. Check LCD Feedback
        # Searching for "Unknown ID" or "Access Denied" in the serial history
        history_str = str(self.mock_serial.history)
        self.assertIn("Unknown", history_str, "Should display error for unknown card")

        # 3. Check Security (Servos should NOT have received OPEN command)
        self.mock_serial.assert_no_command_sent(self, "SRV")

    def test_idle_authorized_user_rfid(self):
        """
        Scenario: A valid user scans their badge.
        Expected: Transition to LOADING, Open Box 1 (default), Welcome message.
        """
        self.bot.handle_event("RFD", USER_UID)

        # 1. Check State
        self.assertEqual(self.bot.state, STATE_LOADING)

        # 2. Check Hardware (Box 1 should open)
        # Assuming allocation logic assigns Box 1 to first user
        self.mock_serial.assert_command_sent(self, "SRV", "1", "OPEN")

        # 3. Ensure Box 2 did NOT open
        history_cmds = self.mock_serial.get_history_as_strings()
        self.assertNotIn("SRV:2:OPEN", history_cmds)

    def test_idle_admin_rfid(self):
        """
        Scenario: Admin scans badge.
        Expected: All Boxes Open, State LOADING.
        """
        self.bot.handle_event("RFD", ADMIN_UID)

        self.assertEqual(self.bot.state, STATE_LOADING)

        # Both boxes should open
        self.mock_serial.assert_command_sent(self, "SRV", "1", "OPEN")
        self.mock_serial.assert_command_sent(self, "SRV", "2", "OPEN")

    def test_idle_ignore_keypad(self):
        """
        Scenario: Cat walks on keypad while robot is IDLE.
        Expected: Inputs ignored, no LCD changes regarding input.
        """
        self.mock_serial.clear_history()
        self.bot.handle_event("KEY", "1")
        self.bot.handle_event("KEY", "D")

        # State remains IDLE
        self.assertEqual(self.bot.state, STATE_IDLE)

        # LCD should not show input buffer
        history_str = str(self.mock_serial.history)
        self.assertNotIn("Dest:", history_str)

    # =========================================================================
    # GROUP 2: Loading & Input Phase
    # =========================================================================

    def test_transition_loading_to_input(self):
        """
        Scenario: User puts item in box and closes the lid.
        Expected: Servo Locks, State transitions to INPUT.
        """
        # Prerequisite: Get to LOADING
        self.bot.handle_event("RFD", USER_UID)
        self.assertEqual(self.bot.state, STATE_LOADING)
        self.mock_serial.clear_history()

        # Trigger Limit Switch (Box 1 Closed)
        # Protocol: LMT:BOX_ID:STATE (1=Closed, 0=Open usually, manual says 'is_closed' arg)
        # Assuming event data "1:1" means Box 1, Closed.
        self.bot.handle_event("LMT", "1:1")

        # 1. State Change
        self.assertEqual(self.bot.state, STATE_INPUT)

        # 2. Hardware: Servo should LOCK immediately
        self.mock_serial.assert_command_sent(self, "SRV", "1", "LOCK")

        # 3. UI: Should prompt for destination
        history_str = str(self.mock_serial.history)
        self.assertIn("Enter Dest", history_str)

    def test_input_parsing_valid_flow(self):
        """
        Scenario: User types '1D101DD'.
        Expected: LCD updates on every key, Transitions to MOVING on 'DD'.
        """
        # Set state manually to INPUT to isolate test
        self.bot.state = STATE_INPUT
        self.mock_serial.clear_history()

        # Type '1'
        self.bot.handle_event("KEY", "1")
        # Check LCD echo
        last_lcd = [x for x in self.mock_serial.history if x[0] == "LCD"][-1]
        self.assertIn("1", last_lcd[2])

        # Type Rest: D -> 1 -> 0 -> 1 -> D -> D
        sequence = "D101DD"
        for char in sequence:
            self.bot.handle_event("KEY", char)

        # Should trigger move immediately after last 'D'
        self.assertEqual(
            self.bot.state, STATE_DELIVERY
        )  # Logic jumps MOVING->DELIVERY if nav sync
        self.assertEqual(self.bot.target_room_code, "101")

        # Verify Navigator was called
        self.assertEqual(self.nav.last_destination, ROOM_COORDS_VALID)

    def test_input_parsing_invalid_syntax(self):
        """
        Scenario: User types garbage '9999DD' (Missing 'D' separator).
        Expected: LCD shows Error, State remains INPUT, buffer clears.
        """
        self.bot.state = STATE_INPUT

        # Type invalid sequence
        for char in "9999DD":
            self.bot.handle_event("KEY", char)

        # State should NOT advance
        self.assertEqual(self.bot.state, STATE_INPUT)

        # LCD should show error
        history_str = str(self.mock_serial.history)
        self.assertIn("Invalid", history_str)

    # =========================================================================
    # GROUP 3: Navigation & Mission Execution
    # =========================================================================

    def test_mission_success_path(self):
        """
        Scenario: Valid input provided, Path exists.
        Expected:
            1. State MOVING (transient)
            2. Nav.goto() called
            3. State DELIVERY
            4. LCD updates "Arrived"
        """
        self.bot.state = STATE_INPUT

        # Simulate typing correct sequence for Room 101
        for char in "1D101DD":
            self.bot.handle_event("KEY", char)

        # Since MockNavigator.goto returns True immediately:
        self.assertEqual(self.bot.state, STATE_DELIVERY)

        # Check LCD for Arrival message
        last_cmds = self.mock_serial.get_history_as_strings()
        # Look for the last LCD write
        lcd_updates = [cmd for cmd in last_cmds if "LCD" in cmd]
        self.assertTrue(any("Arrived" in cmd for cmd in lcd_updates))

    def test_delivery_wrong_recipient(self):
        """
        Scenario: Robot at Room 101. 'Bob' (Room 102) tries to open it.
        Expected: Access Denied. Box remains locked.
        """
        # Setup Delivery State
        self.bot.state = STATE_DELIVERY
        self.bot.target_room_code = "101"
        self.bot.active_box_id = 1
        self.mock_serial.clear_history()

        # Bob scans badge
        self.bot.handle_event("RFD", "USER_102")

        # Verify Lock Status
        self.mock_serial.assert_no_command_sent(self, "SRV", "1", "OPEN")

        # Verify LCD
        history_str = str(self.mock_serial.history)
        self.assertIn("Access Denied", history_str)

    def test_delivery_correct_recipient(self):
        """
        Scenario: Robot at Room 101. 'Alice' scans badge.
        Expected: Box opens.
        """
        self.bot.state = STATE_DELIVERY
        self.bot.target_room_code = "101"
        self.bot.active_box_id = 1
        self.mock_serial.clear_history()

        # Alice scans badge
        self.bot.handle_event("RFD", USER_UID)

        # Verify Open
        self.mock_serial.assert_command_sent(self, "SRV", "1", "OPEN")

        # Verify LCD
        history_str = str(self.mock_serial.history)
        self.assertIn("Pls Remove", history_str)

    def test_delivery_completion_return_home(self):
        """
        Scenario: Recipient took item, closed box.
        Expected: Box Locks -> State RETURNING -> Drive Home -> State IDLE.
        """
        self.bot.state = STATE_DELIVERY
        self.bot.target_room_code = "101"
        self.bot.active_box_id = 1

        # Trigger Limit Switch (Box Closed)
        self.bot.handle_event("LMT", "1:1")

        # 1. Immediate Lock
        self.mock_serial.assert_command_sent(self, "SRV", "1", "LOCK")

        # 2. Logic chain:
        #    State -> RETURNING
        #    nav.goto(HOME) (Blocking mock returns True)
        #    State -> IDLE

        # Since MockNavigator is instant, we expect final state IDLE
        self.assertEqual(self.bot.state, STATE_IDLE)

        # Ensure we actually navigated home
        self.assertEqual(self.nav.last_destination, HOME_COORDS)

    # =========================================================================
    # GROUP 5: Stress & Edge Cases
    # =========================================================================

    def test_rapid_fire_events(self):
        """
        Scenario: Serial port spits out garbage or rapid events.
        Expected: Controller processes them sequentially without crashing.
        """
        self.bot.state = STATE_IDLE

        events = [
            ("KEY", "A"),
            ("KEY", "B"),  # Garbage keys
            ("RFD", HACKER_UID),  # Bad RFID
            ("LMT", "1:1"),  # Limit switch noise
            ("RFD", USER_UID),  # Finally a valid one
        ]

        for etype, edata in events:
            self.bot.handle_event(etype, edata)

        # It should eventually process the valid user and enter LOADING
        self.assertEqual(self.bot.state, STATE_LOADING)

    def test_admin_override_at_delivery(self):
        """
        Scenario: Admin finds robot at delivery point. Scans badge.
        Expected: Box should open (Admin override).
        """
        self.bot.state = STATE_DELIVERY
        self.bot.target_room_code = "101"
        self.bot.active_box_id = 1
        self.mock_serial.clear_history()

        self.bot.handle_event("RFD", ADMIN_UID)

        # Box should open
        self.mock_serial.assert_command_sent(self, "SRV", "1", "OPEN")

    def test_box_already_open_logic(self):
        """
        Scenario: Limit switch reports Open (0) when we expect Closed.
        This tests the handling of the 'LMT' event when value is 0.
        """
        self.bot.state = STATE_LOADING
        self.mock_serial.clear_history()

        # LMT:1:0 indicates Box 1 is OPEN.
        # The logic usually waits for CLOSING (1).
        self.bot.handle_event("LMT", "1:0")

        # State should NOT change
        self.assertEqual(self.bot.state, STATE_LOADING)

        # No lock command sent
        self.mock_serial.assert_no_command_sent(self, "SRV", "1", "LOCK")

    def test_return_home_blocked(self):
        """
        Scenario: Robot delivered item, tries to return home, but path blocked.
        Expected: Should probably stop and cry (or stay in RETURNING/Error state).
        """
        self.bot.state = STATE_DELIVERY
        self.bot.target_room_code = "101"
        self.nav.should_fail_next = True  # Fail the trip home

        # Trigger return
        self.bot.handle_event("LMT", "1:1")  # Box closed

        # It transitions to RETURNING, calls goto(Home), fails.
        # Logic dictates: print error, maybe stay in RETURNING?
        # The manual doesn't specify 'Emergency Stop', but let's ensure it doesn't say IDLE.

        # If return fails, it likely didn't reach home, so it shouldn't reset to IDLE.
        self.assertNotEqual(self.bot.state, STATE_IDLE)
        self.assertEqual(self.bot.state, STATE_RETURNING)

        history_str = str(self.mock_serial.history)
        self.assertIn("Home Error", history_str)

    def test_corrupt_config_handling(self):
        """
        Scenario: Room DB is missing the target room.
        Expected: Input phase fails gracefully.
        """
        self.bot.state = STATE_INPUT

        # User types room "999" which is not in self.rooms_db
        for char in "1D999DD":
            self.bot.handle_event("KEY", char)

        # Should stay in INPUT (Invalid Room)
        self.assertEqual(self.bot.state, STATE_INPUT)

        history_str = str(self.mock_serial.history)
        self.assertIn("Invalid Room", history_str)

    def test_navigation_coordinates_integrity(self):
        """
        Scenario: Verify exactly what coordinates are passed to Navigator.
        """
        self.bot.state = STATE_INPUT

        # Room 101 is at [5, 5]
        for char in "1D101DD":
            self.bot.handle_event("KEY", char)

        self.assertEqual(self.nav.last_destination, [5, 5])

        # Check Admin Room (if valid destination) - Assuming logic allows it
        self.bot.state = STATE_INPUT
        # Assuming admin room "ADMIN" can be typed?
        # The Keypad is 0-9,*,D. You can't type "ADMIN".
        # This tests logical limits of the system.
        pass

    def test_run_loop_execution(self):
        """
        Scenario: Test the main run() loop logic lightly.
        We can't run an infinite loop, so we simulate one pass.
        """
        # Inject an event into queue
        self.mock_serial.inject_event("RFD", USER_UID)

        # We cannot call bot.run() because it's infinite.
        # But we can call the internal logic that run() calls:

        # 1. Fetch event
        event = self.mock_serial.get_event()
        self.assertIsNotNone(event)

        # 2. Handle it
        self.bot.handle_event(event[0], event[1])

        # 3. Check result
        self.assertEqual(self.bot.state, STATE_LOADING)


if __name__ == "__main__":
    unittest.main()
