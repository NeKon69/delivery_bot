# Autonomous Delivery Robot (Differential Drive)

A generic navigation stack for "janky" hardware (DC motors without encoders). Uses time-based movement with voltage compensation and A* pathfinding.

## Architecture

*   **Brain:** Raspberry Pi (Python 3) - Handles Logic, Map, State Machine.
*   **Firmware:** Arduino Mega (C++) - Handles PWM, Sensors, Safety Stop.
*   **Communication:** 115200 Baud Serial (ASCII Protocol).

## Directory Structure

*   `brain/`: Python source code.
*   `firmware/`: C++ Arduino firmware.
*   `tests/`: Unit and Integration tests.

## Setup (Linux/Fish)

1.  **Install System Deps:**
    ```fish
    sudo apt install python3-venv
    ```

2.  **Run Setup Script:**
    ```fish
    ./setup.fish
    ```

3.  **Run Tests:**
    ```fish
    source venv/bin/activate.fish
    python -m unittest discover tests
    ```

## Usage

1.  Connect Arduino to Raspberry Pi via USB.
2.  Start the Brain:
    ```fish
    python brain/main.py
    ```

## Configuration

Edit `brain/config.json` to tune:
*   `voltage_scalar`: Increase this as battery drains to keep turns accurate.
*   `time_turn_90_ms`: Time required to turn 90 degrees at full battery.
