#include <Arduino.h>
#include <unity.h>

#include "../test_config.h"

static bool captureHoldDurationMs(uint8_t pin, unsigned long &durationMs) {
  const unsigned long timeoutMs = 15000;
  const unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    if (digitalRead(pin) == LOW) {
      const unsigned long tPress = millis();
      while (digitalRead(pin) == LOW) {
        if (millis() - tPress > 6000) {
          break;
        }
        delay(5);
      }
      durationMs = millis() - tPress;
      return true;
    }
    delay(5);
  }
  return false;
}

void test_short_and_long_press_detection() {
  pinMode(SWITCH1_PIN, INPUT_PULLUP);
  pinMode(SWITCH2_PIN, INPUT_PULLUP);

  Serial.println("Hold-duration test.");
  Serial.println("For SW1: do one SHORT press (~200-500ms).");
  Serial.println("For SW2: do one LONG press (>1200ms).");

  unsigned long d1 = 0, d2 = 0;
  TEST_ASSERT_TRUE_MESSAGE(captureHoldDurationMs(SWITCH1_PIN, d1), "SW1 short press not captured.");
  Serial.print("SW1 captured ms: ");
  Serial.println(d1);

  TEST_ASSERT_TRUE_MESSAGE(captureHoldDurationMs(SWITCH2_PIN, d2), "SW2 long press not captured.");
  Serial.print("SW2 captured ms: ");
  Serial.println(d2);

  TEST_ASSERT_TRUE_MESSAGE(d1 >= 120 && d1 <= 800, "SW1 press duration not in short range.");
  TEST_ASSERT_TRUE_MESSAGE(d2 >= 1200, "SW2 press duration not in long range.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  UNITY_BEGIN();
  RUN_TEST(test_short_and_long_press_detection);
  UNITY_END();
}

void loop() {
}

