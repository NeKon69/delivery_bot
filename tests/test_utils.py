import queue


class MockSerial:
    """
    Simulates the SerialDriver for testing.
    Captures commands sent by the Brain so we can inspect them.
    """

    def __init__(self, config=None):
        self.history = []  # Stores sent commands: [("MOV", "FWD", "1000"), ...]
        self.event_queue = queue.Queue()
        self.is_open = True

    def send(self, cmd_type, action, value):
        """
        Instead of writing to USB, just log it.
        """
        command_tuple = (cmd_type, action, str(value))
        self.history.append(command_tuple)

    def get_event(self):
        """
        Simulate the main loop asking for events.
        """
        try:
            return self.event_queue.get_nowait()
        except queue.Empty:
            return None

    def close(self):
        self.is_open = False

    # --- Helper Methods for Tests ---

    def inject_event(self, event_type, event_data):
        """
        Test Helper: Pretend the Arduino sent something (e.g., RFID scan)
        """
        self.event_queue.put((event_type, event_data))

    def get_last_sent(self):
        """
        Returns the most recent command sent by the brain.
        """
        if self.history:
            return self.history[-1]
        return None

    def clear_history(self):
        self.history = []
