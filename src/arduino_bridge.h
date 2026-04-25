#pragma once

#include <Arduino.h>

#include "drive_controller.h"
#include "keypad_reader.h"
#include "lcd_display.h"
#include "lock_controller.h"
#include "rfid_reader.h"
#include "serial_protocol.h"
#include "switch_monitor.h"

class ArduinoBridge {
 public:
  void begin();
  void update();

 private:
  SerialProtocol protocol_;
  DriveController drive_;
  LockController locks_;
  KeypadReader keypad_;
  LcdDisplay lcd_;
  RfidReader rfid_;
  SwitchMonitor switches_;

  void handleCommand_(const String &line);
  void handleJsonCommand_(const String &json);
  void handleCompactCommand_(const String &line);
  void emitReady_();
  void emitState_();
  void emitKeypadEvents_();
  void emitSwitchEvents_();
  void emitRfidEvents_();
  void emitDriveEvents_();
};
