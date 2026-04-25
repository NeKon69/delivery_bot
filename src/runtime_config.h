#pragma once

#include <Arduino.h>

static constexpr unsigned long SERIAL_BAUD = 115200;
static constexpr unsigned long SERIAL_WAIT_MS = 3000;

static constexpr uint8_t RC522_SS_PIN = 53;
static constexpr uint8_t RC522_RST_PIN = 49;

static constexpr uint8_t SERVO_BOX1_PIN = 2;
static constexpr uint8_t SERVO_BOX2_PIN = 3;
static constexpr uint8_t SERVO_OPEN_ANGLE = 0;
static constexpr uint8_t SERVO_CLOSE_ANGLE = 90;
static constexpr unsigned long SERVO_OPEN_TRANSITION_MS = 6000;

static constexpr uint8_t MOTOR_RIGHT_DIR_PIN = 4;
static constexpr uint8_t MOTOR_RIGHT_PWM_PIN = 5;
static constexpr uint8_t MOTOR_LEFT_PWM_PIN = 6;
static constexpr uint8_t MOTOR_LEFT_DIR_PIN = 7;

static constexpr bool MOTOR_RIGHT_FORWARD_DIR = LOW;
static constexpr bool MOTOR_LEFT_FORWARD_DIR = LOW;
static constexpr bool MOTOR_RIGHT_REVERSE_DIR = HIGH;
static constexpr bool MOTOR_LEFT_REVERSE_DIR = HIGH;

static constexpr uint8_t MOTOR_FORWARD_PWM = 110;
static constexpr uint8_t MOTOR_TURN_PWM = 120;

static constexpr unsigned long MOTION_FORWARD_CELL_MS = 900;
static constexpr unsigned long MOTION_TURN_LEFT_MS = 500;
static constexpr unsigned long MOTION_TURN_RIGHT_MS = 500;
static constexpr unsigned long MOTION_REVERSE_CELL_MS = 900;

static constexpr uint8_t SWITCH1_PIN = 54;
static constexpr uint8_t SWITCH2_PIN = 55;

static constexpr uint8_t LCD_COLS = 20;
static constexpr uint8_t LCD_ROWS = 4;

static constexpr byte KEYPAD_ROWS = 4;
static constexpr byte KEYPAD_COLS = 4;
static constexpr uint8_t KEYPAD_WIRE_PINS[8] = {45, 8, 9, 10, 11, 12, 46, 47};
static constexpr char KEYPAD_MAP[KEYPAD_ROWS][KEYPAD_COLS] = {
    {'1', '2', '3', 'A'},
    {'4', '5', '6', 'B'},
    {'7', '8', '9', 'C'},
    {'*', '0', '#', 'D'},
};

static constexpr unsigned long KEYPAD_HOLD_MS = 500;
static constexpr unsigned long KEYPAD_DEBOUNCE_MS = 20;
static constexpr unsigned long RFID_REPEAT_SUPPRESS_MS = 1200;
static constexpr unsigned long RFID_RECOVERY_COOLDOWN_MS = 250;
