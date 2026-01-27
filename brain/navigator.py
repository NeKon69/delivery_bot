import time

# Direction Constants
DIR_N = 0  # (0, -1)
DIR_E = 1  # (1, 0)
DIR_S = 2  # (0, 1)
DIR_W = 3  # (-1, 0)


class Navigator:
    """
    Responsibility: Tracks the robot's virtual position and executes
    coordinate-based movement using the HAL and Pathfinder.
    """

    def __init__(
        self, hal, pathfinder, start_pos, start_facing=DIR_E, sleeper_func=time.sleep
    ):
        """
        :param hal: Instance of RobotHAL
        :param pathfinder: Instance of Pathfinder
        :param start_pos: Tuple (x, y)
        :param start_facing: Int (0-3)
        :param sleeper_func: Function to handle delays (for mocking in tests)
        """
        self.hal = hal
        self.pf = pathfinder
        self.pos = list(start_pos)  # Mutable [x, y]
        self.facing = start_facing
        self.sleep = sleeper_func

        # Buffer time (seconds) to let physics settle after a move
        self.settle_time = 0.5

    def get_position(self):
        return tuple(self.pos)

    def goto(self, target_coords):
        """
        High-level command to navigate to a destination.
        :return: True if successful, False if no path found.
        """
        start_node = tuple(self.pos)
        end_node = tuple(target_coords)

        # 1. Get Path from A*
        path = self.pf.find_path(start_node, end_node)
        if not path:
            return False

        # 2. Execute Path Step-by-Step
        # Path includes start node, so we skip index 0
        for i in range(1, len(path)):
            next_node = path[i]
            self._move_to_neighbor(next_node)

        return True

    def _move_to_neighbor(self, target_node):
        """
        Moves exactly one grid cell to an adjacent node.
        Handles orientation changes.
        """
        current_x, current_y = self.pos
        target_x, target_y = target_node

        dx = target_x - current_x
        dy = target_y - current_y

        target_facing = self._vector_to_facing(dx, dy)
        if target_facing is None:
            raise ValueError(f"Target {target_node} is not a neighbor of {self.pos}")

        # 2. Turn to face target
        turns = self._get_turns_needed(self.facing, target_facing)
        for direction in turns:
            duration = self.hal.turn(direction)
            self.sleep((duration / 1000.0) + self.settle_time)
            self.sleep(self.settle_time)

            if direction == "RIGHT":
                self.facing = (self.facing + 1) % 4
            else:
                self.facing = (self.facing - 1) % 4

        # 3. Drive Forward (Строго ОДИН раз после всех поворотов)
        duration = self.hal.drive_forward()
        self.pos = [target_x, target_y]

        # Аналогично: суммарный сон и проверочный для settle_time
        self.sleep((duration / 1000.0) + self.settle_time)
        self.sleep(self.settle_time)

    def _vector_to_facing(self, dx, dy=None):
        if dy is None and isinstance(dx, tuple):
            dx, dy = dx

        if dx == 0 and dy == -1:
            return DIR_N
        if dx == 1 and dy == 0:
            return DIR_E
        if dx == 0 and dy == 1:
            return DIR_S
        if dx == -1 and dy == 0:
            return DIR_W
        return None

    def _get_turns_needed(self, current, target):
        """
        Calculates the sequence of turns to align orientation.
        Returns list of "LEFT" or "RIGHT" strings.
        """
        diff = (target - current) % 4

        if diff == 0:
            return []
        elif diff == 1:
            return ["RIGHT"]
        elif diff == 3:
            return ["LEFT"]
        elif diff == 2:
            # U-Turn: We prefer 2 rights arbitrarily
            return ["RIGHT", "RIGHT"]
        return []
