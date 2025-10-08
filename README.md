# ESP32 2-Axis Controller with Image Processing

ระบบควบคุมมอเตอร์ 2 แกนด้วย ESP32 พร้อมระบบ Image Processing สำหรับตรวจจับสีเหลืองและสีเขียว

**⚠️ สำคัญ: ระบบนี้ใช้ Python Flask Web Interface เป็นหลัก ไม่มี WiFi/Web Server บน Arduino**

## คุณสมบัติ

- ✅ ควบคุมมอเตอร์ผ่าน **Python Flask Web Interface** (Manual และ Auto)
- ✅ ติดตาม Encoder position แบบ real-time
- ✅ ระบบ Image Processing ตรวจจับสีเหลืองและเขียว
- ✅ แสดงภาพกล้องสดบนเว็บ
- ✅ การสื่อสารระหว่าง Python และ Arduino ผ่าน **Serial USB**
- ✅ ระบบตั้งเวลาอัตโนมัติ
- ✅ ควบคุม Arduino ผ่านเว็บอินเทอร์เฟซ Python

## การติดตั้ง

### 1. ติดตั้ง Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. อัปโหลดโค้ด Arduino

- อัปโหลดไฟล์ `All_IdaNEW/All_IdaNEW.ino` ไปยัง ESP32/Arduino
- **ไม่ต้องตั้งค่า WiFi** (โค้ดใหม่ไม่มี WiFi/Web Server)
- เชื่อมต่อ Arduino กับ USB port สำหรับ Serial communication

### 3. รันระบบ

```bash
python flask_controller.py
```

### 4. เปิดเว็บบราวเซอร์

- ไปที่ `http://localhost:5001` **(URL เดียวที่ใช้)**
- ~~ไม่มีเว็บจาก Arduino อีกต่อไป~~

## การใช้งาน

### ระบบกล้องและการตรวจจับสี

1. กดปุ่ม "เปิดกล้อง" เพื่อเริ่มต้นกล้อง
2. ระบบจะตรวจจับสีเหลืองและเขียวอัตโนมัติ
3. ข้อมูลการตรวจจับจะส่งไปยัง Arduino ผ่าน Serial USB

### การควบคุม Arduino

1. กดปุ่ม "เชื่อมต่อ Arduino" เพื่อเชื่อมต่อ
2. ใช้ปุ่มควบคุมมอเตอร์ผ่านเว็บ
3. ดูสถานะการเชื่อมต่อและข้อมูลที่ได้รับ

### โหมดการทำงาน

- **Manual Mode**: ควบคุมมอเตอร์ด้วยตัวเอง
- **Auto Sequence Mode**: ทำงานตามลำดับที่กำหนด + การตรวจจับสี

## คำสั่ง Serial Communication

### จาก Python ไป Arduino:

- `COLOR:y,g,yc,gc` - ส่งข้อมูลการตรวจจับสี (y=yellow detected, g=green detected, yc=yellow count, gc=green count)
- `PING` - ทดสอบการเชื่อมต่อ
- `STATUS` - ขอสถานะปัจจุบัน
- `MOTOR:command` - ส่งคำสั่งมอเตอร์ (STOP, X_FWD, X_BACK, Y_FWD, Y_BACK)

### จาก Arduino ไป Python:

- `PONG` - ตอบกลับ PING
- `ACK:COLOR_RECEIVED` - ยืนยันรับข้อมูลสี
- `STATUS:...` - ส่งสถานะปัจจุบัน
- `COLOR_CHANGE:...` - แจ้งเมื่อมีการเปลี่ยนแปลงสี

## Hardware Requirements

- ESP32 หรือ Arduino microcontroller
- 2x Stepper motors พร้อม encoders
- Motor driver boards
- USB Camera หรือ webcam
- **สาย USB สำหรับเชื่อมต่อ Arduino กับคอมพิวเตอร์**
- แหล่งจ่ายไฟ

## การตั้งค่าสี (HSV Values)

### สีเหลือง

- Lower: [20, 50, 50]
- Upper: [30, 255, 255]

### สีเขียว

- Lower: [40, 50, 50]
- Upper: [80, 255, 255]

สามารถปรับค่าเหล่านี้ในไฟล์ `flask_controller.py` ได้ตามต้องการ

## การแก้ไขปัญหา

1. **กล้องไม่ทำงาน**: ตรวจสอบว่าไม่มีโปรแกรมอื่นใช้กล้องอยู่
2. **Arduino ไม่เชื่อมต่อ**: ตรวจสอบ USB port และ baud rate (115200)
3. **ไม่ตรวจจับสี**: ปรับแสงสว่างและค่า HSV range
4. **Serial Error**: ปิดโปรแกรมอื่นที่อาจใช้ Serial port อยู่ (เช่น Arduino IDE Serial Monitor)

## โครงสร้างไฟล์

```
Ida_PTham/
├── flask_controller.py      # Main Python application
├── requirements.txt         # Python dependencies
├── templates/
│   └── web_interface.html  # Web interface (Flask)
├── All_IdaNEW/
│   └── All_IdaNEW.ino      # Arduino code (Serial only, NO WiFi)
└── SYSTEM_GUIDE.md         # คู่มือการใช้งานโดยละเอียด
```

## เอกสารเพิ่มเติม

อ่านคู่มือการใช้งานฉบับเต็มได้ที่: [SYSTEM_GUIDE.md](SYSTEM_GUIDE.md)

## สรุป

- ✅ ใช้เฉพาะ **Python Flask Web** ที่ `http://localhost:5001`
- ✅ Arduino ทำงานผ่าน **Serial USB** เท่านั้น
- ✅ **ไม่มี WiFi** และ **ไม่มี Web Server** บน Arduino
- ✅ ควบคุมทุกอย่างผ่านเว็บ Python
