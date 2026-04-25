# AGENTS

## Purpose

- This file explains how the project is organized.
- This file explains which part of the system owns which decisions.
- This file explains how contributors should extend the codebase.
- This file is meant for humans and coding agents.
- This file assumes the project is a two-part robot system.
- This file is intentionally detailed.
- This file is the source of truth for implementation conventions.

## Product Summary

- The project is a cabinet transport robot.
- The robot carries two boxes.
- The robot receives jobs from a keypad.
- The robot shows input and status on a 20x4 LCD.
- The robot travels on a map.
- The robot waits at the requested cabinet.
- The robot checks an RFID card.
- The robot opens the correct box after a valid RFID scan.
- The robot returns to home after a successful handoff.

## High-Level Architecture

- The system has two computers.
- The first computer is a Raspberry Pi.
- The second computer is an Arduino Mega 2560.
- The Raspberry Pi is the brain.
- The Arduino is the hardware bridge.
- The Raspberry Pi owns policy.
- The Arduino owns execution.
- The Raspberry Pi is allowed to decide what should happen.
- The Arduino is allowed to carry out those decisions.
- The Raspberry Pi owns queue logic.
- The Raspberry Pi owns cabinet lookup.
- The Raspberry Pi owns card authorization.
- The Raspberry Pi owns route planning.
- The Arduino owns motor pin toggling.
- The Arduino owns servo output.
- The Arduino owns keypad scan reading.
- The Arduino owns RFID reader polling.
- The Arduino owns LCD writes.
- The Arduino owns switch polling.

## Ownership Rules

- Never move high-level business logic into Arduino unless there is a hardware reason.
- Never let Arduino reorder jobs.
- Never let Arduino decide which cabinet should be visited.
- Never let Arduino decide whether a card is authorized.
- Never let Arduino keep hidden route state that Pi cannot reconstruct.
- The Pi should be able to restart and understand the next safe step.
- The Pi should treat Arduino as a deterministic peripheral.
- The Arduino should expose events and command acknowledgements.

## Hardware Inventory

- Board: Arduino Mega 2560.
- Host: Raspberry Pi or development PC.
- Display: LCD 2004 with I2C backpack.
- Reader: RC522 RFID.
- Input: 4x4 matrix keypad.
- Actuation: two servo locks.
- Presence sensing: two switches.
- Locomotion: two motor channels through a driver.

## Pin Map

- Servo box 1 signal: `D2`.
- Servo box 2 signal: `D3`.
- Motor right direction: `D4`.
- Motor right PWM: `D5`.
- Motor left PWM: `D6`.
- Motor left direction: `D7`.
- Keypad rows and columns use the current validated matrix test mapping.
- Switch 1 is on `A0` / `D54`.
- Switch 2 is on `A1` / `D55`.
- LCD uses hardware I2C pins.
- RC522 uses hardware SPI pins plus reset.

## Device Semantics

- Box `1` and box `2` are logical box IDs.
- They may later be renamed based on physical layout.
- Box IDs are stable API values.
- Keypad input is raw user input.
- LCD text is user-facing status.
- Switches indicate box presence.
- Pressed switch means present box.
- Released switch means absent box.
- Present box means lock should close.
- Absent box means lock should open.
- RFID scan is only meaningful when waiting at a cabinet.

## Job Format

- A job is `{cabinet_id, box_id}`.
- Example: cabinet `2`, box `1`.
- Jobs are typed on keypad.
- Separator is `#`.
- Confirm end is double `##`.
- Example request: `2#1##`.
- Example multi-job request: `2#1#1#2##`.
- The same cabinet may appear multiple times.
- Both boxes may target the same cabinet in separate entries.

## Queue Rules

- Input order is preserved.
- The queue is FIFO.
- No route-based job reordering is allowed.
- No optimization may change delivery order.
- A malformed request must not kill the program.
- A request with unknown cabinet ID must not crash the program.
- Invalid input should go to LCD as an error.

## State Machine Intent

- The system starts idle at home.
- The system waits for keypad input.
- The system parses jobs.
- The system enqueues jobs.
- The system selects the first pending job.
- The system computes a route to the target cabinet.
- The system updates the LCD.
- The system sends motor commands one step at a time.
- The system waits for `motion_done` after each move step.
- The system arrives at the cabinet.
- The system waits for an RFID card forever.
- The system checks authorization.
- Invalid authorization leaves the robot waiting.
- Valid authorization opens the requested box.
- The system computes a route home.
- The system returns to home.
- The system starts the next queued job.

## Pi Responsibilities

