#include "arduino_bridge.h"

namespace {
ArduinoBridge bridge;
}

#ifndef UNIT_TEST
void setup() { bridge.begin(); }

void loop() { bridge.update(); }
#endif
