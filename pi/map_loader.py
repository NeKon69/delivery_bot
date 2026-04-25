from __future__ import annotations

from dataclasses import dataclass

from pi.models import Pose


@dataclass(frozen=True)
class GridMap:
    name: str
    grid: list[list[int]]
    home: Pose

    @property
    def width(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @property
    def height(self) -> int:
        return len(self.grid)

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_open(self, x: int, y: int) -> bool:
        return self.in_bounds(x, y) and self.grid[y][x] == 0


def load_grid_map(config: dict) -> GridMap:
    grid = config.get("grid")
    if (
        not isinstance(grid, list)
        or not grid
        or not all(isinstance(row, list) for row in grid)
    ):
        raise ValueError("map.json must contain a non-empty grid")

    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("Map rows must all have the same width")

    home_config = config.get("home", {})
    home = Pose(
        x=int(home_config.get("x", 0)),
        y=int(home_config.get("y", 0)),
        heading=str(home_config.get("heading", "E")),
    )

    result = GridMap(name=str(config.get("name", "map")), grid=grid, home=home)
    if not result.is_open(home.x, home.y):
        raise ValueError("Home position must be on an open cell")
    return result
