#include <Arduino.h>
#include <MFRC522.h>
#include <SPI.h>
#include <unity.h>

#include "../test_config.h"

MFRC522 mfrc522(RC522_SS_PIN, RC522_RST_PIN);

static void printUid(const MFRC522::Uid &uid) {
  Serial.print("UID [");
  Serial.print(uid.size);
  Serial.print(" bytes]: ");
  for (byte i = 0; i < uid.size; i++) {
    if (uid.uidByte[i] < 0x10) {
      Serial.print('0');
    }
    Serial.print(uid.uidByte[i], HEX);
    Serial.print(' ');
  }
  Serial.println();
}

void test_reads_single_card_uid() {
  mfrc522.PCD_Init();
  delay(50);

  const unsigned long timeoutMs = 15000;
  const unsigned long start = millis();

  while (millis() - start < timeoutMs) {
    if (!mfrc522.PICC_IsNewCardPresent()) {
      delay(40);
      continue;
    }
    if (!mfrc522.PICC_ReadCardSerial()) {
      delay(40);
      continue;
    }

    printUid(mfrc522.uid);
    TEST_ASSERT_TRUE_MESSAGE(mfrc522.uid.size >= 4 && mfrc522.uid.size <= 10,
                             "Unexpected UID size.");

    mfrc522.PICC_HaltA();
    mfrc522.PCD_StopCrypto1();
    return;
  }

  TEST_FAIL_MESSAGE(
      "No card UID detected within timeout. Tap a card on reader.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  SPI.begin();
  delay(100);
  Serial.println("Tap an RFID card now...");

  UNITY_BEGIN();
  RUN_TEST(test_reads_single_card_uid);
  UNITY_END();
}

void loop() {}
