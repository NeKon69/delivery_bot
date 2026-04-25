#pragma once

#include <Arduino.h>

struct KeypadInputEvent {
  char key;
  const char *state;
};

class KeypadReader {
 public:
  void begin();
  void update();
  bool pollEvent(KeypadInputEvent &eventOut);

 private:
  static constexpr uint8_t EVENT_QUEUE_CAPACITY = 8;

  char queued_keys_[EVENT_QUEUE_CAPACITY];
  const char *queued_states_[EVENT_QUEUE_CAPACITY];
  uint8_t queued_count_ = 0;

  void enqueue_(char key, const char *state);
};
