#include <Arduino.h>
#include <Wire.h>
#include <unity.h>

#include "../test_lcd_common.h"

void test_detect_and_initialize_lcd() {
  int addr = -1;
  LiquidCrystal_I2C *lcd = initDetectedLcd(addr);
  TEST_ASSERT_NOT_NULL_MESSAGE(lcd, "LCD not detected on I2C bus.");

  Serial.print("LCD detected at 0x");
  Serial.println(addr, HEX);

  lcd->setCursor(0, 0);
  lcd->print("LCD detect: PASS");
  lcd->setCursor(0, 1);
  lcd->print("Addr: 0x");
  lcd->print(addr, HEX);
  lcd->setCursor(0, 2);
  lcd->print("20x4 init OK");
  delay(2500);

  delete lcd;
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }
  Wire.begin();
  Wire.setWireTimeout(25000, true);
  UNITY_BEGIN();
  RUN_TEST(test_detect_and_initialize_lcd);
  UNITY_END();
}

void loop() {
}

