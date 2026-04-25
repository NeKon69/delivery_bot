#pragma once

static constexpr uint8_t RC522_SS_PIN = 53;
static constexpr uint8_t RC522_RST_PIN = 49;
static constexpr unsigned long SERIAL_WAIT_MS = 3000;

static constexpr uint8_t SERVO_PORT1_PIN = 2;
static constexpr uint8_t SERVO_PORT2_PIN = 3;
static constexpr uint8_t SERVO_OPEN_ANGLE = 0;
static constexpr uint8_t SERVO_CLOSE_ANGLE = 90;

static constexpr uint8_t MOTOR_RIGHT_DIR_PIN = 4;
static constexpr uint8_t MOTOR_RIGHT_PWM_PIN = 5;
static constexpr uint8_t MOTOR_LEFT_PWM_PIN = 6;
static constexpr uint8_t MOTOR_LEFT_DIR_PIN = 7;
static constexpr uint8_t MOTOR_TEST_PWM = 30;
static constexpr unsigned long MOTOR_TEST_SPIN_MS = 1600;
static constexpr unsigned long MOTOR_TEST_GAP_MS = 1200;
static constexpr unsigned long MOTOR_TEST_SERIAL_PROMPT_MS = 2500;

static constexpr uint8_t SWITCH1_PIN = 54;
static constexpr uint8_t SWITCH2_PIN = 55;

static constexpr uint8_t LCD_COLS = 20;
static constexpr uint8_t LCD_ROWS = 4;
