#include <Arduino.h>
#include <unity.h>

#include "../test_config.h"

void test_edge_count_for_both_switches() {
  pinMode(SWITCH1_PIN, INPUT_PULLUP);
  pinMode(SWITCH2_PIN, INPUT_PULLUP);

  Serial.println("Edge count test: do at least 3 press-release cycles on each switch.");

  const unsigned long timeoutMs = 30000;
  const unsigned long start = millis();
  int press1 = 0, release1 = 0, press2 = 0, release2 = 0;
  int prev1 = digitalRead(SWITCH1_PIN);
  int prev2 = digitalRead(SWITCH2_PIN);

  while (millis() - start < timeoutMs) {
    int s1 = digitalRead(SWITCH1_PIN);
    int s2 = digitalRead(SWITCH2_PIN);

    if (s1 != prev1) {
      if (s1 == LOW)
        press1++;
      else
        release1++;
      prev1 = s1;
      Serial.print("SW1 edges: press=");
      Serial.print(press1);
      Serial.print(" release=");
      Serial.println(release1);
    }

    if (s2 != prev2) {
      if (s2 == LOW)
        press2++;
      else
        release2++;
      prev2 = s2;
      Serial.print("SW2 edges: press=");
      Serial.print(press2);
      Serial.print(" release=");
      Serial.println(release2);
    }

    if (press1 >= 3 && release1 >= 3 && press2 >= 3 && release2 >= 3) {
      break;
    }
    delay(10);
  }

  TEST_ASSERT_GREATER_OR_EQUAL_MESSAGE(3, press1, "SW1: not enough press edges.");
  TEST_ASSERT_GREATER_OR_EQUAL_MESSAGE(3, release1, "SW1: not enough release edges.");
  TEST_ASSERT_GREATER_OR_EQUAL_MESSAGE(3, press2, "SW2: not enough press edges.");
  TEST_ASSERT_GREATER_OR_EQUAL_MESSAGE(3, release2, "SW2: not enough release edges.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  UNITY_BEGIN();
  RUN_TEST(test_edge_count_for_both_switches);
  UNITY_END();
}

void loop() {
}

