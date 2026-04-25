from __future__ import annotations

from collections import deque

from pi.models import DeliveryJob


class DeliveryQueue:
    def __init__(self) -> None:
        self._items: deque[DeliveryJob] = deque()

    def extend(self, jobs: list[DeliveryJob]) -> None:
        self._items.extend(jobs)

    def push(self, job: DeliveryJob) -> None:
        self._items.append(job)

    def peek(self) -> DeliveryJob | None:
        return self._items[0] if self._items else None

    def pop(self) -> DeliveryJob | None:
        return self._items.popleft() if self._items else None

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)

    def snapshot(self) -> list[DeliveryJob]:
        return list(self._items)
