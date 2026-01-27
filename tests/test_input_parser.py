import unittest
import sys
import os

# Add parent directory to path so we can import 'brain'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.input_parser import InputParser


class TestInputParser(unittest.TestCase):

    def setUp(self):
        self.parser = InputParser()

    def type_sequence(self, chars):
        """Helper to simulate typing a string character by character"""
        for char in chars:
            self.parser.push_key(char)

    def test_happy_path(self):
        """Test a perfect entry: Box 1 to Room 101"""
        # User types: 1 D 1 0 1 D D
        self.type_sequence("1D101DD")

        self.assertTrue(self.parser.is_complete)
        result = self.parser.get_parsed_result()

        self.assertIsNotNone(result)
        self.assertEqual(result["box_id"], 1)
        self.assertEqual(result["room_code"], "101")

    def test_backspace_logic(self):
        """Test valid correction using backspace (*)"""
        # Intention: 1D101DD
        # Typo: 1 2 [Backspace] D 1 0 [Backspace] 0 1 D D
        self.type_sequence("12*D10*01DD")

        self.assertTrue(self.parser.is_complete)
        result = self.parser.get_parsed_result()
        self.assertEqual(result["room_code"], "101")
        self.assertEqual(result["box_id"], 1)

    def test_backspace_on_empty(self):
        """Ensure backspacing on empty buffer doesn't crash"""
        self.parser.push_key("*")
        self.parser.push_key("*")
        self.type_sequence("1D101DD")

        result = self.parser.get_parsed_result()
        self.assertIsNotNone(result)

    def test_backspace_undo_completion(self):
        """
        If user types 1D101DD (Complete), but then hits Backspace,
        it should no longer be complete.
        """
        self.type_sequence("1D101DD")
        self.assertTrue(self.parser.is_complete)

        self.parser.push_key("*")  # Removes last D
        self.assertFalse(self.parser.is_complete)
        self.assertIsNone(self.parser.get_parsed_result())

    def test_bad_syntax_no_d(self):
        """Format must include 'D' separator"""
        self.type_sequence("101DD")  # Missing Box/D separator

        self.assertTrue(self.parser.is_complete)  # It ends in DD, so it triggers check
        result = self.parser.get_parsed_result()
        self.assertIsNone(result)  # But parsing should fail

    def test_bad_syntax_non_integer_box(self):
        """Box ID must be an integer"""
        self.type_sequence("AD101DD")
        self.assertIsNone(self.parser.get_parsed_result())

    def test_bad_syntax_empty_room(self):
        """Room code cannot be empty"""
        self.type_sequence("1DDD")  # 1 D [Empty] DD
        self.assertIsNone(self.parser.get_parsed_result())

    def test_clear(self):
        self.type_sequence("1D101DD")
        self.parser.clear()
        self.assertEqual(self.parser.buffer, "")
        self.assertFalse(self.parser.is_complete)


if __name__ == "__main__":
    unittest.main()
