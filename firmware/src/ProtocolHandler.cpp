/**
 * ProtocolHandler.cpp - Service Layer Implementation
 */

#include "ProtocolHandler.h"

ParsedCommand ProtocolHandler::parse(char *rawBuffer) {
  ParsedCommand cmd;
  if (rawBuffer == nullptr || strlen(rawBuffer) == 0)
    return cmd;

  char *savePtr;

  // 1. Extract TYPE
  char *token = strtok_r(rawBuffer, ":", &savePtr);
  if (token != nullptr) {
    strncpy(cmd.type, token, sizeof(cmd.type) - 1);
    cmd.type[sizeof(cmd.type) - 1] = '\0'; // Ensure null termination
  } else
    return cmd;

  // 2. Extract ACTION
  token = strtok_r(NULL, ":", &savePtr);
  if (token != nullptr) {
    strncpy(cmd.action, token, sizeof(cmd.action) - 1);
    cmd.action[sizeof(cmd.action) - 1] = '\0';
  } else
    return cmd;

  // 3. Extract VALUE (The remainder of the string)
  // We use ":" as delimiter again, but if it's an LCD message,
  // it might contain spaces which strtok handles fine.
  token = strtok_r(NULL, "\n\r", &savePtr); // Grab everything until end of line
  if (token != nullptr) {
    strncpy(cmd.value, token, sizeof(cmd.value) - 1);
    cmd.value[sizeof(cmd.value) - 1] = '\0';
    cmd.isValid = true;
  }

  return cmd;
}

void ProtocolHandler::sendEvent(const char *type, const char *data1,
                                const char *data2) {
  Serial.print(F("EVT:"));
  Serial.print(type);
  Serial.print(F(":"));
  Serial.print(data1);
  if (data2 != nullptr) {
    Serial.print(F(":"));
    Serial.print(data2);
  }
  Serial.println(); // Every message ends with newline
}

void ProtocolHandler::sendAck(const char *type) {
  Serial.print(F("ACK:"));
  Serial.println(type);
}
