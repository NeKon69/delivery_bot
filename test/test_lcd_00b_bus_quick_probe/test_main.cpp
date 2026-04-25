#include <Arduino.h>
#include <Wire.h>
#include <unity.h>

#include "../test_config.h"

static bool probeAddress(uint8_t addr) {
  Wire.beginTransmission(addr);
  return Wire.endTransmission() == 0;
}

void test_i2c_bus_idle_and_common_lcd_addresses() {
  const uint8_t SDA_PIN = 20;
  const uint8_t SCL_PIN = 21;

  pinMode(SDA_PIN, INPUT_PULLUP);
  pinMode(SCL_PIN, INPUT_PULLUP);
  delay(20);

  int sdaLevel = digitalRead(SDA_PIN);
  int sclLevel = digitalRead(SCL_PIN);

  Serial.print("Idle SDA level: ");
  Serial.println(sdaLevel == HIGH ? "HIGH" : "LOW");
  Serial.print("Idle SCL level: ");
  Serial.println(sclLevel == HIGH ? "HIGH" : "LOW");

  Wire.begin();
  Wire.setWireTimeout(25000, true);
  delay(50);

  bool found27 = probeAddress(0x27);
  bool found3f = probeAddress(0x3F);

  Serial.print("Probe 0x27: ");
  Serial.println(found27 ? "ACK" : "NO ACK");
  Serial.print("Probe 0x3F: ");
  Serial.println(found3f ? "ACK" : "NO ACK");

  TEST_ASSERT_TRUE_MESSAGE(sdaLevel == HIGH && sclLevel == HIGH,
                           "SDA/SCL not idle HIGH. Likely wiring, short, or no pull-ups/power.");
  TEST_ASSERT_TRUE_MESSAGE(found27 || found3f,
                           "Neither 0x27 nor 0x3F responded. Check LCD backpack power/wiring.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  UNITY_BEGIN();
  RUN_TEST(test_i2c_bus_idle_and_common_lcd_addresses);
  UNITY_END();
}

void loop() {
}

