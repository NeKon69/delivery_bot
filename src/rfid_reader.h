#pragma once

#include <Arduino.h>

class MFRC522;

class RfidReader {
 public:
  enum class PollStatus : uint8_t {
    NoCard,
    ReadFailed,
    RepeatSuppressed,
    ScanSuccess,
  };

  RfidReader();

  void begin();
  PollStatus pollUid(String &uidOut);
  bool consumeRecoveredSinceLastPoll();

 private:
  MFRC522 *reader_ = nullptr;
  String last_uid_;
  unsigned long last_uid_ms_ = 0;
  unsigned long last_recovery_ms_ = 0;
  bool recovered_since_last_poll_ = false;

  void recover_();
  static String uidToHex_(const MFRC522 &reader);
};
