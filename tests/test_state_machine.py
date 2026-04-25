from pi.cabinet_index import CabinetIndex
from pi.card_registry import CardRegistry
from pi.config import load_project_config
from pi.map_loader import load_grid_map
from pi.state_machine import BOX_CLOSE_SETTLE_S, RobotMode, RobotStateMachine


class FakeArduinoClient:
    def __init__(self) -> None:
        self.commands: list[tuple[str, object]] = []
        self._lcd_busy = False

    def ping(self) -> None:
        self.commands.append(("ping", None))

    def rfid_reset(self) -> None:
        self.commands.append(("rfid_reset", None))

    def stop(self) -> None:
        self.commands.append(("stop", None))

    def lcd_set(self, lines: list[str]) -> None:
        self.commands.append(("lcd_set", lines))
        self._lcd_busy = False

    def lcd_busy(self) -> bool:
        return self._lcd_busy

    def move(self, action: str, duration_ms: int | None = None) -> None:
        self.commands.append(("move", (action, duration_ms)))

    def get_state(self) -> None:
        self.commands.append(("get_state", None))

    def servo_open(self, box: int) -> None:
        self.commands.append(("servo_open", box))

    def servo_close(self, box: int) -> None:
        self.commands.append(("servo_close", box))


def build_machine() -> tuple[RobotStateMachine, FakeArduinoClient]:
    config = load_project_config()
    fake = FakeArduinoClient()
    machine = RobotStateMachine(
        arduino=fake,
        grid_map=load_grid_map(config.map_config),
        cabinet_index=CabinetIndex(config.cabinets_config),
        card_registry=CardRegistry(config.cards_config),
    )
    return machine, fake


def set_switch_state(machine: RobotStateMachine, box1: bool, box2: bool) -> None:
    machine.process_message(
        {"type": "event", "event": "state", "switches": [box1, box2]}
    )


def flush_scheduled_actions(machine: RobotStateMachine) -> None:
    for _ in range(20):
        if machine.next_action_due_s is None:
            return
        machine.tick(now_s=machine.next_action_due_s + 1.0)


def enter_job(machine: RobotStateMachine, sequence: str) -> None:
    for key in sequence:
        machine.process_message(
            {"type": "event", "event": "key_event", "key": key, "state": "pressed"}
        )


def finish_loading(machine: RobotStateMachine, box: int) -> None:
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": box, "pressed": False}
    )
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": box, "pressed": True}
    )


def finish_loading_and_flush(machine: RobotStateMachine, box: int) -> None:
    finish_loading(machine, box)
    flush_scheduled_actions(machine)


def test_switch_events_drive_matching_servo_commands() -> None:
    machine, fake = build_machine()

    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 1, "pressed": True}
    )
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": False}
    )

    assert ("servo_close", 1) in fake.commands
    assert ("servo_open", 2) not in fake.commands


def test_valid_input_starts_first_job_and_motion() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, True)
    enter_job(machine, "2#2##")

    assert machine.mode == RobotMode.WAITING_FOR_BOX
    assert ("servo_open", 2) in fake.commands

    finish_loading(machine, 2)

    assert machine.next_action_due_s is not None
    scheduled_at = machine.next_action_due_s
    machine.tick(now_s=scheduled_at - 0.1)
    assert not any(command == "move" for command, _ in fake.commands)

    flush_scheduled_actions(machine)

    assert machine.mode == RobotMode.MOVING_TO_CABINET
    assert machine.active_job is not None
    assert machine.active_job.cabinet_id == "2"
    assert ("servo_close", 2) in fake.commands
    assert fake.commands.index(("servo_close", 2)) < next(
        index for index, command in enumerate(fake.commands) if command[0] == "move"
    )
    assert any(command == "move" for command, _ in fake.commands)


def test_job_opens_target_box_while_waiting_for_load() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, False)
    enter_job(machine, "1#1##")

    assert machine.mode == RobotMode.WAITING_FOR_BOX
    assert ("servo_open", 1) in fake.commands
    assert ("get_state", None) in fake.commands
    assert not any(command == "move" for command, _ in fake.commands)


def test_multi_box_queue_opens_both_boxes_at_home() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, False)
    enter_job(machine, "2#1#1#2##")

    assert machine.mode == RobotMode.WAITING_FOR_BOX
    assert ("servo_open", 1) in fake.commands
    assert ("servo_open", 2) in fake.commands
    assert fake.commands.index(("servo_open", 1)) < fake.commands.index(
        ("get_state", None)
    )
    assert fake.commands.index(("servo_open", 2)) < fake.commands.index(
        ("get_state", None)
    )
    assert not any(command == "move" for command, _ in fake.commands)


