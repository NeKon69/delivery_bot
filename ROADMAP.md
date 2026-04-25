# ROADMAP

## Purpose

- This file explains what the project is trying to achieve.
- This file explains the current gaps between intent and reality.
- This file explains the concrete delivery sequence for the software.
- This file is written for humans and coding agents.
- This file assumes hardware bring-up is still ongoing.
- This file should evolve as the project stabilizes.

## Core Goal

- Build a reliable robot that carries two boxes to cabinets.
- Accept cabinet and box requests from the keypad.
- Show input and status on the LCD.
- Move from home to the requested cabinet.
- Wait for RFID authorization at the cabinet.
- Open only the requested box after valid authorization.
- Return home after a successful handoff.
- Process the next queued request in order.

## Current Architecture Goal

- Raspberry Pi should own all workflow logic.
- Arduino should behave like a deterministic peripheral.
- Pi should use config-driven routing and authorization.
- Arduino should expose simple device and motion primitives.
- Serial transport should be easy to debug on a bench.

## What Already Exists

- Arduino Mega runtime exists under `src/`.
- Pi controller modules exist under `pi/`.
- Shared config exists under `config/`.
- Hardware tests exist under `test/`.
- RC522 tests work independently.
- LCD tests work independently.
- Keypad tests work independently.
- Switch tests work independently.
- Servo wrapper exists and is in use.

## What Is Still Broken Or Incomplete

- Full integrated movement flow is not fully stable.
- Serial sequencing between LCD updates and move commands is still fragile.
- Open-loop motion constants are not calibrated.
- LCD Cyrillic support may still require ROM-specific tuning.
- The real hardware route execution is not yet validated end-to-end.
- The Pi controller still needs more robust ack tracking.
- Integration tests are still light.

## Main Problem Buckets

- Protocol robustness.
- Runtime sequencing.
- Movement calibration.
- LCD display correctness.
- RFID-to-workflow reliability.
- End-to-end queue handling under real hardware conditions.

## Problem 1: Serial Command Reliability

- The Arduino Mega has limited RX parsing tolerance.
- Long JSON commands from Pi to Arduino caused merged command issues.
- LCD updates created enough serial traffic to crowd later commands.
- Move commands could be delayed or merged when sent immediately after screen updates.
- This is why compact opcodes were introduced for Pi to Arduino traffic.

### Current Mitigation

- Pi to Arduino commands use compact opcodes like `@L|...` and `@M|...`.
- Arduino to Pi still uses JSON events and acks for visibility.
- Debug events currently expose compact RX and move handling.

### Remaining Risk

- Even with compact commands, back-to-back LCD writes can still affect timing.
- The app must avoid flooding the Arduino during critical move transitions.

### Planned Fix Direction

- Gate move dispatch until LCD traffic is acknowledged or drained.
- Reduce unnecessary LCD rewrites.
- Keep compact commands short and predictable.
- Preserve readable debug events on the return path.

## Problem 2: LCD Runtime Versus LCD Tests

- Dedicated LCD tests prove the LCD hardware works.
- The integrated runtime originally failed to update the screen even when the device was detected.
- The issue was not basic I2C detection.
- The issue was command framing and runtime update behavior.

### What Was Learned

- `lcd_demo` can work while `lcd_set` fails.
- That means the LCD hardware path is fine and the runtime protocol path is the real fault.
- Using one command per line is more stable than sending whole line arrays.

### Roadmap For LCD

- Keep per-line LCD commands.
- Reduce full-screen rewrites.
- Track when lines actually change.
- Continue bench testing with verbose logs.
- Tune Cyrillic mapping if characters appear wrong.

## Problem 3: Movement Without Sensors

- The robot currently has no encoders.
- The robot currently has no line sensors.
- The robot currently has no position feedback.
- Movement is open-loop only.
- Open-loop movement means route steps depend on timing constants and PWM values.

### Consequences

- Every forward cell move is approximate.
- Every turn is approximate.
- Different surfaces may require different timing.
- Battery level may affect behavior.

### Roadmap For Movement

- Start with deterministic timed steps.
- Keep the map simple.
- Keep command names discrete: `forward_cell`, `turn_left`, `turn_right`, `reverse_cell`, `stop`.
- Use repeatable calibration runs.
- Store timing constants in config or one obvious constants file.

## Problem 4: Unknown Cabinet Safety

