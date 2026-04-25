#include "arduino_bridge.h"

#include "runtime_config.h"

namespace {
String unescapeCompactField(const String &value) {
  String out;
  bool escaped = false;
  for (unsigned int i = 0; i < value.length(); i++) {
    const char ch = value[i];
    if (escaped) {
      switch (ch) {
        case 'n':
          out += '\n';
          break;
        case 'r':
          out += '\r';
          break;
        case '\\':
        case '|':
          out += ch;
          break;
        default:
          out += ch;
          break;
      }
      escaped = false;
      continue;
    }
    if (ch == '\\') {
      escaped = true;
      continue;
    }
    out += ch;
  }
  return out;
}

uint8_t splitCompactFields(const String &line, String *fields, uint8_t maxFields) {
  uint8_t count = 0;
  String current;
  bool escaped = false;

  for (unsigned int i = 0; i < line.length(); i++) {
    const char ch = line[i];
    if (escaped) {
      current += '\\';
      current += ch;
      escaped = false;
      continue;
    }
    if (ch == '\\') {
      escaped = true;
      continue;
    }
    if (ch == '|') {
      if (count < maxFields) {
        fields[count++] = unescapeCompactField(current);
      }
      current = "";
      continue;
    }
    current += ch;
  }

  if (escaped) {
    current += '\\';
  }
  if (count < maxFields) {
    fields[count++] = unescapeCompactField(current);
  }
  return count;
}
}  // namespace

void ArduinoBridge::begin() {
  Serial.begin(SERIAL_BAUD);
  while (!Serial && millis() < SERIAL_WAIT_MS) {
  }

  protocol_.begin(Serial);
  drive_.begin();
  locks_.begin();
  keypad_.begin();
  lcd_.begin();
  rfid_.begin();
  switches_.begin();
  emitReady_();
}

void ArduinoBridge::update() {
  String line;
  while (protocol_.pollLine(line)) {
    handleCommand_(line);
  }

  drive_.update();
  locks_.update();
  keypad_.update();
  switches_.update();

  emitDriveEvents_();
  emitKeypadEvents_();
  emitSwitchEvents_();
  emitRfidEvents_();
}

void ArduinoBridge::handleCommand_(const String &line) {
  if (line.startsWith("@")) {
    handleCompactCommand_(line);
    return;
  }
  handleJsonCommand_(line);
}

void ArduinoBridge::handleJsonCommand_(const String &json) {
  String command;
  if (!SerialProtocol::extractString(json, "type", command)) {
    protocol_.sendError("missing_type", "Command must contain a type field");
    return;
  }

  if (command == "ping") {
    protocol_.sendAck("ping");
    return;
  }

  if (command == "get_state") {
    emitState_();
    protocol_.sendAck("get_state");
    return;
  }

  if (command == "lcd_clear") {
    lcd_.clear();
    protocol_.sendAck("lcd_clear", String("\"available\":") + (lcd_.available() ? "true" : "false"));
    return;
  }

  if (command == "lcd_backlight") {
    bool enabled = true;
    if (!SerialProtocol::extractBool(json, "enabled", enabled)) {
      protocol_.sendError("missing_enabled", "lcd_backlight requires enabled=true/false");
      return;
    }
    lcd_.setBacklight(enabled);
    protocol_.sendAck("lcd_backlight", String("\"enabled\":") + (enabled ? "true" : "false"));
    return;
  }

  if (command == "lcd_set") {
    protocol_.sendError("unsupported_command",
                        "lcd_set is disabled; use lcd_set_line commands instead");
    return;
  }

  if (command == "lcd_set_line") {
    int lineIndex = -1;
    if (!SerialProtocol::extractInt(json, "line", lineIndex)) {
      protocol_.sendError("missing_line", "lcd_set_line requires line index 0..3");
      return;
    }

    String text;
    if (!SerialProtocol::extractString(json, "text", text)) {
      protocol_.sendError("missing_text", "lcd_set_line requires text string");
      return;
    }

    const bool ok = lcd_.setLine(static_cast<uint8_t>(lineIndex), text);
    if (!ok) {
      protocol_.sendError("lcd_write_failed", "lcd_set_line failed",
                          String("\"line\":") + lineIndex);
      return;
    }

    protocol_.sendAck("lcd_set_line",
                      String("\"line\":") + lineIndex + ",\"text\":\"" +
                          SerialProtocol::escape(text) + "\"");
    return;
  }

  if (command == "lcd_demo") {
    String lines[LCD_ROWS];
    lines[0] = "LCD demo";
    lines[1] = "Arduino bridge";
    lines[2] = String("Addr: 0x") + String(lcd_.address(), HEX);
    lines[2].toUpperCase();
    lines[3] = "If seen, LCD OK";
    const bool ok = lcd_.setLines(lines, LCD_ROWS);
    protocol_.sendAck("lcd_demo", String("\"available\":") + (ok ? "true" : "false"));
    return;
  }

  if (command == "servo_open" || command == "servo_close" || command == "servo_set_angle") {
    int box = 0;
    if (!SerialProtocol::extractInt(json, "box", box)) {
      protocol_.sendError("missing_box", "Servo command requires box=1 or box=2");
      return;
    }

    bool ok = false;
    if (command == "servo_open") {
      ok = locks_.openBox(static_cast<uint8_t>(box));
    } else if (command == "servo_close") {
      ok = locks_.closeBox(static_cast<uint8_t>(box));
    } else {
      int angle = 0;
      if (!SerialProtocol::extractInt(json, "angle", angle)) {
        protocol_.sendError("missing_angle", "servo_set_angle requires angle");
        return;
      }
      ok = locks_.setAngle(static_cast<uint8_t>(box), static_cast<uint8_t>(angle));
    }

    if (!ok) {
      protocol_.sendError("invalid_box", "Unknown box id", String("\"box\":") + box);
      return;
    }
    protocol_.sendAck(command.c_str(), String("\"box\":") + box + ",\"state\":\"" +
                                       locks_.boxState(static_cast<uint8_t>(box)) + "\"");
    return;
  }

  if (command == "move") {
    String action;
    if (!SerialProtocol::extractString(json, "action", action)) {
      protocol_.sendError("missing_action", "move requires an action string");
      return;
    }

    int durationMs = 0;
    SerialProtocol::extractInt(json, "duration_ms", durationMs);
    if (!drive_.startAction(action, durationMs > 0 ? static_cast<unsigned long>(durationMs) : 0)) {
      if (drive_.busy()) {
        protocol_.sendError("drive_busy", "Drive controller is busy",
                            String("\"current\":\"") + drive_.currentAction() + "\"");
      } else {
        protocol_.sendError("invalid_action", "Unknown move action",
                            String("\"action\":\"") + SerialProtocol::escape(action) + "\"");
      }
      return;
    }
    protocol_.sendAck("move", String("\"action\":\"") + SerialProtocol::escape(action) + "\"");
    return;
  }

  if (command == "stop") {
    drive_.stop();
    protocol_.sendAck("stop");
    return;
  }

  protocol_.sendError("unknown_command", "Unsupported command type",
                      String("\"command\":\"") + SerialProtocol::escape(command) + "\"");
}