def test_zero_key_resets_state_and_restarts_handshake() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, True)
    enter_job(machine, "2#2##")

    assert machine.mode == RobotMode.WAITING_FOR_BOX

    machine.process_message(
        {"type": "event", "event": "key_event", "key": "0", "state": "pressed"}
    )

    assert machine.mode == RobotMode.IDLE
    assert machine.active_job is None
    assert machine.active_boxes == ()
    assert machine.pending_actions == []
    assert len(machine.queue) == 0
    assert machine.keypad_parser.buffer == ""
    assert ("stop", None) in fake.commands
    assert ("ping", None) in fake.commands
    assert ("rfid_reset", None) in fake.commands
    assert fake.commands.count(("get_state", None)) >= 2


def test_reset_allows_new_job_to_reach_card_wait_state_cleanly() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, True)
    enter_job(machine, "2#2##")

    machine.process_message(
        {"type": "event", "event": "key_event", "key": "0", "state": "pressed"}
    )

    set_switch_state(machine, False, True)
    enter_job(machine, "2#2##")
    finish_loading_and_flush(machine, 2)

    while machine.mode == RobotMode.MOVING_TO_CABINET:
        machine.process_message({"type": "event", "event": "motion_done"})
        flush_scheduled_actions(machine)

    assert machine.mode == RobotMode.WAITING_FOR_CARD
    machine.process_message({"type": "event", "event": "rfid_scan", "uid": "56DA841F"})

    assert machine.mode == RobotMode.WAITING_FOR_HANDOFF
    assert fake.commands.count(("servo_open", 2)) >= 2


def test_same_cabinet_two_boxes_open_together_after_one_scan() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, False)
    enter_job(machine, "2#1#2#2##")

    assert machine.mode == RobotMode.WAITING_FOR_BOX
    assert ("servo_open", 1) in fake.commands
    assert ("servo_open", 2) in fake.commands

    finish_loading(machine, 1)
    finish_loading_and_flush(machine, 2)

    while machine.mode == RobotMode.MOVING_TO_CABINET:
        machine.process_message({"type": "event", "event": "motion_done"})
        flush_scheduled_actions(machine)

    assert machine.mode == RobotMode.WAITING_FOR_CARD
    machine.process_message({"type": "event", "event": "rfid_scan", "uid": "56DA841F"})

    assert machine.mode == RobotMode.WAITING_FOR_HANDOFF
    assert fake.commands.count(("servo_open", 1)) >= 2
    assert fake.commands.count(("servo_open", 2)) >= 2

    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 1, "pressed": False}
    )
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 1, "pressed": True}
    )
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": False}
    )
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": True}
    )
    machine.tick(now_s=machine.handoff_started_at_s + 6.0)

    assert len(machine.queue) == 0
    assert machine.mode in {RobotMode.RETURNING_HOME, RobotMode.IDLE}


def test_box_close_waits_before_first_move() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, True)
    enter_job(machine, "2#2##")
    finish_loading(machine, 2)

    assert machine.next_action_due_s is not None
    scheduled_at = machine.next_action_due_s

    machine.tick(now_s=scheduled_at - 0.01)
    assert not any(command == "move" for command, _ in fake.commands)

    machine.tick(now_s=scheduled_at + 0.01)
    assert any(command == "move" for command, _ in fake.commands)
    assert BOX_CLOSE_SETTLE_S == 2.5


def test_valid_rfid_opens_box_and_begins_return_home() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, True)
    enter_job(machine, "2#2##")
    finish_loading_and_flush(machine, 2)

    while machine.mode == RobotMode.MOVING_TO_CABINET:
        machine.process_message({"type": "event", "event": "motion_done"})
        flush_scheduled_actions(machine)

    machine.process_message({"type": "event", "event": "rfid_scan", "uid": "56DA841F"})
    machine.tick(now_s=machine.handoff_started_at_s + 1.0)

    assert ("servo_open", 2) in fake.commands
    assert machine.mode == RobotMode.WAITING_FOR_HANDOFF

    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": False}
    )
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": True}
    )
    machine.tick(now_s=machine.handoff_started_at_s + 6.0)

    assert machine.mode in {RobotMode.RETURNING_HOME, RobotMode.IDLE}


def test_queue_continues_to_next_job_before_returning_home() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, True, True)
    enter_job(machine, "2#2#1#1##")
    finish_loading(machine, 1)
    finish_loading_and_flush(machine, 2)

    while machine.mode == RobotMode.MOVING_TO_CABINET:
        machine.process_message({"type": "event", "event": "motion_done"})
        flush_scheduled_actions(machine)

    machine.process_message({"type": "event", "event": "rfid_scan", "uid": "56DA841F"})
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": False}
    )
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": True}
    )
    machine.tick(now_s=machine.handoff_started_at_s + 6.0)

    assert machine.active_job is not None
    assert machine.active_job.cabinet_id == "1"
    assert machine.active_job.box_id == 1
    assert machine.mode == RobotMode.MOVING_TO_CABINET


