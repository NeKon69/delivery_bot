#include <Arduino.h>
#include <unity.h>

#include "../../src/positional_servo_wrapper.h"
#include "../test_config.h"

PositionalServoWrapper s1(SERVO_PORT1_PIN, SERVO_OPEN_ANGLE, SERVO_CLOSE_ANGLE);
PositionalServoWrapper s2(SERVO_PORT2_PIN, SERVO_OPEN_ANGLE, SERVO_CLOSE_ANGLE);

void test_servo_repeatability_cycles() {
  s1.attach();
  s2.attach();
  TEST_ASSERT_TRUE(s1.attached());
  TEST_ASSERT_TRUE(s2.attached());

  Serial.println("Repeatability test (open->close), 6 cycles.");
  Serial.println("Expected: consistent final positions on every cycle.");

  for (int cycle = 1; cycle <= 6; cycle++) {
    Serial.print("Cycle ");
    Serial.println(cycle);

    s1.open();
    s2.open();
    delay(2000);
    s1.close();
    s2.close();
    delay(2200);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  UNITY_BEGIN();
  RUN_TEST(test_servo_repeatability_cycles);
  UNITY_END();
}

void loop() {
}
