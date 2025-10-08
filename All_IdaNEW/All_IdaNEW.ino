// ESP32 2-Axis Controller - Serial Communication Only
// Control via Python Flask Web Interface

// === PIN DEFINITIONS ===
const int encoderPinA_X = 13, encoderPinB_X = 12;
const int encoderPinA_Y = 14, encoderPinB_Y = 27;
const int motorIn1 = 26, motorIn2 = 25, motorENA = 18;
const int motorIn3 = 16, motorIn4 = 17, motorENB = 19;

// === VARIABLES ===
volatile long encoderValue_X = 0, encoderValue_Y = 0;
int motorSpeed_X = 150, motorSpeed_Y = 80;

// Color detection
bool yellowDetected = false, greenDetected = false;
int yellowCount = 0, greenCount = 0;
unsigned long lastColorReceived = 0;
bool serialConnected = false;
String serialBuffer = "";

// State machine
enum MoveState { IDLE, MOVING_X, MOVING_Y };
enum OperationMode { MANUAL, AUTO_SEQUENCE };
MoveState currentMoveState = IDLE;
OperationMode currentMode = MANUAL;

long targetEncoderX = 0, targetEncoderY = 0;
const int ENCODER_TOLERANCE = 20;

// Alarms
#define NUM_ALARMS 3
struct Alarm { int hour = -1; int minute = -1; bool isEnabled = false; };
Alarm alarms[NUM_ALARMS];
int timedSequenceStep = 0;
unsigned long timedSequenceWaitStartTime = 0;
const long TIMED_SEQUENCE_WAIT_TIME = 5000;

// === MOTOR CONTROL ===
void Forward_X() { digitalWrite(motorIn1, HIGH); digitalWrite(motorIn2, LOW); analogWrite(motorENA, motorSpeed_X); }
void Backward_X() { digitalWrite(motorIn1, LOW); digitalWrite(motorIn2, HIGH); analogWrite(motorENA, motorSpeed_X); }
void Forward_Y() { digitalWrite(motorIn3, HIGH); digitalWrite(motorIn4, LOW); analogWrite(motorENB, motorSpeed_Y); }
void Backward_Y() { digitalWrite(motorIn3, LOW); digitalWrite(motorIn4, HIGH); analogWrite(motorENB, motorSpeed_Y); }
void stopMotor() { digitalWrite(motorIn1, LOW); digitalWrite(motorIn2, LOW); digitalWrite(motorIn3, LOW); digitalWrite(motorIn4, LOW); analogWrite(motorENA, 0); analogWrite(motorENB, 0); }

// === ENCODER READING ===
void IRAM_ATTR readEncoder_X() { encoderValue_X += (digitalRead(encoderPinA_X) == digitalRead(encoderPinB_X)) ? 1 : -1; }
void IRAM_ATTR readEncoder_Y() { encoderValue_Y += (digitalRead(encoderPinA_Y) == digitalRead(encoderPinB_Y)) ? 1 : -1; }

// === POSITION CONTROL ===
void setTargetPosition(int pos) {
  if (currentMoveState != IDLE) return;

  switch(pos) {
    case 1: targetEncoderX = 0; targetEncoderY = 0; break;
    case 2: targetEncoderX = 0; targetEncoderY = -4000; break;
    case 3: targetEncoderX = -4000; targetEncoderY = 0; break;
    case 4: targetEncoderX = -4000; targetEncoderY = -4000; break;
  }

  currentMoveState = MOVING_X;
  Serial.println("Moving to position " + String(pos));
}

// === MOVEMENT HANDLER ===
void handleAutomatedMovement() {
  if (currentMoveState == IDLE) return;

  if (currentMoveState == MOVING_X) {
    if (abs(targetEncoderX - encoderValue_X) <= ENCODER_TOLERANCE) {
      stopMotor();
      currentMoveState = MOVING_Y;
    } else {
      (encoderValue_X < targetEncoderX) ? Forward_X() : Backward_X();
    }
  }
  else if (currentMoveState == MOVING_Y) {
    if (abs(targetEncoderY - encoderValue_Y) <= ENCODER_TOLERANCE) {
      stopMotor();
      currentMoveState = IDLE;
      Serial.println("Movement complete");
    } else {
      (encoderValue_Y < targetEncoderY) ? Forward_Y() : Backward_Y();
    }
  }
}

