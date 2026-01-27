#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

// --- COMMUNICATION ---
#define SERIAL_BAUD 115200
#define CMD_BUFFER_SIZE 64
#define WATCHDOG_TIMEOUT_MS 2000

// --- MOTORS (L298N) ---
const uint8_t PIN_MOT_L_EN = 10;
const uint8_t PIN_MOT_L_1 = 22;
const uint8_t PIN_MOT_L_2 = 23;
const uint8_t PIN_MOT_R_EN = 9;
const uint8_t PIN_MOT_R_1 = 24;
const uint8_t PIN_MOT_R_2 = 25;

const int RAMP_INTERVAL_MS = 2;
const int DEFAULT_SPEED = 200;

// --- BOXES (Servo + Limit Switches) ---
const uint8_t BOX_COUNT = 2;
const uint8_t PINS_SERVO[] = {6, 7};
const uint8_t PINS_LIMIT[] = {40, 41};
const int SERVO_OPEN_ANGLE = 0;
const int SERVO_CLOSE_ANGLE = 90;

// --- UI (LCD 1602) ---
const uint8_t PIN_LCD_RS = 12, PIN_LCD_EN = 11;
const uint8_t PIN_LCD_D4 = 5, PIN_LCD_D5 = 4, PIN_LCD_D6 = 3, PIN_LCD_D7 = 2;

// --- SENSORS (RFID SPI) ---
const uint8_t PIN_RFID_SS = 53;
const uint8_t PIN_RFID_RST = 49;

#endif
