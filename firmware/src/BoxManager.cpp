/**
 * BoxManager.cpp - Service Layer Implementation
 */

#include "BoxManager.h"

// --- BOX CLASS IMPLEMENTATION ---

Box::Box()
    : _id(0), _servoPin(0), _limitPin(0), _isLocked(true),
      _lastLimitState(false), _lastDebounceTime(0) {}

void Box::init(uint8_t id, uint8_t servoPin, uint8_t limitPin) {
  _id = id;
  _servoPin = servoPin;
  _limitPin = limitPin;

  pinMode(_limitPin, INPUT_PULLUP);
  _servo.attach(_servoPin);

  // Default state: Closed/Locked
  close();

  // Initial read (Limit switch is LOW when pressed/closed)
  _lastLimitState = !digitalRead(_limitPin);
}

void Box::open() {
  _servo.write(SERVO_OPEN_ANGLE);
  _isLocked = false;
}

void Box::close() {
  _servo.write(SERVO_CLOSE_ANGLE);
  _isLocked = true;
}

void Box::update() {
  // Read sensor (Inverted logic for Pull-up: LOW = Pressed/Closed)
  bool currentReading = !digitalRead(_limitPin);

  // Basic state change detection
  if (currentReading != _lastLimitState) {
    _lastLimitState = currentReading;

    // Report Event to Serial (Master Pi)
    // Format: EVT:LMT:ID:STATE\n
    Serial.print(F("EVT:LMT:"));
    Serial.print(_id);
    Serial.print(F(":"));
    Serial.println(_lastLimitState ? F("1") : F("0"));

    // Safety Check: If we think it's locked but door opens
    if (!_lastLimitState && _isLocked) {
      Serial.print(F("EVT:ALARM:BOX_FORCED:"));
      Serial.println(_id);
    }
  }
}

// --- BOXMANAGER CLASS IMPLEMENTATION ---

BoxManager::BoxManager() {}

void BoxManager::begin() {
  // Initialize boxes using pins from Config.h arrays
  for (uint8_t i = 0; i < BOX_COUNT; i++) {
    _boxes[i].init(i + 1, PINS_SERVO[i], PINS_LIMIT[i]);
  }
}

void BoxManager::update() {
  for (uint8_t i = 0; i < BOX_COUNT; i++) {
    _boxes[i].update();
  }
}

void BoxManager::setBoxState(uint8_t boxId, bool lock) {
  // Convert 1-based ID to 0-based index
  uint8_t index = boxId - 1;
  if (index < BOX_COUNT) {
    if (lock)
      _boxes[index].close();
    else
      _boxes[index].open();
  }
}
