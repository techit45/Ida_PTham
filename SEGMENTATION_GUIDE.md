# คู่มือการเทรน Model Segmentation สำหรับตรวจจับใบพืช

## ข้อมูลพื้นฐาน

### Instance Segmentation คืออะไร?
- เป็นการระบุตำแหน่งวัตถุแบบละเอียดถึงระดับพิกเซล
- แตกต่างจาก Object Detection ที่ใช้กรอบสี่เหลี่ยม
- Segmentation จะวาดรูปร่างวัตถุจริงๆ

### YOLOv8 Segmentation
- Model ล่าสุดจาก Ultralytics
- รวดเร็วและแม่นยำ
- รองรับ Instance Segmentation

---

## การเตรียม Dataset บน Roboflow

### ขั้นตอนที่ 1: สร้างโปรเจค
1. ไปที่ https://roboflow.com
2. สมัครสมาชิก (ฟรี)
3. คลิก "Create New Project"
4. เลือก **Instance Segmentation**
5. ตั้งชื่อ Project เช่น "Plant-Disease-Detection"

### ขั้นตอนที่ 2: อัปโหลดภาพ
1. คลิก "Upload"
2. เลือกภาพใบพืชของคุณ (แนะนำอย่างน้อย 100-500 ภาพ)
3. รอให้อัปโหลดเสร็จ

### ขั้นตอนที่ 3: วาด Annotation
1. คลิกที่ภาพแต่ละภาพ
2. เลือกเครื่องมือ "Smart Polygon" หรือ "Polygon"
3. วาดรอบใบพืชที่ต้องการตรวจจับ
4. ใส่ชื่อ Class เช่น:
   - "yellow_leaf" (ใบเหลือง - ขาดไนโตรเจน)
   - "green_leaf" (ใบเขียว - ปกติ)
   - "purple_leaf" (ใบม่วง - ขาดฟอสฟอรัส)

### ขั้นตอนที่ 4: สร้าง Dataset Version
1. คลิก "Generate"
2. เลือก Split:
   - Train: 70%
   - Valid: 20%
   - Test: 10%
3. เพิ่ม Augmentation (ถ้าต้องการ):
   - Flip: Horizontal
   - Rotation: ±15°
   - Brightness: ±25%
4. คลิก "Generate"

### ขั้นตอนที่ 5: Export Dataset
1. คลิก "Export"
2. เลือก Format: **YOLOv8**
3. คัดลอก Code snippet (จะมี API Key อยู่)

---

## การติดตั้ง Library

### ติดตั้งทีละตัว (แนะนำ)
```bash
pip install ultralytics
pip install roboflow
```

### ติดตั้งแบบครั้งเดียว
```bash
pip install ultralytics roboflow opencv-python
```

### ตรวจสอบว่าติดตั้งสำเร็จ
```python
from ultralytics import YOLO
from roboflow import Roboflow
print("ติดตั้งสำเร็จ!")
```

---

## การแก้ไขโค้ดเทรน

### เปิดไฟล์ `train_segmentation.py`

### แก้ไขส่วนที่ 1: ข้อมูล Roboflow
```python
ROBOFLOW_API_KEY = "abcd1234efgh5678"  # ใส่ API Key ของคุณ
WORKSPACE_NAME = "my-workspace"         # ชื่อ Workspace
PROJECT_NAME = "plant-disease"          # ชื่อ Project
DATASET_VERSION = 1                     # เวอร์ชัน (ปกติเป็น 1)
```

**วิธีหา API Key:**
1. ไปที่ Roboflow
2. คลิกที่รูปโปรไฟล์มุมขวาบน
3. เลือก "Settings"
4. ไปที่แท็บ "API Keys"
5. คัดลอก API Key

### แก้ไขส่วนที่ 2: การตั้งค่าการเทรน
```python
EPOCHS = 100          # จำนวนรอบ (100-300 แนะนำ)
IMAGE_SIZE = 640     # ขนาดภาพ (640 เป็นมาตรฐาน)
BATCH_SIZE = 16      # ลดเป็น 8 หรือ 4 ถ้า RAM ไม่พอ
MODEL_SIZE = "yolov8n-seg.pt"  # เลือกขนาด Model
```

**ขนาด Model:**
- `yolov8n-seg.pt` - Nano (เล็กสุด, เร็วสุด, แม่นยำน้อย)
- `yolov8s-seg.pt` - Small (แนะนำสำหรับเริ่มต้น)
- `yolov8m-seg.pt` - Medium
- `yolov8l-seg.pt` - Large
- `yolov8x-seg.pt` - XLarge (ใหญ่สุด, ช้าสุด, แม่นยำมาก)

---

## การรันโค้ด

### วิธีที่ 1: ใช้ Terminal/Command Prompt
```bash
cd /Users/techit/Desktop/Login-Learning/Single/Ida_PTham
python train_segmentation.py
```

### วิธีที่ 2: ใช้ IDE (VS Code, PyCharm)
1. เปิดไฟล์ `train_segmentation.py`
2. กด F5 หรือคลิก "Run"

---

## ผลลัพธ์ที่ได้

### โครงสร้างโฟลเดอร์
```
runs/
└── segment/
    ├── plant_segmentation/          # ผลการเทรน
    │   ├── weights/
    │   │   ├── best.pt             # Model ที่ดีที่สุด ⭐
    │   │   └── last.pt             # Model รอบสุดท้าย
    │   ├── confusion_matrix.png    # กราฟความสับสน
    │   ├── results.png             # กราฟผลการเทรน
    │   └── val_batch0_pred.jpg     # ตัวอย่างผลทำนาย
    └── plant_predictions/           # ภาพผลลัพธ์
        └── (ภาพที่ทำนายแล้ว)
```

