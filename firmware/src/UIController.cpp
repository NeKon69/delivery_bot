/**
 * UIController.cpp - Service Layer Implementation
 */

#include "UIController.h"

UIController::UIController()
    : _lcd(PIN_LCD_RS, PIN_LCD_EN, PIN_LCD_D4, PIN_LCD_D5, PIN_LCD_D6,
           PIN_LCD_D7),
      _keypad(makeKeymap(_keys), _rowPins, _colPins, ROWS, COLS) {}

void UIController::begin() {
  _lcd.begin(16, 2);
  _lcd.clear();
}

void UIController::display(uint8_t row, const char *text) {
  if (row > 1)
    return;

  _lcd.setCursor(0, row);

  // Clear the line first by printing spaces
  _lcd.print(F("                "));
  _lcd.setCursor(0, row);

  safePrint(text);
}

void UIController::clear() { _lcd.clear(); }

void UIController::safePrint(const char *text) {
  if (text == nullptr)
    return;

  // Print only up to 16 characters to prevent wrapping/glitches
  char buffer[17];
  strncpy(buffer, text, 16);
  buffer[16] = '\0'; // Force null termination

  _lcd.print(buffer);
}

void UIController::update() {
  // Poll Keypad (Non-blocking)
  char key = _keypad.getKey();

  if (key != NO_KEY) {
    // Report Keypress Event to Master Pi
    // Format: EVT:KEY:X\n
    Serial.print(F("EVT:KEY:"));
    Serial.println(key);
  }
}
