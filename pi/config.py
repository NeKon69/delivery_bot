from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"


@dataclass(frozen=True)
class ProjectConfig:
    map_config: dict[str, Any]
    cabinets_config: dict[str, Any]
    cards_config: dict[str, Any]
    motion_config: dict[str, Any]
    hardware_config: dict[str, Any]
    protocol_config: dict[str, Any]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config file {path} must contain a JSON object")
    return data


def load_project_config(config_dir: Path = CONFIG_DIR) -> ProjectConfig:
    return ProjectConfig(
        map_config=_load_json(config_dir / "map.json"),
        cabinets_config=_load_json(config_dir / "cabinets.json"),
        cards_config=_load_json(config_dir / "cards.json"),
        motion_config=_load_json(config_dir / "motion.json"),
        hardware_config=_load_json(config_dir / "hardware.json"),
        protocol_config=_load_json(config_dir / "protocol.json"),
    )


def load_map_config(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    return _load_json(config_dir / "map.json")


def load_cabinets_config(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    return _load_json(config_dir / "cabinets.json")


def load_cards_config(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    return _load_json(config_dir / "cards.json")


def load_motion_config(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    return _load_json(config_dir / "motion.json")


def load_hardware_config(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    return _load_json(config_dir / "hardware.json")


def load_protocol_config(config_dir: Path = CONFIG_DIR) -> dict[str, Any]:
    return _load_json(config_dir / "protocol.json")
