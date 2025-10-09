# ⚡ Arduino Code - ESP32 2-Axis Controller

## 📁 ไฟล์ในโฟลเดอร์นี้

```
3_Arduino/
└── All_IdaNEW/
    └── All_IdaNEW.ino          # Arduino Code สำหรับ ESP32
```

---

## 🔌 Hardware Requirements

### ESP32 Board
- ESP32 DevKit V1 (หรือเทียบเท่า)
- USB Cable (สำหรับอัปโหลดโค้ด)

### Motors & Drivers
- มอเตอร์ 2 ตัว (แกน X และ Y)
- L298N Motor Driver 2 ตัว (หรือเทียบเท่า)

### Encoders
- Rotary Encoder 2 ตัว
- ต่อกับแกน X และ Y

### Water Pump
- Relay Module 1 ช่อง
- ปั๊มน้ำ 12V

---

## 📍 Pin Connections

### Encoders
```
Encoder X:
  - Pin A: GPIO 13
  - Pin B: GPIO 12

Encoder Y:
  - Pin A: GPIO 14
  - Pin B: GPIO 27
```

### Motor X (L298N #1)
```
Motor Driver:
  - IN1: GPIO 26
  - IN2: GPIO 25
  - ENA: GPIO 18 (PWM)

Motor:
  - OUT1, OUT2 → Motor X
```

### Motor Y (L298N #2)
```
Motor Driver:
  - IN3: GPIO 16
  - IN4: GPIO 17
  - ENB: GPIO 19 (PWM)

Motor:
  - OUT3, OUT4 → Motor Y
```

### Water Pump (Relay)
```
Relay Module:
  - Signal: GPIO 21
  - VCC: 5V
  - GND: GND

Pump:
  - + → Relay NO (Normally Open)
  - - → GND
```

---

## 🔧 Arduino IDE Setup

### ขั้นตอนที่ 1: ติดตั้ง Arduino IDE

ดาวน์โหลด: https://www.arduino.cc/en/software

### ขั้นตอนที่ 2: เพิ่ม ESP32 Board

1. เปิด Arduino IDE
2. File → Preferences
3. Additional Board Manager URLs:
   ```
   https://dl.espressif.com/dl/package_esp32_index.json
   ```
4. Tools → Board → Boards Manager
5. ค้นหา "ESP32" → Install

### ขั้นตอนที่ 3: เลือก Board

1. Tools → Board → ESP32 Arduino
2. เลือก "ESP32 Dev Module" (หรือ board ที่คุณใช้)

### ขั้นตอนที่ 4: เลือก Port

1. เสียบ ESP32 กับคอมพิวเตอร์
2. Tools → Port → เลือก COM Port ที่ปรากฏ

### ขั้นตอนที่ 5: อัปโหลดโค้ด

1. เปิดไฟล์ `All_IdaNEW.ino`
2. กดปุ่ม Upload (→)
3. รอจนอัปโหลดเสร็จ

---

## 📡 Serial Commands

### Manual Motor Control

```cpp
// เคลื่อนที่แกน X
MOTOR:X_FWD     // เดินหน้าแกน X
MOTOR:X_BACK    // ถอยหลังแกน X

// เคลื่อนที่แกน Y
MOTOR:Y_FWD     // เดินหน้าแกน Y
MOTOR:Y_BACK    // ถอยหลังแกน Y

// หยุด
MOTOR:STOP      // หยุดมอเตอร์
```

### Position Control

```cpp
// ไปตำแหน่งที่กำหนด
MOVETO:1        // ไป Position 1 (HOME: X=0, Y=0)
MOVETO:2        // ไป Position 2 (X=0, Y=-4000)
MOVETO:3        // ไป Position 3 (X=-4000, Y=0)
MOVETO:4        // ไป Position 4 (X=-4000, Y=-4000)
```

### Mode Control

```cpp
MODE:MANUAL     // เปลี่ยนเป็น Manual Mode
MODE:AUTO       // เปลี่ยนเป็น Auto Sequence Mode
```

### Pump Control

