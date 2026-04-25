from __future__ import annotations

from pi.models import Pose


class CabinetIndex:
    def __init__(self, config: dict) -> None:
        cabinet_locations = config.get("cabinet_locations", {})
        if not isinstance(cabinet_locations, dict):
            raise ValueError("cabinets.json must contain cabinet_locations object")
        self._locations = {
            str(cabinet_id): Pose(
                x=int(data["x"]),
                y=int(data["y"]),
                heading=str(data.get("heading", "E")),
            )
            for cabinet_id, data in cabinet_locations.items()
        }

    def get_pose(self, cabinet_id: str) -> Pose:
        try:
            return self._locations[cabinet_id]
        except KeyError as exc:
            raise KeyError(f"Unknown cabinet id: {cabinet_id}") from exc
