#include <Arduino.h>
#include <unity.h>

#include "../test_config.h"

void test_raw_state_monitor() {
  pinMode(SWITCH1_PIN, INPUT_PULLUP);
  pinMode(SWITCH2_PIN, INPUT_PULLUP);

  Serial.println("Raw monitor: press/release switches for 12s.");
  Serial.println("State format: SW1=<0|1> SW2=<0|1> (0=pressed, 1=released)");

  const unsigned long windowMs = 12000;
  const unsigned long start = millis();
  int changes = 0;
  int last1 = digitalRead(SWITCH1_PIN);
  int last2 = digitalRead(SWITCH2_PIN);

  while (millis() - start < windowMs) {
    int s1 = digitalRead(SWITCH1_PIN);
    int s2 = digitalRead(SWITCH2_PIN);
    if (s1 != last1 || s2 != last2) {
      changes++;
      Serial.print("Change ");
      Serial.print(changes);
      Serial.print(": SW1=");
      Serial.print(s1 == LOW ? 0 : 1);
      Serial.print(" SW2=");
      Serial.println(s2 == LOW ? 0 : 1);
      last1 = s1;
      last2 = s2;
    }
    delay(20);
  }

  TEST_ASSERT_GREATER_THAN_MESSAGE(0, changes, "No state changes seen. Press at least one switch.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  UNITY_BEGIN();
  RUN_TEST(test_raw_state_monitor);
  UNITY_END();
}

void loop() {
}

