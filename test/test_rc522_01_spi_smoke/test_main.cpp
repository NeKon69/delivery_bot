#include <Arduino.h>
#include <SPI.h>
#include <unity.h>
#include <MFRC522.h>

#include "../test_config.h"

MFRC522 mfrc522(RC522_SS_PIN, RC522_RST_PIN);

static bool isValidVersion(byte version) {
  return version != 0x00 && version != 0xFF;
}

void test_reader_version_register_is_valid() {
  mfrc522.PCD_Init();
  delay(50);
  byte version = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);

  Serial.print("RC522 VersionReg: 0x");
  Serial.println(version, HEX);
  TEST_ASSERT_TRUE_MESSAGE(isValidVersion(version), "RC522 not detected on SPI bus.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  SPI.begin();
  delay(100);

  UNITY_BEGIN();
  RUN_TEST(test_reader_version_register_is_valid);
  UNITY_END();
}

void loop() {
}

