/**
 * BoxManager.h - Service Layer
 * Manages the logical state of robot storage compartments.
 */

#ifndef BOX_MANAGER_H
#define BOX_MANAGER_H

#include "Config.h"
#include <Arduino.h>
#include <Servo.h>

/**
 * Represents a single physical box unit.
 */
class Box {
public:
  Box();

  /**
   * @param id        Numeric ID for protocol reporting (1, 2, etc.)
   * @param servoPin  PWM pin for the lock servo
   * @param limitPin  Digital pin for the door limit switch
   */
  void init(uint8_t id, uint8_t servoPin, uint8_t limitPin);

  void open();
  void close();

  // Non-blocking sensor check
  void update();

  // Getters for status
  bool isDoorClosed() const { return _lastLimitState; }
  bool isLocked() const { return _isLocked; }
  uint8_t getId() const { return _id; }

private:
  uint8_t _id;
  uint8_t _servoPin;
  uint8_t _limitPin;
  Servo _servo;

  bool _isLocked;
  bool _lastLimitState;
  unsigned long _lastDebounceTime;
  const uint8_t _debounceDelay = 50; // ms
};

/**
 * Orchestrator for all boxes on the robot.
 */
class BoxManager {
public:
  BoxManager();
  void begin();
  void update(); // Calls update on all boxes

  /**
   * Sets lock state for a specific box.
   * @param boxId 1-indexed ID
   * @param lock  True to lock, False to open
   */
  void setBoxState(uint8_t boxId, bool lock);

private:
  Box _boxes[BOX_COUNT];
};

#endif
