# Transport Robot Project

## Overview

This project is a cabinet-delivery transport robot built around two controllers:

- `Raspberry Pi` is the brain
- `Arduino Mega 2560` is the hardware bridge and motor/servo executor

The robot has:

- `2` delivery boxes
- `2` box-present switches
- `2` lock servos
- a `4x4` matrix keypad for request entry
- an `LCD 2004 I2C` display for input and status
- an `RC522` RFID reader for cabinet authorization
- a motor driver used for open-loop movement

The Pi owns all high-level logic:

- keypad string parsing
- queue management
- map loading
- pathfinding
- cabinet lookup
- card authorization
- workflow/state transitions

The Arduino only executes hardware actions and reports hardware events.

## Current Delivery Flow

1. User types one or more delivery requests on keypad
2. Arduino sends raw key events to Pi
3. Pi parses request strings like:
   - `123#2##`
   - `123#2#111#1##`
   - `2#1#2#2##` to open both boxes at cabinet `2` after one RFID scan
4. Pi sends LCD text updates back to Arduino while the user types
5. Pi resolves each cabinet id to a location on the robot map
6. Pi computes a route and sends movement commands to Arduino
7. Arduino executes open-loop movement commands using calibrated timing constants
8. When robot reaches the target cabinet, Pi waits indefinitely for RFID
9. Arduino reports scanned RFID UIDs to Pi
10. Pi checks `cabinet -> allowed card(s)`
11. If card is invalid, LCD shows `access denied` and the robot keeps waiting
12. If card is valid, Pi commands the target box to `open()`
13. Pi sends the robot back to its configured home node

Queue handling rules:

- requests are executed strictly in entered order
- the same cabinet may appear more than once
- box `1` and box `2` are separate targets
- consecutive `cabinet#1` and `cabinet#2` entries are served in one stop
- keypad `0` clears the current workflow and re-establishes the startup handshake

Box-present switch rules:

- switch pressed -> call `close()` for the corresponding lock
- switch released -> call `open()` for the corresponding lock

## File-By-File Structure

This is the intended repository structure for the real project implementation.

### Arduino Side

- `src/main.cpp`
  - Arduino firmware entry point
  - initializes hardware modules
  - runs the serial command loop
  - polls devices and emits events to Pi

- `src/serial_protocol.h`
  - JSON line framing helpers
  - command parsing helpers
  - response/event serialization

- `src/serial_protocol.cpp`
  - implementation of Pi <-> Arduino protocol parsing and encoding

- `src/arduino_bridge.h`
  - top-level runtime coordinator for Arduino-side modules
  - dispatches Pi commands to devices

- `src/arduino_bridge.cpp`
  - implementation of the hardware-bridge runtime

- `src/drive_controller.h`
  - open-loop drive API
  - forward-cell, turn-left, turn-right, stop helpers

- `src/drive_controller.cpp`
  - motor driver implementation using calibrated timing constants

- `src/lock_controller.h`
  - owns the two box lock servos
  - maps logical box ids to servo wrappers

- `src/lock_controller.cpp`
  - executes `open`, `close`, and update logic for both box locks

- `src/keypad_reader.h`
  - keypad scan wrapper
  - emits key press events in a Pi-friendly format

- `src/keypad_reader.cpp`
  - keypad event implementation around the `Keypad` library

- `src/lcd_display.h`
  - LCD abstraction for clear/write/status rendering commands

- `src/lcd_display.cpp`
  - LCD 2004A implementation via `LiquidCrystal_I2C`

- `src/rfid_reader.h`
  - RC522 wrapper for card presence and UID extraction

- `src/rfid_reader.cpp`
  - RFID implementation around `MFRC522`

- `src/switch_monitor.h`
  - box-present switch polling and edge detection

- `src/switch_monitor.cpp`
  - switch state change reporting and debounce behavior if needed

- `src/positional_servo_wrapper.h`
  - existing reusable servo wrapper

- `src/positional_servo_wrapper.cpp`
  - existing `open`, `close`, `setAngle`, and queued update behavior

- `test/test_config.h`
  - shared test pin map for hardware validation

- `test/`
  - Arduino hardware bring-up and regression tests

### Raspberry Pi Side

- `pi/main.py`
  - application entry point for the Pi controller

- `pi/serial_link.py`
  - newline-delimited JSON transport over USB serial

- `pi/protocol.py`
  - message schema helpers and validation

- `pi/keypad_parser.py`
  - parses strings like `123#2##` into delivery jobs
  - owns editing rules such as `*` backspace/clear behavior

- `pi/queue_manager.py`
  - maintains pending delivery jobs in strict input order

- `pi/map_loader.py`
  - loads the 2D grid map from config

- `pi/pathfinding.py`
  - route planner for the cabinet grid
  - can lightly prefer fewer turns while staying simple

- `pi/cabinet_index.py`
  - maps cabinet ids to map positions

- `pi/card_registry.py`
  - maps cabinet ids to allowed card UIDs

- `pi/state_machine.py`
  - high-level robot workflow orchestration
  - idle -> input -> move -> wait_card -> open_box -> return_home

- `pi/lcd_presenter.py`
  - decides what text should be shown on the LCD in each state

- `pi/arduino_client.py`
  - higher-level wrapper around serial commands/events

- `pi/config.py`
  - loads all project config in one place

### Shared Configuration

