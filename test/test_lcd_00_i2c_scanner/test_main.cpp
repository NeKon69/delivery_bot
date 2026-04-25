#include <Arduino.h>
#include <Wire.h>
#include <unity.h>

#include "../test_config.h"

void test_i2c_scan_for_devices() {
  Serial.println("I2C scan start (expect LCD backpack at 0x27 or 0x3F usually).");
  Wire.setWireTimeout(25000, true);
  Wire.clearWireTimeoutFlag();

  int found = 0;
  for (uint8_t address = 0x03; address <= 0x77; address++) {
    if ((address & 0x0F) == 0x00) {
      Serial.print("Scanning block starting 0x");
      Serial.println(address, HEX);
    }

    Wire.beginTransmission(address);
    uint8_t error = Wire.endTransmission();
    if (error == 0) {
      found++;
      Serial.print("Found device at 0x");
      if (address < 0x10) {
        Serial.print('0');
      }
      Serial.println(address, HEX);
    }

    if (Wire.getWireTimeoutFlag()) {
      Serial.println("I2C timeout detected while scanning. Bus may be held low.");
      Wire.clearWireTimeoutFlag();
      break;
    }
  }

  Serial.print("Total I2C devices found: ");
  Serial.println(found);
  TEST_ASSERT_GREATER_THAN_MESSAGE(0, found, "No I2C devices found. Check SDA/SCL wiring and power.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  Wire.begin();
  delay(100);

  UNITY_BEGIN();
  RUN_TEST(test_i2c_scan_for_devices);
  UNITY_END();
}

void loop() {
}
