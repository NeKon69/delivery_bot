#include <Arduino.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include <avr/pgmspace.h>
#include <unity.h>

#include "../test_lcd_common.h"

namespace {
const uint8_t kUtfRecode[] PROGMEM = {
    0x70, 0x63, 0xBF, 0x79, 0xE4, 0x78, 0xE5, 0xC0, 0xC1, 0xE6, 0xC2,
    0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0x41, 0xA0, 0x42, 0xA1, 0xE0, 0x45,
    0xA3, 0xA4, 0xA5, 0xA6, 0x4B, 0xA7, 0x4D, 0x48, 0x4F, 0xA8, 0x50,
    0x43, 0x54, 0xA9, 0xAA, 0x58, 0xE1, 0xAB, 0xAC, 0xE2, 0xAD, 0xAE,
    0x62, 0xAF, 0xB0, 0xB1, 0x61, 0xB2, 0xB3, 0xB4, 0xE3, 0x65, 0xB6,
    0xB7, 0xB8, 0xB9, 0xBA, 0xBB, 0xBC, 0xBD, 0x6F, 0xBE,
};

uint8_t nextMappedByte(const char *text, size_t &index, int8_t &utfHiChar) {
  const uint8_t value = static_cast<uint8_t>(text[index++]);

  if (utfHiChar >= 0) {
    if (value >= 0xC0 || value < 0x80) {
      const int8_t hiChar = utfHiChar;
      utfHiChar = -1;
      index -= 1;
      return static_cast<uint8_t>(0xD0 + hiChar);
    }

    const uint8_t low = value & 0x3F;
    const int8_t hiChar = utfHiChar;
    utfHiChar = -1;
    if (hiChar == 0 && low == 0x01) {
      return 0xA2;
    }
    if (hiChar == 1 && low == 0x11) {
      return 0xB5;
    }
    return pgm_read_byte_near(kUtfRecode + low);
  }

  if (value >= 0xD0 && value < 0xD2) {
    utfHiChar = static_cast<int8_t>(value - 0xD0);
    if (text[index] == '\0') {
      utfHiChar = -1;
      return value;
    }
    return nextMappedByte(text, index, utfHiChar);
  }

  return value;
}

void printMappedUtf8(LiquidCrystal_I2C *lcd, const char *text) {
  size_t index = 0;
  int8_t utfHiChar = -1;
  while (text[index] != '\0') {
    lcd->write(nextMappedByte(text, index, utfHiChar));
  }
}

void writeMappedLine(LiquidCrystal_I2C *lcd, uint8_t row, const char *text) {
  lcd->setCursor(0, row);
  for (uint8_t i = 0; i < LCD_COLS; i++) {
    lcd->write(' ');
  }
  lcd->setCursor(0, row);
  printMappedUtf8(lcd, text);
}

void showWordProbePage(LiquidCrystal_I2C *lcd) {
  lcd->clear();
  writeMappedLine(lcd, 0, "Проба кириллицы");
  writeMappedLine(lcd, 1, "Шкаф Бокс Карта");
  writeMappedLine(lcd, 2, "Жду выдачу Ёёж");
  writeMappedLine(lcd, 3, "Сверь буквы");
  Serial.println("[cyr_probe] Page 1: Russian words using LiquidCrystalRus mapping");
  delay(5000);
}

void showBytePage(LiquidCrystal_I2C *lcd, uint8_t startByte, const char *label) {
  char line0[21];
  snprintf(line0, sizeof(line0), "%s %02X-%02X", label, startByte, startByte + 15);

  lcd->clear();
  lcd->setCursor(0, 0);
  lcd->print(line0);

  lcd->setCursor(0, 1);
  for (uint8_t i = 0; i < 16; i++) {
    lcd->write(startByte + i);
  }

  lcd->setCursor(0, 2);
  for (uint8_t i = 0; i < 16; i++) {
    if (i > 0) {
      lcd->write(' ');
    }
    const uint8_t nibble = i & 0x0F;
    lcd->print(nibble, HEX);
  }

  lcd->setCursor(0, 3);
  lcd->print("See Serial notes");

  Serial.print("[cyr_probe] ");
  Serial.print(label);
  Serial.print(" bytes ");
  Serial.print(startByte, HEX);
  Serial.print("-");
  Serial.println(startByte + 15, HEX);
  delay(4000);
}
}  // namespace

void test_cyrillic_probe_pages() {
  int addr = -1;
  LiquidCrystal_I2C *lcd = initDetectedLcd(addr);
  TEST_ASSERT_NOT_NULL_MESSAGE(lcd, "LCD not detected.");

  Serial.print("[cyr_probe] LCD address: 0x");
  Serial.println(addr, HEX);
  Serial.println("[cyr_probe] Compare Russian words to expected spelling.");
  Serial.println("[cyr_probe] Then note which raw byte page looks closest to Cyrillic on your LCD.");

  showWordProbePage(lcd);
  showBytePage(lcd, 0xA0, "Page A");
  showBytePage(lcd, 0xB0, "Page B");
  showBytePage(lcd, 0xC0, "Page C");
  showBytePage(lcd, 0xD0, "Page D");
  showBytePage(lcd, 0xE0, "Page E");

  lcd->clear();
  writeMappedLine(lcd, 0, "Проба завершена");
  writeMappedLine(lcd, 1, "Смотри Serial");
  writeMappedLine(lcd, 2, "Запиши лучшую");
  writeMappedLine(lcd, 3, "страницу ROM");

  delete lcd;
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  UNITY_BEGIN();
  RUN_TEST(test_cyrillic_probe_pages);
  UNITY_END();
}

void loop() {
}
