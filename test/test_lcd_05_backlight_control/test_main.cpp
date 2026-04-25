#include <Arduino.h>
#include <Wire.h>
#include <unity.h>

#include "../test_lcd_common.h"

void test_backlight_toggle_control() {
  int addr = -1;
  LiquidCrystal_I2C *lcd = initDetectedLcd(addr);
  TEST_ASSERT_NOT_NULL_MESSAGE(lcd, "LCD not detected.");

  lcd->setCursor(0, 0);
  lcd->print("Backlight test");
  lcd->setCursor(0, 1);
  lcd->print("Should blink x3");
  delay(1200);

  for (int i = 0; i < 3; i++) {
    lcd->noBacklight();
    delay(700);
    lcd->backlight();
    delay(700);
  }

  lcd->setCursor(0, 2);
  lcd->print("Backlight: PASS");
  delay(1500);

  delete lcd;
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  UNITY_BEGIN();
  RUN_TEST(test_backlight_toggle_control);
  UNITY_END();
}

void loop() {
}

