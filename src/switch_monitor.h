#pragma once

#include <Arduino.h>

struct SwitchEvent {
  uint8_t box;
  bool pressed;
};

class SwitchMonitor {
 public:
  void begin();
  void update();
  bool pollEvent(SwitchEvent &eventOut);
  bool isPressed(uint8_t box) const;

 private:
  static constexpr uint8_t EVENT_QUEUE_CAPACITY = 4;

  bool last_pressed_[2] = {false, false};
  SwitchEvent queued_[EVENT_QUEUE_CAPACITY];
  uint8_t queued_count_ = 0;

  void enqueue_(uint8_t box, bool pressed);
  bool readPressed_(uint8_t box) const;
};