```cpp
PUMP:ON         // เปิดปั๊มน้ำ (Manual mode เท่านั้น)
PUMP:OFF        // ปิดปั๊มน้ำ

// ตั้งเวลาปั๊ม (มิลลิวินาที)
PUMP_DURATION:5000    // ตั้งเวลา 5 วินาที
PUMP_DURATION:10000   // ตั้งเวลา 10 วินาที
```

### Alarm Control

```cpp
// ตั้งเวลา Alarm (slot 0-2, time HH:MM)
ALARM:0,14:30   // ตั้ง Alarm 1 เวลา 14:30
ALARM:1,08:00   // ตั้ง Alarm 2 เวลา 08:00
ALARM:2,18:00   // ตั้ง Alarm 3 เวลา 18:00

// ยกเลิก Alarm
CANCEL:0        // ยกเลิก Alarm 1
CANCEL:1        // ยกเลิก Alarm 2
CANCEL:2        // ยกเลิก Alarm 3
```

### Auto Sequence

```cpp
START_SEQUENCE  // เริ่ม Auto Sequence ทันที
                // (ปกติจะเริ่มเมื่อถึงเวลา Alarm)
```

### Status & Reset

```cpp
PING            // ตรวจสอบการเชื่อมต่อ → ตอบกลับ PONG
STATUS          // ขอข้อมูลสถานะปัจจุบัน
RESET           // รีเซ็ตค่า Encoder เป็น 0
```

### Color Data (จาก Python)

```cpp
// Python จะส่งข้อมูลสีมาทุกๆ 1 วินาที
COLOR:yellow,green,purple,yellowCount,greenCount,purpleCount

// ตัวอย่าง:
COLOR:1,0,0,3,0,0     // พบสีเหลือง 3 จุด
COLOR:0,1,0,0,5,0     // พบสีเขียว 5 จุด
```

---

## 🔄 System States

### Move States
- `IDLE` - ไม่ได้เคลื่อนที่
- `MOVING_X` - กำลังเคลื่อนที่แกน X
- `MOVING_Y` - กำลังเคลื่อนที่แกน Y

### Operation Modes
- `MANUAL` - ควบคุมด้วยตนเอง
- `AUTO_SEQUENCE` - ทำงานอัตโนมัติตาม Alarm

### Pump States
- `NOT_WAITING` - ไม่ได้รอ
- `WAITING_BEFORE_PUMP` - รอ 1 วินาที ก่อนเปิดปั๊ม
- `PUMPING` - กำลังเปิดปั๊ม

---

## 📊 Auto Sequence Flow

```
1. ตั้งเวลา Alarm (เช่น 14:30)
2. เปลี่ยนเป็น AUTO mode

3. เมื่อถึงเวลา 14:30:
   ├─ ไป HOME (Position 1)
   ├─ รอ 5 วินาที
   ├─ รอ 1 วินาที
   ├─ เปิดปั๊มน้ำ (ตามเวลาที่ตั้ง)
   │
   ├─ ไป Position 2
   ├─ รอ 5 วินาที
   ├─ รอ 1 วินาที
   ├─ เปิดปั๊มน้ำ
   │
   ├─ ไป Position 3
   ├─ (ทำซ้ำ)
   │
   ├─ ไป Position 4
   ├─ (ทำซ้ำ)
   │
   └─ กลับ HOME → เสร็จสิ้น
```

---

## 🔧 การปรับแต่ง

### ความเร็วมอเตอร์

```cpp
// บรรทัดที่ 12-13
int motorSpeed_X = 150;  // ความเร็วแกน X (0-255)
int motorSpeed_Y = 80;   // ความเร็วแกน Y (0-255)
```

### ตำแหน่ง

```cpp
// บรรทัดที่ 54-57 (ใน setTargetPosition)
case 1: targetEncoderX = 0; targetEncoderY = 0; break;
case 2: targetEncoderX = 0; targetEncoderY = -4000; break;
case 3: targetEncoderX = -4000; targetEncoderY = 0; break;
case 4: targetEncoderX = -4000; targetEncoderY = -4000; break;
```

### เวลารอในแต่ละตำแหน่ง

```cpp
// บรรทัดที่ 37
const long TIMED_SEQUENCE_WAIT_TIME = 5000;  // 5 วินาที
```

### เวลารอก่อนเปิดปั๊ม

```cpp
// บรรทัดที่ 46
const long PUMP_WAIT_TIME = 1000;  // 1 วินาที
```

