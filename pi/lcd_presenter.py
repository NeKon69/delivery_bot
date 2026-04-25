from __future__ import annotations

from pi.models import DeliveryJob


def _box_line(job: DeliveryJob, boxes: tuple[int, ...] | None = None) -> str:
    if boxes is not None and len(boxes) > 1:
        joined = "+".join(str(box) for box in boxes)
        return f"Boxes {joined}"[:20]
    return f"Box {job.box_id}"


def idle_lines(buffer_text: str, queue_size: int) -> list[str]:
    return [
        buffer_text[:20],
        "Enter cab#box##",
        f"Queue: {queue_size}",
        "*=bk D=clr 0=rst",
    ]


def moving_lines(
    job: DeliveryJob, remaining: int, boxes: tuple[int, ...] | None = None
) -> list[str]:
    return [
        f"Cabinet {job.cabinet_id}",
        _box_line(job, boxes),
        "Moving...",
        f"Left: {remaining}",
    ]


def waiting_card_lines(
    job: DeliveryJob, remaining: int, boxes: tuple[int, ...] | None = None
) -> list[str]:
    return [
        f"Cabinet {job.cabinet_id}",
        _box_line(job, boxes),
        "Scan card",
        f"Left: {remaining}",
    ]


def access_denied_lines(
    job: DeliveryJob, remaining: int, boxes: tuple[int, ...] | None = None
) -> list[str]:
    return [
        f"Cabinet {job.cabinet_id}",
        _box_line(job, boxes),
        "Access denied",
        f"Left: {remaining}",
    ]


def waiting_box_lines(
    job: DeliveryJob, remaining: int, boxes: tuple[int, ...] | None = None
) -> list[str]:
    return [
        f"Cabinet {job.cabinet_id}",
        _box_line(job, boxes),
        "Insert box",
        f"Left: {remaining}",
    ]


def waiting_handoff_lines(
    job: DeliveryJob, remaining: int, boxes: tuple[int, ...] | None = None
) -> list[str]:
    return [
        f"Cabinet {job.cabinet_id}",
        _box_line(job, boxes),
        "Waiting handoff",
        f"Left: {remaining}",
    ]


def returning_home_lines(remaining: int) -> list[str]:
    return ["Delivery done", "Returning home", "", f"Queue: {remaining}"]