def test_second_job_handoff_can_finish_from_polled_state_snapshots() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, True, True)
    enter_job(machine, "2#2#1#1##")
    finish_loading(machine, 1)
    finish_loading_and_flush(machine, 2)

    while machine.mode == RobotMode.MOVING_TO_CABINET:
        machine.process_message({"type": "event", "event": "motion_done"})
        flush_scheduled_actions(machine)

    machine.process_message({"type": "event", "event": "rfid_scan", "uid": "56DA841F"})
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": False}
    )
    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": True}
    )
    machine.tick(now_s=machine.handoff_started_at_s + 6.0)

    while machine.mode == RobotMode.MOVING_TO_CABINET:
        machine.process_message({"type": "event", "event": "motion_done"})
        flush_scheduled_actions(machine)

    assert machine.mode == RobotMode.WAITING_FOR_CARD

    get_state_count_before = fake.commands.count(("get_state", None))
    machine.process_message({"type": "event", "event": "rfid_scan", "uid": "56DA841F"})
    machine.tick(now_s=machine.handoff_started_at_s + 0.6)

    assert fake.commands.count(("get_state", None)) > get_state_count_before

    set_switch_state(machine, False, True)
    set_switch_state(machine, True, True)
    machine.tick(now_s=machine.handoff_started_at_s + 6.0)

    assert machine.mode in {RobotMode.RETURNING_HOME, RobotMode.IDLE}


def test_invalid_rfid_keeps_waiting_for_card() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, True)
    enter_job(machine, "2#2##")
    finish_loading_and_flush(machine, 2)

    while machine.mode == RobotMode.MOVING_TO_CABINET:
        machine.process_message({"type": "event", "event": "motion_done"})
        flush_scheduled_actions(machine)

    open_count_before_rfid = fake.commands.count(("servo_open", 2))
    machine.process_message({"type": "event", "event": "rfid_scan", "uid": "56886A1F"})

    assert machine.mode == RobotMode.WAITING_FOR_CARD
    assert fake.commands.count(("servo_open", 2)) == open_count_before_rfid


def test_return_home_waits_for_switch_cycle_and_five_seconds() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, True)
    enter_job(machine, "2#2##")
    finish_loading_and_flush(machine, 2)

    while machine.mode == RobotMode.MOVING_TO_CABINET:
        machine.process_message({"type": "event", "event": "motion_done"})
        flush_scheduled_actions(machine)

    machine.process_message({"type": "event", "event": "rfid_scan", "uid": "56DA841F"})

    assert machine.mode == RobotMode.WAITING_FOR_HANDOFF
    assert ("servo_open", 2) in fake.commands

    machine.tick(now_s=machine.handoff_started_at_s + 6.0)
    assert machine.mode == RobotMode.WAITING_FOR_HANDOFF

    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": False}
    )
    machine.tick(now_s=machine.handoff_started_at_s + 6.0)
    assert machine.mode == RobotMode.WAITING_FOR_HANDOFF

    machine.process_message(
        {"type": "event", "event": "switch_state", "box": 2, "pressed": True}
    )
    machine.tick(now_s=machine.handoff_started_at_s + 4.0)
    assert machine.mode == RobotMode.WAITING_FOR_HANDOFF

    machine.tick(now_s=machine.handoff_started_at_s + 6.0)
    assert machine.mode in {RobotMode.RETURNING_HOME, RobotMode.IDLE}


def test_unknown_cabinet_does_not_crash_and_returns_to_idle() -> None:
    machine, fake = build_machine()
    machine.start()

    for key in "11111#1##":
        machine.process_message(
            {"type": "event", "event": "key_event", "key": key, "state": "pressed"}
        )

    assert machine.mode == RobotMode.IDLE
    assert machine.active_job is None
    assert any(command == "lcd_set" for command, _ in fake.commands)


def test_job_waits_for_target_box_before_moving() -> None:
    machine, fake = build_machine()
    machine.start()
    set_switch_state(machine, False, False)
    enter_job(machine, "2#2##")

    flush_scheduled_actions(machine)

    assert machine.mode == RobotMode.WAITING_FOR_BOX
    assert not any(command == "move" for command, _ in fake.commands)
    assert ("get_state", None) in fake.commands
    assert ("servo_open", 2) in fake.commands

    finish_loading_and_flush(machine, 2)

    assert machine.mode == RobotMode.MOVING_TO_CABINET
    assert ("servo_close", 2) in fake.commands
    assert any(command == "move" for command, _ in fake.commands)


def test_job_recovers_from_unknown_initial_box_state_after_state_refresh() -> None:
    machine, fake = build_machine()
    machine.start()
    enter_job(machine, "2#2##")

    assert machine.mode == RobotMode.WAITING_FOR_BOX
    assert ("get_state", None) in fake.commands
    assert not any(command == "move" for command, _ in fake.commands)

    set_switch_state(machine, False, True)
    finish_loading_and_flush(machine, 2)

    assert machine.mode == RobotMode.MOVING_TO_CABINET
    assert ("servo_close", 2) in fake.commands
    assert any(command == "move" for command, _ in fake.commands)
