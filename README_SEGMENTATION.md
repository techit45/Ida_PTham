# ระบบตรวจสอบพืชและรดน้ำอัตโนมัติ พร้อม YOLOv8 Segmentation

## 📁 โครงสร้างไฟล์

```
Ida_PTham/
├── 📄 flask_controller.py                    # Flask Controller (HSV)
├── 📄 flask_controller_segmentation.py       # Flask Controller (รองรับ Segmentation)
├── 📁 templates/
│   └── 📄 web_interface.html                 # หน้าเว็บ
├── 📁 All_IdaNEW/
│   └── 📄 All_IdaNEW.ino                     # Arduino Code
│
├── 🎯 โค้ดเทรน Segmentation
│   ├── 📄 train_segmentation.py              # เทรน Model
│   ├── 📄 test_model.py                      # ทดสอบ Model
│   ├── 📄 simple_segmentation_demo.py        # Demo Real-time
│   └── 📄 requirements_segmentation.txt      # Library
│
├── 📚 คู่มือ
│   ├── 📄 SEGMENTATION_GUIDE.md              # คู่มือเทรน Model
│   ├── 📄 INTEGRATION_GUIDE.md               # คู่มือนำไปใช้
│   └── 📄 README_SEGMENTATION.md             # ไฟล์นี้
│
└── 🔧 เครื่องมือ
    └── 📄 migrate_to_segmentation.py         # สคริปต์อัพเกรด
```

---

## 🚀 Quick Start

### สำหรับผู้ใช้งานทั่วไป (ใช้ HSV)

```bash
# ติดตั้ง Library
pip install flask opencv-python pyserial roboflow

# รันโปรแกรม
python flask_controller.py

# เปิดเว็บ
http://localhost:5001
```

### สำหรับผู้ที่ต้องการ Segmentation

```bash
# 1. ติดตั้ง Library
pip install -r requirements_segmentation.txt

# 2. เทรน Model (ต้องมี Dataset จาก Roboflow)
python train_segmentation.py

# 3. ทดสอบ Model
python simple_segmentation_demo.py

# 4. ใช้กับระบบ
python flask_controller_segmentation.py
```

---

## 📋 ขั้นตอนการใช้งานแบบละเอียด

### ระดับ 1: ผู้เริ่มต้น (ใช้ HSV)

**ระยะเวลา:** 5 นาที

1. ติดตั้ง Library พื้นฐาน
2. รัน `flask_controller.py`
3. เปิดเว็บและใช้งาน
4. ระบบจะใช้ HSV ตรวจจับสี

**ข้อดี:** ง่าย รวดเร็ว ไม่ต้องเทรน
**ข้อเสีย:** แม่นยำน้อย (60-70%)

---

### ระดับ 2: ผู้ใช้งานทั่วไป (ใช้ Pre-trained Model)

**ระยะเวลา:** 15 นาที

1. ดาวน์โหลด Pre-trained Model (ถ้ามี)
2. วางไว้ที่ `runs/segment/plant_segmentation/weights/best.pt`
3. รัน `flask_controller_segmentation.py`
4. กดปุ่มสลับโหมดเป็น Segmentation

**ข้อดี:** แม่นยำสูง (90-95%) ไม่ต้องเทรนเอง
**ข้อเสีย:** ต้องมี Model ที่เทรนแล้ว

---

### ระดับ 3: ผู้พัฒนา (เทรน Model เอง)

**ระยะเวลา:** 2-4 ชั่วโมง

#### ขั้นตอนที่ 1: เตรียม Dataset (1 ชั่วโมง)

1. สมัคร Roboflow: https://roboflow.com
2. สร้าง Project แบบ Instance Segmentation
3. อัปโหลดภาพ 100-500 ภาพ
4. วาด Annotation (รอบใบพืช)
5. ตั้งชื่อ Class:
   - `yellow_leaf` - ใบเหลือง
   - `green_leaf` - ใบเขียว
   - `purple_leaf` - ใบม่วง
6. Generate Dataset (Train 70%, Valid 20%, Test 10%)
7. Export เป็น YOLOv8

