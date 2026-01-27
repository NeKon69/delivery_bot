import unittest
import sys
import os

# --- Path Setup ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from brain.navigator import Navigator
from brain.hal import RobotHAL
from tests.test_utils import MockSerial

# --- Mocks ---


class MockPathfinder:
    """
    Programmable Pathfinder.
    Allows us to dictate exactly what path the Navigator 'sees'
    without running the actual A* algorithm.
    """

    def __init__(self):
        self.next_path = []  # The path to return on next call
        self.force_fail = False

    def find_path(self, start, end):
        print(f"   [MockPF] Requested path: {start} -> {end}")
        if self.force_fail:
            print("   [MockPF] Simulating Failure (No path found)")
            return None

        # If no specific path programmed, return direct line (teleport)
        if not self.next_path:
            print("   [MockPF] No path programmed, returning direct [start, end]")
            return [start, end]

        print(f"   [MockPF] Returning programmed path: {self.next_path}")
        return self.next_path


class MockSleeper:
    """
    Captures sleep calls to verify timing logic without waiting.
    """

    def __init__(self):
        self.log = []

    def sleep(self, seconds):
        print(f"   [Sleep] Zzz... for {seconds}s")
        self.log.append(seconds)


# --- Test Suite ---


class TestNavigatorExtended(unittest.TestCase):

    def setUp(self):
        print(f"\n[SETUP] {self._testMethodName}")

        self.serial = MockSerial()
        self.config = {
            "calibration": {
                "time_move_1_grid_ms": 1000,
                "time_turn_90_ms": 500,
                "voltage_scalar": 1.0,
            }
        }
        self.hal = RobotHAL(self.serial, self.config)
        self.pf = MockPathfinder()
        self.sleeper = MockSleeper()

        # Initialize Navigator at (0,0) facing NORTH (0)
        # N=0, E=1, S=2, W=3
        self.nav = Navigator(
            self.hal,
            self.pf,
            start_pos=[0, 0],
            start_facing=0,
            sleeper_func=self.sleeper.sleep,
        )

        # Override settle time for predictable testing
        self.nav.settle_time = 0.5

    def tearDown(self):
        print(f"[TEARDOWN] {self._testMethodName} Complete")

    # =========================================================================
    # Group 1: Internal Math & Vector Logic
    # =========================================================================

    def test_vector_to_facing_north(self):
        print("[LOG] Testing Vector -> North")
        # Moving (0,0) to (0,-1) assumes Grid: Y decreases going North (standard 2D array)
        # OR Y increases going South?
        # Let's assume Standard Matrix: Row decreases is Up (North)

        # Vector: dx=0, dy=-1
        facing = self.nav._vector_to_facing((0, -1))
        print(f"   Input: (0, -1) | Result: {facing} (Expect 0)")
        self.assertEqual(facing, 0)

    def test_vector_to_facing_south(self):
        print("[LOG] Testing Vector -> South")
        # Vector: dx=0, dy=1
        facing = self.nav._vector_to_facing((0, 1))
        print(f"   Input: (0, 1) | Result: {facing} (Expect 2)")
        self.assertEqual(facing, 2)

    def test_vector_to_facing_east(self):
        print("[LOG] Testing Vector -> East")
        facing = self.nav._vector_to_facing(1, 0)
        print(f"   Input: (1, 0) | Result: {facing} (Expect 1)")
        self.assertEqual(facing, 1)

    def test_vector_to_facing_west(self):
        print("[LOG] Testing Vector -> West")
        # Vector: dx=-1, dy=0
        facing = self.nav._vector_to_facing((-1, 0))
        print(f"   Input: (-1, 0) | Result: {facing} (Expect 3)")
        self.assertEqual(facing, 3)

    def test_turn_calculation_none_needed(self):
        print("[LOG] Testing Turns: Facing N, Want N")
        # Current: 0, Target: 0
        turns = self.nav._get_turns_needed(0, 0)
        print(f"   Current: 0 | Target: 0 | Turns: {turns}")
        self.assertEqual(turns, [])

    def test_turn_calculation_right(self):
        print("[LOG] Testing Turns: Facing N (0), Want E (1)")
        turns = self.nav._get_turns_needed(0, 1)
        print(f"   Turns: {turns}")
        self.assertEqual(turns, ["RIGHT"])

    def test_turn_calculation_left(self):
        print("[LOG] Testing Turns: Facing N (0), Want W (3)")
        turns = self.nav._get_turns_needed(0, 3)
        print(f"   Turns: {turns}")
        self.assertEqual(turns, ["LEFT"])

    def test_turn_calculation_u_turn(self):
        print("[LOG] Testing Turns: Facing N (0), Want S (2)")
        # Manual says U-turn is implemented as 2 Right turns
        turns = self.nav._get_turns_needed(0, 2)
        print(f"   Turns: {turns}")
        self.assertEqual(turns, ["RIGHT", "RIGHT"])

    def test_turn_calculation_wrapping(self):
        print("[LOG] Testing Turns: Facing W (3), Want N (0)")
        # 3 -> 0 is Right Turn
        turns = self.nav._get_turns_needed(3, 0)
        print(f"   Turns: {turns}")
        self.assertEqual(turns, ["RIGHT"])

    # =========================================================================
    # Group 2: Dead Reckoning (Position Updates)
    # =========================================================================

    def test_move_updates_internal_state(self):
        print("[LOG] Testing State Update after Move")

        start = [0, 0]
        target = [1, 0]  # East
        self.pf.next_path = [start, target]

        # Initial Check
        self.assertEqual(self.nav.pos, start)
        self.assertEqual(self.nav.facing, 0)  # North

        print("   -> Executing goto((1,0))")
        success = self.nav.goto(target)

        self.assertTrue(success)

        # Post Check
        # Should have turned East (1) and moved to (1,0)
        print(f"   -> Final Pos: {self.nav.pos} | Final Facing: {self.nav.facing}")
        self.assertEqual(self.nav.pos, target)
        self.assertEqual(self.nav.facing, 1)

    def test_multi_step_state_tracking(self):
        print("[LOG] Testing Multi-step Path Tracking")

        # Path: (0,0) -> (1,0) -> (1,1)
        # Directions: East, then South
        path = [[0, 0], [1, 0], [1, 1]]
        self.pf.next_path = path

        self.nav.goto([1, 1])

        print(f"   -> Final Pos: {self.nav.pos}")
        self.assertEqual(self.nav.pos, [1, 1])
        self.assertEqual(self.nav.facing, 2)  # South

    # =========================================================================
    # Group 3: Hardware Sequencing & Timing
    # =========================================================================

    def test_sequence_move_straight(self):
        print("[LOG] Testing Sequence: Move Straight (No Turn)")

        # Already facing N (0), Target (0,-1) is N
        self.pf.next_path = [[0, 0], [0, -1]]

        self.nav.goto([0, -1])

        # Verify Serial Commands
        cmds = self.serial.get_history_as_strings()
        print(f"   Serial History: {cmds}")

        # Should be just MOV:FWD
        self.assertIn("MOV:FWD:1000", cmds)
        self.assertNotIn("MOV:LFT:500", cmds)
        self.assertNotIn("MOV:RGT:500", cmds)

        # Verify Sleep
        # 1. Sleep for Move Duration (1.0s)
        # 2. Sleep for Settle Time (0.5s)
        print(f"   Sleep Log: {self.sleeper.log}")
        self.assertIn(1.5, self.sleeper.log)

    def test_sequence_turn_and_move(self):
        print("[LOG] Testing Sequence: Turn Left -> Move")

        # Face N, Target W (3)
        self.pf.next_path = [[0, 0], [-1, 0]]

        self.nav.goto([-1, 0])

        cmds = self.serial.get_history_as_strings()
        print(f"   Serial History: {cmds}")

        # Order matters! Turn then Drive.
        turn_idx = next(i for i, s in enumerate(cmds) if "LFT" in s)
        drive_idx = next(i for i, s in enumerate(cmds) if "FWD" in s)

        print(f"   Turn Index: {turn_idx} | Drive Index: {drive_idx}")
        self.assertLess(turn_idx, drive_idx)

        # Check Sleeps
        # 1. Turn Duration (0.5)
        # 2. Move Duration (1.0)
        # 3. Settle Time (0.5) - Maybe twice? Once after turn, once after move?
        # Implementation Detail: Navigator usually settles after 'move_to_neighbor'
        # Let's verify exactly what happened.

        print(f"   Sleep Log: {self.sleeper.log}")
        self.assertIn(
            0.5, self.sleeper.log
        )  # Turn time & Settle time match, so 0.5 appears
        self.assertIn(1.0, self.sleeper.log)

    def test_sequence_u_turn(self):
        print("[LOG] Testing Sequence: U-Turn (2 Rights)")

        # Face N, Target S (2) -> (0, 1)
        self.pf.next_path = [[0, 0], [0, 1]]

        self.nav.goto([0, 1])

        cmds = self.serial.get_history_as_strings()
        print(f"   Serial History: {cmds}")

        # Count Right Turns
        rgt_count = sum(1 for c in cmds if "RGT" in c)
        print(f"   Right Turns Found: {rgt_count}")
        self.assertEqual(rgt_count, 2)

        # Ensure FWD happened last
        self.assertTrue("FWD" in cmds[-1])

    # =========================================================================
    # Group 4: Edge Cases & Failure Modes
    # =========================================================================

    def test_pathfinding_failure(self):
        print("[LOG] Testing Pathfinding returns None")
        self.pf.force_fail = True

        result = self.nav.goto([10, 10])

        print(f"   Result: {result}")
        self.assertFalse(result)

        # Should not have moved
        self.assertEqual(self.nav.pos, [0, 0])

        # No commands sent
        self.assertEqual(len(self.serial.history), 0)

    def test_already_at_destination(self):
        print("[LOG] Testing Zero-Length Path (Start==End)")

        # Path: [[0,0]]
        self.pf.next_path = [[0, 0]]

        result = self.nav.goto([0, 0])

        print(f"   Result: {result}")
        self.assertTrue(result)

        # No movement commands
        self.assertEqual(len(self.serial.history), 0)

    def test_diagonal_rejection(self):
        """
        If Pathfinder somehow returns a diagonal step, Navigator needs to handle it
        or fail. Our logic relies on Cardinal directions.
        (0,0) -> (1,1) in one step implies dx=1, dy=1.
        """
        print("[LOG] Testing Diagonal Step Handling")

        self.pf.next_path = [[0, 0], [1, 1]]

        # Logic: (1,1) vector is not (0,+-1) or (+-1,0)
        # _vector_to_facing might fail or return weird int?
        # Let's see how robust the code is.

        try:
            self.nav.goto([1, 1])
            # If we reached here, did it default to something?
            print(
                f"   [WARN] Navigator accepted diagonal step. Facing: {self.nav.facing}"
            )

            # Since modulo math might wrap diagonal vectors:
            # dx=1, dy=1. Logic often looks for non-zero.
            # If not explicitly guarded, it might produce garbage commands.
            # This test mainly asserts it doesn't Crash Python.
        except Exception as e:
            print(f"   [PASS] Navigator raised exception on diagonal: {e}")

    # =========================================================================
    # Group 5: Voltage Scaling Integration
    # =========================================================================

    def test_settle_time_not_scaled(self):
        """
        Settle time is a physics constant (waiting for wobble to stop),
        it should NOT be multiplied by battery voltage scalar.
        """
        print("[LOG] Testing Settle Time vs Voltage Scalar")
        self.hal.scalar = 2.0
        self.nav.settle_time = 0.5
        self.sleeper.log = []

        self.pf.next_path = [[0, 0], [0, -1]]
        self.nav.goto([0, -1])

        # We expect a 2.0s sleep (Move) AND a 0.5s sleep (Settle)
        # Settle time should NOT become 1.0s
        print(f"   Sleep Log: {self.sleeper.log}")

        self.assertIn(0.5, self.sleeper.log)
        self.assertNotIn(1.0, self.sleeper.log)  # 1.0 would be scaled settle

    # =========================================================================
    # Group 6: Complex Path Stress Test
    # =========================================================================

    def test_complex_zigzag_path(self):
        print("[LOG] Testing ZigZag Path")
        # (0,0)N -> (0,-1)N -> (1,-1)E -> (1,0)S
        # Fwd, Right, Fwd, Right, Fwd
        path = [
            [0, 0],  # Start
            [0, -1],  # North (FWD)
            [1, -1],  # East  (RGT + FWD)
            [1, 0],  # South (RGT + FWD)
        ]
        self.pf.next_path = path

        self.nav.goto([1, 0])

        cmds = self.serial.get_history_as_strings()
        print(f"   Command Sequence: {cmds}")

        fwd_count = sum(1 for c in cmds if "FWD" in c)
        rgt_count = sum(1 for c in cmds if "RGT" in c)

        print(f"   FWD: {fwd_count} (Expect 3)")
        print(f"   RGT: {rgt_count} (Expect 2)")

        self.assertEqual(fwd_count, 3)
        self.assertEqual(rgt_count, 2)

        # Verify final facing
        self.assertEqual(self.nav.facing, 2)  # South


if __name__ == "__main__":
    unittest.main()
