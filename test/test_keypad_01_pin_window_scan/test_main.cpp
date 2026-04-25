#include <Arduino.h>
#include <unity.h>

#include "../test_config.h"

static constexpr uint8_t PIN_MIN = 7;
static constexpr uint8_t PIN_MAX = 14;
static constexpr uint8_t WINDOW_SIZE = 8;
static constexpr uint8_t ROWS = 4;
static constexpr uint8_t COLS = 4;
static constexpr unsigned long WINDOW_MS = 12000;

static constexpr char KEYPAD_MAP[ROWS][COLS] = {
    {'1', '2', '3', 'A'},
    {'4', '5', '6', 'B'},
    {'7', '8', '9', 'C'},
    {'*', '0', '#', 'D'},
};

static uint8_t rowPins[ROWS];
static uint8_t colPins[COLS];

static void applyWindow(uint8_t startPin) {
  for (uint8_t i = 0; i < ROWS; i++) {
    rowPins[i] = static_cast<uint8_t>(startPin + i);
    pinMode(rowPins[i], OUTPUT);
    digitalWrite(rowPins[i], HIGH);
  }

  for (uint8_t i = 0; i < COLS; i++) {
    colPins[i] = static_cast<uint8_t>(startPin + ROWS + i);
    pinMode(colPins[i], INPUT_PULLUP);
  }
}

static uint16_t readMask() {
  uint16_t mask = 0;

  for (uint8_t r = 0; r < ROWS; r++) {
    digitalWrite(rowPins[r], LOW);
    delayMicroseconds(5);

    for (uint8_t c = 0; c < COLS; c++) {
      if (digitalRead(colPins[c]) == LOW) {
        const uint8_t bitIndex = static_cast<uint8_t>(r * COLS + c);
        mask |= static_cast<uint16_t>(1U << bitIndex);
      }
    }

    digitalWrite(rowPins[r], HIGH);
  }

  return mask;
}

static void printChanges(uint16_t lastMask, uint16_t nowMask) {
  for (uint8_t r = 0; r < ROWS; r++) {
    for (uint8_t c = 0; c < COLS; c++) {
      const uint8_t bitIndex = static_cast<uint8_t>(r * COLS + c);
      const uint16_t bit = static_cast<uint16_t>(1U << bitIndex);
      const bool wasPressed = (lastMask & bit) != 0;
      const bool isPressed = (nowMask & bit) != 0;
      if (wasPressed == isPressed) {
        continue;
      }

      Serial.print(isPressed ? "PRESS " : "RELEASE ");
      Serial.print(KEYPAD_MAP[r][c]);
      Serial.print(" [r");
      Serial.print(r);
      Serial.print(" c");
      Serial.print(c);
      Serial.print("] pins(");
      Serial.print(rowPins[r]);
      Serial.print(",");
      Serial.print(colPins[c]);
      Serial.println(")");
    }
  }
}

void test_keypad_sliding_window_scan() {
  static_assert(PIN_MAX >= PIN_MIN, "Invalid pin range");
  static_assert(PIN_MAX - PIN_MIN + 1 >= WINDOW_SIZE, "Pin range too small for window");

  const uint8_t windowCount = static_cast<uint8_t>((PIN_MAX - PIN_MIN + 1) - WINDOW_SIZE + 1);

  Serial.println("Keypad sliding-window scan (infinite)");
  Serial.print("Range: ");
  Serial.print(PIN_MIN);
  Serial.print("..");
  Serial.println(PIN_MAX);
  Serial.println("Each 12s, window shifts by +1 pin.");
  Serial.println("Rows = first 4 pins, Cols = next 4 pins.");
  Serial.println("Note: 4x4 keypad needs 8 wires/pins total.");

  uint8_t windowIndex = 0;
  while (true) {
    const uint8_t startPin = static_cast<uint8_t>(PIN_MIN + windowIndex);
    applyWindow(startPin);

    Serial.println();
    Serial.print("=== WINDOW ");
    Serial.print(windowIndex + 1);
    Serial.print("/");
    Serial.print(windowCount);
    Serial.print(" start=");
    Serial.print(startPin);
    Serial.print(" rows=");
    Serial.print(rowPins[0]);
    Serial.print(",");
    Serial.print(rowPins[1]);
    Serial.print(",");
    Serial.print(rowPins[2]);
    Serial.print(",");
    Serial.print(rowPins[3]);
    Serial.print(" cols=");
    Serial.print(colPins[0]);
    Serial.print(",");
    Serial.print(colPins[1]);
    Serial.print(",");
    Serial.print(colPins[2]);
    Serial.print(",");
    Serial.print(colPins[3]);
    Serial.println(" ===");

    uint16_t lastMask = 0;
    uint16_t transitions = 0;
    const unsigned long startMs = millis();
    while (millis() - startMs < WINDOW_MS) {
      const uint16_t nowMask = readMask();
      if (nowMask != lastMask) {
        transitions++;
        printChanges(lastMask, nowMask);
        lastMask = nowMask;
      }
      delay(10);
    }

    Serial.print("Window transitions: ");
    Serial.println(transitions);

    windowIndex = static_cast<uint8_t>((windowIndex + 1) % windowCount);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  UNITY_BEGIN();
  RUN_TEST(test_keypad_sliding_window_scan);
  UNITY_END();
}

void loop() {
}
