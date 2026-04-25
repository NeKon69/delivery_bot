#pragma once

#include <Arduino.h>

#include "positional_servo_wrapper.h"

class LockController {
 public:
  LockController();

  void begin();
  void update();

  bool openBox(uint8_t boxId);
  bool closeBox(uint8_t boxId);
  bool setAngle(uint8_t boxId, uint8_t angle);
  const char *boxState(uint8_t boxId) const;

 private:
  enum class BoxState : uint8_t { Unknown, Open, Closed, CustomAngle };

  PositionalServoWrapper box1_;
  PositionalServoWrapper box2_;
  BoxState box_states_[2] = {BoxState::Unknown, BoxState::Unknown};

  PositionalServoWrapper *servoFor_(uint8_t boxId);
  BoxState *stateFor_(uint8_t boxId);
};
