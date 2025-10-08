# คู่มือการใช้งานระบบ ESP32 2-Axis Controller with Image Processing

## ภาพรวมระบบ

ระบบนี้ประกอบด้วย 2 ส่วนหลัก:
1. **Python Flask Web Application** - ทำหน้าที่ตรวจจับสี (Image Processing) และเป็น Web Interface หลัก
2. **Arduino/ESP32** - ควบคุมมอเตอร์และ encoders พร้อมระบบ WiFi Web Server

## การทำงานของระบบ

```
[กล้อง] → [Python Flask] → [Serial USB] → [Arduino/ESP32] → [มอเตอร์]
                ↓
         [Web Browser]
       http://localhost:5001
```

### Python Flask (Port 5001)
- ตรวจจับสีเหลืองและเขียวจากกล้อง
- แสดงภาพแบบ Real-time
- ส่งข้อมูลการตรวจจับสีไปยัง Arduino ผ่าน Serial
- ควบคุม Arduino ผ่าน Web Interface

### Arduino/ESP32 (Port 80 - WiFi)
- รับคำสั่งจาก Python ผ่าน Serial
- ควบคุมมอเตอร์ 2 แกน (X, Y)
- อ่านค่า Encoder
- มีระบบ Web Server ของตัวเอง (แต่แนะนำให้ใช้ Python Web Interface)

## วิธีการใช้งาน (ขั้นตอนที่ถูกต้อง)

### 1. เตรียมฮาร์ดแวร์
```
✓ เชื่อมต่อ Arduino/ESP32 กับคอมพิวเตอร์ผ่าน USB
✓ ต่อมอเตอร์และ encoder ตามพิน (ดูด้านล่าง)
✓ เชื่อมต่อกล้อง USB หรือ webcam
```

### 2. Upload โค้ดไปยัง Arduino
```bash
# ใช้ Arduino IDE เปิดไฟล์
All_IdaNEW/All_IdaNEW.ino

# แก้ไข WiFi credentials (ถ้าต้องการใช้ WiFi)
char ssid[] = "YourWiFi";
char pass[] = "YourPassword";

# อัปโหลดไปยัง ESP32
```

### 3. รัน Python Flask Application
```bash
# ติดตั้ง dependencies (ครั้งแรกเท่านั้น)
pip install -r requirements.txt

# รันโปรแกรม
python flask_controller.py
```

### 4. เปิดเว็บบราวเซอร์
```
เข้าไปที่: http://localhost:5001
```

⚠️ **สำคัญ: ใช้เว็บจาก Python (Port 5001) เป็นหลัก ไม่ใช่เว็บจาก Arduino**

## Serial Communication Protocol

### คำสั่งจาก Python → Arduino

| คำสั่ง | รูปแบบ | คำอธิบาย | ตัวอย่าง |
|--------|--------|----------|----------|
| **COLOR** | `COLOR:y,g,yc,gc\n` | ส่งข้อมูลการตรวจจับสี | `COLOR:1,0,3,0\n` |
| **PING** | `PING\n` | ทดสอบการเชื่อมต่อ | `PING\n` |
| **STATUS** | `STATUS\n` | ขอสถานะปัจจุบัน | `STATUS\n` |
| **MOTOR** | `MOTOR:command\n` | ควบคุมมอเตอร์ | `MOTOR:X_FWD\n` |

#### รายละเอียดคำสั่ง COLOR
```
COLOR:y,g,yc,gc

y  = Yellow detected (0 หรือ 1)
g  = Green detected (0 หรือ 1)
yc = Yellow count (จำนวนจุดสีเหลือง)
gc = Green count (จำนวนจุดสีเขียว)
```

#### คำสั่ง MOTOR ที่รองรับ
- `MOTOR:STOP` - หยุดมอเตอร์ทั้งหมด
- `MOTOR:X_FWD` - เคลื่อนแกน X ไปข้างหน้า
- `MOTOR:X_BACK` - เคลื่อนแกน X ถอยหลัง
- `MOTOR:Y_FWD` - เคลื่อนแกน Y ไปข้างหน้า
- `MOTOR:Y_BACK` - เคลื่อนแกน Y ถอยหลัง

### การตอบกลับจาก Arduino → Python

| การตอบกลับ | รูปแบบ | คำอธิบาย |
|-----------|--------|----------|
| **PONG** | `PONG\n` | ตอบกลับ PING |
| **ACK:COLOR_RECEIVED** | `ACK:COLOR_RECEIVED\n` | ยืนยันรับข้อมูลสี |
| **ACK:MOTOR_STOPPED** | `ACK:MOTOR_STOPPED\n` | ยืนยันหยุดมอเตอร์ |
| **STATUS** | `STATUS:X=0,Y=0,MODE=MANUAL,...\n` | ส่งสถานะ |
| **COLOR_CHANGE** | `COLOR_CHANGE:Y=1,G=0,YC=3,GC=0\n` | แจ้งเปลี่ยนสี |
| **ERROR** | `ERROR:UNKNOWN_COMMAND\n` | แจ้งข้อผิดพลาด |