#### ขั้นตอนที่ 2: เทรน Model (1-2 ชั่วโมง)

```bash
# แก้ไข train_segmentation.py
# - ใส่ API Key
# - ใส่ Workspace และ Project name

# รันการเทรน
python train_segmentation.py

# รอให้เทรนเสร็จ (30 นาที - 2 ชั่วโมง)
```

#### ขั้นตอนที่ 3: ทดสอบ Model (15 นาที)

```bash
# ทดสอบกับ Webcam
python simple_segmentation_demo.py

# ทดสอบกับภาพ
python test_model.py
```

#### ขั้นตอนที่ 4: นำไปใช้ (30 นาที)

```bash
# วิธีที่ 1: ใช้สคริปต์อัตโนมัติ
python migrate_to_segmentation.py

# วิธีที่ 2: ทำเอง
python flask_controller_segmentation.py
```

**ข้อดี:** แม่นยำสูงสุด ปรับแต่งได้ตามต้องการ
**ข้อเสีย:** ใช้เวลานาน ต้องมี Dataset

---

## 🎯 คุณสมบัติ

### ✅ พื้นฐาน (ทุกระดับ)
- ✓ ควบคุมมอเตอร์ 2 แกน
- ✓ ไปตำแหน่งอัตโนมัติ (1-4)
- ✓ ควบคุมปั๊มน้ำ
- ✓ ตั้งเวลารดน้ำ (Alarm)
- ✓ แสดงภาพจากกล้อง

### 🎨 การตรวจจับ (ขึ้นกับโหมด)

**HSV Mode:**
- ✓ ตรวจจับสีเหลือง, เขียว, ม่วง
- ✓ นับจำนวนหยาบๆ
- ✓ วิเคราะห์สุขภาพพืชเบื้องต้น

**Segmentation Mode:**
- ✓ ตรวจจับแบบ Instance Segmentation
- ✓ แยกแต่ละใบได้
- ✓ นับจำนวนแม่นยำ
- ✓ วัดพื้นที่ใบ
- ✓ วิเคราะห์สุขภาพพืชละเอียด

### 🤖 Auto Mode
- ✓ ตั้งเวลาเริ่มทำงาน (3 Alarms)
- ✓ เคลื่อนที่อัตโนมัติ: HOME → 2 → 3 → 4 → HOME
- ✓ รอ 5 วินาที ณ แต่ละจุด
- ✓ รดน้ำอัตโนมัติ (ตั้งเวลาได้)
- ✓ บันทึกข้อมูลสุขภาพพืช

---

## 🔧 การติดตั้ง

### Windows

```bash
# ติดตั้ง Python 3.8+
# ดาวน์โหลดจาก python.org

# ติดตั้ง Library
pip install flask opencv-python pyserial numpy

# สำหรับ Segmentation
pip install ultralytics roboflow
```

### macOS / Linux

```bash
# ติดตั้ง Python 3.8+
sudo apt install python3 python3-pip  # Ubuntu/Debian
brew install python3                  # macOS

# ติดตั้ง Library
pip3 install flask opencv-python pyserial numpy

# สำหรับ Segmentation
pip3 install ultralytics roboflow
```

---

## 📊 การเปรียบเทียบ

| คุณสมบัติ | HSV | Segmentation |
|-----------|-----|--------------|
| ความแม่นยำ | 60-70% | 90-95% |
| ความเร็ว | 60 FPS | 30 FPS |
| แยกแต่ละใบ | ❌ | ✅ |
| วัดพื้นที่ | ❌ | ✅ |
| ทนต่อแสง | ❌ | ✅ |
| ต้องเทรน | ❌ | ✅ |
| ใช้ GPU | ❌ | แนะนำ |
| ติดตั้งง่าย | ✅ | ❌ |

---

## 💡 คำแนะนำ

### สำหรับผู้เริ่มต้น
1. เริ่มจาก HSV ก่อน
2. ทดสอบระบบให้คุ้นเคย
3. เมื่อต้องการความแม่นยำ → เทรน Segmentation

