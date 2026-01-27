/**
 * DELIVERY ROBOT FIRMWARE - ARDUINO MEGA 2560
 * Protocol: ASCII Command/Event
 * Baud: 115200
 */

#include <Arduino.h>
#include <Keypad.h>
#include <LiquidCrystal.h>
#include <MFRC522.h>
#include <SPI.h>
#include <Servo.h>

// ==========================================
// 1. PIN DEFINITIONS & CONSTANTS
// ==========================================

// --- LCD (4-bit mode) ---
constexpr int PIN_LCD_RS = 12;
constexpr int PIN_LCD_EN = 11;
constexpr int PIN_LCD_D4 = 5;
constexpr int PIN_LCD_D5 = 4;
constexpr int PIN_LCD_D6 = 3;
constexpr int PIN_LCD_D7 = 2;

// --- MOTORS (L298N Logic) ---
// Left Motor
constexpr int PIN_MOT_L_EN = 10; // PWM
constexpr int PIN_MOT_L_1 = 22;
constexpr int PIN_MOT_L_2 = 23;
// Right Motor
constexpr int PIN_MOT_R_EN = 9; // PWM
constexpr int PIN_MOT_R_1 = 24;
constexpr int PIN_MOT_R_2 = 25;

// --- SERVOS ---
constexpr int PIN_SERVO_1 = 6;
constexpr int PIN_SERVO_2 = 7;

// --- SENSORS ---
constexpr int PIN_LIMIT_1 = 40;
constexpr int PIN_LIMIT_2 = 41;

// --- RFID (SPI) ---
constexpr int PIN_RFID_SS = 53;
constexpr int PIN_RFID_RST = 49;
// Note: MOSI=51, MISO=50, SCK=52 are fixed by SPI library

// --- KEYPAD (4x4 Matrix) ---
const byte KEYPAD_ROWS = 4;
const byte KEYPAD_COLS = 4;
byte rowPins[KEYPAD_ROWS] = {30, 31, 32, 33};
byte colPins[KEYPAD_COLS] = {34, 35, 36, 37};
char keys[KEYPAD_ROWS][KEYPAD_COLS] = {{'1', '2', '3', 'A'},
                                       {'4', '5', '6', 'B'},
                                       {'7', '8', '9', 'C'},
                                       {'*', '0', '#', 'D'}};

// ==========================================
// 2. GLOBAL OBJECTS
// ==========================================

LiquidCrystal lcd(PIN_LCD_RS, PIN_LCD_EN, PIN_LCD_D4, PIN_LCD_D5, PIN_LCD_D6,
                  PIN_LCD_D7);
Keypad keypad =
    Keypad(makeKeymap(keys), rowPins, colPins, KEYPAD_ROWS, KEYPAD_COLS);
MFRC522 rfid(PIN_RFID_SS, PIN_RFID_RST);
Servo servo1;
Servo servo2;

// ==========================================
// 3. STATE VARIABLES
// ==========================================

// Communications
String inputBuffer = "";
unsigned long lastSerialTime = 0;
const unsigned long SAFETY_TIMEOUT_MS = 2000;

// Motor Control (Soft Start & Timing)
int currentPWM_L = 0;
int currentPWM_R = 0;
int targetPWM_L = 0;
int targetPWM_R = 0;
unsigned long moveEndTime = 0;
unsigned long lastRampTime = 0;
const int RAMP_INTERVAL_MS = 2; // Add 1 PWM step every 2ms (Soft Start)

// Limit Switches
bool lastLimit1State = false;
bool lastLimit2State = false;

// ==========================================
// 4. HELPER FUNCTIONS
// ==========================================

void stopMotors() {
  targetPWM_L = 0;
  targetPWM_R = 0;
  // Immediate kill for safety, override soft stop
  currentPWM_L = 0;
  currentPWM_R = 0;
  digitalWrite(PIN_MOT_L_EN, LOW);
  digitalWrite(PIN_MOT_R_EN, LOW);
  digitalWrite(PIN_MOT_L_1, LOW);
  digitalWrite(PIN_MOT_L_2, LOW);
  digitalWrite(PIN_MOT_R_1, LOW);
  digitalWrite(PIN_MOT_R_2, LOW);
}

