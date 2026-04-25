#include <Arduino.h>
#include <SPI.h>
#include <unity.h>
#include <MFRC522.h>

#include "../test_config.h"

MFRC522 mfrc522(RC522_SS_PIN, RC522_RST_PIN);

static void printUid(const MFRC522::Uid &uid) {
  for (byte i = 0; i < uid.size; i++) {
    if (uid.uidByte[i] < 0x10) {
      Serial.print('0');
    }
    Serial.print(uid.uidByte[i], HEX);
    if (i + 1 < uid.size) {
      Serial.print(':');
    }
  }
}

void test_repeated_uid_reads_are_stable() {
  mfrc522.PCD_Init();
  delay(50);

  const int targetReads = 5;
  const unsigned long timeoutMs = 60000;
  const unsigned long start = millis();
  int successfulReads = 0;

  while (millis() - start < timeoutMs && successfulReads < targetReads) {
    if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
      delay(30);
      continue;
    }

    Serial.print("Read ");
    Serial.print(successfulReads + 1);
    Serial.print('/');
    Serial.print(targetReads);
    Serial.print(": ");
    printUid(mfrc522.uid);
    Serial.println();

    TEST_ASSERT_TRUE_MESSAGE(mfrc522.uid.size >= 4 && mfrc522.uid.size <= 10, "Unexpected UID size during stability test.");

    successfulReads++;
    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    delay(500);
  }

  TEST_ASSERT_EQUAL_MESSAGE(targetReads, successfulReads, "Not enough successful UID reads before timeout.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  SPI.begin();
  delay(100);
  Serial.println("Tap/remove cards repeatedly for stability test...");

  UNITY_BEGIN();
  RUN_TEST(test_repeated_uid_reads_are_stable);
  UNITY_END();
}

void loop() {
}

