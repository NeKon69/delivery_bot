#include <Arduino.h>
#include <unity.h>

#include "../test_config.h"

struct SwitchSnapshot {
  int idle_level;
  int pressed_level;
  bool captured_idle;
  bool captured_pressed;
};

static bool waitForStableLevel(uint8_t pin, int target, unsigned long timeout_ms) {
  const unsigned long start = millis();
  while (millis() - start < timeout_ms) {
    if (digitalRead(pin) == target) {
      int stable_reads = 0;
      for (int i = 0; i < 12; i++) {
        if (digitalRead(pin) == target) {
          stable_reads++;
        }
        delay(4);
      }
      if (stable_reads >= 10) {
        return true;
      }
    }
    delay(5);
  }
  return false;
}

static SwitchSnapshot characterizeSwitch(uint8_t pin, const char *label) {
  SwitchSnapshot snap = {-1, -1, false, false};

  Serial.println("--------------------------------");
  Serial.print(label);
  Serial.println(": release the switch now.");
  delay(1200);
  snap.idle_level = digitalRead(pin);
  snap.captured_idle = true;

  Serial.print(label);
  Serial.print(" idle level = ");
  Serial.println(snap.idle_level == HIGH ? "HIGH" : "LOW");

  Serial.print(label);
  Serial.println(": press and hold switch now...");
  if (waitForStableLevel(pin, snap.idle_level == HIGH ? LOW : HIGH, 10000)) {
    snap.pressed_level = digitalRead(pin);
    snap.captured_pressed = true;
    Serial.print(label);
    Serial.print(" pressed level = ");
    Serial.println(snap.pressed_level == HIGH ? "HIGH" : "LOW");
  } else {
    Serial.print(label);
    Serial.println(" did not change level during press window.");
  }

  Serial.print(label);
  Serial.println(": release switch.");
  delay(1000);
  return snap;
}

static void printInference(const char *label, const SwitchSnapshot &snap) {
  if (!snap.captured_idle || !snap.captured_pressed) {
    Serial.print(label);
    Serial.println(" => unable to infer (no clear state transition).");
    return;
  }

  if (snap.idle_level == HIGH && snap.pressed_level == LOW) {
    Serial.print(label);
    Serial.println(" => behaves as NO with INPUT_PULLUP (active LOW when pressed).");
    return;
  }

  if (snap.idle_level == LOW && snap.pressed_level == HIGH) {
    Serial.print(label);
    Serial.println(" => behaves as NC with INPUT_PULLUP (active HIGH when pressed).");
    return;
  }

  Serial.print(label);
  Serial.println(" => ambiguous behavior; check wiring/board electronics.");
}

void test_identify_switch_behavior_on_configured_pins() {
  pinMode(SWITCH1_PIN, INPUT_PULLUP);
  pinMode(SWITCH2_PIN, INPUT_PULLUP);

  Serial.println("Switch identification test on configured pins");
  Serial.println("This test infers NO/NC behavior based on idle and pressed levels.");
  Serial.print("SW1 pin: D");
  Serial.println(SWITCH1_PIN);
  Serial.print("SW2 pin: D");
  Serial.println(SWITCH2_PIN);

  SwitchSnapshot sw1 = characterizeSwitch(SWITCH1_PIN, "SW1");
  SwitchSnapshot sw2 = characterizeSwitch(SWITCH2_PIN, "SW2");

  Serial.println("==== Inference Summary ====");
  printInference("SW1", sw1);
  printInference("SW2", sw2);

  TEST_ASSERT_TRUE_MESSAGE(sw1.captured_idle, "SW1 idle level not captured.");
  TEST_ASSERT_TRUE_MESSAGE(sw2.captured_idle, "SW2 idle level not captured.");
}

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  UNITY_BEGIN();
  RUN_TEST(test_identify_switch_behavior_on_configured_pins);
  UNITY_END();
}

void loop() {
}
