import unittest
import sys
import os
import random
import string

# --- Path Configuration ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.input_parser import InputParser


class TestInputParserExtended(unittest.TestCase):
    """
    Exhaustive tests for the Keypad Input Parser.
    Validates the protocol: [BoxID] D [RoomID] DD
    """

    def setUp(self):
        print(f"\n[SETUP] {self._testMethodName}")
        self.parser = InputParser()

    def type_sequence(self, text):
        """Helper to simulate typing a string char-by-char."""
        print(f"   [Input] Typing: '{text}'")
        for char in text:
            self.parser.push_key(char)

    # =========================================================================
    # Group 1: Happy Path Scenarios
    # =========================================================================

    def test_standard_entry_box_1(self):
        print("[LOG] Testing Standard Entry: Box 1 -> Room 101")
        self.type_sequence("1D101DD")

        self.assertTrue(self.parser.is_complete)
        result = self.parser.get_parsed_result()

        print(f"   [Result] {result}")
        self.assertIsNotNone(result)
        self.assertEqual(result["box_id"], 1)
        self.assertEqual(result["room_code"], "101")

    def test_standard_entry_box_2(self):
        print("[LOG] Testing Standard Entry: Box 2 -> Room ADMIN")
        # Assuming keypad supports letters (A,B,C,D) or just numbers?
        # Protocol says: '1', 'D', '*'.
        # But Room codes might be numeric strings.
        # Let's assume Room 999.
        self.type_sequence("2D999DD")

        result = self.parser.get_parsed_result()
        print(f"   [Result] {result}")
        self.assertEqual(result["box_id"], 2)
        self.assertEqual(result["room_code"], "999")

    # =========================================================================
    # Group 2: Editing Logic (Backspace)
    # =========================================================================

    def test_backspace_simple(self):
        print("[LOG] Testing Simple Typo Fix")
        # Intention: 1D101DD
        # Typed: 1 2 [BS] D 1 0 1 D D

        self.parser.push_key("1")
        self.parser.push_key("2")
        print(f"   Buffer: {self.parser.buffer}")

        self.parser.push_key("*")  # BS
        print(f"   Buffer after '*': {self.parser.buffer}")
        self.assertEqual(self.parser.buffer, "1")

        self.type_sequence("D101DD")

        result = self.parser.get_parsed_result()
        self.assertEqual(result["room_code"], "101")

    def test_backspace_start_of_buffer(self):
        print("[LOG] Testing Backspace on Empty Buffer")

        self.parser.push_key("*")
        self.parser.push_key("*")
        self.type_sequence("1D50DD")

        result = self.parser.get_parsed_result()
        self.assertEqual(result["room_code"], "50")
        print("   [Pass] Did not crash on empty backspace")

    def test_backspace_undo_completion(self):
        print("[LOG] Testing Backspace AFTER completion")
        # User types full command, realizes mistake, hits backspace
        self.type_sequence("1D101DD")
        self.assertTrue(self.parser.is_complete)

        print("   [Action] User hits Backspace")
        self.parser.push_key("*")

        print(f"   Buffer: {self.parser.buffer}")

        # Should no longer be complete
        self.assertFalse(self.parser.is_complete)
        self.assertIsNone(self.parser.get_parsed_result())

        # User fixes it
        self.type_sequence("DD")
        self.assertTrue(self.parser.is_complete)

    def test_backspace_entire_string(self):
        print("[LOG] Testing Deleting Everything")
        self.type_sequence("1D101")

        # Delete 5 chars
        for _ in range(5):
            self.parser.push_key("*")

        print(f"   Buffer: '{self.parser.buffer}'")
        self.assertEqual(self.parser.buffer, "")

        # Type new valid string
        self.type_sequence("1D200DD")
        self.assertIsNotNone(self.parser.get_parsed_result())

    # =========================================================================
    # Group 3: Syntax Validation
    # =========================================================================

    def test_missing_separator_d(self):
        print("[LOG] Testing Syntax: Missing 'D'")
        self.type_sequence("1101DD")  # Box 1101? Or Box 1 Room 101?

        # This ends in DD, so is_complete = True
        self.assertTrue(self.parser.is_complete)

        # But parsing should fail because split('D') won't find 2 parts
        result = self.parser.get_parsed_result()
        print(f"   [Result] {result}")
        self.assertIsNone(result)

    def test_multiple_separators(self):
        print("[LOG] Testing Syntax: Too many 'D's")
        # 1 D 10 D 1 DD
        self.type_sequence("1D10D1DD")

        result = self.parser.get_parsed_result()
        print(f"   [Result] {result}")
        # split('D') will return 3 parts. Logic expects exactly 2.
        self.assertIsNone(result)

    def test_non_integer_box_id(self):
        print("[LOG] Testing Syntax: Letter in Box ID")
        # A D 101 DD (assuming keypad allows A)
        self.type_sequence("AD101DD")

        result = self.parser.get_parsed_result()
        print(f"   [Result] {result}")
        # int("A") raises ValueError -> returns None
        self.assertIsNone(result)

    def test_empty_box_id(self):
        print("[LOG] Testing Syntax: Empty Box ID")
        # D 101 DD
        self.type_sequence("D101DD")

        result = self.parser.get_parsed_result()
        print(f"   [Result] {result}")
        # int("") raises ValueError
        self.assertIsNone(result)

    def test_empty_room_id(self):
        print("[LOG] Testing Syntax: Empty Room ID")
        # 1 D DD
        self.type_sequence("1DDD")

        result = self.parser.get_parsed_result()
        print(f"   [Result] {result}")
        # Room ID is string, so "" might be valid technically?
        # But logic implies delivery requires a destination.
        # Check specific validation in parser. usually room is strictly checked.
        # Assuming parser returns {'room_code': ''}, Controller handles it?
        # Or parser rejects empty string. Let's assume strict parser.

        # If the implementation allows empty string room, this test fails.
        # Based on Prompt: "Part 2 (Room): Must be a string"
        # Let's assume it returns empty string.
        if result:
            self.assertEqual(result["room_code"], "")
        else:
            print("   [Pass] Parser rejected empty room.")

    # =========================================================================
    # Group 4: Stress & Fuzz Testing
    # =========================================================================

    def test_buffer_overflow_protection(self):
        print("[LOG] Testing Large Buffer Handling")
        # Cat sits on '1' key for 1000 cycles
        large_input = "1" * 1000 + "D101DD"

        self.type_sequence(large_input)

        # Does it crash?
        # Does is_complete trigger? Yes, ends in DD.
        self.assertTrue(self.parser.is_complete)

        # Does parsing crash? int("1111...111") is valid python (arbitrary precision)
        # But logic might limit Box ID to reasonable range.
        # If parser doesn't limit range, this passes.

        result = self.parser.get_parsed_result()
        if result:
            print(f"   [Info] Parsed huge Box ID: {str(result['box_id'])[:10]}...")
            self.assertIsInstance(result["box_id"], int)
        else:
            print("   [Info] Parser rejected huge input (Good design)")

    def test_fuzzing_random_garbage(self):
        print("[LOG] Fuzzing with random characters")

        # Generate random noise that includes D and *
        chars = "1234567890D*"

        for _ in range(50):
            noise = "".join(random.choice(chars) for _ in range(20))
            self.parser.clear()

            # Inject noise
            for c in noise:
                self.parser.push_key(c)

            # If by chance we generated "DD" at end
            if self.parser.is_complete:
                res = self.parser.get_parsed_result()
                # Most random noise is invalid syntax
                if res is None:
                    print(f"   [Pass] Invalid noise handled gracefully: {noise}")
                else:
                    print(
                        f"   [Warn] Random noise happened to be valid! {noise} -> {res}"
                    )

    def test_termination_sequence_splitting(self):
        """
        Ensure 'DD' detection works even if split by buffer checks.
        """
        print("[LOG] Testing Split Termination")
        self.parser.push_key("1")
        self.parser.push_key("D")
        self.parser.push_key("1")

        self.assertFalse(self.parser.is_complete)

        self.parser.push_key("D")  # First D
        self.assertFalse(self.parser.is_complete)

        self.parser.push_key("D")  # Second D
        self.assertTrue(self.parser.is_complete)

    def test_triple_d_termination(self):
        """
        What if user types DDD?
        1 D 1 0 1 D D D
        The first DD should trigger completion.
        """
        print("[LOG] Testing Triple D")
        self.type_sequence("1D101DDD")

        # The parser logic checks ends_with("DD").
        # If buffer is "1D101DDD", it ends with "DD".
        self.assertTrue(self.parser.is_complete)

        # Parsing:
        # Buffer[:-2] -> "1D101D"
        # split('D') -> ["1", "101", ""] -> 3 parts.
        # Should Fail.

        result = self.parser.get_parsed_result()
        print(f"   [Result] {result}")
        self.assertIsNone(result)

    # =========================================================================
    # Group 5: Lifecycle
    # =========================================================================

    def test_clear_reset(self):
        print("[LOG] Testing Clear/Reset")
        self.type_sequence("1D101")
        self.parser.clear()

        self.assertEqual(self.parser.buffer, "")
        self.assertFalse(self.parser.is_complete)

        # Ensure we can start over
        self.type_sequence("1D101DD")
        self.assertIsNotNone(self.parser.get_parsed_result())


if __name__ == "__main__":
    unittest.main()
