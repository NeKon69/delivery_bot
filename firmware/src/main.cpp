/**
 * DELIVERY ROBOT - MAIN ARCHITECTURE
 */

#include "BoxManager.h"
#include "Config.h"
#include "MotorController.h"
#include "ProtocolHandler.h"
#include "UIController.h"

// Instantiate Services
MotorController motors;
BoxManager boxes;
UIController ui;

// Serial Buffer
char cmdBuffer[CMD_BUFFER_SIZE];
uint8_t bufferIdx = 0;
unsigned long lastSerialTime = 0;

void setup() {
  Serial.begin(SERIAL_BAUD);

  motors.begin();
  boxes.begin();
  ui.begin();

  ui.display(0, "ROBOT ONLINE");
  lastSerialTime = millis();
}

void handleCommand(ParsedCommand &cmd) {
  // 1. Motor Commands (MOV:ACTION:VALUE)
  if (strcmp(cmd.type, "MOV") == 0) {
    int duration = atoi(cmd.value);
    if (strcmp(cmd.action, "FWD") == 0)
      motors.move(1, 1, DEFAULT_SPEED, duration);
    else if (strcmp(cmd.action, "BCK") == 0)
      motors.move(-1, -1, DEFAULT_SPEED, duration);
    else if (strcmp(cmd.action, "STP") == 0)
      motors.stop(true);
    ProtocolHandler::sendAck("MOV");
  }

  // 2. Box Commands (SRV:ID:ACTION)
  else if (strcmp(cmd.type, "SRV") == 0) {
    uint8_t id = atoi(cmd.action);
    bool lock = (strcmp(cmd.value, "OPEN") != 0);
    boxes.setBoxState(id, lock);
    ProtocolHandler::sendAck("SRV");
  }

  // 3. UI Commands (LCD:ROW:MESSAGE)
  else if (strcmp(cmd.type, "LCD") == 0) {
    if (strcmp(cmd.action, "CLS") == 0)
      ui.clear();
    else
      ui.display(atoi(cmd.action), cmd.value);
  }

  // 4. System Commands
  else if (strcmp(cmd.type, "SYS") == 0) {
    if (strcmp(cmd.action, "PING") == 0)
      Serial.println(F("SYS:PONG"));
  }
}

void loop() {
  unsigned long now = millis();

  // --- 1. DATA INGESTION ---
  while (Serial.available()) {
    lastSerialTime = now; // Reset Watchdog
    char c = Serial.read();
    if (c == '\n') {
      cmdBuffer[bufferIdx] = '\0';
      ParsedCommand cmd = ProtocolHandler::parse(cmdBuffer);
      if (cmd.isValid)
        handleCommand(cmd);
      bufferIdx = 0;
    } else if (bufferIdx < CMD_BUFFER_SIZE - 1) {
      cmdBuffer[bufferIdx++] = c;
    }
  }

  // --- 2. SAFETY WATCHDOG ---
  if (now - lastSerialTime > WATCHDOG_TIMEOUT_MS) {
    if (motors.isMoving()) {
      motors.stop(true); // Emergency kill
      ui.display(0, "ALARM: CMD LOST");
    }
  }

  // --- 3. SERVICE UPDATES ---
  motors.update(); // Handles ramping and move timers
  boxes.update();  // Handles limit switch polling
  ui.update();     // Handles keypad polling
}
