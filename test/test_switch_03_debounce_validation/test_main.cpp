#include <Arduino.h>
#include <unity.h>

#include "../test_config.h"

static bool waitStableTransition(uint8_t pin, int from, int to, unsigned long timeoutMs, unsigned long stableMs) {
  const unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    if (digitalRead(pin) != from) {
      const unsigned long t0 = millis();
      while (millis() - t0 < stableMs) {
        if (digitalRead(pin) != to) {
          goto unstable;
        }
        delay(2);
      }
      return true;
    }
  unstable:
    delay(2);
  }
  return false;
}

void test_debounce_stable_cycles() {
  pinMode(SWITCH1_PIN, INPUT_PULLUP);
  pinMode(SWITCH2_PIN, INPUT_PULLUP);

  Serial.println("Debounce validation: perform 2 clean press-release cycles for each switch.");
  const unsigned long timeoutPerPhase = 8000;
  const unsigned long stableMs = 35;

  for (int sw = 0; sw < 2; sw++) {
    uint8_t pin = sw == 0 ? SWITCH1_PIN : SWITCH2_PIN;
    Serial.print("Now operating ");
    Serial.println(sw == 0 ? "SW1" : "SW2");

    for (int cycle = 1; cycle <= 2; cycle++) {
      Serial.print("Cycle ");
      Serial.print(cycle);
      Serial.println(": press now.");
      TEST_ASSERT_TRUE_MESSAGE(waitStableTransition(pin, HIGH, LOW, timeoutPerPhase, stableMs),
                               "Press did not reach stable LOW.");

      Serial.println("Release now.");
      TEST_ASSERT_TRUE_MESSAGE(waitStableTransition(pin, LOW, HIGH, timeoutPerPhase, stableMs),
                               "Release did not reach stable HIGH.");
    }
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  UNITY_BEGIN();
  RUN_TEST(test_debounce_stable_cycles);
  UNITY_END();
}

void loop() {
}

