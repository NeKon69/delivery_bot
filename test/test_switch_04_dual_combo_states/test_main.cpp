#include <Arduino.h>
#include <unity.h>

#include "../test_config.h"

static uint8_t comboState() {
  const bool sw1Pressed = digitalRead(SWITCH1_PIN) == LOW;
  const bool sw2Pressed = digitalRead(SWITCH2_PIN) == LOW;
  return (sw1Pressed ? 1 : 0) | (sw2Pressed ? 2 : 0);
}

void test_all_dual_switch_combos_detected() {
  pinMode(SWITCH1_PIN, INPUT_PULLUP);
  pinMode(SWITCH2_PIN, INPUT_PULLUP);

  Serial.println("Dual combo test.");
  Serial.println("Reach all states within 30s:");
  Serial.println("0:none, 1:SW1 only, 2:SW2 only, 3:both");

  bool seen[4] = {false, false, false, false};
  const unsigned long start = millis();
  const unsigned long timeoutMs = 30000;

  while (millis() - start < timeoutMs) {
    uint8_t state = comboState();
    if (!seen[state]) {
      seen[state] = true;
      Serial.print("Seen state: ");
      Serial.println(state);
    }
    if (seen[0] && seen[1] && seen[2] && seen[3]) {
      break;
    }
    delay(12);
  }

  TEST_ASSERT_TRUE_MESSAGE(seen[0], "State 0 (none pressed) not seen.");
  TEST_ASSERT_TRUE_MESSAGE(seen[1], "State 1 (SW1 only) not seen.");
  TEST_ASSERT_TRUE_MESSAGE(seen[2], "State 2 (SW2 only) not seen.");
  TEST_ASSERT_TRUE_MESSAGE(seen[3], "State 3 (both pressed) not seen.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  UNITY_BEGIN();
  RUN_TEST(test_all_dual_switch_combos_detected);
  UNITY_END();
}

void loop() {
}

