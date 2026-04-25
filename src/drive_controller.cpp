#include "drive_controller.h"

#include "runtime_config.h"

void DriveController::begin() {
  pinMode(MOTOR_RIGHT_DIR_PIN, OUTPUT);
  pinMode(MOTOR_RIGHT_PWM_PIN, OUTPUT);
  pinMode(MOTOR_LEFT_DIR_PIN, OUTPUT);
  pinMode(MOTOR_LEFT_PWM_PIN, OUTPUT);
  stop();
}

void DriveController::update() {
  if (current_action_ == MotionAction::Idle) {
    return;
  }

  if ((long)(millis() - action_ends_at_ms_) >= 0) {
    completed_action_ = actionName_(current_action_);
    stop();
  }
}

void DriveController::stop() {
  analogWrite(MOTOR_RIGHT_PWM_PIN, 0);
  analogWrite(MOTOR_LEFT_PWM_PIN, 0);
  current_action_ = MotionAction::Idle;
  action_ends_at_ms_ = 0;
}

bool DriveController::startAction(const String &action, unsigned long durationOverrideMs) {
  if (busy()) {
    return false;
  }

  if (action == "forward_cell") {
    applyMotion_(MOTOR_RIGHT_FORWARD_DIR, MOTOR_FORWARD_PWM, MOTOR_LEFT_FORWARD_DIR, MOTOR_FORWARD_PWM);
    startTimedAction_(MotionAction::ForwardCell,
                      durationOverrideMs > 0 ? durationOverrideMs : MOTION_FORWARD_CELL_MS);
    return true;
  }

  if (action == "reverse_cell") {
    applyMotion_(MOTOR_RIGHT_REVERSE_DIR, MOTOR_FORWARD_PWM, MOTOR_LEFT_REVERSE_DIR, MOTOR_FORWARD_PWM);
    startTimedAction_(MotionAction::ReverseCell,
                      durationOverrideMs > 0 ? durationOverrideMs : MOTION_REVERSE_CELL_MS);
    return true;
  }

  if (action == "turn_left") {
    applyMotion_(MOTOR_RIGHT_FORWARD_DIR, MOTOR_TURN_PWM, MOTOR_LEFT_REVERSE_DIR, MOTOR_TURN_PWM);
    startTimedAction_(MotionAction::TurnLeft,
                      durationOverrideMs > 0 ? durationOverrideMs : MOTION_TURN_LEFT_MS);
    return true;
  }

  if (action == "turn_right") {
    applyMotion_(MOTOR_RIGHT_REVERSE_DIR, MOTOR_TURN_PWM, MOTOR_LEFT_FORWARD_DIR, MOTOR_TURN_PWM);
    startTimedAction_(MotionAction::TurnRight,
                      durationOverrideMs > 0 ? durationOverrideMs : MOTION_TURN_RIGHT_MS);
    return true;
  }

  if (action == "stop") {
    stop();
    completed_action_ = "stop";
    return true;
  }

  return false;
}

bool DriveController::busy() const { return current_action_ != MotionAction::Idle; }

bool DriveController::consumeCompletedAction(String &actionOut) {
  if (completed_action_.length() == 0) {
    return false;
  }
  actionOut = completed_action_;
  completed_action_ = "";
  return true;
}

const char *DriveController::currentAction() const { return actionName_(current_action_); }

void DriveController::applyMotion_(bool rightDir, uint8_t rightPwm, bool leftDir, uint8_t leftPwm) {
  digitalWrite(MOTOR_RIGHT_DIR_PIN, rightDir);
  analogWrite(MOTOR_RIGHT_PWM_PIN, rightPwm);
  digitalWrite(MOTOR_LEFT_DIR_PIN, leftDir);
  analogWrite(MOTOR_LEFT_PWM_PIN, leftPwm);
}

void DriveController::startTimedAction_(MotionAction action, unsigned long durationMs) {
  current_action_ = action;
  action_ends_at_ms_ = millis() + durationMs;
}

const char *DriveController::actionName_(MotionAction action) const {
  switch (action) {
    case MotionAction::ForwardCell:
      return "forward_cell";
    case MotionAction::ReverseCell:
      return "reverse_cell";
    case MotionAction::TurnLeft:
      return "turn_left";
    case MotionAction::TurnRight:
      return "turn_right";
    case MotionAction::Idle:
    default:
      return "idle";
  }
}
