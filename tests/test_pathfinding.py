from pi.cabinet_index import CabinetIndex
from pi.config import load_project_config
from pi.map_loader import load_grid_map
from pi.models import Pose
from pi.pathfinding import plan_route


def test_route_to_cabinet_2_exists_and_ends_at_goal_pose() -> None:
    config = load_project_config()
    grid_map = load_grid_map(config.map_config)
    cabinets = CabinetIndex(config.cabinets_config)
    goal = cabinets.get_pose("2")

    route = plan_route(grid_map, grid_map.home, goal)

    assert route.actions
    assert route.final_pose == goal
    assert route.turns >= 0
    assert route.steps >= len(route.actions)


def test_same_pose_route_is_empty() -> None:
    config = load_project_config()
    grid_map = load_grid_map(config.map_config)

    route = plan_route(grid_map, grid_map.home, grid_map.home)

    assert route.actions == []
    assert route.turns == 0
    assert route.steps == 0


def test_route_prefers_reverse_when_goal_is_directly_behind() -> None:
    config = load_project_config()
    grid_map = load_grid_map(config.map_config)

    start = Pose(x=1, y=1, heading="E")
    goal = Pose(x=0, y=1, heading="E")
    route = plan_route(grid_map, start, goal)

    assert route.actions == ["reverse_cell"]
    assert route.turns == 0
    assert route.steps == 1
