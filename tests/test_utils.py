import queue
import unittest
import time
import logging

logging.basicConfig(level=logging.CRITICAL)


class MockSerial:
    """
    A High-Fidelity Simulator for the SerialDriver.

    Capabilities:
    1. Captures all outgoing commands.
    2. Simulates incoming events via a queue.
    3. Simulates hardware failures (Connection Lost).
    4. Provides assertion helpers for clean test code.
    """

    def __init__(self, config=None):
        # The history stores tuples: (timestamp, cmd_type, action, value)
        self.history = []
        self.event_queue = queue.Queue()
        self.is_open = True
        self.config = config or {}

        # Fault Injection Flags
        self.simulate_write_failure = False
        self.simulate_connection_loss = False

    def send(self, cmd_type, action, value):
        """
        Simulates writing to the serial port.
        """
        if not self.is_open:
            # mimic PySerial behavior: writing to closed port raises error or does nothing
            return

        if self.simulate_connection_loss:
            self.is_open = False
            raise OSError("Simulated Hardware Disconnect during write")

        if self.simulate_write_failure:
            # Simulate a glitch where write happens but fails on the other end
            # or raises a timeout
            return

        # Store command with a fake timestamp to verify sequencing
        timestamp = time.time()
        command_tuple = (cmd_type, action, str(value))
        self.history.append(command_tuple)

        # Debug print for local development (optional, usually keep commented)
        # print(f"[MOCK SERIAL] >> {command_tuple}")

    def get_event(self):
        """
        Simulates the main loop asking for events from the read thread.
        """
        if not self.is_open:
            return None

        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return None

    def close(self):
        """
        Simulates closing the connection.
        """
        self.is_open = False
        # Optional: Add a marker in history that close was called
        self.history.append(("SYS", "CLOSE", "0"))

    # --- Test Helper Methods (Not part of real SerialDriver API) ---

    def inject_event(self, event_type, event_data):
        """
        Test Helper: Pushes a mock event (like RFID scan) into the queue
        that the Controller will 'read'.
        """
        self.event_queue.put((event_type, event_data))

    def get_last_sent(self):
        """
        Returns the most recent command tuple sent by the brain.
        Format: (TYPE, ACTION, VALUE)
        """
        if self.history:
            return self.history[-1]
        return None

    def get_history_as_strings(self):
        """
        Returns history as a list of "TYPE:ACTION:VALUE" strings
        for easier string matching in tests.
        """
        return [f"{h[0]}:{h[1]}:{h[2]}" for h in self.history]

    def clear_history(self):
        """Wipes the command history log."""
        self.history = []

    def assert_command_sent(self, test_case, cmd_type, action, value=None):
        """
        Custom assertion logic.
        Checks if a specific command exists in the history.
        If value is None, it ignores the value field during check.
        """
        found = False
        for cmd in self.history:
            t, a, v = cmd
            if t == cmd_type and a == action:
                if value is None or v == str(value):
                    found = True
                    break

        test_case.assertTrue(
            found,
            f"Expected command {cmd_type}:{action}:{value} not found in history.\nHistory: {self.history}",
        )

    def assert_no_command_sent(self, test_case, cmd_type, action=None, value=None):
        """
        Ensures a specific command (or specific action/value) was NOT sent.
        """
        found = False
        for cmd in self.history:
            t, a, v = cmd
            if t == cmd_type:
                # If action is specified, only match if it matches
                if action is None or a == action:
                    # If value is specified, only match if it matches
                    if value is None or v == str(value):
                        found = True
                        break

        test_case.assertFalse(
            found,
            f"Command {cmd_type}:{action}:{value} was sent but should not have been.",
        )


class MockNavigator:
    """
    Simulates the Navigator class.
    Allows controlling whether navigation succeeds or fails.
    """

    def __init__(self):
        self.last_destination = None
        self.history = []

        # Configuration to force failures
        self.should_fail_next = False
        self.fail_on_coords = []  # List of coords that trigger failure

    def goto(self, coords):
        """
        Simulates the blocking navigation call.
        """
        self.last_destination = coords
        self.history.append(coords)

        # Check for forced failure scenarios
        if self.should_fail_next:
            self.should_fail_next = False
            return False

        if coords in self.fail_on_coords:
            return False

        # Default success
        return True

    def get_position(self):
        """Mock position return"""
        return [0, 0]


class MockSleeper:
    """
    A utility to replace time.sleep() during tests.
    It records how long the code *wanted* to sleep without actually waiting.
    """

    def __init__(self):
        self.total_slept = 0.0
        self.sleep_calls = []

    def sleep(self, duration):
        """Replacement function for time.sleep"""
        self.total_slept += duration
        self.sleep_calls.append(duration)

    def reset(self):
        self.total_slept = 0.0
        self.sleep_calls = []


class IntegrationScenarioBuilder:
    """
    Helper class to build complex event chains for Controller tests.
    """

    def __init__(self, mock_serial):
        self.serial = mock_serial

    def sequence_login_and_load(self, user_id):
        self.serial.inject_event("RFD", user_id)
        # Wait for potential processing?
        # In a real async test we might need sleeps, here strictly synchronous

    def sequence_input_destination(self, room_code):
        # 1. Start Input
        self.serial.inject_event("LMT", "1:1")  # Box 1 Closed
        # 2. Type keys
        for char in f"1D{room_code}DD":
            self.serial.inject_event("KEY", char)
