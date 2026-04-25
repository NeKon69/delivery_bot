#include "serial_protocol.h"

#include <ctype.h>
#include <stdlib.h>

void SerialProtocol::begin(Stream &stream) {
  stream_ = &stream;
  used_ = 0;
}

bool SerialProtocol::pollLine(String &line) {
  if (stream_ == nullptr) {
    return false;
  }

  while (stream_->available() > 0) {
    const char ch = static_cast<char>(stream_->read());
    if (ch == '\r') {
      continue;
    }
    if (ch == '\n') {
      buffer_[used_] = '\0';
      line = String(buffer_);
      used_ = 0;
      line.trim();
      return line.length() > 0;
    }

    if (used_ + 1 < BUFFER_CAPACITY) {
      buffer_[used_++] = ch;
    } else {
      used_ = 0;
      sendError("line_too_long", "Input line exceeded buffer capacity");
      return false;
    }
  }

  return false;
}

void SerialProtocol::sendAck(const char *command, const String &extraFields) {
  String fields = String("\"command\":\"") + escape(command) + "\"";
  if (extraFields.length() > 0) {
    fields += ",";
    fields += extraFields;
  }
  sendObject_("ack", fields);
}

void SerialProtocol::sendError(const char *code, const String &message, const String &extraFields) {
  String fields = String("\"code\":\"") + escape(code) + "\",\"message\":\"" +
                  escape(message) + "\"";
  if (extraFields.length() > 0) {
    fields += ",";
    fields += extraFields;
  }
  sendObject_("error", fields);
}

void SerialProtocol::sendEvent(const char *eventType, const String &extraFields) {
  String fields = String("\"event\":\"") + escape(eventType) + "\"";
  if (extraFields.length() > 0) {
    fields += ",";
    fields += extraFields;
  }
  sendObject_("event", fields);
}

bool SerialProtocol::extractString(const String &json, const char *key, String &valueOut) {
  const int start = findKeyValueStart_(json, key);
  if (start < 0 || start >= json.length() || json[start] != '"') {
    return false;
  }

  String value;
  bool escaped = false;
  for (int i = start + 1; i < json.length(); i++) {
    const char ch = json[i];
    if (escaped) {
      value += ch;
      escaped = false;
      continue;
    }
    if (ch == '\\') {
      escaped = true;
      continue;
    }
    if (ch == '"') {
      valueOut = value;
      return true;
    }
    value += ch;
  }

  return false;
}

bool SerialProtocol::extractInt(const String &json, const char *key, int &valueOut) {
  const int start = findKeyValueStart_(json, key);
  if (start < 0) {
    return false;
  }

  int end = start;
  while (end < json.length() && (json[end] == '-' || isdigit(json[end]))) {
    end++;
  }
  if (end == start) {
    return false;
  }

  valueOut = json.substring(start, end).toInt();
  return true;
}

bool SerialProtocol::extractBool(const String &json, const char *key, bool &valueOut) {
  const int start = findKeyValueStart_(json, key);
  if (start < 0) {
    return false;
  }

  if (json.startsWith("true", start)) {
    valueOut = true;
    return true;
  }
  if (json.startsWith("false", start)) {
    valueOut = false;
    return true;
  }
  return false;
}

bool SerialProtocol::extractStringArray(const String &json, const char *key, String *valuesOut,
                                        size_t maxValues, size_t &countOut) {
  countOut = 0;
  const int start = findKeyValueStart_(json, key);
  if (start < 0 || start >= json.length() || json[start] != '[') {
    return false;
  }

  int i = start + 1;
  while (i < json.length()) {
    while (i < json.length() && isspace(json[i])) {
      i++;
    }
    if (i >= json.length()) {
      return false;
    }
    if (json[i] == ']') {
      return true;
    }
    if (json[i] != '"' || countOut >= maxValues) {
      return false;
    }

    i++;
    String item;
    bool escaped = false;
    while (i < json.length()) {
      const char ch = json[i++];
      if (escaped) {
        item += ch;
        escaped = false;
        continue;
      }
      if (ch == '\\') {
        escaped = true;
        continue;
      }
      if (ch == '"') {
        break;
      }
      item += ch;
    }
    valuesOut[countOut++] = item;

    while (i < json.length() && isspace(json[i])) {
      i++;
    }
    if (i < json.length() && json[i] == ',') {
      i++;
      continue;
    }
    if (i < json.length() && json[i] == ']') {
      return true;
    }
  }

  return false;
}

String SerialProtocol::escape(const String &value) {
  String out;
  out.reserve(value.length() + 8);
  for (size_t i = 0; i < value.length(); i++) {
    const char ch = value[i];
    if (ch == '\\' || ch == '"') {
      out += '\\';
    }
    out += ch;
  }
  return out;
}

void SerialProtocol::sendObject_(const char *type, const String &fields) {
  if (stream_ == nullptr) {
    return;
  }

  String line = String("{\"type\":\"") + escape(type) + "\"";
  if (fields.length() > 0) {
    line += ",";
    line += fields;
  }
  line += "}";
  stream_->println(line);
}

int SerialProtocol::findKeyValueStart_(const String &json, const char *key) {
  const String pattern = String("\"") + key + "\"";
  const int keyIndex = json.indexOf(pattern);
  if (keyIndex < 0) {
    return -1;
  }

  int colonIndex = json.indexOf(':', keyIndex + pattern.length());
  if (colonIndex < 0) {
    return -1;
  }
  colonIndex++;
  while (colonIndex < json.length() && isspace(json[colonIndex])) {
    colonIndex++;
  }
  return colonIndex;
}
