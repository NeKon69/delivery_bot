#include <Arduino.h>
#include <Servo.h>
#include <unity.h>

#include "../test_config.h"

Servo s1;
Servo s2;

static void holdPair(int a1, int a2, unsigned long ms, const char *label) {
  s1.write(a1);
  s2.write(a2);
  Serial.println(label);
  delay(ms);
}

void test_servo_baseline_behavior() {
  s1.attach(SERVO_PORT1_PIN);
  s2.attach(SERVO_PORT2_PIN);
  TEST_ASSERT_TRUE(s1.attached());
  TEST_ASSERT_TRUE(s2.attached());

  Serial.println("Baseline behavior test.");
  Serial.println("Expected: both servos move to angle and hold.");

  holdPair(90, 90, 4000, "Step 1: both -> 90");
  holdPair(0, 0, 5000, "Step 2: both -> 0");
  holdPair(90, 90, 3000, "Step 3: both -> 90");
  holdPair(180, 180, 5000, "Step 4: both -> 180");
  holdPair(90, 90, 3000, "Step 5: both -> 90");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  UNITY_BEGIN();
  RUN_TEST(test_servo_baseline_behavior);
  UNITY_END();
}

void loop() {
}