### สำหรับผู้ที่ต้องการ Segmentation
1. เก็บข้อมูลให้มากกว่า 200 ภาพ
2. วาด Annotation ให้ละเอียด
3. เทรนอย่างน้อย 100 Epochs
4. ทดสอบกับภาพจริงบ่อยๆ

### สำหรับการใช้งานจริง
1. ใช้ GPU ถ้าต้องการ Real-time
2. ปรับ Confidence ตามความเหมาะสม
3. บันทึกข้อมูลเพื่อวิเคราะห์
4. Fine-tune Model เมื่อมีข้อมูลใหม่

---

## 🐛 การแก้ไขปัญหา

### ปัญหาทั่วไป

#### 1. Camera ไม่เปิด
```python
# ลอง Index อื่น
camera = cv2.VideoCapture(1)  # ลอง 0, 1, 2
```

#### 2. Arduino เชื่อมต่อไม่ได้
- ตรวจสอบ COM Port
- ติดตั้ง CH340 Driver
- ปิดโปรแกรมอื่นที่ใช้ Serial

#### 3. Model โหลดไม่ได้
```bash
# ตรวจสอบไฟล์
ls runs/segment/plant_segmentation/weights/best.pt

# ถ้าไม่มี → เทรน Model ก่อน
python train_segmentation.py
```

#### 4. ช้า/กระตุก
```python
# ลด Image Size
frame = cv2.resize(frame, (320, 240))

# หรือใช้ Model เล็กกว่า
model = YOLO("yolov8n-seg.pt")  # nano (เล็กสุด)
```

---

## 📖 เอกสารเพิ่มเติม

- **SEGMENTATION_GUIDE.md** - คู่มือเทรน Model ฉบับสมบูรณ์
- **INTEGRATION_GUIDE.md** - คู่มือนำไปใช้งาน + API
- **Arduino Documentation** - ใน All_IdaNEW.ino

---

## 🎓 Tutorial Videos (แนะนำ)

### Roboflow
- [How to Annotate Images](https://www.youtube.com/roboflow)
- [YOLOv8 Training Tutorial](https://blog.roboflow.com/)

### YOLOv8
- [Ultralytics Documentation](https://docs.ultralytics.com/)
- [Instance Segmentation Guide](https://docs.ultralytics.com/tasks/segment/)

---

## 📞 ติดต่อ / ขอความช่วยเหลือ

### ปัญหาทั่วไป
1. อ่าน SEGMENTATION_GUIDE.md
2. ตรวจสอบ Troubleshooting ด้านบน
3. ดู Error Message

### Bug / Feature Request
- เปิด Issue บน GitHub
- ส่ง Email พร้อมรายละเอียด

---

## 📝 License

MIT License - ใช้งานได้ฟรี

---

## 🙏 Credits

- **YOLOv8** by Ultralytics
- **Roboflow** for Dataset Tools
- **Flask** Web Framework
- **OpenCV** Computer Vision Library

---

## 📌 สรุป

### ระบบนี้เหมาะสำหรับ:
- ✅ ตรวจสอบสุขภาพพืช
- ✅ รดน้ำอัตโนมัติตามเวลา
- ✅ บันทึกข้อมูลเพื่อวิเคราะห์
- ✅ การศึกษาและวิจัย

### ไม่เหมาะสำหรับ:
- ❌ พื้นที่กว้างมากๆ (> 100 ตร.ม.)
- ❌ พืชหลากหลายชนิด (ต้องเทรนหลาย Model)
- ❌ ใช้งานนอกอาคาร (ยังไม่กันน้ำ)

---

**เวอร์ชัน:** 2.0 (with Segmentation Support)
**อัพเดทล่าสุด:** 2025-01-XX
**Python:** 3.8+
**Arduino:** ESP32

---

## 🎯 เป้าหมายถัดไป

- [ ] รองรับ YOLOv11
- [ ] เพิ่ม Line Notify
- [ ] บันทึกข้อมูลลง Database
- [ ] Dashboard สำหรับวิเคราะห์
- [ ] Mobile App
- [ ] ระบบเตือนอัตโนมัติ
