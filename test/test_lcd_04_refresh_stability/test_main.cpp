#include <Arduino.h>
#include <Wire.h>
#include <unity.h>

#include "../test_lcd_common.h"

void test_refresh_stability_counter() {
  int addr = -1;
  LiquidCrystal_I2C *lcd = initDetectedLcd(addr);
  TEST_ASSERT_NOT_NULL_MESSAGE(lcd, "LCD not detected.");

  lcd->setCursor(0, 0);
  lcd->print("Refresh stability");

  for (int i = 1; i <= 20; i++) {
    lcd->setCursor(0, 1);
    lcd->print("Count:            ");
    lcd->setCursor(7, 1);
    lcd->print(i);
    lcd->setCursor(0, 2);
    lcd->print("Addr: 0x");
    lcd->print(addr, HEX);
    delay(350);
  }

  lcd->setCursor(0, 3);
  lcd->print("No freeze: PASS");
  delay(1800);

  delete lcd;
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  UNITY_BEGIN();
  RUN_TEST(test_refresh_stability_counter);
  UNITY_END();
}

void loop() {
}

