# 🚀 เริ่มต้นที่นี่!

## 👋 ยินดีต้อนรับสู่ระบบตรวจสอบพืชและรดน้ำอัตโนมัติ

---

## 📁 โครงสร้างโปรเจค

```
Ida_PTham/
├── 📂 1_HSV_Version/           ← เริ่มที่นี่ (ผู้เริ่มต้น)
├── 📂 2_Segmentation_Version/  ← ขั้นสูง (ความแม่นยำสูง)
├── 📂 3_Arduino/                ← Arduino Code
└── 📂 4_Documentation/          ← คู่มือทั้งหมด
```

---

## ⚡ Quick Start (เลือก 1 เส้นทาง)

### 🟢 เส้นทาง 1: ผู้เริ่มต้น (แนะนำ)

**ระยะเวลา:** 5 นาที

```bash
# 1. ไปที่โฟลเดอร์ HSV
cd 1_HSV_Version

# 2. ติดตั้ง
pip install -r requirements.txt

# 3. รัน
python flask_controller.py

# 4. เปิดเว็บ
http://localhost:5001
```

**คุณสมบัติ:**
- ✅ ตรวจจับสีด้วย HSV
- ✅ ความแม่นยำ 60-70%
- ✅ ติดตั้งง่าย ไม่ต้อง GPU

**อ่านเพิ่ม:** `1_HSV_Version/README.md`

---

### 🔵 เส้นทาง 2: ขั้นสูง (Segmentation)

**ระยะเวลา:** 2-4 ชั่วโมง

```bash
# 1. ไปที่โฟลเดอร์ Segmentation
cd 2_Segmentation_Version

# 2. ติดตั้ง
pip install -r requirements.txt

# 3. เทรน Model (ต้องมี Dataset จาก Roboflow)
python train_segmentation.py

# 4. รัน
python flask_controller.py
```

**คุณสมบัติ:**
- ✅ ตรวจจับด้วย YOLOv8 Segmentation
- ✅ ความแม่นยำ 90-95%
- ✅ แยกแต่ละใบได้
- ⚠️ ต้องเทรน Model + แนะนำใช้ GPU

**อ่านเพิ่ม:** `2_Segmentation_Version/README.md`

---

## 📊 เปรียบเทียบเวอร์ชัน

| | HSV (เริ่มต้น) | Segmentation (ขั้นสูง) |
|---|---|---|
| ความแม่นยำ | 60-70% | 90-95% |
| ติดตั้ง | 5 นาที | 2-4 ชั่วโมง |
| GPU | ไม่ต้อง | แนะนำ |
| เหมาะสำหรับ | ทดสอบ/เรียนรู้ | ใช้งานจริง |

---

## 📖 คู่มือการใช้งาน

### สำหรับผู้เริ่มต้น
1. `1_HSV_Version/README.md` - เริ่มต้นใช้งาน
2. `3_Arduino/README.md` - อัปโหลด Arduino Code
3. `4_Documentation/SYSTEM_GUIDE.md` - คู่มือระบบ

### สำหรับ Segmentation
1. `2_Segmentation_Version/README.md` - Quick Start
2. `4_Documentation/SEGMENTATION_GUIDE.md` - เทรน Model
3. `4_Documentation/INTEGRATION_GUIDE.md` - API

### อ่านภาพรวม
- `PROJECT_STRUCTURE.md` - โครงสร้างโปรเจค
- `4_Documentation/README_SEGMENTATION.md` - คู่มือรวม

---

## 🎯 คำแนะนำ

### สำหรับนักเรียน/นักศึกษา
→ ใช้ **HSV Version** (โฟลเดอร์ `1_HSV_Version/`)

### สำหรับงานวิจัย/วิทยานิพนธ์
→ ใช้ **Segmentation Version** (โฟลเดอร์ `2_Segmentation_Version/`)

### สำหรับใช้งานจริง
→ เริ่มจาก **HSV** → อัพเกรดเป็น **Segmentation**

---

## 🔧 Hardware ที่ต้องใช้

### พื้นฐาน
- ESP32 DevKit V1
- L298N Motor Driver (2 ชิ้น)
- มอเตอร์ DC 12V (2 ตัว)
- Rotary Encoder (2 ชิ้น)
- Relay 1 Channel
- ปั๊มน้ำ 12V
- Webcam USB

### ดูรายละเอียด
`3_Arduino/README.md` → Pin Connections

---

## ❓ FAQ

### Q: เริ่มต้นยังไง?
**A:** ไปที่ `1_HSV_Version/` และอ่าน README.md

### Q: ต้องการความแม่นยำสูง?
**A:** ไปที่ `2_Segmentation_Version/` และเทรน Model

### Q: ไม่มี GPU ใช้ Segmentation ได้ไหม?
**A:** ได้ แต่จะช้า (ใช้ CPU แทน)

### Q: ต้องมี Dataset เท่าไหร่?
**A:** อย่างน้อย 100-500 ภาพ

### Q: ติดปัญหาอ่านที่ไหน?
**A:** ทุก README มี Troubleshooting Section

---

## 🎉 เริ่มต้นเลย!

```bash
# เริ่มแบบง่าย (5 นาที)
cd 1_HSV_Version
pip install -r requirements.txt
python flask_controller.py

# เปิดเว็บ
http://localhost:5001
```

---

**Happy Coding! 🌱**

ดูคู่มือเพิ่มเติม: `PROJECT_STRUCTURE.md`
