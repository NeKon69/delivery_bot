import heapq
import json
import math


class Pathfinder:
    def __init__(self, map_file_path):
        """
        :param map_file_path: Path to map_grid.json
        """
        self.grid = []
        self.width = 0
        self.height = 0
        self.TURN_COST = 5.0  # High penalty to prefer straight lines
        self.MOVE_COST = 1.0

        self.load_map(map_file_path)

    def load_map(self, path):
        try:
            with open(path, "r") as f:
                self.grid = json.load(f)
                self.height = len(self.grid)
                self.width = len(self.grid[0]) if self.height > 0 else 0
                print(f"[PATH] Map loaded: {self.width}x{self.height} Grid")
        except Exception as e:
            print(f"[PATH] Error loading map: {e}")

    def heuristic(self, a, b):
        """
        Manhattan distance for grid movement.
        """
        (x1, y1) = a
        (x2, y2) = b
        return abs(x1 - x2) + abs(y1 - y2)

    def get_neighbors(self, node):
        """
        Returns valid walkable neighbors (Up, Down, Left, Right).
        """
        (x, y) = node
        results = []
        # Directions: (dx, dy) -> Right, Left, Down, Up
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]

        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            # Check bounds
            if 0 <= nx < self.width and 0 <= ny < self.height:
                # Check walls (0 = Walkable, 1 = Wall)
                if self.grid[ny][nx] == 0:
                    results.append((nx, ny))
        return results

    def find_path(self, start, end):
        """
        A* Algorithm with Turn Penalties.
        :param start: Tuple (x, y)
        :param end: Tuple (x, y)
        :return: List of tuples [(x, y), ...] or None if no path.
        """
        if not self.is_walkable(end):
            print(f"[PATH] Destination {end} is a wall/out of bounds.")
            return None

        # Priority Queue: (priority, current_node, last_direction)
        # We track last_direction to calculate turn costs.
        # Direction is a tuple (dx, dy). Start has None.
        frontier = []
        heapq.heappush(frontier, (0, start, None))

        came_from = {}
        cost_so_far = {}

        came_from[start] = None
        cost_so_far[start] = 0

        # To properly handle turn costs, we might re-visit a node
        # if we arrive at it from a "better" direction (straighter).
        # However, for simple grids, standard A* with weight adjustment is usually sufficient.

        while frontier:
            _, current, last_dir = heapq.heappop(frontier)

            if current == end:
                break

            for next_node in self.get_neighbors(current):
                # Calculate movement vector
                new_dir = (next_node[0] - current[0], next_node[1] - current[1])

                # Base cost
                new_cost = cost_so_far[current] + self.MOVE_COST

                # Turn Penalty Logic
                if last_dir is not None and new_dir != last_dir:
                    new_cost += self.TURN_COST

                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self.heuristic(end, next_node)
                    heapq.heappush(frontier, (priority, next_node, new_dir))
                    came_from[next_node] = current

        return self.reconstruct_path(came_from, start, end)

    def reconstruct_path(self, came_from, start, end):
        if end not in came_from:
            return None

        current = end
        path = []
        while current != start:
            path.append(current)
            current = came_from[current]
        path.append(start)
        path.reverse()
        return path

    def is_walkable(self, node):
        (x, y) = node
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x] == 0
        return False
