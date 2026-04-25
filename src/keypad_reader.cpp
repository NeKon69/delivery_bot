#include "keypad_reader.h"

#include <Keypad.h>

#include "runtime_config.h"

namespace {
byte kRowPins[KEYPAD_ROWS] = {KEYPAD_WIRE_PINS[0], KEYPAD_WIRE_PINS[1], KEYPAD_WIRE_PINS[2],
                              KEYPAD_WIRE_PINS[3]};
byte kColPins[KEYPAD_COLS] = {KEYPAD_WIRE_PINS[4], KEYPAD_WIRE_PINS[5], KEYPAD_WIRE_PINS[6],
                              KEYPAD_WIRE_PINS[7]};
char kKeymap[KEYPAD_ROWS][KEYPAD_COLS] = {
    {KEYPAD_MAP[0][0], KEYPAD_MAP[0][1], KEYPAD_MAP[0][2], KEYPAD_MAP[0][3]},
    {KEYPAD_MAP[1][0], KEYPAD_MAP[1][1], KEYPAD_MAP[1][2], KEYPAD_MAP[1][3]},
    {KEYPAD_MAP[2][0], KEYPAD_MAP[2][1], KEYPAD_MAP[2][2], KEYPAD_MAP[2][3]},
    {KEYPAD_MAP[3][0], KEYPAD_MAP[3][1], KEYPAD_MAP[3][2], KEYPAD_MAP[3][3]},
};

Keypad gKeypad(makeKeymap(kKeymap), kRowPins, kColPins, KEYPAD_ROWS, KEYPAD_COLS);

const char *keyStateName(KeyState state) {
  switch (state) {
    case PRESSED:
      return "pressed";
    case HOLD:
      return "hold";
    case RELEASED:
      return "released";
    case IDLE:
    default:
      return "idle";
  }
}
}  // namespace

void KeypadReader::begin() {
  gKeypad.setHoldTime(KEYPAD_HOLD_MS);
  gKeypad.setDebounceTime(KEYPAD_DEBOUNCE_MS);
}

void KeypadReader::update() {
  if (!gKeypad.getKeys()) {
    return;
  }

  for (byte i = 0; i < LIST_MAX; i++) {
    if (!gKeypad.key[i].stateChanged) {
      continue;
    }
    enqueue_(gKeypad.key[i].kchar, keyStateName(gKeypad.key[i].kstate));
  }
}

bool KeypadReader::pollEvent(KeypadInputEvent &eventOut) {
  if (queued_count_ == 0) {
    return false;
  }

  eventOut.key = queued_keys_[0];
  eventOut.state = queued_states_[0];
  for (uint8_t i = 1; i < queued_count_; i++) {
    queued_keys_[i - 1] = queued_keys_[i];
    queued_states_[i - 1] = queued_states_[i];
  }
  queued_count_--;
  return true;
}

void KeypadReader::enqueue_(char key, const char *state) {
  if (queued_count_ >= EVENT_QUEUE_CAPACITY) {
    return;
  }
  queued_keys_[queued_count_] = key;
  queued_states_[queued_count_] = state;
  queued_count_++;
}
