from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from pi.arduino_client import ArduinoClient
from pi.cabinet_index import CabinetIndex
from pi.card_registry import CardRegistry
from pi.keypad_parser import KeypadParser
from pi.lcd_presenter import (
    access_denied_lines,
    idle_lines,
    moving_lines,
    returning_home_lines,
    waiting_box_lines,
    waiting_handoff_lines,
    waiting_card_lines,
)
from pi.map_loader import GridMap
from pi.models import DeliveryJob, Pose
from pi.pathfinding import plan_route
from pi.queue_manager import DeliveryQueue


BOX_CLOSE_SETTLE_S = 2.5


class RobotMode(str, Enum):
    IDLE = "idle"
    WAITING_FOR_BOX = "waiting_for_box"
    MOVING_TO_CABINET = "moving_to_cabinet"
    WAITING_FOR_CARD = "waiting_for_card"
    WAITING_FOR_HANDOFF = "waiting_for_handoff"
    RETURNING_HOME = "returning_home"


@dataclass
class RobotStateMachine:
    arduino: ArduinoClient
    grid_map: GridMap
    cabinet_index: CabinetIndex
    card_registry: CardRegistry
    keypad_parser: KeypadParser = field(default_factory=KeypadParser)
    queue: DeliveryQueue = field(default_factory=DeliveryQueue)
    logger: Callable[[str], None] | None = None
    current_pose: Pose = field(init=False)
    mode: RobotMode = RobotMode.IDLE
    active_job: DeliveryJob | None = None
    active_boxes: tuple[int, ...] = field(default_factory=tuple)
    pending_actions: list[str] = field(default_factory=list)
    next_action_due_s: float | None = None
    box_present: dict[int, bool | None] = field(
        default_factory=lambda: {1: None, 2: None}
    )
    handoff_started_at_s: float | None = None
    handoff_boxes_pressed: set[int] = field(default_factory=set)
    handoff_boxes_released: set[int] = field(default_factory=set)
    next_presence_refresh_s: float | None = None
    loading_boxes_needed: set[int] = field(default_factory=set)
    loading_boxes_ready: set[int] = field(default_factory=set)
    loading_seen_released: dict[int, bool] = field(
        default_factory=lambda: {1: False, 2: False}
    )

    def __post_init__(self) -> None:
        self.current_pose = self.grid_map.home

    def start(self) -> None:
        self._log(f"start mode={self.mode} pose={self.current_pose}")
        self.arduino.lcd_set(idle_lines(self.keypad_parser.buffer, len(self.queue)))

    def tick(self, now_s: float | None = None) -> None:
        current = time.monotonic() if now_s is None else now_s
        if self.mode == RobotMode.WAITING_FOR_HANDOFF:
            self._maybe_start_return_home(current)
        if self.mode in {RobotMode.WAITING_FOR_BOX, RobotMode.WAITING_FOR_HANDOFF}:
            self._maybe_refresh_box_presence(current)
        if self.next_action_due_s is None:
            return
        if hasattr(self.arduino, "lcd_busy") and self.arduino.lcd_busy():
            return
        if current < self.next_action_due_s:
            return
        self.next_action_due_s = None
        self._dispatch_next_action_now()

    def process_message(self, message: dict) -> None:
        message_type = message.get("type")
        if message_type == "event":
            self._handle_event(message)
            return
        if message_type == "ack" and message.get("command") == "move":
            self._log(f"move_ack action={message.get('action', '')}")
            return
        if message_type == "error":
            self._log(
                f"arduino_error code={message.get('code', '')} message={message.get('message', '')}"
            )

    def _handle_event(self, message: dict) -> None:
        event = message.get("event")
        if event == "state":
            self._handle_state_snapshot(message)
            return
        if event == "key_event" and message.get("state") == "pressed":
            key = str(message.get("key", ""))
            if key == "0":
                self._handle_reset_request()
                return
            if self.mode == RobotMode.IDLE:
                self._handle_key(key)
                return
        if event == "motion_done":
            self._log(f"motion_done action={message.get('action', '')}")
            self._handle_motion_done()
            return
        if event == "debug_move_request":
            self._log(
                f"move_request action={message.get('action', '')} duration_ms={message.get('duration_ms', 0)} busy={message.get('busy', False)}"
            )
            return
        if event == "switch_state":
            self._handle_switch_state(message)
            return
        if event == "rfid_scan" and self.mode == RobotMode.WAITING_FOR_CARD:
            self._handle_rfid(str(message.get("uid", "")))

    def _handle_key(self, key: str) -> None:
        self._log(f"key pressed={key!r} buffer_before={self.keypad_parser.buffer!r}")
        result = self.keypad_parser.handle_key(key)
        if result.reset_requested:
            self._handle_reset_request()
            return
        if result.error:
            self._log(f"key parse error={result.error}")
            self.arduino.lcd_set(["Input error", result.error[:20], "", "D = clear"])
            return

        if result.completed_jobs:
            self._log(
                "jobs parsed="
                + str([(job.cabinet_id, job.box_id) for job in result.completed_jobs])
            )
            self.queue.extend(result.completed_jobs)
            self._refresh_idle_lcd()
            self._try_start_next_job()
            return

        self._log(f"buffer_after={result.display_text!r}")
        self.arduino.lcd_set(idle_lines(result.display_text, len(self.queue)))

    def _try_start_next_job(self) -> None:
        if self.mode != RobotMode.IDLE or self.active_job is not None:
            return
        self.active_job = self.queue.pop()
        if self.active_job is None:
            self._refresh_idle_lcd()
            return

        self.active_boxes = self._collect_active_boxes(self.active_job)

        try:
            goal_pose = self.cabinet_index.get_pose(self.active_job.cabinet_id)
            route = plan_route(self.grid_map, self.current_pose, goal_pose)
        except (KeyError, ValueError) as exc:
            self._log(f"job_rejected cabinet={self.active_job.cabinet_id} error={exc}")
            self.arduino.lcd_set(
                ["Unknown cabinet", self.active_job.cabinet_id[:20], "", "D = clear"]
            )
            self._clear_active_delivery_state()
            self._try_start_next_job()
            return
        self._log(
            f"start_job cabinet={self.active_job.cabinet_id} boxes={list(self.active_boxes)} "
            f"route_steps={route.steps} turns={route.turns} actions={route.actions}"
        )
        self.pending_actions = route.actions.copy()
        if self.current_pose == self.grid_map.home:
            self._begin_loading_phase()
            return
        self._prepare_job_start()

    def _begin_loading_phase(self) -> None:
        if self.active_job is None:
            return
        self.mode = RobotMode.WAITING_FOR_BOX
        self.next_action_due_s = None
        self.next_presence_refresh_s = time.monotonic() + 0.5
        self.loading_boxes_needed = set(self.active_boxes)
        self.loading_boxes_needed.update(job.box_id for job in self.queue.snapshot())
        self.loading_boxes_ready.clear()
        self.loading_seen_released = {1: False, 2: False}
        self._log(f"waiting_for_box boxes={sorted(self.loading_boxes_needed)}")
        for box_id in sorted(self.loading_boxes_needed):
            self.arduino.servo_open(box_id)
        self._request_state_refresh()
        self.arduino.lcd_set(
            waiting_box_lines(self.active_job, len(self.queue), self.active_boxes)
        )

    def _prepare_job_start(self) -> None:
        if self.active_job is None:
            return
        if self.current_pose == self.grid_map.home:
            if not self.loading_boxes_needed.issubset(self.loading_boxes_ready):
                return
        elif any(self.box_present.get(box) is not True for box in self.active_boxes):
            return

        self.mode = RobotMode.MOVING_TO_CABINET
        self.next_presence_refresh_s = None
        self.loading_boxes_needed.clear()
        self.loading_boxes_ready.clear()
        self.loading_seen_released = {1: False, 2: False}
        self._log(f"closing_boxes_before_move boxes={list(self.active_boxes)}")
        for box in sorted(self.active_boxes):
            self.arduino.servo_close(box)
        self.arduino.lcd_set(
            moving_lines(self.active_job, len(self.queue), self.active_boxes)
        )
        self._schedule_next_action(BOX_CLOSE_SETTLE_S)

    def _dispatch_next_action_now(self) -> None:
        if not self.pending_actions:
            if self.mode == RobotMode.RETURNING_HOME:
                self._finish_return_home()
                return
            self.mode = RobotMode.WAITING_FOR_CARD
            if self.active_job is not None:
                self._log(
                    f"arrived cabinet={self.active_job.cabinet_id} waiting_for_card boxes={list(self.active_boxes)}"
                )
                self.current_pose = self.cabinet_index.get_pose(
                    self.active_job.cabinet_id
                )
                self.arduino.lcd_set(
                    waiting_card_lines(
                        self.active_job, len(self.queue), self.active_boxes
                    )
                )
            return
        action = self.pending_actions.pop(0)
        self._log(f"dispatch_action mode={self.mode} action={action}")
        self.arduino.move(action)

    def _schedule_next_action(self, delay_s: float) -> None:
        self.next_action_due_s = time.monotonic() + delay_s

    def _handle_motion_done(self) -> None:
        if self.mode in {RobotMode.MOVING_TO_CABINET, RobotMode.RETURNING_HOME}:
            self._schedule_next_action(0.05)

    def _handle_state_snapshot(self, message: dict) -> None:
        switches = message.get("switches")
        if not isinstance(switches, list):
            return
        for index, pressed in enumerate(switches[:2], start=1):
            self.box_present[index] = bool(pressed)
            self._record_handoff_switch_state(index, bool(pressed))
            self._record_loading_switch_state(index, bool(pressed))
        if self.mode == RobotMode.WAITING_FOR_BOX and self.active_job is not None:
            self._prepare_job_start()

    def _handle_switch_state(self, message: dict) -> None:
        box = int(message.get("box", 0))
        pressed = bool(message.get("pressed", False))
        if box not in {1, 2}:
            return
        self.box_present[box] = pressed
        self._record_handoff_switch_state(box, pressed)
        self._record_loading_switch_state(box, pressed)
        self._log(f"switch_event box={box} pressed={pressed}")
        if pressed:
            self.arduino.servo_close(box)
            if (
                self.mode == RobotMode.WAITING_FOR_BOX
                and self.active_job is not None
                and box in self.active_boxes
            ):
                self._prepare_job_start()

    def _record_loading_switch_state(self, box: int, pressed: bool) -> None:
        if self.mode != RobotMode.WAITING_FOR_BOX or self.active_job is None:
            return
        if self.current_pose == self.grid_map.home:
            if box not in self.loading_boxes_needed:
                return
            if not pressed:
                self.loading_seen_released[box] = True
                self.loading_boxes_ready.discard(box)
                return
            if self.loading_seen_released.get(box, False):
                self.loading_boxes_ready.add(box)
                self._prepare_job_start()
            return

        if box not in self.active_boxes:
            return

    def _handle_rfid(self, uid: str) -> None:
        if self.active_job is None:
            return
        self._log(f"rfid_scan uid={uid} cabinet={self.active_job.cabinet_id}")
        if not self.card_registry.is_allowed(self.active_job.cabinet_id, uid):
            self._log("rfid_result=denied")
            self.arduino.lcd_set(
                access_denied_lines(self.active_job, len(self.queue), self.active_boxes)
            )
            return

        self._log(f"rfid_result=allowed opening_boxes={list(self.active_boxes)}")
        for box in sorted(self.active_boxes):
            self.arduino.servo_open(box)
        self.mode = RobotMode.WAITING_FOR_HANDOFF
        self.handoff_started_at_s = time.monotonic()
        self.handoff_boxes_pressed = {
            box for box in self.active_boxes if self.box_present.get(box) is True
        }
        self.handoff_boxes_released.clear()
        self.next_presence_refresh_s = self.handoff_started_at_s + 0.5
        self._request_state_refresh()
        self.arduino.lcd_set(
            waiting_handoff_lines(self.active_job, len(self.queue), self.active_boxes)
        )

    def _record_handoff_switch_state(self, box: int, pressed: bool) -> None:
        if self.mode != RobotMode.WAITING_FOR_HANDOFF or self.active_job is None:
            return
        if box not in self.active_boxes:
            return
        if pressed:
            self.handoff_boxes_pressed.add(box)
        else:
            self.handoff_boxes_released.add(box)

    def _maybe_start_return_home(self, now_s: float) -> None:
        if self.active_job is None or self.handoff_started_at_s is None:
            return
        active_boxes = set(self.active_boxes)
        elapsed_s = now_s - self.handoff_started_at_s
        if elapsed_s < 5.0:
            return
        if not active_boxes.issubset(self.handoff_boxes_pressed):
            return
        if not active_boxes.issubset(self.handoff_boxes_released):
            return
        if any(self.box_present.get(box) is not True for box in active_boxes):
            return

        if len(self.queue) > 0:
            completed_job = self.active_job
            self._log(
                f"delivery_complete cabinet={completed_job.cabinet_id} boxes={list(self.active_boxes)} next_job_pending=true"
            )
            self._clear_active_delivery_state()
            self._try_start_next_job()
            return

        home_route = plan_route(self.grid_map, self.current_pose, self.grid_map.home)
        self._log(
            f"return_home route_steps={home_route.steps} turns={home_route.turns} actions={home_route.actions}"
        )
        self.pending_actions = home_route.actions.copy()
        self.mode = RobotMode.RETURNING_HOME
        self.handoff_started_at_s = None
        self.handoff_boxes_pressed.clear()
        self.handoff_boxes_released.clear()
        self.next_presence_refresh_s = None
        self.arduino.lcd_set(returning_home_lines(len(self.queue)))
        if not self.pending_actions:
            self._finish_return_home()
        else:
            self._schedule_next_action(0.2)

    def _finish_return_home(self) -> None:
        self._log("return_home_complete")
        self.current_pose = self.grid_map.home
        self._clear_active_delivery_state()
        self._refresh_idle_lcd()
        self._try_start_next_job()

    def _maybe_refresh_box_presence(self, now_s: float) -> None:
        if self.next_presence_refresh_s is None or now_s < self.next_presence_refresh_s:
            return
        self.next_presence_refresh_s = now_s + 0.5
        self._request_state_refresh()

    def _request_state_refresh(self) -> None:
        if hasattr(self.arduino, "get_state"):
            self.arduino.get_state()

    def _handle_reset_request(self) -> None:
        self._log("reset_requested")
        if hasattr(self.arduino, "stop"):
            self.arduino.stop()
        self.keypad_parser.reset()
        self.queue.clear()
        self.current_pose = self.grid_map.home
        self.box_present = {1: None, 2: None}
        self._clear_active_delivery_state()
        if hasattr(self.arduino, "ping"):
            self.arduino.ping()
        if hasattr(self.arduino, "rfid_reset"):
            self.arduino.rfid_reset()
        self._request_state_refresh()
        self._refresh_idle_lcd()

    def _collect_active_boxes(self, first_job: DeliveryJob) -> tuple[int, ...]:
        boxes = [first_job.box_id]
        while True:
            next_job = self.queue.peek()
            if next_job is None or next_job.cabinet_id != first_job.cabinet_id:
                break
            if next_job.box_id in boxes:
                break
            boxes.append(next_job.box_id)
            self.queue.pop()
        return tuple(boxes)

    def _clear_active_delivery_state(self) -> None:
        self.active_job = None
        self.active_boxes = ()
        self.pending_actions.clear()
        self.mode = RobotMode.IDLE
        self.next_action_due_s = None
        self.next_presence_refresh_s = None
        self.handoff_started_at_s = None
        self.handoff_boxes_pressed.clear()
        self.handoff_boxes_released.clear()
        self.loading_boxes_needed.clear()
        self.loading_boxes_ready.clear()
        self.loading_seen_released = {1: False, 2: False}

    def _refresh_idle_lcd(self) -> None:
        self.arduino.lcd_set(idle_lines(self.keypad_parser.buffer, len(self.queue)))

    def _log(self, message: str) -> None:
        if self.logger is not None:
            self.logger(f"[state] {message}")
