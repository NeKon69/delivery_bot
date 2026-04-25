#pragma once

#include <Arduino.h>

class DriveController {
 public:
  void begin();
  void update();
  void stop();

  bool startAction(const String &action, unsigned long durationOverrideMs = 0);
  bool busy() const;
  bool consumeCompletedAction(String &actionOut);
  const char *currentAction() const;

 private:
  enum class MotionAction : uint8_t { Idle, ForwardCell, ReverseCell, TurnLeft, TurnRight };

  MotionAction current_action_ = MotionAction::Idle;
  String completed_action_;
  unsigned long action_ends_at_ms_ = 0;

  void applyMotion_(bool rightDir, uint8_t rightPwm, bool leftDir, uint8_t leftPwm);
  void startTimedAction_(MotionAction action, unsigned long durationMs);
  const char *actionName_(MotionAction action) const;
};