- Unknown cabinets used to crash the Pi controller.
- That is unacceptable in a queued hardware workflow.
- The system must survive malformed requests.

### Current Direction

- Reject unknown cabinets gracefully.
- Show user-facing LCD error.
- Skip the invalid job.
- Continue running the app.

### Long-Term Requirement

- No user keypad mistake should kill the program.
- No bad config lookup should leave the robot in undefined workflow state.

## Problem 5: Cyrillic LCD Output

- The user explicitly wants Cyrillic text.
- Many HD44780-compatible LCDs do not share the same ROM.
- A direct UTF-8 print is not enough.
- Software byte mapping is required.

### Current Direction

- Pi emits UTF-8 strings.
- Arduino attempts to map Unicode code points to LCD byte values.
- The mapping must be tuned on the real display if letters are wrong.

### Risk

- A specific LCD may not support the expected Cyrillic page.
- Some letters may render correctly while others may not.
- The solution may require empirical adjustments.

### Roadmap For Cyrillic

- Keep Russian strings user-facing.
- Test actual rendered words on the module.
- Log which words render incorrectly.
- Adjust mapping table rather than dropping the feature.

## Development Phases

## Phase 0: Hardware Bring-Up

- Verify LCD scanning.
- Verify LCD rendering.
- Verify keypad matrix mapping.
- Verify switch behavior.
- Verify RFID reader.
- Verify servo movement.
- Verify motor command outputs.

### Exit Criteria

- Every peripheral has at least one independent passing bring-up test.

## Phase 1: Arduino Bridge Runtime

- Replace demo firmware with modular runtime.
- Poll keypad and emit key events.
- Poll RFID and emit normalized UIDs.
- Poll switches and emit box state changes.
- Accept servo commands.
- Accept LCD commands.
- Accept movement commands.
- Emit `ready`, `state`, `ack`, `error`, and `motion_done`.

### Exit Criteria

- Every Pi-facing command path is testable through serial.
- Arduino can be treated as a device bridge rather than a standalone app.

## Phase 2: Pi Controller Foundations

- Load config files.
- Parse keypad strings.
- Maintain delivery queue.
- Resolve cabinet coordinates.
- Resolve cabinet-to-card authorization.
- Generate routes.
- Build LCD presentation layer.

### Exit Criteria

- Python tests cover the main logic modules.
- Invalid input and unknown cabinet cases do not crash the controller.

## Phase 3: Integrated Serial Workflow

- Connect Pi controller to live Arduino runtime.
- Show typed keypad input on LCD.
- Start jobs after valid request confirmation.
- Dispatch route steps one by one.
- Wait for `motion_done` between steps.
- Wait for RFID at destination.
- Open target box after valid card.
- Return home.

### Current Status

- This phase is partially working.
- Keypad input arrives.
- LCD commands are mostly working.
- The move dispatch path still needs sequencing work.

## Phase 4: Bench Reliability

- Reduce serial race conditions.
- Minimize redundant LCD updates.
- Tune timeouts and delays.
- Add more protocol visibility.
- Ensure the robot can survive repeated job input cycles.

### Exit Criteria

- Repeated bench runs do not produce random protocol failures.
- Command acknowledgements match what the Pi expects.

## Phase 5: Motion Calibration

- Measure one forward cell time.
- Measure left turn time.
- Measure right turn time.
- Measure stop behavior.
- Repeat tests on actual floor surface.
- Document the chosen constants.

### Exit Criteria

- The robot can approximately reach target cabinet cells repeatedly on the chosen test surface.

## Phase 6: Full Delivery Demo

- Enter multiple jobs on keypad.
- Watch queue appear on LCD.
- Drive to first cabinet.
- Wait for correct RFID.
- Open correct box.
- Return home.
- Continue next job.

### Exit Criteria

- One full queue demo succeeds without operator intervention beyond intended keypad and RFID use.

## Current Priority Order

- First: fix integrated move sequencing.
- Second: verify Cyrillic rendering on the real LCD.
- Third: calibrate motion constants.
- Fourth: validate real RFID authorization path on hardware.
- Fifth: strengthen logging and tests around integration edge cases.

## Current Known Good Signals

- LCD can be detected.
- LCD can render in dedicated tests.
- Keypad raw events arrive.
- Switch events arrive.
- Compact command RX debugging works.
- Move commands can be acknowledged in isolated command tests.

## Current Known Bad Or Uncertain Signals