void ArduinoBridge::handleCompactCommand_(const String &line) {
  String fields[4];
  const uint8_t count = splitCompactFields(line.substring(1), fields, 4);
  if (count == 0) {
    protocol_.sendError("missing_opcode", "Compact command missing opcode");
    return;
  }

  const String opcode = fields[0];
  protocol_.sendEvent("debug_compact_rx",
                      String("\"opcode\":\"") + SerialProtocol::escape(opcode) +
                          "\",\"field_count\":" + count + ",\"raw\":\"" +
                          SerialProtocol::escape(line) + "\"");

  if (opcode == "P") {
    protocol_.sendAck("ping");
    return;
  }

   if (opcode == "R") {
    rfid_.begin();
    protocol_.sendAck("rfid_reset");
    return;
  }

  if (opcode == "G") {
    emitState_();
    protocol_.sendAck("get_state");
    return;
  }

  if (opcode == "C") {
    lcd_.clear();
    protocol_.sendAck("lcd_clear", String("\"available\":") + (lcd_.available() ? "true" : "false"));
    return;
  }

  if (opcode == "D") {
    String demo[LCD_ROWS];
    demo[0] = "LCD demo";
    demo[1] = "Arduino bridge";
    demo[2] = String("Addr: 0x") + String(lcd_.address(), HEX);
    demo[2].toUpperCase();
    demo[3] = "If seen, LCD OK";
    const bool ok = lcd_.setLines(demo, LCD_ROWS);
    protocol_.sendAck("lcd_demo", String("\"available\":") + (ok ? "true" : "false"));
    return;
  }

  if (opcode == "L") {
    if (count < 3) {
      protocol_.sendError("missing_fields", "L requires line and text");
      return;
    }
    const uint8_t lineIndex = static_cast<uint8_t>(fields[1].toInt());
    const bool ok = lcd_.setLine(lineIndex, fields[2]);
    if (!ok) {
      protocol_.sendError("lcd_write_failed", "lcd_set_line failed",
                          String("\"line\":") + lineIndex);
      return;
    }
    protocol_.sendAck("lcd_set_line",
                      String("\"line\":") + lineIndex + ",\"text\":\"" +
                          SerialProtocol::escape(fields[2]) + "\"");
    return;
  }

  if (opcode == "O" || opcode == "X") {
    if (count < 2) {
      protocol_.sendError("missing_box", "Servo command requires box id");
      return;
    }
    const uint8_t box = static_cast<uint8_t>(fields[1].toInt());
    const bool ok = opcode == "O" ? locks_.openBox(box) : locks_.closeBox(box);
    if (!ok) {
      protocol_.sendError("invalid_box", "Unknown box id", String("\"box\":") + box);
      return;
    }
    protocol_.sendAck(opcode == "O" ? "servo_open" : "servo_close",
                      String("\"box\":") + box + ",\"state\":\"" + locks_.boxState(box) +
                          "\"");
    return;
  }

  if (opcode == "A") {
    if (count < 3) {
      protocol_.sendError("missing_fields", "A requires box and angle");
      return;
    }
    const uint8_t box = static_cast<uint8_t>(fields[1].toInt());
    const uint8_t angle = static_cast<uint8_t>(fields[2].toInt());
    if (!locks_.setAngle(box, angle)) {
      protocol_.sendError("invalid_box", "Unknown box id", String("\"box\":") + box);
      return;
    }
    protocol_.sendAck("servo_set_angle",
                      String("\"box\":") + box + ",\"angle\":" + angle);
    return;
  }

  if (opcode == "M") {
    if (count < 2) {
      protocol_.sendError("missing_action", "M requires action");
      return;
    }
    const String action = fields[1];
    const unsigned long durationMs = count >= 3 ? static_cast<unsigned long>(fields[2].toInt()) : 0;
    protocol_.sendEvent("debug_move_request",
                        String("\"action\":\"") + SerialProtocol::escape(action) +
                            "\",\"duration_ms\":" + durationMs + ",\"busy\":" +
                            (drive_.busy() ? "true" : "false"));
    if (!drive_.startAction(action, durationMs)) {
      if (drive_.busy()) {
        protocol_.sendError("drive_busy", "Drive controller is busy",
                            String("\"current\":\"") + drive_.currentAction() + "\"");
      } else {
        protocol_.sendError("invalid_action", "Unknown move action",
                            String("\"action\":\"") + SerialProtocol::escape(action) + "\"");
      }
      return;
    }
    protocol_.sendAck("move", String("\"action\":\"") + SerialProtocol::escape(action) + "\"");
    return;
  }

  if (opcode == "T") {
    drive_.stop();
    protocol_.sendAck("stop");
    return;
  }

  protocol_.sendError("unknown_opcode", "Unsupported compact opcode",
                      String("\"opcode\":\"") + SerialProtocol::escape(opcode) + "\"");
}

