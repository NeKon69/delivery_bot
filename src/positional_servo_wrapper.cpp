#include "positional_servo_wrapper.h"

#include "runtime_config.h"

PositionalServoWrapper::PositionalServoWrapper(uint8_t signal_pin,
                                               uint8_t open_angle,
                                               uint8_t close_angle)
    : signal_pin_(signal_pin), open_angle_(open_angle),
      close_angle_(close_angle) {}

void PositionalServoWrapper::attach() { servo_.attach(signal_pin_); }

void PositionalServoWrapper::detach() { servo_.detach(); }

bool PositionalServoWrapper::attached() { return servo_.attached(); }

void PositionalServoWrapper::setAngle(uint8_t angle) {
  clearQueue();
  writeNow(angle);
}

void PositionalServoWrapper::open() {
  clearQueue();
  enqueueAngle(open_angle_, 0);
  enqueueAngle(180, SERVO_OPEN_TRANSITION_MS);
}

void PositionalServoWrapper::close() {
  clearQueue();
  enqueueAngle(close_angle_, 0);
}

void PositionalServoWrapper::update() {
  if (queue_count_ == 0) {
    return;
  }
  const unsigned long now = millis();
  if ((long)(now - queue_[0].execute_at_ms) < 0) {
    return;
  }

  writeNow(queue_[0].angle);

  for (uint8_t i = 1; i < queue_count_; i++) {
    queue_[i - 1] = queue_[i];
  }
  queue_count_--;
}

void PositionalServoWrapper::clearQueue() { queue_count_ = 0; }

bool PositionalServoWrapper::enqueueAngle(uint8_t angle,
                                          unsigned long delay_ms) {
  if (queue_count_ >= QUEUE_CAPACITY) {
    return false;
  }
  queue_[queue_count_].angle = angle;
  queue_[queue_count_].execute_at_ms = millis() + delay_ms;
  queue_count_++;
  return true;
}

void PositionalServoWrapper::writeNow(uint8_t angle) { servo_.write(angle); }