// === TIMED SEQUENCE ===
void handleTimedSequence() {
  if (timedSequenceStep == 0 || currentMoveState != IDLE) return;

  if (timedSequenceStep == 1) {
    setTargetPosition(1);
    timedSequenceStep++;
    return;
  }

  if (timedSequenceWaitStartTime == 0) {
    if (timedSequenceStep > 5) {
      Serial.println("Sequence completed");
      timedSequenceStep = 0;
      return;
    }
    timedSequenceWaitStartTime = millis();
  }

  if (millis() - timedSequenceWaitStartTime >= TIMED_SEQUENCE_WAIT_TIME) {
    setTargetPosition((timedSequenceStep == 5) ? 1 : timedSequenceStep);
    timedSequenceStep++;
    timedSequenceWaitStartTime = 0;
  }
}

// === SERIAL COMMAND PROCESSING ===
void processSerialCommand(String cmd) {
  cmd.trim();

  if (cmd.startsWith("COLOR:")) {
    String data = cmd.substring(6);
    int idx1 = data.indexOf(',');
    int idx2 = data.indexOf(',', idx1 + 1);
    int idx3 = data.indexOf(',', idx2 + 1);

    if (idx1 != -1 && idx2 != -1 && idx3 != -1) {
      yellowDetected = data.substring(0, idx1).toInt() == 1;
      greenDetected = data.substring(idx1 + 1, idx2).toInt() == 1;
      yellowCount = data.substring(idx2 + 1, idx3).toInt();
      greenCount = data.substring(idx3 + 1).toInt();
      lastColorReceived = millis();
      serialConnected = true;
      Serial.println("ACK:COLOR_RECEIVED");

      // Auto movement based on color
      if (currentMode == AUTO_SEQUENCE && currentMoveState == IDLE) {
        if (yellowDetected && !greenDetected) setTargetPosition(2);
        else if (!yellowDetected && greenDetected) setTargetPosition(3);
        else if (yellowDetected && greenDetected) setTargetPosition(4);
        else setTargetPosition(1);
      }
    } else {
      Serial.println("ERROR:INVALID_COLOR_FORMAT");
    }
  }
  else if (cmd == "PING") {
    Serial.println("PONG");
    serialConnected = true;
  }
  else if (cmd == "STATUS") {
    Serial.print("STATUS:X="); Serial.print(encoderValue_X);
    Serial.print(",Y="); Serial.print(encoderValue_Y);
    Serial.print(",MODE="); Serial.print(currentMode == AUTO_SEQUENCE ? "AUTO" : "MANUAL");
    Serial.print(",MOVING="); Serial.print(currentMoveState != IDLE ? "YES" : "NO");
    Serial.print(",YELLOW="); Serial.print(yellowDetected ? "YES" : "NO");
    Serial.print(",GREEN="); Serial.print(greenDetected ? "YES" : "NO");
    Serial.print(",YC="); Serial.print(yellowCount);
    Serial.print(",GC="); Serial.println(greenCount);
  }
  else if (cmd.startsWith("MOTOR:")) {
    String motorCmd = cmd.substring(6);

    if (currentMode != MANUAL) {
      Serial.println("ERROR:NOT_IN_MANUAL_MODE");
      return;
    }

    if (currentMoveState != IDLE) {
      Serial.println("ERROR:MOTOR_BUSY");
      return;
    }

    if (motorCmd == "STOP") { stopMotor(); Serial.println("ACK:MOTOR_STOPPED"); }
    else if (motorCmd == "X_FWD") { Forward_X(); Serial.println("ACK:MOTOR_X_FORWARD"); }
    else if (motorCmd == "X_BACK") { Backward_X(); Serial.println("ACK:MOTOR_X_BACKWARD"); }
    else if (motorCmd == "Y_FWD") { Forward_Y(); Serial.println("ACK:MOTOR_Y_FORWARD"); }
    else if (motorCmd == "Y_BACK") { Backward_Y(); Serial.println("ACK:MOTOR_Y_BACKWARD"); }
    else Serial.println("ERROR:INVALID_MOTOR_COMMAND");
  }
  else if (cmd.startsWith("MOVETO:")) {
    int pos = cmd.substring(7).toInt();
    setTargetPosition(pos);
    Serial.println("ACK:MOVETO");
  }
  else if (cmd.startsWith("MODE:")) {
    String mode = cmd.substring(5);
    if (mode == "AUTO") {
      currentMode = AUTO_SEQUENCE;
      Serial.println("ACK:MODE_AUTO");
    } else {
      currentMode = MANUAL;
      Serial.println("ACK:MODE_MANUAL");
    }
  }
  else if (cmd.startsWith("ALARM:")) {
    // รับเวลา เช่น ALARM:0,14:30
    String data = cmd.substring(6);
    int idx = data.indexOf(',');
    if (idx != -1) {
      int slot = data.substring(0, idx).toInt();
      String timeStr = data.substring(idx + 1);
      int colonPos = timeStr.indexOf(':');
      if (colonPos != -1 && slot >= 0 && slot < NUM_ALARMS) {
        alarms[slot].hour = timeStr.substring(0, colonPos).toInt();
        alarms[slot].minute = timeStr.substring(colonPos + 1).toInt();
        alarms[slot].isEnabled = true;
        Serial.println("ACK:ALARM_SET");
      }
    }
  }
  else if (cmd.startsWith("CANCEL:")) {
    int slot = cmd.substring(7).toInt();
    if (slot >= 0 && slot < NUM_ALARMS) {
      alarms[slot].isEnabled = false;
      Serial.println("ACK:ALARM_CANCEL");
    }
  }
  else if (cmd == "RESET") {
    encoderValue_X = 0;
    encoderValue_Y = 0;
    Serial.println("ACK:RESET");
  }
  else {
    Serial.println("ERROR:UNKNOWN_COMMAND");
  }
}

