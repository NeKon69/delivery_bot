#include <Arduino.h>
#include <Keypad.h>
#include <unity.h>

#include "../test_config.h"

static constexpr byte KEYPAD_ROWS = 4;
static constexpr byte KEYPAD_COLS = 4;

static byte rowPins[KEYPAD_ROWS] = {45, 8, 9, 10};
static byte colPins[KEYPAD_COLS] = {11, 12, 46, 47};

static char keypadMap[KEYPAD_ROWS][KEYPAD_COLS] = {
    {'1', '2', '3', 'A'},
    {'4', '5', '6', 'B'},
    {'7', '8', '9', 'C'},
    {'*', '0', '#', 'D'},
};

static constexpr char EXPECTED_SEQUENCE[16] = {
    '1', '2', '3', 'A', '4', '5', '6', 'B',
    '7', '8', '9', 'C', '*', '0', '#', 'D',
};

static Keypad keypad = Keypad(makeKeymap(keypadMap), rowPins, colPins, KEYPAD_ROWS, KEYPAD_COLS);

static const char *stateToText(KeyState state) {
  switch (state) {
    case IDLE:
      return "IDLE";
    case PRESSED:
      return "PRESSED";
    case HOLD:
      return "HOLD";
    case RELEASED:
      return "RELEASED";
    default:
      return "UNKNOWN";
  }
}

static int indexOfKey(char ch) {
  for (int i = 0; i < 16; i++) {
    if (EXPECTED_SEQUENCE[i] == ch) {
      return i;
    }
  }
  return -1;
}

static void printEvent(const Key &k) {
  const byte row = static_cast<byte>(k.kcode / KEYPAD_COLS);
  const byte col = static_cast<byte>(k.kcode % KEYPAD_COLS);

  Serial.print("KEY ");
  Serial.print(k.kchar);
  Serial.print(" -> ");
  Serial.print(stateToText(k.kstate));
  Serial.print(" [r");
  Serial.print(row);
  Serial.print(" c");
  Serial.print(col);
  Serial.print("] pins(");
  Serial.print(rowPins[row]);
  Serial.print(",");
  Serial.print(colPins[col]);
  Serial.println(")");
}

static uint16_t captureEvents(unsigned long windowMs) {
  uint16_t pressOrHoldEvents = 0;
  const unsigned long start = millis();
  while (millis() - start < windowMs) {
    if (!keypad.getKeys()) {
      delay(5);
      continue;
    }

    for (byte i = 0; i < LIST_MAX; i++) {
      if (!keypad.key[i].stateChanged) {
        continue;
      }

      printEvent(keypad.key[i]);
      if (keypad.key[i].kstate == PRESSED || keypad.key[i].kstate == HOLD) {
        pressOrHoldEvents++;
      }
    }
    delay(5);
  }
  return pressOrHoldEvents;
}

static bool waitForSingleKeyCycle(char expected, unsigned long timeoutMs) {
  bool sawPress = false;
  bool sawRelease = false;
  uint16_t unexpectedPresses = 0;

  const unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    if (!keypad.getKeys()) {
      delay(5);
      continue;
    }

    for (byte i = 0; i < LIST_MAX; i++) {
      if (!keypad.key[i].stateChanged) {
        continue;
      }

      const Key &k = keypad.key[i];
      printEvent(k);

      if (k.kchar == expected && k.kstate == PRESSED) {
        sawPress = true;
      }
      if (k.kchar == expected && k.kstate == RELEASED) {
        sawRelease = true;
      }
      if (k.kchar != expected && (k.kstate == PRESSED || k.kstate == HOLD)) {
        unexpectedPresses++;
      }
    }

    if (sawPress && sawRelease && unexpectedPresses == 0) {
      return true;
    }

    delay(5);
  }

  Serial.print("Expected key '");
  Serial.print(expected);
  Serial.print("' failed. sawPress=");
  Serial.print(sawPress ? "yes" : "no");
  Serial.print(" sawRelease=");
  Serial.print(sawRelease ? "yes" : "no");
  Serial.print(" unexpectedPresses=");
  Serial.println(unexpectedPresses);
  return false;
}

static bool waitForHoldAndRelease(char expected, unsigned long timeoutMs) {
  bool sawPress = false;
  bool sawHold = false;
  bool sawRelease = false;

  const unsigned long start = millis();
  while (millis() - start < timeoutMs) {
    if (!keypad.getKeys()) {
      delay(5);
      continue;
    }

    for (byte i = 0; i < LIST_MAX; i++) {
      if (!keypad.key[i].stateChanged) {
        continue;
      }

      const Key &k = keypad.key[i];
      printEvent(k);

      if (k.kchar != expected) {
        continue;
      }

      if (k.kstate == PRESSED) {
        sawPress = true;
      } else if (k.kstate == HOLD) {
        sawHold = true;
      } else if (k.kstate == RELEASED) {
        sawRelease = true;
      }
    }

    if (sawPress && sawHold && sawRelease) {
      return true;
    }
    delay(5);
  }

  Serial.print("Hold test failed for '");
  Serial.print(expected);
  Serial.print("' sawPress=");
  Serial.print(sawPress ? "yes" : "no");
  Serial.print(" sawHold=");
  Serial.print(sawHold ? "yes" : "no");
  Serial.print(" sawRelease=");
  Serial.println(sawRelease ? "yes" : "no");
  return false;
}

void test_keypad_full_matrix_validation() {
  keypad.setDebounceTime(20);
  keypad.setHoldTime(500);

  Serial.println("4x4 keypad extensive validation");
  Serial.print("Rows: ");
  for (byte i = 0; i < KEYPAD_ROWS; i++) {
    Serial.print(rowPins[i]);
    Serial.print(i < KEYPAD_ROWS - 1 ? ',' : '\n');
  }
  Serial.print("Cols: ");
  for (byte i = 0; i < KEYPAD_COLS; i++) {
    Serial.print(colPins[i]);
    Serial.print(i < KEYPAD_COLS - 1 ? ',' : '\n');
  }

  Serial.println("Step 1/3: Do NOT touch keypad for 3s (stuck/noise check)");
  const uint16_t idleEvents = captureEvents(3000);
  TEST_ASSERT_EQUAL_UINT16_MESSAGE(0, idleEvents, "Unexpected press while idle (possible stuck key/short).\n");

  Serial.println("Step 2/3: Press each key once in prompted order.");
  uint8_t passed = 0;
  for (int i = 0; i < 16; i++) {
    const char expected = EXPECTED_SEQUENCE[i];
    Serial.print("Press and release '");
    Serial.print(expected);
    Serial.println("' now...");

    if (waitForSingleKeyCycle(expected, 12000)) {
      passed++;
      Serial.println("OK");
    } else {
      Serial.println("FAIL");
    }
  }

  Serial.print("Per-key pass count: ");
  Serial.print(passed);
  Serial.println("/16");
  TEST_ASSERT_EQUAL_UINT8_MESSAGE(16, passed, "Not all keys passed individual press/release validation.");

  Serial.println("Step 3/3: Hold '5' for >0.5s, then release.");
  const bool holdOk = waitForHoldAndRelease('5', 12000);
  TEST_ASSERT_TRUE_MESSAGE(holdOk, "Hold behavior failed for key '5'.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  UNITY_BEGIN();
  RUN_TEST(test_keypad_full_matrix_validation);
  UNITY_END();
}

void loop() {
}
