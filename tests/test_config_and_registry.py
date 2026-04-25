from pi.cabinet_index import CabinetIndex
from pi.card_registry import CardRegistry
from pi.config import load_project_config
from pi.map_loader import load_grid_map


def test_project_config_loads_expected_files() -> None:
    config = load_project_config()

    assert "grid" in config.map_config
    assert "cabinet_locations" in config.cabinets_config
    assert "cabinet_access" in config.cards_config
    assert "drive" in config.motion_config
    assert "servo_boxes" in config.hardware_config
    assert "commands" in config.protocol_config


def test_cabinet_index_and_card_registry_match_demo_data() -> None:
    config = load_project_config()

    cabinets = CabinetIndex(config.cabinets_config)
    cards = CardRegistry(config.cards_config)
    pose = cabinets.get_pose("2")

    assert (pose.x, pose.y, pose.heading) == (6, 3, "W")
    assert cards.is_allowed("2", "56DA841F") is True
    assert cards.is_allowed("2", "56886A1F") is False


def test_map_loader_builds_grid_map_with_open_home() -> None:
    config = load_project_config()
    grid_map = load_grid_map(config.map_config)

    assert grid_map.width == 7
    assert grid_map.height == 7
    assert grid_map.is_open(grid_map.home.x, grid_map.home.y) is True
