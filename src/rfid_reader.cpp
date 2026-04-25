#include "rfid_reader.h"

#include <MFRC522.h>
#include <SPI.h>

#include "runtime_config.h"

RfidReader::RfidReader() { reader_ = new MFRC522(RC522_SS_PIN, RC522_RST_PIN); }

void RfidReader::begin() {
  SPI.begin();
  recover_();
}

RfidReader::PollStatus RfidReader::pollUid(String &uidOut) {
  if (!reader_->PICC_IsNewCardPresent()) {
    return PollStatus::NoCard;
  }
  if (!reader_->PICC_ReadCardSerial()) {
    if (millis() - last_recovery_ms_ >= RFID_RECOVERY_COOLDOWN_MS) {
      recover_();
    }
    return PollStatus::ReadFailed;
  }

  const String uid = uidToHex_(*reader_);
  reader_->PICC_HaltA();
  reader_->PCD_StopCrypto1();

  if (uid == last_uid_ && millis() - last_uid_ms_ < RFID_REPEAT_SUPPRESS_MS) {
    return PollStatus::RepeatSuppressed;
  }

  last_uid_ = uid;
  last_uid_ms_ = millis();
  uidOut = uid;
  return PollStatus::ScanSuccess;
}

bool RfidReader::consumeRecoveredSinceLastPoll() {
  const bool recovered = recovered_since_last_poll_;
  recovered_since_last_poll_ = false;
  return recovered;
}

void RfidReader::recover_() {
  reader_->PCD_Init();
  delay(50);
  reader_->PICC_HaltA();
  reader_->PCD_StopCrypto1();
  last_recovery_ms_ = millis();
  recovered_since_last_poll_ = true;
}

String RfidReader::uidToHex_(const MFRC522 &reader) {
  String out;
  for (byte i = 0; i < reader.uid.size; i++) {
    if (reader.uid.uidByte[i] < 0x10) {
      out += '0';
    }
    out += String(reader.uid.uidByte[i], HEX);
  }
  out.toUpperCase();
  return out;
}
