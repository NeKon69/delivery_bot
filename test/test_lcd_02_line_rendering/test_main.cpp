#include <Arduino.h>
#include <Wire.h>
#include <unity.h>

#include "../test_lcd_common.h"

void test_line_rendering_all_rows() {
  int addr = -1;
  LiquidCrystal_I2C *lcd = initDetectedLcd(addr);
  TEST_ASSERT_NOT_NULL_MESSAGE(lcd, "LCD not detected.");

  lcd->setCursor(0, 0);
  lcd->print("Row1: 1234567890");
  lcd->setCursor(0, 1);
  lcd->print("Row2: abcdefghij");
  lcd->setCursor(0, 2);
  lcd->print("Row3: !@#$%^&*()");
  lcd->setCursor(0, 3);
  lcd->print("Row4: PASS CHECK");
  delay(3500);

  delete lcd;
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  UNITY_BEGIN();
  RUN_TEST(test_line_rendering_all_rows);
  UNITY_END();
}

void loop() {
}

