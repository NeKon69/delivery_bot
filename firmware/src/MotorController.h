/**
 * MotorController.h - Service Layer
 * Handles L298N logic, PWM ramping, and timed movement.
 */

#ifndef MOTOR_CONTROLLER_H
#define MOTOR_CONTROLLER_H

#include "Config.h"
#include <Arduino.h>

class MotorController {
public:
  MotorController();

  /**
   * Initialize pin modes. Call in setup().
   */
  void begin();

  /**
   * Orchestrates movement.
   * @param leftDir   Direction for left motor (1: Fwd, -1: Bwd, 0: Stop)
   * @param rightDir  Direction for right motor (1: Fwd, -1: Bwd, 0: Stop)
   * @param speed     Target PWM (0-255)
   * @param duration  Time in ms before stopping (0 for infinite)
   */
  void move(int8_t leftDir, int8_t rightDir, int speed, uint32_t duration = 0);

  /**
   * Stops all movement.
   * @param immediate If true, bypasses ramping and kills power instantly.
   */
  void stop(bool immediate = false);

  /**
   * Main processing loop. Must be called in the main loop() frequently.
   */
  void update();

  /**
   * Status Check
   * @return true if motors are currently ramping or moving.
   */
  bool isMoving() const { return (_currentPWM_L > 0 || _currentPWM_R > 0); }

private:
  // Internal state
  int _currentPWM_L, _currentPWM_R;
  int _targetPWM_L, _targetPWM_R;

  // Direction tracking (used to set IN1/IN2 pins)
  int8_t _dirL, _dirR;

  // Timing
  unsigned long _lastRampTime;
  unsigned long _moveEndTime;

  /**
   * Low-level HAL method to write to pins.
   */
  void applyHardwarePins(uint8_t en, uint8_t in1, uint8_t in2, int8_t dir,
                         int pwm);
};

#endif