- `config/map.json`
  - 2D grid map using `0 = free`, `1 = wall`
  - also stores the home node if desired

- `config/cabinets.json`
  - cabinet id -> map position mapping

- `config/cards.json`
  - cabinet id -> allowed card list

- `config/motion.json`
  - open-loop movement timing constants
  - forward duration, left turn duration, right turn duration, stop behavior

- `cards.json`
  - current local RFID capture artifact already present in the repo
  - can later be folded into `config/cards.json` or replaced by it

### Documentation / Planning

- `README.md`
  - high-level architecture, hardware map, structure plan, and bring-up notes

- `TODO.md`
  - phased implementation checklist

## Recommended Serial Protocol Direction

Use newline-delimited JSON objects over USB serial.

Example Arduino -> Pi events:

```json
{"type":"key_event","key":"1","state":"pressed"}
{"type":"debug_rfid_read_failed"}
{"type":"debug_rfid_recovered"}
{"type":"rfid_scan","uid":"56DA841F"}
{"type":"switch_state","box":1,"pressed":true}
{"type":"motion_done","step":"forward_cell"}
```

Example Pi -> Arduino commands:

```json
{"type":"lcd_set","lines":["123#2#","Ready","Queue: 1",""]}
{"type":"servo_open","box":2}
{"type":"servo_close","box":1}
{"type":"move","action":"forward_cell"}
{"type":"move","action":"turn_left"}
```

Compact command note:
- `@R` reinitializes the Arduino RFID reader and is used by Pi-side full reset.

Protocol rules:

- Pi owns decisions
- Arduino owns execution and event reporting
- each command should return an acknowledgement or error
- movement is open-loop and driven by calibrated constants

## Current Hardware Map

### RC522 RFID

| RC522 pin | Mega2560 pin |
|---|---|
| SDA (SS) | 53 |
| SCK | 52 |
| MOSI | 51 |
| MISO | 50 |
| IRQ | Not connected |
| GND | GND |
| RST | 49 |
| 3.3V | 3.3V |

### Servo Locks

- `SERVO_PORT1_PIN -> D2`
- `SERVO_PORT2_PIN -> D3`
- current logical angles:
  - `open -> 0`
  - `close -> 90`

### Motor Driver

- right motor: `DIR -> D4`, `PWM -> D5`
- left motor: `DIR -> D7`, `PWM -> D6`

### Box-Present Switches

- `SWITCH1_PIN -> A0 (D54)`
- `SWITCH2_PIN -> A1 (D55)`

### LCD 2004A (I2C backpack)

- `VCC -> 5V`
- `GND -> GND`
- `SDA -> SDA`
- `SCL -> SCL`

### Matrix Keypad

Current validated matrix keypad assumption from tests:

- rows: `D45`, `D8`, `D9`, `D10`
- cols: `D11`, `D12`, `D46`, `D47`

Key layout:

```text
1 2 3 A
4 5 6 B
7 8 9 C
* 0 # D
```

## Existing Bring-Up Commands

Useful monitor:

- `pio device monitor -b 115200`

### RFID test flow

1. `pio test -e megaatmega2560 --filter test_rc522_01_spi_smoke -v`
2. `pio test -e megaatmega2560 --filter test_rc522_02_reader_health -v`
3. `pio test -e megaatmega2560 --filter test_rc522_03_uid_read -v`
4. `pio test -e megaatmega2560 --filter test_rc522_04_stability -v`

### Servo test flow

1. `pio test -e megaatmega2560 --filter test_servo_01_baseline -v`
2. `pio test -e megaatmega2560 --filter test_servo_02_repeatability -v`
3. `pio test -e megaatmega2560 --filter test_servo_03_wrapper_api -v`

### Motor test flow

1. `pio test -e megaatmega2560 --filter test_motor_00_spin_smoke -v`
2. `pio test -e megaatmega2560 --filter test_motor_00a_driver_signal_probe -v`

### Switch test flow

1. `pio test -e megaatmega2560 --filter test_switch_00_identify_wiring -v`
2. `pio test -e megaatmega2560 --filter test_switch_01_raw_state_monitor -v`
3. `pio test -e megaatmega2560 --filter test_switch_02_edge_count -v`
4. `pio test -e megaatmega2560 --filter test_switch_03_debounce_validation -v`
5. `pio test -e megaatmega2560 --filter test_switch_04_dual_combo_states -v`
6. `pio test -e megaatmega2560 --filter test_switch_05_hold_duration -v`

### LCD test flow

1. `pio test -e megaatmega2560 --filter test_lcd_00_i2c_scanner -v`
2. `pio test -e megaatmega2560 --filter test_lcd_00b_bus_quick_probe -v`
3. `pio test -e megaatmega2560 --filter test_lcd_01_detect_and_init -v`
4. `pio test -e megaatmega2560 --filter test_lcd_02_line_rendering -v`
5. `pio test -e megaatmega2560 --filter test_lcd_03_cursor_clear_home -v`
6. `pio test -e megaatmega2560 --filter test_lcd_04_refresh_stability -v`
7. `pio test -e megaatmega2560 --filter test_lcd_05_backlight_control -v`

### RFID capture helper

1. `pio run -e megaatmega2560 -t upload`
2. `pip install pyserial`
3. `python3 capture_cards.py --port /dev/ttyUSB0 --count 3`
