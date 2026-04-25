#pragma once

#include <Arduino.h>

class SerialProtocol {
 public:
  void begin(Stream &stream);
  bool pollLine(String &line);

  void sendAck(const char *command, const String &extraFields = "");
  void sendError(const char *code, const String &message, const String &extraFields = "");
  void sendEvent(const char *eventType, const String &extraFields = "");

  static bool extractString(const String &json, const char *key, String &valueOut);
  static bool extractInt(const String &json, const char *key, int &valueOut);
  static bool extractBool(const String &json, const char *key, bool &valueOut);
  static bool extractStringArray(const String &json, const char *key, String *valuesOut,
                                 size_t maxValues, size_t &countOut);
  static String escape(const String &value);

 private:
  Stream *stream_ = nullptr;
  static constexpr size_t BUFFER_CAPACITY = 384;
  char buffer_[BUFFER_CAPACITY];
  size_t used_ = 0;

  void sendObject_(const char *type, const String &fields);
  static int findKeyValueStart_(const String &json, const char *key);
};
