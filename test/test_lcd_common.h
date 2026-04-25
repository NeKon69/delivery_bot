#pragma once

#include <Arduino.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#include "test_config.h"

static int findLcdAddress() {
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

static LiquidCrystal_I2C *initDetectedLcd(int &addrOut) {
  addrOut = findLcdAddress();
  if (addrOut < 0) {
    return nullptr;
  }

  auto *lcd = new LiquidCrystal_I2C((uint8_t)addrOut, LCD_COLS, LCD_ROWS);
  lcd->init();
  lcd->backlight();
  lcd->clear();
  lcd->setCursor(0, 0);
  return lcd;
}

