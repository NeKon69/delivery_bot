#pragma once

#include <Arduino.h>
#include <Servo.h>

class PositionalServoWrapper {
 public:
  PositionalServoWrapper(uint8_t signal_pin, uint8_t open_angle = 0, uint8_t close_angle = 90);

  void attach();
  void detach();
  bool attached();

  void setAngle(uint8_t angle);
  void open();
  void close();
  void update();
  void clearQueue();

 private:
  struct QueuedAngle {
    uint8_t angle;
    unsigned long execute_at_ms;
  };

  static constexpr uint8_t QUEUE_CAPACITY = 4;

  bool enqueueAngle(uint8_t angle, unsigned long delay_ms);
  void writeNow(uint8_t angle);

  uint8_t signal_pin_;
  uint8_t open_angle_;
  uint8_t close_angle_;
  Servo servo_;
  QueuedAngle queue_[QUEUE_CAPACITY];
  uint8_t queue_count_ = 0;
};
