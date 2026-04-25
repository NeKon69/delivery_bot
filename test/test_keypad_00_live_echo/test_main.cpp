#include <Arduino.h>
#include <Keypad.h>
#include <unity.h>

#include "../test_config.h"

static constexpr uint8_t KEYPAD_WIRE_PINS[8] = {45, 8, 9, 10, 11, 12, 46, 47};
static constexpr byte KEYPAD_ROWS = 4;
static constexpr byte KEYPAD_COLS = 4;

static byte KEYPAD_ROW_PINS[KEYPAD_ROWS] = {
    KEYPAD_WIRE_PINS[0], KEYPAD_WIRE_PINS[1], KEYPAD_WIRE_PINS[2], KEYPAD_WIRE_PINS[3]};
static byte KEYPAD_COL_PINS[KEYPAD_COLS] = {
    KEYPAD_WIRE_PINS[4], KEYPAD_WIRE_PINS[5], KEYPAD_WIRE_PINS[6], KEYPAD_WIRE_PINS[7]};

static char KEYPAD_MAP[KEYPAD_ROWS][KEYPAD_COLS] = {
    {'1', '2', '3', 'A'},
    {'4', '5', '6', 'B'},
    {'7', '8', '9', 'C'},
    {'*', '0', '#', 'D'},
};

static Keypad customKeypad =
    Keypad(makeKeymap(KEYPAD_MAP), KEYPAD_ROW_PINS, KEYPAD_COL_PINS, KEYPAD_ROWS, KEYPAD_COLS);

static const char *keyStateToText(KeyState state) {
  switch (state) {
    case IDLE:
      return "IDLE";
    case PRESSED:
      return "PRESSED";
    case HOLD:
      return "HOLD";
    case RELEASED:
      return "RELEASED";
    default:
      return "UNKNOWN";
  }
}

void test_keypad_live_echo() {
  customKeypad.setHoldTime(500);
  customKeypad.setDebounceTime(20);

  Serial.println("4x4 keypad live echo (infinite)");
  Serial.println("Wiring assumption: wires[0..3]=rows, wires[4..7]=cols");
  Serial.println("Press keys. Output shows key, state, row, col, pin pair.");
  Serial.println("If key labels are wrong, row/col order is wrong.");
  Serial.println("Electrical mode: rows OUTPUT (idle HIGH, scan LOW), cols INPUT_PULLUP, press=LOW.");
  Serial.print("Rows: ");
  for (uint8_t i = 0; i < KEYPAD_ROWS; i++) {
    Serial.print(KEYPAD_ROW_PINS[i]);
    Serial.print(i < KEYPAD_ROWS - 1 ? ',' : '\n');
  }
  Serial.print("Cols: ");
  for (uint8_t i = 0; i < KEYPAD_COLS; i++) {
    Serial.print(KEYPAD_COL_PINS[i]);
    Serial.print(i < KEYPAD_COLS - 1 ? ',' : '\n');
  }
  Serial.println("Running forever. Reset board to stop.");

  while (true) {
    if (customKeypad.getKeys()) {
      for (byte i = 0; i < LIST_MAX; i++) {
        if (!customKeypad.key[i].stateChanged) {
          continue;
        }

        const int code = customKeypad.key[i].kcode;
        const byte row = static_cast<byte>(code / KEYPAD_COLS);
        const byte col = static_cast<byte>(code % KEYPAD_COLS);

        Serial.print("KEY ");
        Serial.print(customKeypad.key[i].kchar);
        Serial.print(" -> ");
        Serial.print(keyStateToText(customKeypad.key[i].kstate));
        Serial.print(" [r");
        Serial.print(row);
        Serial.print(" c");
        Serial.print(col);
        Serial.print("] pins(");
        Serial.print(KEYPAD_ROW_PINS[row]);
        Serial.print(",");
        Serial.print(KEYPAD_COL_PINS[col]);
        Serial.println(")");
      }
    }
    delay(12);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  UNITY_BEGIN();
  RUN_TEST(test_keypad_live_echo);
  UNITY_END();
}

void loop() {
}
