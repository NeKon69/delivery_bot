/**
 * UIController.h - Service Layer
 * Manages the LCD1602 Display and 4x4 Keypad Matrix.
 */

#ifndef UI_CONTROLLER_H
#define UI_CONTROLLER_H

#include "Config.h"
#include <Arduino.h>
#include <Keypad.h>
#include <LiquidCrystal.h>

class UIController {
public:
  UIController();

  /**
   * Initializes the LCD and Keypad hardware.
   */
  void begin();

  /**
   * Updates the UI state (polls Keypad). Call in main loop.
   */
  void update();

  /**
   * Displays text on a specific row.
   * @param row  0 or 1
   * @param text The string to display (auto-truncated to 16 chars)
   */
  void display(uint8_t row, const char *text);

  /**
   * Clears the LCD screen.
   */
  void clear();

private:
  LiquidCrystal _lcd;

  // Keypad Setup
  static const byte ROWS = 4;
  static const byte COLS = 4;
  char _keys[ROWS][COLS] = {{'1', '2', '3', 'A'},
                            {'4', '5', '6', 'B'},
                            {'7', '8', '9', 'C'},
                            {'*', '0', '#', 'D'}};
  byte _rowPins[ROWS] = {30, 31, 32, 33}; // Defined in Config.h normally
  byte _colPins[COLS] = {34, 35, 36, 37};
  Keypad _keypad;

  // Internal helper for truncation
  void safePrint(const char *text);
};

#endif