### ไฟล์สำคัญ
- `best.pt` - Model ที่ดีที่สุด (ใช้ไฟล์นี้)
- `results.png` - กราฟแสดงผลการเทรน
- `confusion_matrix.png` - แสดงความแม่นยำแต่ละ Class

---

## การใช้งาน Model ที่เทรนแล้ว

### ตัวอย่างโค้ดพื้นฐาน
```python
from ultralytics import YOLO

# โหลด Model
model = YOLO("runs/segment/plant_segmentation/weights/best.pt")

# ทำนายผลจากภาพ
results = model.predict("path/to/plant.jpg", save=True)

# ดูผลลัพธ์
for result in results:
    print("จำนวนวัตถุที่พบ: " + str(len(result.boxes)))
```

### ตัวอย่างโค้ดแบบละเอียด
```python
from ultralytics import YOLO
import cv2

# โหลด Model
model = YOLO("runs/segment/plant_segmentation/weights/best.pt")

# ทำนายผล
results = model.predict("plant.jpg", conf=0.5)

# ดึงข้อมูล
for result in results:
    # วาดผลลัพธ์บนภาพ
    annotated = result.plot()

    # แสดงผล
    cv2.imshow("Result", annotated)
    cv2.waitKey(0)

    # ดูรายละเอียด
    for i, box in enumerate(result.boxes):
        class_id = int(box.cls[0])
        class_name = result.names[class_id]
        confidence = float(box.conf[0])

        print("วัตถุที่ " + str(i+1) + ": " + class_name)
        print("ความมั่นใจ: " + str(confidence * 100) + "%")
```

---

## การนำไปใช้กับระบบปัจจุบัน

### เพิ่มเข้าไปใน `flask_controller.py`

```python
from ultralytics import YOLO

# โหลด Model Segmentation
segmentation_model = YOLO("runs/segment/plant_segmentation/weights/best.pt")

# ใน Camera class
def get_frame(self):
    # ... โค้ดเดิม ...

    # ใช้ Model Segmentation แทน HSV
    results = segmentation_model.predict(frame, conf=0.5)

    # วาดผลลัพธ์
    annotated = results[0].plot()

    # นับจำนวนแต่ละ Class
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = result.names[class_id]

            if class_name == "yellow_leaf":
                self.yellow_count = self.yellow_count + 1
            elif class_name == "green_leaf":
                self.green_count = self.green_count + 1
            elif class_name == "purple_leaf":
                self.purple_count = self.purple_count + 1

    return annotated
```

---

## การแก้ไขปัญหา

### ปัญหา: CUDA out of memory
**แก้ไข:** ลด `BATCH_SIZE` เป็น 8, 4 หรือ 2

### ปัญหา: ไม่พบ GPU
**แก้ไข:** เพิ่ม `device='cpu'` ในคำสั่งเทรน (ช้ากว่ามาก)

### ปัญหา: Dataset ไม่โหลด
**แก้ไข:** ตรวจสอบ API Key, Workspace, Project name

### ปัญหา: Model ไม่แม่นยำ
**แก้ไข:**
1. เพิ่ม Epochs (300-500)
2. เพิ่มจำนวนภาพใน Dataset
3. ใช้ Model ขนาดใหญ่กว่า (m, l, x)
4. เพิ่ม Augmentation ใน Roboflow

---

## เคล็ดลับ

### Dataset ที่ดี
- อย่างน้อย 100-500 ภาพ
- หลากหลายมุมมอง
- แสงสว่างต่างกัน
- พื้นหลังหลากหลาย

### การเทรนที่ดี
- ใช้ GPU (เร็วกว่า CPU หลายเท่า)
- Epochs 100-300 (มากเกินไปอาจ Overfitting)
- ติดตามกราฟ results.png

### การใช้งาน
- ตั้ง `conf=0.5` (ความมั่นใจ 50%)
- ปรับขึ้น/ลงตามความเหมาะสม
- ทดสอบกับภาพจริง

---

## ตัวอย่าง Project จริง

### ระบบตรวจจับโรคพืช
```python
# ตัวอย่างการใช้งานจริง
model = YOLO("best.pt")

# วิเคราะห์ใบพืช
results = model.predict("plant_leaf.jpg")

# ตรวจสอบสุขภาพ
healthy_count = 0
disease_count = 0

for box in results[0].boxes:
    class_name = results[0].names[int(box.cls[0])]

    if class_name == "green_leaf":
        healthy_count = healthy_count + 1
    else:
        disease_count = disease_count + 1

# สรุปผล
if disease_count > healthy_count:
    print("พืชมีอาการขาดธาตุอาหาร")
    print("ควรให้ปุ๋ย")
else:
    print("พืชมีสุขภาพดี")
```

---

## อ้างอิง

- [Roboflow Documentation](https://docs.roboflow.com/)
- [Ultralytics YOLOv8](https://docs.ultralytics.com/)
- [YOLOv8 Segmentation Tutorial](https://blog.roboflow.com/how-to-train-yolov8-instance-segmentation/)

---

**หมายเหตุ:**
- การเทรนครั้งแรกอาจใช้เวลา 30 นาที - 2 ชั่วโมง ขึ้นอยู่กับ Dataset และ GPU
- ถ้าไม่มี GPU จะใช้เวลานานกว่ามาก (อาจ 5-10 ชั่วโมง)
- แนะนำใช้ Google Colab (ฟรี GPU) ถ้าคอมพิวเตอร์ไม่มี GPU
