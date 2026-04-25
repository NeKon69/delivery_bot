# TODO

## Phase 0 - Repository Layout

- Move Arduino runtime code toward a dedicated hardware-bridge structure in `src/`
- Add Raspberry Pi controller code under a new `pi/` package
- Add shared JSON/config assets under a new `config/` directory
- Keep hardware validation tests in `test/` as bring-up and regression coverage

## Phase 1 - Arduino Hardware Bridge

- Replace the current demo-style `src/main.cpp` with an Arduino command dispatcher
- Add serial JSON receive/transmit support for Pi <-> Arduino messaging
- Add keypad event reporting to the Pi as raw key presses
- Add LCD command handling from the Pi
- Add RFID scan reporting to the Pi
- Add switch state monitoring for both box-present switches
- Add servo/lock command execution for box 1 and box 2
- Add motor movement command execution for open-loop travel steps
- Add acknowledgements and error replies for every command class

## Phase 2 - Raspberry Pi Controller

- Add serial transport layer to speak newline-delimited JSON with Arduino
- Add keypad input parser for requests like `123#2##` and `123#2#111#1##`
- Add delivery queue manager with strict input order preservation
- Add cabinet-to-location mapping config
- Add cabinet-to-allowed-cards mapping config
- Add map loader for a simple 2D grid (`0 = free`, `1 = wall`)
- Add route planner with light turn minimization preference
- Add robot workflow/state machine: idle -> input -> route -> wait card -> open -> return home
- Add LCD view updates for typed input, status, errors, and queue state

## Phase 3 - Movement Calibration

- Define open-loop movement constants for one forward cell
- Define open-loop turn constants for left and right turns
- Define motor stop/brake behavior
- Add a simple calibration procedure to tune these constants on the real robot
- Store tuned constants in config instead of hardcoding them in logic

## Phase 4 - Integration Rules

- Keep Arduino as a peripheral only; Pi owns all high-level decisions
- Process queued deliveries strictly in entered order
- Wait indefinitely for RFID after arriving at a cabinet
- Show `access denied` on LCD for invalid cards and continue waiting
- Open only the currently active target box after valid authorization
- Return to the configured home node after successful delivery

## Phase 5 - Test Coverage

- Keep existing hardware smoke tests runnable while new runtime code is added
- Add protocol-level tests for Arduino JSON parsing where practical
- Add parser/unit tests on the Pi side for keypad request strings
- Add Pi-side tests for route planning and cabinet/card authorization lookup
- Add an end-to-end mock serial integration test between Pi protocol and Arduino protocol framing

## Immediate Next Steps

- Finalize the file-by-file project structure in `README.md`
- Create the `pi/` and `config/` directories
- Replace `src/main.cpp` with the first Arduino bridge skeleton
- Define the first version of the serial JSON message schema
