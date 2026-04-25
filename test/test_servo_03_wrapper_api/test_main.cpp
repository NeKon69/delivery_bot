#include <Arduino.h>
#include <unity.h>

#include "../../src/positional_servo_wrapper.h"
#include "../test_config.h"

PositionalServoWrapper s1(SERVO_PORT1_PIN, SERVO_OPEN_ANGLE, SERVO_CLOSE_ANGLE);
PositionalServoWrapper s2(SERVO_PORT2_PIN, SERVO_OPEN_ANGLE, SERVO_CLOSE_ANGLE);

static void pumpFor(unsigned long durationMs) {
  const unsigned long start = millis();
  while (millis() - start < durationMs) {
    s1.update();
    s2.update();
    delay(10);
  }
}

static void holdAngle(uint16_t angle, unsigned long holdMs, const char *label) {
  s1.setAngle(angle);
  s2.setAngle(angle);
  Serial.print(label);
  Serial.print(" angle=");
  Serial.println(angle);
  pumpFor(holdMs);
}

void test_servo_wrapper_open_close_and_angles() {
  s1.attach();
  s2.attach();
  TEST_ASSERT_TRUE(s1.attached());
  TEST_ASSERT_TRUE(s2.attached());

  Serial.println("Wrapper API check.");
  Serial.println("Expected: open() => 0 then 180 after 2 seconds.");
  Serial.println("Expected: close() => 90.");

  s1.open();
  s2.open();
  Serial.println("Step 1: open()");
  pumpFor(5000);

  s1.close();
  s2.close();
  Serial.println("Step 2: close()");
  pumpFor(2500);

  holdAngle(180, 2800, "Step 3");
  holdAngle(90, 2200, "Step 4");
  holdAngle(0, 2200, "Step 5");
  holdAngle(90, 2200, "Step 6");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  UNITY_BEGIN();
  RUN_TEST(test_servo_wrapper_open_close_and_angles);
  UNITY_END();
}

void loop() {}
