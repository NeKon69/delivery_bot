#include "lock_controller.h"

#include "runtime_config.h"

LockController::LockController()
    : box1_(SERVO_BOX1_PIN, SERVO_OPEN_ANGLE, SERVO_CLOSE_ANGLE),
      box2_(SERVO_BOX2_PIN, SERVO_OPEN_ANGLE, SERVO_CLOSE_ANGLE) {}

void LockController::begin() {
  box1_.attach();
  box2_.attach();
}

void LockController::update() {
  box1_.update();
  box2_.update();
}

bool LockController::openBox(uint8_t boxId) {
  PositionalServoWrapper *servo = servoFor_(boxId);
  BoxState *state = stateFor_(boxId);
  if (servo == nullptr || state == nullptr) {
    return false;
  }
  servo->open();
  *state = BoxState::Open;
  return true;
}

bool LockController::closeBox(uint8_t boxId) {
  PositionalServoWrapper *servo = servoFor_(boxId);
  BoxState *state = stateFor_(boxId);
  if (servo == nullptr || state == nullptr) {
    return false;
  }
  servo->close();
  *state = BoxState::Closed;
  return true;
}

bool LockController::setAngle(uint8_t boxId, uint8_t angle) {
  PositionalServoWrapper *servo = servoFor_(boxId);
  BoxState *state = stateFor_(boxId);
  if (servo == nullptr || state == nullptr) {
    return false;
  }
  servo->setAngle(angle);
  *state = BoxState::CustomAngle;
  return true;
}

const char *LockController::boxState(uint8_t boxId) const {
  const uint8_t index = boxId >= 1 && boxId <= 2 ? boxId - 1 : 255;
  if (index > 1) {
    return "invalid";
  }

  switch (box_states_[index]) {
    case BoxState::Open:
      return "open";
    case BoxState::Closed:
      return "closed";
    case BoxState::CustomAngle:
      return "custom";
    case BoxState::Unknown:
    default:
      return "unknown";
  }
}

PositionalServoWrapper *LockController::servoFor_(uint8_t boxId) {
  switch (boxId) {
    case 1:
      return &box1_;
    case 2:
      return &box2_;
    default:
      return nullptr;
  }
}

LockController::BoxState *LockController::stateFor_(uint8_t boxId) {
  if (boxId < 1 || boxId > 2) {
    return nullptr;
  }
  return &box_states_[boxId - 1];
}
