#include <Arduino.h>
#include <Wire.h>
#include <unity.h>

#include "../test_lcd_common.h"

void test_cursor_clear_and_home() {
  int addr = -1;
  LiquidCrystal_I2C *lcd = initDetectedLcd(addr);
  TEST_ASSERT_NOT_NULL_MESSAGE(lcd, "LCD not detected.");

  lcd->setCursor(5, 1);
  lcd->print("CURSOR");
  delay(1500);

  lcd->setCursor(10, 2);
  lcd->print("MOVE");
  delay(1500);

  lcd->clear();
  lcd->setCursor(0, 0);
  lcd->print("After clear");
  delay(1200);

  lcd->home();
  lcd->print(" + home OK");
  delay(2000);

  delete lcd;
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  UNITY_BEGIN();
  RUN_TEST(test_cursor_clear_and_home);
  UNITY_END();
}

void loop() {
}