- Load all JSON config.
- Parse keypad entry stream.
- Maintain queue state.
- Own map model.
- Own cabinet coordinate model.
- Own card access model.
- Plan routes.
- Decide next movement action.
- Decide LCD content.
- Decide when to open a box.
- Decide when to return home.
- Log protocol events.
- Surface errors without crashing when possible.

## Arduino Responsibilities

- Boot hardware safely.
- Detect LCD address.
- Poll keypad.
- Poll RFID.
- Poll switches.
- Update servo wrappers.
- Execute movement actions using configured timings.
- Emit startup ready event.
- Emit state snapshots when requested.
- Emit motion complete events.
- Emit RFID scan events.
- Emit switch change events.
- Emit keypad events.

## Serial Protocol Philosophy

- Keep human-readable debugging where useful.
- Keep command payloads short on the Arduino RX side.
- Keep event payloads descriptive on the Pi RX side.
- Favor simple framing over clever framing.
- Every command should have an acknowledgement or error.
- Every state transition should be reconstructable from logs.

## Current Protocol Split

- Pi to Arduino uses compact opcodes.
- Arduino to Pi uses JSON events, acks, and errors.
- Compact commands reduce RX parsing stress on the Mega.
- JSON events preserve inspectability.
- This hybrid is deliberate.

## Compact Command Conventions

- `@P` means ping.
- `@R` means reinitialize RFID reader.
- `@G` means get state.
- `@C` means LCD clear.
- `@D` means LCD demo screen.
- `@L|line|text` means write LCD line.
- `@O|box` means servo open.
- `@X|box` means servo close.
- `@A|box|angle` means explicit servo angle.
- `@M|action` means move action.
- `@M|action|duration_ms` means move action override.
- `@T` means stop motors.

## Event Conventions

- `ready` means Arduino booted and initialized runtime services.
- `state` is a snapshot of hardware state.
- `key_event` is a keypad event.
- `switch_state` is a switch edge/change event.
- `rfid_scan` is a normalized card UID event.
- `debug_rfid_read_failed` means RC522 saw a candidate card but UID read failed.
- `debug_rfid_recovered` means Arduino reinitialized RC522 after a read failure.
- `motion_done` means one timed movement step completed.
- `debug_compact_rx` is temporary transport debugging.
- `debug_move_request` is temporary move handling debugging.

## Error Handling Principles

- Errors should be explicit.
- Unknown commands should be reported.
- Unknown cabinets should not crash the Pi.
- Invalid keypad strings should not crash the Pi.
- Unavailable LCD should not crash Arduino.
- Missing RFID should not crash either side.
- Serial noise should be visible in debug logs.
- Hardware missing from the current bench setup should not prevent software validation when possible.

## LCD Rules

- LCD is user-facing, not engineer-facing.
- Text should fit 20 columns.
- Text should be stable enough to read.
- Full screen rewrites should be minimized.
- The Pi decides content.
- The Arduino writes the content.
- Cyrillic is a requested feature.
- Actual Cyrillic display depends on LCD ROM compatibility.
- The software now attempts UTF-8 to LCD byte mapping for Cyrillic.
- If a specific LCD ROM differs, the mapping table must be tuned empirically.

## Cyrillic Notes

- Standard HD44780 displays do not all share the same character ROM.
- Some modules support Cyrillic-like pages.
- Some modules only support ASCII plus a few symbols.
- Some modules partially support Cyrillic but with different code points.
- Therefore software support is necessary but not always sufficient.
- If displayed letters are wrong, adjust the mapping table rather than reverting to transliteration immediately.

## Keypad Rules

- The keypad sends raw pressed events.
- Only pressed events should drive input parsing.
- Released and idle events are still useful for debugging.
- `*` is backspace.
- `D` is clear whole input.
- `#` is separator and final terminator component.
- Unknown keys should be ignored or flagged, not crash parsing.

## Movement Rules

- Movement is open-loop for now.
- No wheel encoders are assumed.
- No position sensors are assumed.
- No line following sensors are assumed.
- A route is translated into discrete actions.
- Current actions are `forward_cell`, `reverse_cell`, `turn_left`, `turn_right`, and `stop`.
- Arduino movement completion is time-based.
- Each step must emit `motion_done`.
- The Pi should not fire the next move until the previous one is complete.

## Movement Calibration Rules

- PWM values are placeholders until hardware tuning is done.
- Cell timing constants are placeholders until floor testing is done.
- Calibration must be repeatable.
- Calibration must be captured in config or constants.
- Documentation must say which surface the robot was calibrated on.
- Motor test behavior must remain available independently of the main app.