- Integrated `pi.main` flow can still lose move timing around LCD traffic.
- Actual motor movement is not calibrated.
- Cyrillic mapping may or may not match the real LCD ROM.
- RFID path is not yet fully exercised in the integrated app on the real bench.

## Important Engineering Rules For The Roadmap

- Do not optimize route order by cabinet distance.
- Do not move policy logic into Arduino.
- Do not assume a specific LCD Cyrillic ROM without testing.
- Do not break standalone hardware tests while fixing integrated runtime.
- Do not let malformed keypad input crash the controller.
- Do not let unknown cabinet IDs crash the controller.
- Do not hide protocol events that are useful during bring-up.

## Config Evolution Plan

- Keep map in JSON.
- Keep cabinets in JSON.
- Keep card authorization in JSON.
- Keep home node explicit.
- Keep timing constants easy to edit.
- Keep hardware-related constants obvious and centralized.

## Testing Roadmap

## Unit Tests

- Keep parser tests.
- Keep config loading tests.
- Keep registry tests.
- Keep route planning tests.
- Keep state machine safety tests.

## Hardware Tests

- Continue LCD suite.
- Continue keypad suite.
- Continue switch suite.
- Continue RFID suite.
- Continue motor suite.
- Continue servo suite.

## Integration Tests To Add Later

- Simulated serial ack ordering.
- LCD-command-then-move sequencing.
- Multiple queued jobs in one request.
- Wrong card then right card flow.
- Unknown cabinet mixed with valid jobs.
- Home-return after successful delivery.

## Risks And Countermeasures

## Risk: Serial Merge On Mega RX

- Countermeasure: compact opcodes.
- Countermeasure: throttle traffic.
- Countermeasure: send move after LCD drain.
- Countermeasure: keep debug receive logs.

## Risk: LCD ROM Mismatch For Cyrillic

- Countermeasure: map table tuning.
- Countermeasure: bench verification with known Russian words.
- Countermeasure: avoid silent fallback that hides the real issue.

## Risk: Open-Loop Drift

- Countermeasure: simple maps first.
- Countermeasure: conservative cell size assumptions.
- Countermeasure: repeated timed calibration runs.

## Risk: User Input Errors

- Countermeasure: robust parser.
- Countermeasure: LCD error feedback.
- Countermeasure: queue safety.

## Risk: Hidden State Divergence

- Countermeasure: Pi remains workflow source of truth.
- Countermeasure: Arduino emits events for transitions.
- Countermeasure: logs remain inspectable.

## Practical Bench Workflow

- Power Arduino.
- Upload latest bridge firmware.
- Run Pi app with verbose RPC logs.
- Confirm `ready` event.
- Confirm LCD demo or live line updates.
- Type a single simple job.
- Watch parsed queue.
- Watch first move dispatch.
- Confirm `ack move` and `motion_done`.
- Confirm wait-for-card screen.
- Tap allowed card.
- Confirm servo open command.
- Confirm return-home route starts.

## What Success Looks Like

- The user can type `2#1##`.
- The LCD shows that input while typing.
- The Pi enqueues one job.
- The Pi plans a route to cabinet `2`.
- The Pi sends one movement step at a time.
- Arduino acknowledges steps and reports completion.
- The robot waits at cabinet `2`.
- A valid card for cabinet `2` is accepted.
- Box `1` opens.
- The robot returns home.
- The system becomes ready for the next job.

## What Failure Looks Like

- The LCD is detected but runtime text never changes.
- Keypad events arrive but are serialized incorrectly.
- Move commands are sent but never acknowledged.
- Unknown cabinet input crashes the process.
- Wrong RFID accidentally opens a box.
- Return-home starts before authorization.

## Immediate Next Steps

- Continue debugging integrated move dispatch timing.
- Re-upload firmware after the latest changes.
- Verify live Cyrillic rendering on the actual LCD.
- If Cyrillic letters are wrong, tune the LCD mapping table.
- Once move acks are stable, begin motor timing calibration.

## Medium-Term Next Steps

- Add stronger ack tracking on the Pi side.
- Add integration tests for serial sequencing.
- Reduce remaining temporary debug noise once stable.
- Tune route and motion behavior for real floor conditions.

## Long-Term Goal

- A reliable demo-ready cabinet robot.
- Clear ownership between Pi and Arduino.
- Stable config-driven behavior.
- Readable logs during bench debugging.
- Predictable operation even when user input is imperfect.
