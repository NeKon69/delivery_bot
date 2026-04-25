from __future__ import annotations


class CardRegistry:
    def __init__(self, config: dict) -> None:
        cabinet_access = config.get("cabinet_access", {})
        if not isinstance(cabinet_access, dict):
            raise ValueError("cards.json must contain cabinet_access object")
        self._cabinet_access = {
            str(cabinet_id): {str(uid).upper() for uid in uids}
            for cabinet_id, uids in cabinet_access.items()
        }

    def is_allowed(self, cabinet_id: str, uid: str) -> bool:
        return uid.upper() in self._cabinet_access.get(cabinet_id, set())
