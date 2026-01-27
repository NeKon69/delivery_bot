
/**
 * MotorController.cpp - Service Layer Implementation
 */

#include "MotorController.h"

MotorController::MotorController()
    : _currentPWM_L(0), _currentPWM_R(0), _targetPWM_L(0), _targetPWM_R(0),
      _dirL(0), _dirR(0), _lastRampTime(0), _moveEndTime(0) {}

void MotorController::begin() {
  pinMode(PIN_MOT_L_EN, OUTPUT);
  pinMode(PIN_MOT_L_1, OUTPUT);
  pinMode(PIN_MOT_L_2, OUTPUT);

  pinMode(PIN_MOT_R_EN, OUTPUT);
  pinMode(PIN_MOT_R_1, OUTPUT);
  pinMode(PIN_MOT_R_2, OUTPUT);

  stop(true); // Ensure motors are off on boot
}

void MotorController::move(int8_t leftDir, int8_t rightDir, int speed,
                           uint32_t duration) {
  _dirL = leftDir;
  _dirR = rightDir;
  _targetPWM_L = speed;
  _targetPWM_R = speed;

  if (duration > 0) {
    _moveEndTime = millis() + duration;
  } else {
    _moveEndTime = 0; // Infinite move
  }
}

void MotorController::stop(bool immediate) {
  _targetPWM_L = 0;
  _targetPWM_R = 0;
  _moveEndTime = 0;

  if (immediate) {
    _currentPWM_L = 0;
    _currentPWM_R = 0;
    // Kill enable pins immediately
    analogWrite(PIN_MOT_L_EN, 0);
    analogWrite(PIN_MOT_R_EN, 0);
  }
}

void MotorController::update() {
  unsigned long now = millis();

  // 1. Handle Timed Moves
  if (_moveEndTime > 0 && now >= _moveEndTime) {
    stop(false); // Begin soft stop
  }

  // 2. Handle Ramping (Non-blocking)
  if (now - _lastRampTime >= RAMP_INTERVAL_MS) {
    _lastRampTime = now;

    // Ramp Left
    if (_currentPWM_L < _targetPWM_L)
      _currentPWM_L++;
    else if (_currentPWM_L > _targetPWM_L)
      _currentPWM_L--;

    // Ramp Right
    if (_currentPWM_R < _targetPWM_R)
      _currentPWM_R++;
    else if (_currentPWM_R > _targetPWM_R)
      _currentPWM_R--;

    // Apply to hardware
    applyHardwarePins(PIN_MOT_L_EN, PIN_MOT_L_1, PIN_MOT_L_2, _dirL,
                      _currentPWM_L);
    applyHardwarePins(PIN_MOT_R_EN, PIN_MOT_R_1, PIN_MOT_R_2, _dirR,
                      _currentPWM_R);
  }
}

void MotorController::applyHardwarePins(uint8_t en, uint8_t in1, uint8_t in2,
                                        int8_t dir, int pwm) {
  // 1. Set Direction Pins
  if (dir > 0) { // Forward
    digitalWrite(in1, HIGH);
    digitalWrite(in2, LOW);
  } else if (dir < 0) { // Backward
    digitalWrite(in1, LOW);
    digitalWrite(in2, HIGH);
  } else { // Neutral/Stop
    digitalWrite(in1, LOW);
    digitalWrite(in2, LOW);
  }

  // 2. Write PWM (Speed)
  analogWrite(en, pwm);
}
