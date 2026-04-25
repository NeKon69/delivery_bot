#include "lcd_display.h"

#include <LiquidCrystal_I2C.h>
#include <Wire.h>

#include "runtime_config.h"

namespace {
const uint8_t kUtfRecode[] PROGMEM = {
    0x70, 0x63, 0xBF, 0x79, 0xE4, 0x78, 0xE5, 0xC0, 0xC1, 0xE6, 0xC2,
    0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0x41, 0xA0, 0x42, 0xA1, 0xE0, 0x45,
    0xA3, 0xA4, 0xA5, 0xA6, 0x4B, 0xA7, 0x4D, 0x48, 0x4F, 0xA8, 0x50,
    0x43, 0x54, 0xA9, 0xAA, 0x58, 0xE1, 0xAB, 0xAC, 0xE2, 0xAD, 0xAE,
    0x62, 0xAF, 0xB0, 0xB1, 0x61, 0xB2, 0xB3, 0xB4, 0xE3, 0x65, 0xB6,
    0xB7, 0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0x6F, 0xBE,
};

int detectLcdAddress() {
  const uint8_t common[] = {0x27, 0x3F};
  for (uint8_t i = 0; i < sizeof(common); i++) {
    Wire.beginTransmission(common[i]);
    if (Wire.endTransmission() == 0) {
      return common[i];
    }
  }

  for (uint8_t addr = 0x03; addr <= 0x77; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      return addr;
    }
  }

  return -1;
}

}  // namespace

void LcdDisplay::begin() {
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  address_ = detectLcdAddress();
  if (address_ < 0) {
    return;
  }

  lcd_ = new LiquidCrystal_I2C(static_cast<uint8_t>(address_), LCD_COLS, LCD_ROWS);
  lcd_->init();
  lcd_->backlight();
  lcd_->clear();

  lines_[0] = "LCD ready";
  lines_[1] = String("Addr: 0x") + String(address_, HEX);
  lines_[1].toUpperCase();
  lines_[2] = "Waiting for host";
  lines_[3] = "";
  redraw_();
}

bool LcdDisplay::available() const { return lcd_ != nullptr; }

int LcdDisplay::address() const { return address_; }

void LcdDisplay::clear() {
  for (uint8_t i = 0; i < LCD_ROWS; i++) {
    lines_[i] = "";
  }
  redraw_();
}

void LcdDisplay::setBacklight(bool enabled) {
  if (!available()) {
    return;
  }
  if (enabled) {
    lcd_->backlight();
  } else {
    lcd_->noBacklight();
  }
}

bool LcdDisplay::setLines(const String *lines, size_t count) {
  for (uint8_t i = 0; i < LCD_ROWS; i++) {
    lines_[i] = i < count ? normalizeLine_(lines[i]) : normalizeLine_("");
  }
  redraw_();
  return available();
}

bool LcdDisplay::setLine(uint8_t lineIndex, const String &text) {
  if (lineIndex >= LCD_ROWS) {
    return false;
  }
  lines_[lineIndex] = normalizeLine_(text);
  redraw_();
  return available();
}

void LcdDisplay::redraw_() {
  if (!available()) {
    return;
  }

  for (uint8_t i = 0; i < LCD_ROWS; i++) {
    writeEncodedLine_(i, lines_[i]);
  }
}

void LcdDisplay::writeEncodedLine_(uint8_t row, const String &text) {
  lcd_->setCursor(0, row);
  for (uint8_t i = 0; i < LCD_COLS; i++) {
    lcd_->write(' ');
  }

  lcd_->setCursor(0, row);
  uint16_t index = 0;
  uint8_t printed = 0;
  int8_t utfHiChar = -1;
  while (index < text.length() && printed < LCD_COLS) {
    lcd_->write(writeEncodedChar_(text, index, utfHiChar));
    printed++;
  }
}

uint8_t LcdDisplay::writeEncodedChar_(const String &text, uint16_t &index, int8_t &utfHiChar) {
  if (index >= text.length()) {
    return ' ';
  }

  uint8_t value = static_cast<uint8_t>(text[index++]);

  if (utfHiChar >= 0) {
    if (value >= 0xC0 || value < 0x80) {
      const int8_t hiChar = utfHiChar;
      utfHiChar = -1;
      index -= 1;
      return static_cast<uint8_t>(0xD0 + hiChar);
    }

    value &= 0x3F;
    utfHiChar = -1;
    if (value == 0x01 && static_cast<uint8_t>(text[index - 2]) == 0xD0) {
      return 0xA2;
    }
    if (value == 0x11 && static_cast<uint8_t>(text[index - 2]) == 0xD1) {
      return 0xB5;
    }
    return pgm_read_byte_near(kUtfRecode + value);
  }

  if (value >= 0xD0 && value < 0xD2) {
    utfHiChar = static_cast<int8_t>(value - 0xD0);
    if (index >= text.length()) {
      utfHiChar = -1;
      return value;
    }
    return writeEncodedChar_(text, index, utfHiChar);
  }

  return value;
}

String LcdDisplay::normalizeLine_(const String &text) const {
  String out = text;
  if (out.length() > LCD_COLS) {
    out.remove(LCD_COLS);
  }
  return out;
}
