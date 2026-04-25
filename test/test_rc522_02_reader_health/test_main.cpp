#include <Arduino.h>
#include <SPI.h>
#include <unity.h>
#include <MFRC522.h>

#include "../test_config.h"

MFRC522 mfrc522(RC522_SS_PIN, RC522_RST_PIN);

static bool isValidVersion(byte version) {
  return version != 0x00 && version != 0xFF;
}

void test_reader_stays_responsive_without_card() {
  mfrc522.PCD_Init();
  delay(50);

  const int checks = 30;
  for (int i = 0; i < checks; ++i) {
    byte version = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
    if (!isValidVersion(version)) {
      Serial.print("Invalid version read at iteration ");
      Serial.println(i);
    }
    TEST_ASSERT_TRUE_MESSAGE(isValidVersion(version), "RC522 communication dropped.");
    delay(100);
  }
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  SPI.begin();
  delay(100);

  UNITY_BEGIN();
  RUN_TEST(test_reader_stays_responsive_without_card);
  UNITY_END();
}

void loop() {
}

