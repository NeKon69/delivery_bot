from __future__ import annotations

import heapq
from dataclasses import dataclass

from pi.map_loader import GridMap
from pi.models import Heading, Pose


HEADINGS: tuple[Heading, ...] = ("N", "E", "S", "W")
TURN_LEFT: dict[Heading, Heading] = {"N": "W", "W": "S", "S": "E", "E": "N"}
TURN_RIGHT: dict[Heading, Heading] = {"N": "E", "E": "S", "S": "W", "W": "N"}
FORWARD_DELTA: dict[Heading, tuple[int, int]] = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
}
REVERSE_DELTA: dict[Heading, tuple[int, int]] = {
    heading: (-dx, -dy) for heading, (dx, dy) in FORWARD_DELTA.items()
}


@dataclass(frozen=True)
class PlannedRoute:
    actions: list[str]
    final_pose: Pose
    turns: int
    steps: int


def plan_route(grid_map: GridMap, start: Pose, goal: Pose) -> PlannedRoute:
    queue: list[tuple[int, int, int, int, str]] = []
    start_key = (start.x, start.y, start.heading)
    heapq.heappush(queue, (0, 0, start.x, start.y, start.heading))

    best_cost: dict[tuple[int, int, Heading], tuple[int, int]] = {start_key: (0, 0)}
    previous: dict[tuple[int, int, Heading], tuple[tuple[int, int, Heading], str]] = {}

    goal_key: tuple[int, int, Heading] | None = None

    while queue:
        turns, steps, x, y, heading = heapq.heappop(queue)
        state = (x, y, heading)
        if best_cost.get(state) != (turns, steps):
            continue

        if x == goal.x and y == goal.y and heading == goal.heading:
            goal_key = state
            break

        left_heading = TURN_LEFT[heading]
        left_state = (x, y, left_heading)
        left_cost = (turns + 1, steps + 1)
        if left_cost < best_cost.get(left_state, (10**9, 10**9)):
            best_cost[left_state] = left_cost
            previous[left_state] = (state, "turn_left")
            heapq.heappush(queue, (left_cost[0], left_cost[1], x, y, left_heading))

        right_heading = TURN_RIGHT[heading]
        right_state = (x, y, right_heading)
        right_cost = (turns + 1, steps + 1)
        if right_cost < best_cost.get(right_state, (10**9, 10**9)):
            best_cost[right_state] = right_cost
            previous[right_state] = (state, "turn_right")
            heapq.heappush(queue, (right_cost[0], right_cost[1], x, y, right_heading))

        dx, dy = FORWARD_DELTA[heading]
        nx, ny = x + dx, y + dy
        if grid_map.is_open(nx, ny):
            forward_state = (nx, ny, heading)
            forward_cost = (turns, steps + 1)
            if forward_cost < best_cost.get(forward_state, (10**9, 10**9)):
                best_cost[forward_state] = forward_cost
                previous[forward_state] = (state, "forward_cell")
                heapq.heappush(
                    queue, (forward_cost[0], forward_cost[1], nx, ny, heading)
                )

        reverse_dx, reverse_dy = REVERSE_DELTA[heading]
        reverse_x, reverse_y = x + reverse_dx, y + reverse_dy
        if grid_map.is_open(reverse_x, reverse_y):
            reverse_state = (reverse_x, reverse_y, heading)
            reverse_cost = (turns, steps + 1)
            if reverse_cost < best_cost.get(reverse_state, (10**9, 10**9)):
                best_cost[reverse_state] = reverse_cost
                previous[reverse_state] = (state, "reverse_cell")
                heapq.heappush(
                    queue,
                    (
                        reverse_cost[0],
                        reverse_cost[1],
                        reverse_x,
                        reverse_y,
                        heading,
                    ),
                )

    if goal_key is None:
        raise ValueError(f"No route from {start} to {goal}")

    actions: list[str] = []
    cursor = goal_key
    while cursor != start_key:
        prior, action = previous[cursor]
        actions.append(action)
        cursor = prior
    actions.reverse()

    turns, steps = best_cost[goal_key]
    return PlannedRoute(actions=actions, final_pose=goal, turns=turns, steps=steps)
