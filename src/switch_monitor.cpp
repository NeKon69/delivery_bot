#include "switch_monitor.h"

#include "runtime_config.h"

void SwitchMonitor::begin() {
  pinMode(SWITCH1_PIN, INPUT_PULLUP);
  pinMode(SWITCH2_PIN, INPUT_PULLUP);
  last_pressed_[0] = readPressed_(1);
  last_pressed_[1] = readPressed_(2);
}

void SwitchMonitor::update() {
  for (uint8_t box = 1; box <= 2; box++) {
    const bool pressed = readPressed_(box);
    const uint8_t index = box - 1;
    if (pressed != last_pressed_[index]) {
      last_pressed_[index] = pressed;
      enqueue_(box, pressed);
    }
  }
}

bool SwitchMonitor::pollEvent(SwitchEvent &eventOut) {
  if (queued_count_ == 0) {
    return false;
  }

  eventOut = queued_[0];
  for (uint8_t i = 1; i < queued_count_; i++) {
    queued_[i - 1] = queued_[i];
  }
  queued_count_--;
  return true;
}

bool SwitchMonitor::isPressed(uint8_t box) const { return readPressed_(box); }

void SwitchMonitor::enqueue_(uint8_t box, bool pressed) {
  if (queued_count_ >= EVENT_QUEUE_CAPACITY) {
    return;
  }
  queued_[queued_count_].box = box;
  queued_[queued_count_].pressed = pressed;
  queued_count_++;
}

bool SwitchMonitor::readPressed_(uint8_t box) const {
  const uint8_t pin = box == 1 ? SWITCH1_PIN : SWITCH2_PIN;
  return digitalRead(pin) == LOW;
}