void ArduinoBridge::emitReady_() {
  String fields = String("\"firmware\":\"arduino_bridge\",\"lcd_available\":") +
                  (lcd_.available() ? "true" : "false") + ",\"lcd_address\":" + lcd_.address();
  protocol_.sendEvent("ready", fields);
}

void ArduinoBridge::emitState_() {
  String fields = String("\"drive_busy\":") + (drive_.busy() ? "true" : "false") +
                  ",\"drive_action\":\"" + drive_.currentAction() + "\"" +
                  ",\"switches\":[" + (switches_.isPressed(1) ? "true" : "false") + "," +
                  (switches_.isPressed(2) ? "true" : "false") + "]" + ",\"locks\":[\"" +
                  locks_.boxState(1) + "\",\"" + locks_.boxState(2) + "\"]";
  protocol_.sendEvent("state", fields);
}

void ArduinoBridge::emitKeypadEvents_() {
  KeypadInputEvent event;
  while (keypad_.pollEvent(event)) {
    String key;
    key += event.key;
    protocol_.sendEvent("key_event", String("\"key\":\"") + SerialProtocol::escape(key) +
                                         "\",\"state\":\"" + event.state + "\"");
  }
}

void ArduinoBridge::emitSwitchEvents_() {
  SwitchEvent event;
  while (switches_.pollEvent(event)) {
    protocol_.sendEvent("switch_state", String("\"box\":") + event.box + ",\"pressed\":" +
                                            (event.pressed ? "true" : "false"));
  }
}

void ArduinoBridge::emitRfidEvents_() {
  String uid;
  const RfidReader::PollStatus status = rfid_.pollUid(uid);
  if (rfid_.consumeRecoveredSinceLastPoll()) {
    protocol_.sendEvent("debug_rfid_recovered", "");
  }
  if (status == RfidReader::PollStatus::ReadFailed) {
    protocol_.sendEvent("debug_rfid_read_failed", "");
    return;
  }
  if (status == RfidReader::PollStatus::ScanSuccess) {
    protocol_.sendEvent("rfid_scan",
                        String("\"uid\":\"") + SerialProtocol::escape(uid) + "\"");
  }
}

void ArduinoBridge::emitDriveEvents_() {
  String action;
  if (drive_.consumeCompletedAction(action)) {
    protocol_.sendEvent("motion_done",
                        String("\"action\":\"") + SerialProtocol::escape(action) + "\"");
  }
}