### ระยะทาง Tolerance

```cpp
// บรรทัดที่ 29
const int ENCODER_TOLERANCE = 20;  // ยิ่งน้อย = แม่นยำ (แต่อาจไม่หยุด)
```

---

## 🐛 Troubleshooting

### ปัญหา: อัปโหลดไม่ได้

**สาเหตุ:** ไม่พบ Port หรือ Driver ไม่ถูกต้อง

**แก้ไข:**
1. ติดตั้ง CH340 Driver (สำหรับ ESP32 ราคาถูก)
2. เปลี่ยน USB Cable
3. กด Boot button ขณะอัปโหลด

### ปัญหา: มอเตอร์ไม่เคลื่อนที่

**สาเหตุ:** Pin ผิด หรือ Motor Driver ไม่ได้เสียบไฟ

**แก้ไข:**
1. ตรวจสอบ Pin Connections
2. ตรวจสอบไฟเลี้ยง Motor Driver (12V)
3. ทดสอบ Manual Control: `MOTOR:X_FWD`

### ปัญหา: Encoder นับผิด

**สาเหตุ:** สาย Encoder หลวม หรือ Pin ผิด

**แก้ไข:**
1. ตรวจสอบ Pin A, B
2. ตรวจสอบสายต่อ
3. ส่งคำสั่ง `RESET` รีเซ็ตค่า

### ปัญหา: ปั๊มไม่ทำงาน

**สาเหตุ:** Relay ไม่ทำงาน หรือไฟไม่พอ

**แก้ไข:**
1. ตรวจสอบ Pin 21
2. ตรวจสอบไฟเลี้ยง Relay (5V)
3. ตรวจสอบการต่อปั๊ม (NO/NC)
4. ทดสอบ: `PUMP:ON` และ `PUMP:OFF`

### ปัญหา: Auto Sequence ไม่ทำงาน

**สาเหตุ:** ยังอยู่ Manual Mode หรือไม่ได้ START_SEQUENCE

**แก้ไข:**
1. ส่ง `MODE:AUTO`
2. ตั้ง Alarm: `ALARM:0,14:30`
3. รอจนถึงเวลา หรือส่ง `START_SEQUENCE` ทดสอบ

---

## 📡 Serial Monitor

### เปิด Serial Monitor
- Tools → Serial Monitor
- Baud Rate: **115200**

### ข้อความที่จะเห็น

```
========================================
ESP32 2-Axis Controller
Serial Mode - Python Control Only
========================================
Ready for connection
Hardware ready
========================================
```

### ทดสอบการทำงาน

```
>>> PING
PONG

>>> STATUS
STATUS:X=0,Y=0,MODE=MANUAL,MOVING=NO,YELLOW=NO,GREEN=NO,YC=0,GC=0

>>> MOTOR:X_FWD
ACK:MOTOR_X_FORWARD
```

---

## 🔗 การเชื่อมต่อกับ Python

### Python จะส่งคำสั่งผ่าน Serial:

```python
# ใน flask_controller.py
arduino.send("PING\n")
arduino.send("STATUS\n")
arduino.send("MOTOR:X_FWD\n")
arduino.send("MOVETO:2\n")
arduino.send("PUMP:ON\n")
```

### Arduino จะตอบกลับ:

```cpp
Serial.println("PONG");
Serial.println("ACK:MOTOR_X_FORWARD");
Serial.println("Movement complete");
Serial.println("Pump: ON");
```

---

## 📞 ช่วยเหลือ

### เอกสาร
- HSV Version: `../1_HSV_Version/`
- Segmentation: `../2_Segmentation_Version/`
- Documentation: `../4_Documentation/`

### Resources
- [ESP32 Datasheet](https://www.espressif.com/en/products/socs/esp32)
- [L298N Tutorial](https://lastminuteengineers.com/l298n-dc-stepper-driver-arduino-tutorial/)
- [Rotary Encoder Tutorial](https://www.arduino.cc/en/Tutorial/Encoder)

---

**Board:** ESP32 DevKit V1
**Baud Rate:** 115200
**Voltage:** 3.3V (Logic), 5V (Motors/Relay)
**Flash Size:** 4MB
