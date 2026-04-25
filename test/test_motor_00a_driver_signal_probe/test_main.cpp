#include <Arduino.h>
#include <unity.h>

#include "../test_config.h"

static void allOff() {
  analogWrite(MOTOR_RIGHT_PWM_PIN, 0);
  analogWrite(MOTOR_LEFT_PWM_PIN, 0);
}

static void pulseChannel(const char *label, uint8_t dirPin, uint8_t pwmPin) {
  Serial.println("----------------------------------------");
  Serial.print("Channel: ");
  Serial.println(label);

  Serial.println("Step 1: DIR=LOW, PWM=0");
  digitalWrite(dirPin, LOW);
  analogWrite(pwmPin, 0);
  delay(800);

  Serial.println("Step 2: DIR=LOW, PWM=140");
  analogWrite(pwmPin, 140);
  delay(1800);

  Serial.println("Step 3: DIR=LOW, PWM=255");
  analogWrite(pwmPin, 255);
  delay(1800);

  Serial.println("Step 4: PWM=0");
  analogWrite(pwmPin, 0);
  delay(800);

  Serial.println("Step 5: DIR=HIGH, PWM=140");
  digitalWrite(dirPin, HIGH);
  analogWrite(pwmPin, 140);
  delay(1800);

  Serial.println("Step 6: DIR=HIGH, PWM=255");
  analogWrite(pwmPin, 255);
  delay(1800);

  Serial.println("Step 7: PWM=0");
  analogWrite(pwmPin, 0);
  delay(1000);
}

void test_driver_control_signals_are_pulsed() {
  TEST_ASSERT_TRUE_MESSAGE(MOTOR_RIGHT_DIR_PIN <= 53, "MOTOR_RIGHT_DIR_PIN out of Mega range");
  TEST_ASSERT_TRUE_MESSAGE(MOTOR_RIGHT_PWM_PIN <= 53, "MOTOR_RIGHT_PWM_PIN out of Mega range");
  TEST_ASSERT_TRUE_MESSAGE(MOTOR_LEFT_DIR_PIN <= 53, "MOTOR_LEFT_DIR_PIN out of Mega range");
  TEST_ASSERT_TRUE_MESSAGE(MOTOR_LEFT_PWM_PIN <= 53, "MOTOR_LEFT_PWM_PIN out of Mega range");

  Serial.println("Driver signal probe test");
  Serial.println("Goal: check Arduino -> shield control path first.");
  Serial.println("If your shield has channel LEDs, they should react during PWM steps.");
  Serial.println("If motor power is not connected, motor movement can still be zero.");
  Serial.println("Pins used:");
  Serial.print("RIGHT: DIR=");
  Serial.print(MOTOR_RIGHT_DIR_PIN);
  Serial.print(" PWM=");
  Serial.println(MOTOR_RIGHT_PWM_PIN);
  Serial.print("LEFT:  DIR=");
  Serial.print(MOTOR_LEFT_DIR_PIN);
  Serial.print(" PWM=");
  Serial.println(MOTOR_LEFT_PWM_PIN);

  pulseChannel("RIGHT", MOTOR_RIGHT_DIR_PIN, MOTOR_RIGHT_PWM_PIN);
  pulseChannel("LEFT", MOTOR_LEFT_DIR_PIN, MOTOR_LEFT_PWM_PIN);

  allOff();
  TEST_PASS_MESSAGE("Signal pulses sent on both channels. Confirm LED or motor reaction manually.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  pinMode(MOTOR_RIGHT_DIR_PIN, OUTPUT);
  pinMode(MOTOR_RIGHT_PWM_PIN, OUTPUT);
  pinMode(MOTOR_LEFT_DIR_PIN, OUTPUT);
  pinMode(MOTOR_LEFT_PWM_PIN, OUTPUT);

  allOff();

  UNITY_BEGIN();
  RUN_TEST(test_driver_control_signals_are_pulsed);
  UNITY_END();
}

void loop() {}
