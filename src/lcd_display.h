#pragma once

#include <Arduino.h>

class LiquidCrystal_I2C;

class LcdDisplay {
 public:
  void begin();

  bool available() const;
  int address() const;
  void clear();
  void setBacklight(bool enabled);
  bool setLines(const String *lines, size_t count);
  bool setLine(uint8_t lineIndex, const String &text);

 private:
  LiquidCrystal_I2C *lcd_ = nullptr;
  int address_ = -1;

  void redraw_();
  void writeEncodedLine_(uint8_t row, const String &text);
  uint8_t writeEncodedChar_(const String &text, uint16_t &index, int8_t &utfHiChar);
  String normalizeLine_(const String &text) const;
  String lines_[4];
};