void processColorData() {
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        processSerialCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }

  // Timeout check
  if (lastColorReceived > 0 && (millis() - lastColorReceived > 5000)) {
    yellowDetected = greenDetected = false;
    yellowCount = greenCount = 0;
    serialConnected = false;
  }
}

// === SETUP ===
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("========================================");
  Serial.println("ESP32 2-Axis Controller");
  Serial.println("Serial Mode - Python Control Only");
  Serial.println("========================================");
  Serial.println("Ready for connection");

  // Encoders
  pinMode(encoderPinA_X, INPUT_PULLUP);
  pinMode(encoderPinB_X, INPUT_PULLUP);
  pinMode(encoderPinA_Y, INPUT_PULLUP);
  pinMode(encoderPinB_Y, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(encoderPinA_X), readEncoder_X, CHANGE);
  attachInterrupt(digitalPinToInterrupt(encoderPinA_Y), readEncoder_Y, CHANGE);

  // Motors
  pinMode(motorIn1, OUTPUT); pinMode(motorIn2, OUTPUT); pinMode(motorENA, OUTPUT);
  pinMode(motorIn3, OUTPUT); pinMode(motorIn4, OUTPUT); pinMode(motorENB, OUTPUT);
  stopMotor();

  Serial.println("Hardware ready");
  Serial.println("========================================");
}

// === LOOP ===
void loop() {
  handleAutomatedMovement();
  handleTimedSequence();
  processColorData();

  static unsigned long lastReport = 0;
  if (millis() - lastReport > 10000) {
    lastReport = millis();
    if (serialConnected) Serial.println("INFO:Connected");
  }
}