// Applies direction pins based on positive/negative target
void setMotorDirection(int leftDir, int rightDir) {
  // Left: 1=Fwd, -1=Bwd
  if (leftDir > 0) {
    digitalWrite(PIN_MOT_L_1, HIGH);
    digitalWrite(PIN_MOT_L_2, LOW);
  } else if (leftDir < 0) {
    digitalWrite(PIN_MOT_L_1, LOW);
    digitalWrite(PIN_MOT_L_2, HIGH);
  } else {
    digitalWrite(PIN_MOT_L_1, LOW);
    digitalWrite(PIN_MOT_L_2, LOW);
  }

  // Right: 1=Fwd, -1=Bwd
  if (rightDir > 0) {
    digitalWrite(PIN_MOT_R_1, HIGH);
    digitalWrite(PIN_MOT_R_2, LOW);
  } else if (rightDir < 0) {
    digitalWrite(PIN_MOT_R_1, LOW);
    digitalWrite(PIN_MOT_R_2, HIGH);
  } else {
    digitalWrite(PIN_MOT_R_1, LOW);
    digitalWrite(PIN_MOT_R_2, LOW);
  }
}

// ==========================================
// 5. COMMAND PARSER
// ==========================================

void parseCommand(String cmd) {
  lastSerialTime = millis(); // Reset Watchdog

  // cmd format: "MOV:FWD:1000"
  int firstColon = cmd.indexOf(':');
  int secondColon = cmd.indexOf(':', firstColon + 1);

  String type = cmd.substring(0, firstColon);
  String action = cmd.substring(firstColon + 1, secondColon);
  String valueStr = cmd.substring(secondColon + 1);

  // --- MOTOR COMMANDS ---
  // Syntax: MOV:TYPE:DURATION_MS
  // Note: Max PWM is hardcoded here or sent? Let's assume standard max speed
  // (200) The Python config.json holds the exact "max_pwm", but for now we run
  // at full allowed speed Ideally, pass PWM via command, but for simplicity we
  // assume fixed speed for now.
  int speed = 200; // Default

  if (type == "MOV") {
    long duration = valueStr.toInt();
    moveEndTime = millis() + duration;

    if (action == "FWD") {
      setMotorDirection(1, 1);
      targetPWM_L = speed;
      targetPWM_R = speed;
    } else if (action == "BCK") {
      setMotorDirection(-1, -1);
      targetPWM_L = speed;
      targetPWM_R = speed;
    } else if (action == "LFT") {
      setMotorDirection(-1, 1);
      targetPWM_L = speed;
      targetPWM_R = speed;
    } else if (action == "RGT") {
      setMotorDirection(1, -1);
      targetPWM_L = speed;
      targetPWM_R = speed;
    } else if (action == "STP") {
      stopMotors();
    }
    Serial.println("ACK:MOV");
  }

  // --- SERVO COMMANDS ---
  // Syntax: SRV:1:OPEN
  else if (type == "SRV") {
    int id = action.toInt();
    int angle = (valueStr == "OPEN") ? 0 : 90; // 0=Open, 90=Locked

    if (id == 1)
      servo1.write(angle);
    if (id == 2)
      servo2.write(angle);
    Serial.println("ACK:SRV");
  }

  // --- LCD COMMANDS ---
  // Syntax: LCD:0:Hello World
  else if (type == "LCD") {
    if (action == "CLS") {
      lcd.clear();
    } else {
      int row = action.toInt();
      lcd.setCursor(0, row);
      lcd.print(valueStr);
    }
    // No ACK needed for LCD to keep bus quiet
  }

  // --- SYSTEM COMMANDS ---
  else if (type == "SYS") {
    if (action == "PING")
      Serial.println("SYS:PONG");
  }
}

