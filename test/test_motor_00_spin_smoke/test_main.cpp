#include <Arduino.h>
#include <unity.h>

#include "../test_config.h"

static void stopAllMotors() {
  analogWrite(MOTOR_RIGHT_PWM_PIN, 0);
  analogWrite(MOTOR_LEFT_PWM_PIN, 0);
}

static void driveMotorSequence(const char *label, uint8_t dirPin, uint8_t pwmPin) {
  stopAllMotors();

  Serial.print("Starting ");
  Serial.print(label);
  Serial.println(" motor sequence");

  digitalWrite(dirPin, LOW);
  Serial.print(label);
  Serial.print(" motor direction = LOW, PWM=");
  Serial.print(MOTOR_TEST_PWM);
  Serial.print(" for ");
  Serial.print(MOTOR_TEST_SPIN_MS);
  Serial.println(" ms");
  Serial.println("Check the motor and the shield LEDs during this window.");
  analogWrite(pwmPin, MOTOR_TEST_PWM);
  delay(MOTOR_TEST_SPIN_MS);

  digitalWrite(dirPin, HIGH);
  Serial.print(label);
  Serial.print(" motor direction = HIGH, PWM stays ");
  Serial.print(MOTOR_TEST_PWM);
  Serial.print(" for ");
  Serial.print(MOTOR_TEST_SPIN_MS);
  Serial.println(" ms");
  Serial.println("Check again for motion or LED change.");
  delay(MOTOR_TEST_SPIN_MS);

  analogWrite(pwmPin, 0);
  Serial.print(label);
  Serial.println(" motor sequence complete");
  delay(MOTOR_TEST_GAP_MS);
}

void test_each_motor_channel_spins_briefly() {
  TEST_ASSERT_TRUE_MESSAGE(MOTOR_RIGHT_DIR_PIN <= 53, "MOTOR_RIGHT_DIR_PIN is out of Mega digital pin range.");
  TEST_ASSERT_TRUE_MESSAGE(MOTOR_RIGHT_PWM_PIN <= 53, "MOTOR_RIGHT_PWM_PIN is out of Mega digital pin range.");
  TEST_ASSERT_TRUE_MESSAGE(MOTOR_LEFT_PWM_PIN <= 53, "MOTOR_LEFT_PWM_PIN is out of Mega digital pin range.");
  TEST_ASSERT_TRUE_MESSAGE(MOTOR_LEFT_DIR_PIN <= 53, "MOTOR_LEFT_DIR_PIN is out of Mega digital pin range.");

  Serial.println("Motor smoke test: Amperka L298P");
  Serial.println("Assumed mapping:");
  Serial.println("RIGHT motor: DIR=D4 PWM=D5");
  Serial.println("LEFT motor: DIR=D7 PWM=D6");
  Serial.println("Motor power must be connected.");
  Serial.println("Each motor will run one sequence matching the Amperka example code.");
  Serial.println("If LEDs react but the motor does not move, suspect power, wiring, or the motor itself.");
  delay(MOTOR_TEST_SERIAL_PROMPT_MS);

  Serial.println("Expected result: RIGHT motor moves or makes audible gear noise.");
  driveMotorSequence("RIGHT", MOTOR_RIGHT_DIR_PIN, MOTOR_RIGHT_PWM_PIN);

  Serial.println("Expected result: LEFT motor moves or makes audible gear noise.");
  driveMotorSequence("LEFT", MOTOR_LEFT_DIR_PIN, MOTOR_LEFT_PWM_PIN);

  stopAllMotors();
  Serial.println("Expected result: each connected motor moved or made audible gear noise during its sequence.");
  TEST_PASS_MESSAGE("Motor smoke pulses completed. Confirm motor/LED activity on both channels.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  pinMode(MOTOR_RIGHT_DIR_PIN, OUTPUT);
  pinMode(MOTOR_RIGHT_PWM_PIN, OUTPUT);
  pinMode(MOTOR_LEFT_PWM_PIN, OUTPUT);
  pinMode(MOTOR_LEFT_DIR_PIN, OUTPUT);

  stopAllMotors();

  UNITY_BEGIN();
  RUN_TEST(test_each_motor_channel_spins_briefly);
  UNITY_END();
}

void loop() {
}
