# โค้ดสำหรับเทรน YOLOv11 Segmentation Model
# ใช้ Dataset ที่โหลดมาแล้ว (ไม่ต้องใช้ Roboflow API)

# ขั้นตอนที่ 1: ติดตั้ง Library ที่จำเป็น
# เปิด Terminal แล้วพิมพ์:
# pip install ultralytics

from ultralytics import YOLO
import os

print("=" * 60)
print("YOLOv11 Segmentation Training (Local Dataset)")
print("=" * 60)

# ===== ตั้งค่าพื้นฐาน =====
# ระบุตำแหน่งไฟล์ data.yaml ของ Dataset ที่โหลดมาแล้ว
DATASET_PATH = "dataset/data.yaml"  # เปลี่ยนเป็นตำแหน่งจริงของ data.yaml

# การตั้งค่าการเทรน
EPOCHS = 100                    # จำนวนรอบการเทรน (แนะนำ 100-300)
IMAGE_SIZE = 640               # ขนาดภาพ (640 เป็นค่ามาตรฐาน)
BATCH_SIZE = 16                # จำนวนภาพต่อรอบ (ลดถ้า RAM ไม่พอ)
MODEL_SIZE = "yolo11n-seg.pt"  # ขนาด Model: n, s, m, l, x
PATIENCE = 50                  # หยุดถ้าไม่ดีขึ้นใน 50 รอบ

# ===== ขั้นตอนที่ 1: ตรวจสอบ Dataset =====
print("\n" + "=" * 60)
print("ขั้นตอนที่ 1: ตรวจสอบ Dataset")
print("=" * 60)

# ตรวจสอบว่ามีไฟล์ data.yaml หรือไม่
if not os.path.exists(DATASET_PATH):
    print("✗ ไม่พบไฟล์: " + DATASET_PATH)
    print("\nวิธีแก้ไข:")
    print("1. ดาวน์โหลด Dataset จาก Roboflow (Export เป็น YOLOv8)")
    print("2. แตกไฟล์ลงในโฟลเดอร์ 'dataset'")
    print("3. ตรวจสอบว่ามีไฟล์ data.yaml")
    print("\nหรือแก้ไขค่า DATASET_PATH ในโค้ดนี้")
    exit()

print("✓ พบไฟล์ data.yaml: " + DATASET_PATH)

# อ่านข้อมูลจาก data.yaml
try:
    import yaml
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset_info = yaml.safe_load(f)

    print("\nข้อมูล Dataset:")
    print("  - Train: " + str(dataset_info.get('train', 'N/A')))
    print("  - Val: " + str(dataset_info.get('val', 'N/A')))
    print("  - Test: " + str(dataset_info.get('test', 'N/A')))
    print("  - Classes: " + str(dataset_info.get('nc', 0)) + " classes")
    print("  - Names: " + str(dataset_info.get('names', [])))

except Exception as e:
    print("⚠ ไม่สามารถอ่านข้อมูล yaml: " + str(e))
    print("  แต่ยังสามารถเทรนได้")

# ตรวจสอบโฟลเดอร์ train, val, test
dataset_dir = os.path.dirname(DATASET_PATH)

train_dir = os.path.join(dataset_dir, "train", "images")
val_dir = os.path.join(dataset_dir, "valid", "images")
test_dir = os.path.join(dataset_dir, "test", "images")