// ==========================================
// 6. MAIN SETUP
// ==========================================

void setup() {
  Serial.begin(115200);

  // Hardware Init
  lcd.begin(16, 2);
  lcd.print("BOOTING...");

  SPI.begin();
  rfid.PCD_Init();

  servo1.attach(PIN_SERVO_1);
  servo2.attach(PIN_SERVO_2);
  servo1.write(90); // Default locked
  servo2.write(90);

  pinMode(PIN_MOT_L_EN, OUTPUT);
  pinMode(PIN_MOT_L_1, OUTPUT);
  pinMode(PIN_MOT_L_2, OUTPUT);
  pinMode(PIN_MOT_R_EN, OUTPUT);
  pinMode(PIN_MOT_R_1, OUTPUT);
  pinMode(PIN_MOT_R_2, OUTPUT);

  pinMode(PIN_LIMIT_1, INPUT_PULLUP);
  pinMode(PIN_LIMIT_2, INPUT_PULLUP);

  stopMotors();
  lcd.clear();
  lcd.print("READY");
  lastSerialTime = millis();
}

// ==========================================
// 7. MAIN LOOP
// ==========================================

void loop() {
  unsigned long currentMillis = millis();

  // --- 1. READ SERIAL (Non-blocking) ---
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      parseCommand(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }

  // --- 2. SAFETY CHECK ---
  if (currentMillis - lastSerialTime > SAFETY_TIMEOUT_MS) {
    if (targetPWM_L > 0 || targetPWM_R > 0) {
      stopMotors();
      lcd.clear();
      lcd.print("ERR: SERIAL LOST");
      Serial.println("ERR:TIMEOUT");
    }
  }

  // --- 3. SENSOR POLLING ---

  // Keypad
  char key = keypad.getKey();
  if (key) {
    Serial.print("KEY:");
    Serial.println(key);
  }

  // RFID
  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    Serial.print("RFD:");
    for (byte i = 0; i < rfid.uid.size; i++) {
      Serial.print(rfid.uid.uidByte[i] < 0x10 ? "0" : "");
      Serial.print(rfid.uid.uidByte[i], HEX);
      if (i < rfid.uid.size - 1)
        Serial.print("-");
    }
    Serial.println();
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }

  // Limit Switches (Logic: Low = Pressed/Closed)
  bool limit1 = !digitalRead(PIN_LIMIT_1);
  if (limit1 != lastLimit1State) {
    lastLimit1State = limit1;
    Serial.print("LMT:1:");
    Serial.println(limit1 ? "1" : "0");
  }

  bool limit2 = !digitalRead(PIN_LIMIT_2);
  if (limit2 != lastLimit2State) {
    lastLimit2State = limit2;
    Serial.print("LMT:2:");
    Serial.println(limit2 ? "1" : "0");
  }

  // --- 4. MOTOR CONTROL (Soft Start & Timer) ---

  // Check Timer
  if (currentMillis > moveEndTime && moveEndTime > 0) {
    targetPWM_L = 0;
    targetPWM_R = 0;
    moveEndTime = 0; // Timer expired
    Serial.println("EVT:MOVE_DONE");
  }

  // Ramp Logic (Soft Start / Soft Stop)
  if (currentMillis - lastRampTime >= RAMP_INTERVAL_MS) {
    lastRampTime = currentMillis;

    // Left Ramp
    if (currentPWM_L < targetPWM_L)
      currentPWM_L++;
    else if (currentPWM_L > targetPWM_L)
      currentPWM_L--;

    // Right Ramp
    if (currentPWM_R < targetPWM_R)
      currentPWM_R++;
    else if (currentPWM_R > targetPWM_R)
      currentPWM_R--;

    analogWrite(PIN_MOT_L_EN, currentPWM_L);
    analogWrite(PIN_MOT_R_EN, currentPWM_R);
  }
}
