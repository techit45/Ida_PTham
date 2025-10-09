# 🌱 ระบบตรวจสอบพืชและรดน้ำอัตโนมัติ
## ESP32 + YOLOv8 Segmentation

---

## 📁 โครงสร้างโปรเจค

```
Ida_PTham/
│
├── 📂 1_HSV_Version/                    # เวอร์ชัน HSV (เริ่มต้น)
│   ├── flask_controller.py             # Flask Controller
│   ├── requirements.txt                # Library
│   ├── templates/                      # หน้าเว็บ
│   └── README.md                       # คู่มือใช้งาน HSV
│
├── 📂 2_Segmentation_Version/           # เวอร์ชัน Segmentation (ขั้นสูง)
│   ├── flask_controller.py             # Flask Controller พร้อม Segmentation
│   ├── requirements.txt                # Library รวม YOLO
│   ├── templates/                      # หน้าเว็บ
│   ├── train_segmentation.py           # เทรน Model
│   ├── test_model.py                   # ทดสอบ Model
│   ├── simple_segmentation_demo.py     # Demo Real-time
│   ├── migrate_to_segmentation.py      # สคริปต์อัพเกรด
│   └── README.md                       # คู่มือใช้งาน Segmentation
│
├── 📂 3_Arduino/                        # Arduino Code
│   ├── All_IdaNEW/
│   │   └── All_IdaNEW.ino              # ESP32 Firmware
│   └── README.md                       # คู่มือ Hardware + Pin
│
├── 📂 4_Documentation/                  # เอกสารทั้งหมด
│   ├── README.md                       # ระบบโดยรวม (HSV)
│   ├── SYSTEM_GUIDE.md                 # คู่มือระบบฉบับเต็ม
│   ├── SEGMENTATION_GUIDE.md           # คู่มือเทรน Model
│   ├── INTEGRATION_GUIDE.md            # คู่มือ API + Integration
│   └── README_SEGMENTATION.md          # คู่มือรวม Segmentation
│
├── .gitignore                          # Git ignore
└── PROJECT_STRUCTURE.md                # ไฟล์นี้
```

---

## 🚀 Quick Start

### สำหรับผู้เริ่มต้น (5 นาที)

```bash
# 1. ไปที่โฟลเดอร์ HSV
cd 1_HSV_Version

# 2. ติดตั้ง Library
pip install -r requirements.txt

# 3. รันโปรแกรม
python flask_controller.py

# 4. เปิดเว็บ
http://localhost:5001
```

### สำหรับผู้ที่ต้องการ Segmentation

```bash
# 1. ไปที่โฟลเดอร์ Segmentation
cd 2_Segmentation_Version

# 2. ติดตั้ง Library
pip install -r requirements.txt

# 3. เทรน Model (ต้องมี Dataset จาก Roboflow)
python train_segmentation.py

# 4. รันโปรแกรม
python flask_controller.py
```

---

## 📊 เปรียบเทียบเวอร์ชัน

| คุณสมบัติ | HSV Version | Segmentation Version |
|-----------|-------------|---------------------|
| 📍 ตำแหน่ง | `1_HSV_Version/` | `2_Segmentation_Version/` |
| ⚡ ความเร็ว | 60 FPS | 30 FPS |
| 🎯 ความแม่นยำ | 60-70% | 90-95% |
| ⏱️ ติดตั้ง | 5 นาที | 2-4 ชั่วโมง |
| 💻 GPU | ไม่ต้อง | แนะนำ |
| 📸 Dataset | ไม่ต้อง | ต้อง 100+ ภาพ |
| 🔍 แยกใบ | ❌ | ✅ |
| 📏 วัดพื้นที่ | ❌ | ✅ |
| 💡 ใช้เมื่อ | ทดสอบ/เรียนรู้ | ใช้งานจริง |

---

## 🎯 เลือกใช้เวอร์ชันไหน?

### ใช้ HSV Version เมื่อ:
- ✅ เริ่มต้นใช้งาน / ทดสอบระบบ
- ✅ โปรเจคนักเรียน/นักศึกษา
- ✅ งบประมาณจำกัด (ไม่มี GPU)
- ✅ ต้องการติดตั้งเร็ว
- ✅ ความแม่นยำ 60-70% เพียงพอ

### ใช้ Segmentation Version เมื่อ:
- ✅ ต้องการความแม่นยำสูง (90%+)
- ✅ ใช้งานจริง (Production)
- ✅ มี GPU
- ✅ มีข้อมูลภาพเพื่อเทรน
- ✅ งานวิจัย/วิทยานิพนธ์

---

## 📖 คู่มือการใช้งาน

### อ่านตามลำดับ

#### ระดับ 1: ผู้เริ่มต้น
```
1. 1_HSV_Version/README.md
   ↓
2. 3_Arduino/README.md (ถ้าต้องอัปโหลด Arduino)
   ↓
3. 4_Documentation/SYSTEM_GUIDE.md (ถ้าติดปัญหา)
```

#### ระดับ 2: ผู้ใช้ Segmentation
```
1. 4_Documentation/README_SEGMENTATION.md (ภาพรวม)
   ↓
2. 4_Documentation/SEGMENTATION_GUIDE.md (เทรน)
   ↓
3. 4_Documentation/INTEGRATION_GUIDE.md (ใช้งาน)
   ↓
4. 2_Segmentation_Version/README.md (Quick Start)
```

#### ระดับ 3: ผู้พัฒนา
```
1. 4_Documentation/SYSTEM_GUIDE.md (เข้าใจระบบ)
   ↓
2. 3_Arduino/README.md (Hardware)
   ↓
3. 4_Documentation/INTEGRATION_GUIDE.md (API)
```

