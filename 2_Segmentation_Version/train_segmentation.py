# โค้ดสำหรับเทรน YOLOv8 Segmentation Model
# ใช้ Dataset จาก Roboflow

# ขั้นตอนที่ 1: ติดตั้ง Library ที่จำเป็น
# เปิด Terminal แล้วพิมพ์:
# pip install ultralytics roboflow

from roboflow import Roboflow
from ultralytics import YOLO
import os

# ===== ตั้งค่าพื้นฐาน =====
# ใส่ API Key ของคุณจาก Roboflow
ROBOFLOW_API_KEY = "YOUR_API_KEY_HERE"  # เปลี่ยนเป็น API Key ของคุณ
WORKSPACE_NAME = "YOUR_WORKSPACE"       # ชื่อ Workspace ของคุณ
PROJECT_NAME = "YOUR_PROJECT"           # ชื่อ Project ของคุณ
DATASET_VERSION = 1                     # เวอร์ชันของ Dataset

# การตั้งค่าการเทรน
EPOCHS = 100                # จำนวนรอบการเทรน (ยิ่งมากยิ่งดี แต่ใช้เวลานาน)
IMAGE_SIZE = 640           # ขนาดภาพ (640 เป็นค่ามาตรฐาน)
BATCH_SIZE = 16            # จำนวนภาพต่อรอบ (ลดลงถ้า RAM ไม่พอ)
MODEL_SIZE = "yolov8n-seg.pt"  # ขนาด Model: n=nano, s=small, m=medium, l=large, x=xlarge

# ===== ขั้นตอนที่ 1: ดาวน์โหลด Dataset จาก Roboflow =====
print("=" * 50)
print("ขั้นตอนที่ 1: ดาวน์โหลด Dataset จาก Roboflow")
print("=" * 50)

try:
    # เชื่อมต่อกับ Roboflow
    rf = Roboflow(api_key=ROBOFLOW_API_KEY)

    # เลือก Project
    project = rf.workspace(WORKSPACE_NAME).project(PROJECT_NAME)

    # ดาวน์โหลด Dataset
    dataset = project.version(DATASET_VERSION).download("yolov8")

    print("ดาวน์โหลด Dataset สำเร็จ!")
    print("ตำแหน่ง Dataset: " + dataset.location)

except Exception as e:
    print("เกิดข้อผิดพลาด: " + str(e))
    print("\nโปรดตรวจสอบ:")
    print("1. API Key ถูกต้องหรือไม่")
    print("2. ชื่อ Workspace และ Project ถูกต้องหรือไม่")
    print("3. เวอร์ชัน Dataset มีอยู่จริงหรือไม่")
    exit()

# ===== ขั้นตอนที่ 2: โหลด Model =====
print("\n" + "=" * 50)
print("ขั้นตอนที่ 2: โหลด Model YOLOv8")
print("=" * 50)

model = YOLO(MODEL_SIZE)
print("โหลด Model สำเร็จ: " + MODEL_SIZE)

# ===== ขั้นตอนที่ 3: เทรน Model =====
print("\n" + "=" * 50)
print("ขั้นตอนที่ 3: เริ่มเทรน Model")
print("=" * 50)
print("จำนวนรอบ: " + str(EPOCHS))
print("ขนาดภาพ: " + str(IMAGE_SIZE))
print("Batch Size: " + str(BATCH_SIZE))
print("\nกำลังเทรน... (อาจใช้เวลานาน)")

# สร้างโฟลเดอร์สำหรับเก็บผลลัพธ์
output_folder = "runs/segment/train"

# เทรน Model
results = model.train(
    data=dataset.location + "/data.yaml",  # ไฟล์ข้อมูล Dataset
    epochs=EPOCHS,                         # จำนวนรอบ
    imgsz=IMAGE_SIZE,                      # ขนาดภาพ
    batch=BATCH_SIZE,                      # Batch size
    name="plant_segmentation",             # ชื่อการเทรนนี้
    patience=50,                           # หยุดถ้าไม่ดีขึ้นใน 50 รอบ
    save=True,                             # บันทึก Model
    device=0                               # ใช้ GPU (ถ้าไม่มีจะใช้ CPU อัตโนมัติ)
)

print("\nเทรน Model เสร็จแล้ว!")

# ===== ขั้นตอนที่ 4: ทดสอบ Model =====
print("\n" + "=" * 50)
print("ขั้นตอนที่ 4: ทดสอบ Model")
print("=" * 50)

# หาตำแหน่ง Model ที่เทรนเสร็จ
best_model_path = "runs/segment/plant_segmentation/weights/best.pt"

# โหลด Model ที่เทรนเสร็จ
trained_model = YOLO(best_model_path)

# ทดสอบกับ Dataset
val_results = trained_model.val(data=dataset.location + "/data.yaml")

print("\nผลการทดสอบ:")
print("mAP50: " + str(val_results.box.map50))
print("mAP50-95: " + str(val_results.box.map))

# ===== ขั้นตอนที่ 5: ทดลองใช้ Model =====
print("\n" + "=" * 50)
print("ขั้นตอนที่ 5: ทดลองใช้ Model กับภาพทดสอบ")
print("=" * 50)

# หาภาพทดสอบ
test_images_folder = dataset.location + "/test/images"

# ตรวจสอบว่ามีภาพทดสอบหรือไม่
if os.path.exists(test_images_folder):
    # ทำนายผลกับภาพทดสอบทั้งหมด
    predict_results = trained_model.predict(
        source=test_images_folder,
        save=True,                    # บันทึกภาพผลลัพธ์
        conf=0.25,                    # ความมั่นใจขั้นต่ำ 25%
        name="plant_predictions"      # ชื่อโฟลเดอร์ผลลัพธ์
    )

    print("ทำนายผลสำเร็จ!")
    print("ภาพผลลัพธ์บันทึกที่: runs/segment/plant_predictions")
else:
    print("ไม่พบโฟลเดอร์ภาพทดสอบ")

# ===== สรุปผล =====
print("\n" + "=" * 50)
print("สรุปผล")
print("=" * 50)
print("Model ที่เทรนเสร็จ: " + best_model_path)
print("ภาพผลลัพธ์: runs/segment/plant_predictions")
print("\nวิธีใช้ Model:")
print("1. from ultralytics import YOLO")
print("2. model = YOLO('" + best_model_path + "')")
print("3. results = model.predict('path/to/image.jpg')")
print("\nเสร็จสิ้น!")