## Route Planning Rules

- Use simple deterministic planning first.
- Prefer fewer turns before shorter distance when practical.
- Preserve stable behavior over theoretical optimality.
- Keep map data editable in JSON.
- Keep home node explicit in config.
- Cabinet positions are explicit, not inferred.

## Switch Rules

- Switches control box-open and box-close reactions.
- Switch state changes may be mirrored into servo actions.
- Switch events are still emitted to the Pi.
- Pi remains source of truth for workflow.
- Hardware-side auto reactions should stay simple and predictable.

## RFID Rules

- RFID UIDs must be normalized to uppercase hex strings.
- Authorization is cabinet-centric.
- A cabinet may map to multiple allowed cards.
- Wrong card should keep the robot waiting.
- Wrong card should show an LCD denial message.
- Correct card should open the target box only.

## Config Rules

- JSON files under `config/` define the Pi-side model.
- Keep cabinet IDs aligned across `cabinets.json` and `cards.json`.
- Keep map coordinates valid and inside the grid.
- Keep home on an open cell.
- Keep comments out of JSON.
- Keep IDs as strings where they represent user-facing cabinet IDs.

## Test Strategy

- Unit tests cover Pi logic.
- Hardware tests cover Arduino peripherals.
- LCD tests should remain runnable independently.
- Keypad tests should remain runnable independently.
- RFID tests should remain runnable independently.
- Switch tests should remain runnable independently.
- Motor tests should remain runnable independently.
- Protocol debugging should be visible from normal verbose logs.

## Current Python Test Coverage

- Keypad parser happy path.
- Keypad parser editing keys.
- Invalid box rejection.
- Config loading.
- Cabinet lookup.
- Card authorization lookup.
- Map loading.
- Route planning basics.
- State machine switch behavior.
- State machine happy path start.
- State machine RFID success path.
- State machine RFID denial path.
- State machine unknown cabinet safety.

## Current Arduino Test Coverage

- LCD scanner and quick probe.
- LCD detect and line rendering.
- LCD backlight control.
- Keypad live echo.
- Keypad matrix validation.
- Switch identification and debounce coverage.
- RC522 smoke and UID read.
- Motor smoke and signal probe.
- Servo baseline and wrapper API.

## Contributor Rules

- Prefer modular files over giant monoliths.
- Keep Pi logic in Python modules under `pi/`.
- Keep Arduino logic in `src/`.
- Keep config in `config/`.
- Keep tests meaningful and local to the layer they verify.
- Do not silently change protocol semantics.
- Update docs when changing user-visible behavior.
- Preserve debug flags when troubleshooting transport issues.

## Agent Rules

- Read the current config before changing logic that depends on it.
- Do not assume cabinet IDs are large numbers.
- Do not assume transliterated LCD text is acceptable if the user asked for Cyrillic.
- Do not silently remove debug events during active debugging.
- Add temporary debug instrumentation only when it serves a current fault.
- Remove or downgrade temporary debugging once the fault is understood, unless it is still useful and low risk.
- Prefer one-file patches when possible.
- Verify with both Python tests and Arduino build when changing cross-layer behavior.

## Common Failure Modes

- LCD address detected but text not rendered.
- LCD rendered in tests but not in integrated runtime.
- Keypad key serialized incorrectly.
- Compact commands merged due to serial timing.
- Move step sent before LCD traffic drained.
- Cabinet IDs mismatched between config and tests.
- Card map mismatched from cabinet map.
- Cyrillic characters mismapped on a specific LCD ROM.
- Unknown cabinet crashing the state machine.

## Recovery Guidance

- If keypad input is weird, inspect `key_event` logs first.
- If LCD does not update, compare `lcd_demo` versus runtime line writes.
- If movement is missing, check for `ack move` and `motion_done` before touching motor constants.
- If RFID seems broken, verify raw `rfid_scan` events before debugging authorization.
- If a route looks wrong, verify cabinet coordinates before touching pathfinding.
- If tests fail after config edits, check cabinet ID consistency first.

## Current Reality Check

- The system is still in active bring-up.
- The hardware command path mostly works.
- The integrated runtime still needs serial sequencing refinement around LCD and move interactions.
- Cyrillic support now exists in software, but real display correctness still depends on the specific LCD ROM.

## Long-Term Direction

- Stabilize the serial command pipeline.
- Make the full job flow reliable on hardware.
- Tune motor timings.
- Tune Cyrillic mapping if needed.
- Add richer integration tests.
- Keep the system simple enough to debug on a bench.
