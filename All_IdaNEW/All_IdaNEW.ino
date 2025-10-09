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
void IRAM_ATTR readEncoder_X() {
  if (digitalRead(encoderPinA_X) == digitalRead(encoderPinB_X)) {
    encoderValue_X = encoderValue_X + 1;
  } else {
    encoderValue_X = encoderValue_X - 1;
  }
}

void IRAM_ATTR readEncoder_Y() {
  if (digitalRead(encoderPinA_Y) == digitalRead(encoderPinB_Y)) {
    encoderValue_Y = encoderValue_Y + 1;
  } else {
    encoderValue_Y = encoderValue_Y - 1;
  }
}

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
      // เคลื่อนที่แกน X
      if (encoderValue_X < targetEncoderX) {
        Forward_X();
      } else {
        Backward_X();
      }
    }
  }
  else if (currentMoveState == MOVING_Y) {
    if (abs(targetEncoderY - encoderValue_Y) <= ENCODER_TOLERANCE) {
      stopMotor();
      currentMoveState = IDLE;
      Serial.println("Movement complete");
    } else {
      // เคลื่อนที่แกน Y
      if (encoderValue_Y < targetEncoderY) {
        Forward_Y();
      } else {
        Backward_Y();
      }
    }
  }
}

// === CHECK ALARM TIME ===
bool checkAlarmTime() {
  // ตรวจสอบว่าถึงเวลา alarm หรือยัง (ต้องมี RTC จริงๆ)
  // ตอนนี้ยังไม่มี RTC ก็ไม่ทำอะไร
  // ถ้ามี RTC ให้เช็คว่าเวลาตรงกับ alarm ที่ตั้งไว้หรือไม่

  for (int i = 0; i < NUM_ALARMS; i++) {
    if (alarms[i].isEnabled) {
      // TODO: เช็คกับเวลาจริงจาก RTC
      // if (currentHour == alarms[i].hour && currentMinute == alarms[i].minute) {
      //   return true;
      // }
    }
  }
  return false;
}

// === TIMED SEQUENCE ===
void handleTimedSequence() {
  // ทำงานเฉพาะใน AUTO_SEQUENCE mode และเมื่อ idle
  if (currentMode != AUTO_SEQUENCE) return;
  if (currentMoveState != IDLE) return;

  // ตรวจสอบว่าเริ่ม sequence หรือยัง
  if (timedSequenceStep == 0) {
    // รอให้ Python ส่งสัญญาณ START_SEQUENCE (เมื่อถึงเวลา alarm)
    return;
  }

  // ขั้นตอนที่ 1: กลับ HOME ทันที
  if (timedSequenceStep == 1) {
    setTargetPosition(1);
    timedSequenceStep = 2;
    timedSequenceWaitStartTime = millis();  // เริ่มนับเวลารอ
    return;
  }

  // เช็คว่าเสร็จแล้วหรือยัง
  if (timedSequenceStep > 5) {
    Serial.println("Sequence completed");
    timedSequenceStep = 0;
    timedSequenceWaitStartTime = 0;
    return;
  }

  // รอ 5 วินาทีหลังจากเคลื่อนที่ครั้งก่อน แล้วไปจุดถัดไป
  if (millis() - timedSequenceWaitStartTime >= TIMED_SEQUENCE_WAIT_TIME) {
    // ไป Position 2, 3, 4 แล้วกลับ 1
    if (timedSequenceStep == 2) setTargetPosition(2);
    else if (timedSequenceStep == 3) setTargetPosition(3);
    else if (timedSequenceStep == 4) setTargetPosition(4);
    else if (timedSequenceStep == 5) setTargetPosition(1);

    timedSequenceStep = timedSequenceStep + 1;
    timedSequenceWaitStartTime = millis();  // เริ่มนับเวลารอใหม่
  }
}

// === SERIAL COMMAND PROCESSING ===
void processSerialCommand(String cmd) {
  cmd.trim();

  if (cmd.startsWith("COLOR:")) {
    // รับข้อมูลสี: COLOR:yellow,green,purple,yellowCount,greenCount,purpleCount
    String data = cmd.substring(6);
    int idx1 = data.indexOf(',');
    int idx2 = data.indexOf(',', idx1 + 1);
    int idx3 = data.indexOf(',', idx2 + 1);
    int idx4 = data.indexOf(',', idx3 + 1);
    int idx5 = data.indexOf(',', idx4 + 1);

    if (idx1 != -1 && idx2 != -1 && idx3 != -1 && idx4 != -1 && idx5 != -1) {
      yellowDetected = data.substring(0, idx1).toInt() == 1;
      greenDetected = data.substring(idx1 + 1, idx2).toInt() == 1;
      // purple ไม่ได้ใช้ในการควบคุม แต่รับไว้
      int purpleVal = data.substring(idx2 + 1, idx3).toInt();
      yellowCount = data.substring(idx3 + 1, idx4).toInt();
      greenCount = data.substring(idx4 + 1, idx5).toInt();
      // purpleCount ไม่ได้ใช้ แต่รับไว้
      int purpleCount = data.substring(idx5 + 1).toInt();

      lastColorReceived = millis();
      serialConnected = true;
      Serial.println("ACK:COLOR_RECEIVED");

      // สีไม่มีส่วนในการควบคุมการเคลื่อนที่
      // ใช้เพื่อบันทึกสภาพพืชเท่านั้น
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

    // โหมด
    Serial.print(",MODE=");
    if (currentMode == AUTO_SEQUENCE) {
      Serial.print("AUTO");
    } else {
      Serial.print("MANUAL");
    }

    // กำลังเคลื่อนที่หรือไม่
    Serial.print(",MOVING=");
    if (currentMoveState != IDLE) {
      Serial.print("YES");
    } else {
      Serial.print("NO");
    }

    // สีเหลือง
    Serial.print(",YELLOW=");
    if (yellowDetected) {
      Serial.print("YES");
    } else {
      Serial.print("NO");
    }

    // สีเขียว
    Serial.print(",GREEN=");
    if (greenDetected) {
      Serial.print("YES");
    } else {
      Serial.print("NO");
    }

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
  else if (cmd == "START_SEQUENCE") {
    // เริ่ม sequence (เมื่อถึงเวลาที่ตั้ง)
    if (currentMode == AUTO_SEQUENCE) {
      timedSequenceStep = 1;
      timedSequenceWaitStartTime = 0;
      Serial.println("ACK:SEQUENCE_STARTED");
    } else {
      Serial.println("ERROR:NOT_IN_AUTO_MODE");
    }
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
