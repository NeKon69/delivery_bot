/**
 * ProtocolHandler.h - Service Layer
 * Responsible for parsing ASCII commands: "TYPE:ACTION:VALUE\n"
 */

#ifndef PROTOCOL_HANDLER_H
#define PROTOCOL_HANDLER_H

#include "Config.h"
#include <Arduino.h>
#include <string.h>

// Struct to hold parsed results.
// Uses fixed-size buffers for memory safety.
struct ParsedCommand {
  char type[8];    // e.g., "MOV", "SRV", "LCD"
  char action[12]; // e.g., "FWD", "1" (Box ID), "CLS"
  char value[32];  // e.g., "1000", "OPEN", "Hello World"
  bool isValid;

  ParsedCommand() : isValid(false) { type[0] = action[0] = value[0] = '\0'; }
};

class ProtocolHandler {
public:
  /**
   * Parses a raw char buffer into a ParsedCommand struct.
   * Logic: Splits string by ':' delimiter.
   * @param rawBuffer The null-terminated string to parse.
   */
  static ParsedCommand parse(char *rawBuffer);

  /**
   * Utility to send events back to the Master Pi in a standard format.
   * Format: EVT:TYPE:DATA1:DATA2
   */
  static void sendEvent(const char *type, const char *data1,
                        const char *data2 = nullptr);

  // Overload for numeric data
  static void sendAck(const char *type);
};

#endif