print("\nตรวจสอบโฟลเดอร์:")
if os.path.exists(train_dir):
    train_count = len([f for f in os.listdir(train_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
    print("  ✓ Train: " + str(train_count) + " ภาพ")
else:
    print("  ✗ ไม่พบโฟลเดอร์ train/images")

if os.path.exists(val_dir):
    val_count = len([f for f in os.listdir(val_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
    print("  ✓ Valid: " + str(val_count) + " ภาพ")
else:
    print("  ✗ ไม่พบโฟลเดอร์ valid/images")

if os.path.exists(test_dir):
    test_count = len([f for f in os.listdir(test_dir) if f.endswith(('.jpg', '.png', '.jpeg'))])
    print("  ✓ Test: " + str(test_count) + " ภาพ")
else:
    print("  ! ไม่พบโฟลเดอร์ test/images (ไม่จำเป็น)")

# ===== ขั้นตอนที่ 2: โหลด Model =====
print("\n" + "=" * 60)
print("ขั้นตอนที่ 2: โหลด Model YOLOv11")
print("=" * 60)

try:
    model = YOLO(MODEL_SIZE)
    print("✓ โหลด Model สำเร็จ: " + MODEL_SIZE)
except Exception as e:
    print("✗ ไม่สามารถโหลด Model: " + str(e))
    print("\nวิธีแก้ไข:")
    print("  pip install ultralytics")
    exit()

# ตรวจสอบว่ามี GPU หรือไม่
import torch
if torch.cuda.is_available():
    device = "0"
    print("\n✓ พบ GPU: " + torch.cuda.get_device_name(0))
else:
    device = "cpu"
    print("\n! ไม่พบ GPU - ใช้ CPU (จะช้ากว่า)")

# ===== ขั้นตอนที่ 3: เทรน Model =====
print("\n" + "=" * 60)
print("ขั้นตอนที่ 3: เริ่มเทรน Model")
print("=" * 60)
print("ตำแหน่ง Dataset: " + DATASET_PATH)
print("จำนวนรอบ: " + str(EPOCHS))
print("ขนาดภาพ: " + str(IMAGE_SIZE))
print("Batch Size: " + str(BATCH_SIZE))
print("Patience: " + str(PATIENCE))
print("Device: " + device)
print("\nกำลังเทรน... (อาจใช้เวลา 30 นาที - 2 ชั่วโมง)")
print("=" * 60)

try:
    # เทรน Model
    results = model.train(
        data=DATASET_PATH,              # ไฟล์ data.yaml
        epochs=EPOCHS,                  # จำนวนรอบ
        imgsz=IMAGE_SIZE,              # ขนาดภาพ
        batch=BATCH_SIZE,              # Batch size
        name="plant_segmentation",     # ชื่อการเทรนนี้
        patience=PATIENCE,             # หยุดถ้าไม่ดีขึ้น
        save=True,                     # บันทึก Model
        device=device,                 # ใช้ GPU หรือ CPU
        project="runs/segment",        # โฟลเดอร์เก็บผลลัพธ์
        exist_ok=True                  # อนุญาตให้ทับโฟลเดอร์เดิม
    )

    print("\n" + "=" * 60)
    print("✓ เทรน Model เสร็จแล้ว!")
    print("=" * 60)

except Exception as e:
    print("\n✗ เกิดข้อผิดพลาดระหว่างเทรน: " + str(e))
    exit()

# ===== ขั้นตอนที่ 4: ทดสอบ Model =====
print("\n" + "=" * 60)
print("ขั้นตอนที่ 4: ทดสอบ Model")
print("=" * 60)

# หาตำแหน่ง Model ที่เทรนเสร็จ
best_model_path = "runs/segment/plant_segmentation/weights/best.pt"
last_model_path = "runs/segment/plant_segmentation/weights/last.pt"

if os.path.exists(best_model_path):
    print("✓ พบ Model: " + best_model_path)

    # โหลด Model ที่เทรนเสร็จ
    trained_model = YOLO(best_model_path)

    # ทดสอบกับ Dataset
    print("\nกำลังทดสอบ Model...")
    try:
        val_results = trained_model.val(data=DATASET_PATH)

        print("\n" + "-" * 60)
        print("ผลการทดสอบ:")
        print("-" * 60)

        # แสดงผล metrics
        if hasattr(val_results, 'box'):
            print("Box Metrics:")
            print("  - mAP50: " + str(round(val_results.box.map50, 4)))
            print("  - mAP50-95: " + str(round(val_results.box.map, 4)))

        if hasattr(val_results, 'seg'):
            print("\nSegmentation Metrics:")
            print("  - mAP50: " + str(round(val_results.seg.map50, 4)))
            print("  - mAP50-95: " + str(round(val_results.seg.map, 4)))

    except Exception as e:
        print("⚠ ไม่สามารถทดสอบ Model: " + str(e))

else:
    print("✗ ไม่พบ Model ที่เทรนเสร็จ")

# ===== ขั้นตอนที่ 5: ทดลองใช้ Model =====
print("\n" + "=" * 60)
print("ขั้นตอนที่ 5: ทดลองใช้ Model กับภาพทดสอบ")
print("=" * 60)

if os.path.exists(best_model_path) and os.path.exists(test_dir):
    print("กำลังทำนายผลกับภาพทดสอบ...")

    try:
        # ทำนายผลกับภาพทดสอบทั้งหมด
        predict_results = trained_model.predict(
            source=test_dir,
            save=True,                    # บันทึกภาพผลลัพธ์
            conf=0.25,                    # ความมั่นใจขั้นต่ำ 25%
            project="runs/segment",       # โฟลเดอร์
            name="plant_predictions",     # ชื่อโฟลเดอร์ผลลัพธ์
            exist_ok=True
        )

        print("✓ ทำนายผลสำเร็จ!")
        print("  ภาพผลลัพธ์: runs/segment/plant_predictions")

    except Exception as e:
        print("⚠ ไม่สามารถทำนายผล: " + str(e))

elif not os.path.exists(test_dir):
    print("! ไม่พบโฟลเดอร์ภาพทดสอบ: " + test_dir)

# ===== สรุปผล =====
print("\n" + "=" * 60)
print("สรุปผล")
print("=" * 60)

if os.path.exists(best_model_path):
    print("✓ Model ที่เทรนเสร็จ:")
    print("  - Best: " + best_model_path)
    print("  - Last: " + last_model_path)

    print("\n✓ ไฟล์ผลลัพธ์:")
    print("  - ผลการเทรน: runs/segment/plant_segmentation/")
    print("  - ภาพทำนาย: runs/segment/plant_predictions/")
    print("  - กราฟ: runs/segment/plant_segmentation/results.png")
    print("  - Confusion Matrix: runs/segment/plant_segmentation/confusion_matrix.png")

    print("\n✓ วิธีใช้ Model:")
    print("  1. from ultralytics import YOLO")
    print("  2. model = YOLO('" + best_model_path + "')")
    print("  3. results = model.predict('path/to/image.jpg')")

    print("\n✓ ทดสอบด้วยโค้ดตัวอย่าง:")
    print("  python test_model.py")
    print("  python simple_segmentation_demo.py")

else:
    print("✗ การเทรนไม่สำเร็จ")
    print("  โปรดตรวจสอบ Error Message ด้านบน")

print("\n" + "=" * 60)
print("เสร็จสิ้น!")
print("=" * 60)
