class InputParser:
    """
    Responsibility: Buffers keypad input, handles backspaces,
    and parses the specific '[Box] D [Room] DD' syntax.
    """

    def __init__(self):
        self.buffer = ""
        self.is_complete = False

    def push_key(self, key):
        """
        Ingests a single character from the keypad.
        :param key: char ('0'-'9', 'A'-'D', '*', '#')
        """
        if key == "*":
            # Handle Backspace
            if len(self.buffer) > 0:
                self.buffer = self.buffer[:-1]
                # If we backspaced out of a completed state, reset flag
                self.is_complete = False
        else:
            self.buffer += key
            self._check_termination()

    def _check_termination(self):
        """
        Checks if the buffer ends with the terminator 'DD'.
        """
        if self.buffer.endswith("DD"):
            self.is_complete = True
        else:
            self.is_complete = False

    def get_display_text(self):
        """
        Returns what should be shown on the LCD.
        """
        if not self.buffer:
            return ""
        return self.buffer

    def get_parsed_result(self):
        """
        Parses the buffer if complete.
        Returns:
            None if incomplete or invalid.
            Dictionary {'box_id': int, 'room_code': str} if valid.
        """
        if not self.is_complete:
            return None

        # Remove the 'DD' suffix
        raw = self.buffer[:-2]

        # Syntax Check: Must contain exactly one 'D' separator
        # Edge Case: "D101" (No box) or "1D" (No room)
        if raw.count("D") != 1:
            return None

        parts = raw.split("D")
        box_part = parts[0]
        room_part = parts[1]

        # Validate Box ID (Must be integer, typically 1 or 2)
        if not box_part.isdigit():
            return None

        # Validate Room Code (Must not be empty)
        if len(room_part) == 0:
            return None

        return {"box_id": int(box_part), "room_code": room_part}

    def clear(self):
        """Resets the parser state."""
        self.buffer = ""
        self.is_complete = False