## การใช้งาน Web Interface (Python Flask)

### หน้าจอหลักมี 4 ส่วน

#### 1. System Status & Control
- แสดงตำแหน่งแกน X และ Y
- ปุ่ม STOP ALL - หยุดทุกอย่าง
- ปุ่ม Reset Encoders - รีเซ็ตค่าตำแหน่ง

#### 2. Camera & Color Detection
- แสดงภาพจากกล้องแบบ Real-time
- ปุ่ม "เปิดกล้อง" / "ปิดกล้อง"
- แสดงสถานะการตรวจจับสีเหลืองและเขียว
- แสดงจำนวนจุดสีที่ตรวจพบ

#### 3. Arduino Control
- แสดงสถานะการเชื่อมต่อกับ Arduino
- ปุ่ม "เชื่อมต่อ Arduino" - เชื่อมต่อใหม่
- ปุ่ม "Ping Test" - ทดสอบการเชื่อมต่อ
- ปุ่ม "ดูสถานะ" - ขอสถานะจาก Arduino
- ปุ่มควบคุมมอเตอร์ (X/Y Forward/Backward)
- ปุ่ม STOP (Arduino) - หยุดมอเตอร์

#### 4. Operation Mode
- **Manual Mode**: ควบคุมด้วยตนเอง
  - Manual Jog: กดค้างเพื่อเคลื่อนไหว
  - Go To Position: ไปยังตำแหน่งที่บันทึกไว้ (1-4)

- **Auto Sequence Mode**: ทำงานอัตโนมัติ
  - ตั้งเวลาทำงาน (3 ช่วง)
  - เมื่อถึงเวลา จะทำงานตามลำดับ

## โหมดการทำงานอัตโนมัติ (Auto Mode)

เมื่ออยู่ในโหมด Auto Sequence และมีการตรวจจับสี Arduino จะทำงานดังนี้:

```
พบสีเหลืองอย่างเดียว    → ไปตำแหน่ง 2
พบสีเขียวอย่างเดียว     → ไปตำแหน่ง 3
พบทั้งสีเหลืองและเขียว  → ไปตำแหน่ง 4
ไม่พบสี                → กลับตำแหน่ง 1 (HOME)
```

## การตั้งค่าการตรวจจับสี

ค่า HSV สำหรับการตรวจจับสี (ปรับได้ใน flask_controller.py บรรทัด 50-56):

```python
# สีเหลือง
yellow_lower = np.array([20, 50, 50])
yellow_upper = np.array([30, 255, 255])

# สีเขียว
green_lower = np.array([40, 50, 50])
green_upper = np.array([80, 255, 255])
```

ขนาดขั้นต่ำของวัตถุ (pixels):
```python
min_area = 500  # บรรทัด 67
```

## Pin Configuration (Arduino/ESP32)

```
Encoder X:
  - Pin A: GPIO 13
  - Pin B: GPIO 12

Encoder Y:
  - Pin A: GPIO 14
  - Pin B: GPIO 27

Motor X:
  - IN1: GPIO 26
  - IN2: GPIO 25
  - ENA (PWM): GPIO 18

Motor Y:
  - IN3: GPIO 16
  - IN4: GPIO 17
  - ENB (PWM): GPIO 19
```

## การแก้ไขปัญหา

### 1. กล้องไม่ทำงาน
```
❌ ปัญหา: ไม่เห็นภาพจากกล้อง
✅ แก้ไข:
   - ตรวจสอบว่าไม่มีโปรแกรมอื่นใช้กล้องอยู่
   - ลองกด "ปิดกล้อง" แล้ว "เปิดกล้อง" ใหม่
   - ตรวจสอบว่ามีกล้อง USB เชื่อมต่ออยู่
```

### 2. Arduino ไม่เชื่อมต่อ
```
❌ ปัญหา: สถานะแสดง "ไม่เชื่อมต่อ"
✅ แก้ไข:
   - ตรวจสอบสาย USB เชื่อมต่อ
   - ตรวจสอบว่า Arduino อัปโหลดโค้ดแล้ว
   - กด "เชื่อมต่อ Arduino" ใหม่
   - ตรวจสอบ baud rate (ต้องเป็น 115200)
   - ปิดโปรแกรม Arduino IDE (อาจจะล็อค Serial Port)
```

