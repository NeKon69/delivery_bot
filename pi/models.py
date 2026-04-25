from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Heading = Literal["N", "E", "S", "W"]


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class Pose:
    x: int
    y: int
    heading: Heading


@dataclass(frozen=True)
class DeliveryJob:
    cabinet_id: str
    box_id: int