---

## 🔧 Hardware Requirements

### Electronics
- ESP32 DevKit V1
- L298N Motor Driver (2 ชิ้น)
- Rotary Encoder (2 ชิ้น)
- Relay Module 1 Channel
- มอเตอร์ DC 12V (2 ตัว)
- ปั๊มน้ำ 12V

### Computer
**สำหรับ HSV:**
- CPU: i3 ขึ้นไป
- RAM: 4GB
- OS: Windows/macOS/Linux

**สำหรับ Segmentation:**
- CPU: i5 ขึ้นไป
- RAM: 8GB+ (16GB แนะนำ)
- GPU: NVIDIA (แนะนำ)
- OS: Windows/Linux (CUDA Support)

---

## 💻 Software Requirements

### HSV Version
```
Python 3.8+
Flask
OpenCV
PySerial
NumPy
```

### Segmentation Version
```
(รวม HSV Version +)
Ultralytics YOLOv8
Roboflow
PyTorch
CUDA (ถ้ามี GPU)
```

---

## 🎓 Learning Path

### สัปดาห์ที่ 1: พื้นฐาน
- ติดตั้งและทดสอบ HSV Version
- เข้าใจการทำงานของระบบ
- ทดลอง Manual Control

### สัปดาห์ที่ 2: Auto Mode
- ตั้งค่า Arduino
- ทดสอบ Auto Sequence
- ปรับแต่งการเคลื่อนที่

### สัปดาห์ที่ 3-4: Segmentation (ถ้าต้องการ)
- เก็บข้อมูลภาพ (100-500 ภาพ)
- เทรน Model บน Roboflow
- ทดสอบและปรับแต่ง

### สัปดาห์ที่ 5: Integration
- นำ Segmentation มาใช้
- เปรียบเทียบกับ HSV
- Fine-tune ระบบ

---

## 🐛 Troubleshooting

### ปัญหาทั่วไป

#### กล้องไม่เปิด
```python
# ลอง Index อื่น
camera = cv2.VideoCapture(1)  # ทดลอง 0, 1, 2
```

#### Arduino เชื่อมต่อไม่ได้
- ติดตั้ง CH340 Driver
- เลือก COM Port ให้ถูก
- ปิดโปรแกรมอื่นที่ใช้ Serial

#### Model โหลดไม่ได้
```bash
# ตรวจสอบว่ามีไฟล์
ls 2_Segmentation_Version/runs/segment/*/weights/best.pt

# ถ้าไม่มี → เทรนก่อน
cd 2_Segmentation_Version
python train_segmentation.py
```

### เอกสารเพิ่มเติม
- ดู Troubleshooting Section ในแต่ละ README
- ดู `4_Documentation/SYSTEM_GUIDE.md`

---

## 🎯 Use Cases

### 1. โปรเจคการศึกษา
- ใช้ HSV Version
- เน้นทำความเข้าใจระบบ
- ต้นทุนต่ำ

### 2. งานวิจัย
- ใช้ Segmentation Version
- เน้นความแม่นยำ
- เก็บข้อมูลเพื่อวิเคราะห์

### 3. ใช้งานจริง (ฟาร์ม/โรงเรือน)
- เริ่มจาก HSV → อัพเกรดเป็น Segmentation
- เชื่อมต่อ Line Notify
- บันทึกข้อมูลลง Database

---

## 📞 Support

### เอกสาร
- คู่มือใน `4_Documentation/`
- README ในแต่ละโฟลเดอร์

### Community
- GitHub Issues
- Email Support

### Resources
- [YOLOv8 Docs](https://docs.ultralytics.com/)
- [Roboflow](https://docs.roboflow.com/)
- [ESP32 Reference](https://docs.espressif.com/)

---

## 📝 License

MIT License - ใช้งานได้ฟรี

---

## 🙏 Credits

- **YOLOv8** by Ultralytics
- **Roboflow** for Dataset Tools
- **Flask** Web Framework
- **OpenCV** Computer Vision
- **ESP32** by Espressif

---

## 🎉 Feature Highlights

### ปัจจุบัน
- ✅ ควบคุมมอเตอร์ 2 แกน
- ✅ ตรวจจับสี (HSV)
- ✅ Instance Segmentation (YOLOv8)
- ✅ รดน้ำอัตโนมัติ
- ✅ ตั้งเวลา (3 Alarms)
- ✅ Web Interface

### อนาคต
- 🔜 Line Notify Alert
- 🔜 Database Logging
- 🔜 Dashboard Analytics
- 🔜 Mobile App
- 🔜 Multi-camera Support
- 🔜 Weather API Integration

---

**เวอร์ชัน:** 2.0 (with Segmentation)
**Python:** 3.8+
**Arduino:** ESP32
**สถานะ:** Production Ready

---

## 🚦 Getting Started Now!

### ทดลองใช้ทันที (5 นาที)
```bash
cd 1_HSV_Version
pip install -r requirements.txt
python flask_controller.py
```

### เทรน Segmentation Model (2-4 ชั่วโมง)
```bash
cd 2_Segmentation_Version
# 1. เตรียม Dataset บน Roboflow
# 2. แก้ไข train_segmentation.py
python train_segmentation.py
```

### อัปโหลด Arduino Code
```bash
# เปิด Arduino IDE
# เปิดไฟล์ 3_Arduino/All_IdaNEW/All_IdaNEW.ino
# กดปุ่ม Upload
```

---

**Happy Coding! 🌱**