### 3. ตรวจจับสีไม่ได้
```
❌ ปัญหา: ไม่พบสีแม้จะมีวัตถุสีในภาพ
✅ แก้ไข:
   - ปรับแสงสว่างให้เหมาะสม
   - ปรับค่า HSV range ใน flask_controller.py
   - ลดค่า min_area หากวัตถุเล็กเกินไป
```

### 4. Serial Error
```
❌ ปัญหา: [Errno 16] Resource busy
✅ แก้ไข:
   - ปิด Arduino IDE Serial Monitor
   - ตรวจสอบว่าไม่มีโปรแกรมอื่นเปิด Serial Port
   - ถอดปลั๊ก USB แล้วเสียบใหม่
```

## Flow การทำงานแบบเต็ม

```
1. Arduino เริ่มต้น
   ├─ เชื่อมต่อ WiFi
   ├─ เริ่ม Web Server (Port 80)
   ├─ เริ่ม Serial (115200 baud)
   └─ พร้อมรับคำสั่ง

2. Python Flask เริ่มต้น
   ├─ เริ่ม Web Server (Port 5001)
   ├─ พยายามเชื่อมต่อกล้อง
   ├─ พยายามเชื่อมต่อ Arduino (Auto-detect port)
   └─ เริ่ม Background thread สำหรับตรวจจับสี

3. User เข้าเว็บ http://localhost:5001
   ├─ กด "เปิดกล้อง"
   ├─ ดูภาพแบบ Real-time
   └─ เห็นข้อมูลการตรวจจับสี

4. ระบบส่งข้อมูล (ทุก 1 วินาที)
   ├─ Python ตรวจจับสี
   ├─ ส่งคำสั่ง COLOR:y,g,yc,gc ไปยัง Arduino
   └─ Arduino ตอบกลับ ACK:COLOR_RECEIVED

5. User ควบคุมมอเตอร์
   ├─ กดปุ่มบนเว็บ
   ├─ Flask ส่งคำสั่ง MOTOR:X_FWD
   └─ Arduino ควบคุมมอเตอร์และตอบกลับ ACK
```

## ข้อควรระวัง

⚠️ **อย่าใช้เว็บทั้ง 2 ตัวพร้อมกัน**
- ใช้เฉพาะ Python Web (http://localhost:5001)
- เว็บจาก Arduino (http://[ESP32_IP]) เป็นระบบสำรอง

⚠️ **Serial Port**
- Python และ Arduino IDE ใช้ Serial Port เดียวกันไม่ได้
- ต้องปิด Serial Monitor ก่อนรัน Python

⚠️ **Camera**
- ปิดโปรแกรมที่ใช้กล้องอื่นๆ ก่อน
- กล้อง 1 ตัว ใช้กับ 1 โปรแกรมในเวลาเดียวกัน

## คำสั่งที่มีประโยชน์

### ตรวจสอบ Serial Ports (macOS)
```bash
ls /dev/cu.*
```

### ตรวจสอบ Serial Ports (Linux)
```bash
ls /dev/ttyUSB* /dev/ttyACM*
```

### ทดสอบกล้อง
```bash
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Error')"
```

### ดู Log จาก Arduino (Serial Monitor)
```bash
screen /dev/cu.usbserial-1410 115200
# กด Ctrl+A แล้ว K เพื่อออก
```

## API Endpoints (สำหรับ Developer)

### Python Flask API
```
GET  /                          - หน้าเว็บหลัก
GET  /video_feed                - Video stream (MJPEG)
GET  /data                      - ข้อมูลสถานะระบบ (JSON)
GET  /detection_data            - ข้อมูลการตรวจจับสี (JSON)
GET  /camera_control?action=    - เปิด/ปิดกล้อง (start/stop)
GET  /arduino_control?action=   - ควบคุม Arduino
GET  /motor?dir=                - ควบคุมมอเตอร์ (xfwd/xback/yfwd/yback/stop)
GET  /moveto?pos=               - ไปยังตำแหน่ง (1-4)
GET  /setmode?mode=             - เปลี่ยนโหมด (manual/auto_sequence)
GET  /set-alarm?alarmTime=&slot= - ตั้งเวลา
GET  /cancel-alarm?slot=        - ยกเลิกเวลา
GET  /reset                     - รีเซ็ต encoders
```

## สรุป

ระบบนี้เป็นการรวมระหว่าง:
- **Image Processing (Python)**: ตรวจจับสี Real-time
- **Motor Control (Arduino)**: ควบคุมแกน X-Y
- **Web Interface (Flask)**: ควบคุมทุกอย่างผ่านเว็บ
- **Serial Communication**: เชื่อมต่อ Python และ Arduino

**การใช้งานที่ถูกต้อง**: ใช้เว็บจาก Python (localhost:5001) เป็นหน้าหลักในการควบคุมทั้งระบบ
