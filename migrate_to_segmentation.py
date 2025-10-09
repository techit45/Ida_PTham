# สคริปต์สำหรับแปลงระบบจาก HSV เป็น Segmentation
# รันสคริปต์นี้เพื่ออัพเกรดระบบอัตโนมัติ

import os
import shutil
from datetime import datetime

print("=" * 60)
print("Migration Script: HSV → Segmentation")
print("=" * 60)

# === ขั้นตอนที่ 1: ตรวจสอบไฟล์ที่จำเป็น ===
print("\n[1/5] ตรวจสอบไฟล์...")

required_files = {
    "flask_controller.py": "ไฟล์ Flask เดิม",
    "flask_controller_segmentation.py": "ไฟล์ Flask ใหม่",
    "templates/web_interface.html": "ไฟล์ HTML"
}

all_files_exist = True
for file, desc in required_files.items():
    if os.path.exists(file):
        print("  ✓ พบ " + desc)
    else:
        print("  ✗ ไม่พบ " + desc)
        all_files_exist = False

if not all_files_exist:
    print("\n✗ ไฟล์ไม่ครบ! โปรดตรวจสอบ")
    exit()

# === ขั้นตอนที่ 2: สำรองไฟล์เดิม ===
print("\n[2/5] สำรองไฟล์เดิม...")

backup_folder = "backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
os.makedirs(backup_folder, exist_ok=True)

files_to_backup = ["flask_controller.py", "templates/web_interface.html"]

for file in files_to_backup:
    if os.path.exists(file):
        # สร้างโฟลเดอร์ย่อยถ้าจำเป็น
        dest_dir = os.path.join(backup_folder, os.path.dirname(file))
        os.makedirs(dest_dir, exist_ok=True)

        # คัดลอกไฟล์
        dest_file = os.path.join(backup_folder, file)
        shutil.copy2(file, dest_file)
        print("  ✓ สำรอง " + file + " → " + dest_file)

print("\n  ไฟล์สำรองทั้งหมดอยู่ที่: " + backup_folder)

# === ขั้นตอนที่ 3: อัพเดท Flask Controller ===
print("\n[3/5] อัพเดท Flask Controller...")

answer = input("\nคุณต้องการแทนที่ flask_controller.py หรือไม่? (y/n): ")

if answer.lower() == 'y':
    shutil.copy2("flask_controller_segmentation.py", "flask_controller.py")
    print("  ✓ แทนที่ flask_controller.py สำเร็จ")
else:
    print("  ⊘ ข้ามการแทนที่ flask_controller.py")

# === ขั้นตอนที่ 4: อัพเดทหน้าเว็บ ===
print("\n[4/5] อัพเดทหน้าเว็บ...")

html_file = "templates/web_interface.html"

# อ่านไฟล์ HTML
with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

# ตรวจสอบว่ามีส่วน Detection Mode หรือยัง
if "detection-mode" in html_content:
    print("  ✓ หน้าเว็บมีส่วน Detection Mode อยู่แล้ว")
else:
    print("  ! หน้าเว็บยังไม่มีส่วน Detection Mode")
    print("  โปรดเพิ่มโค้ดด้านล่างในหน้าเว็บ:")
    print("\n  " + "-" * 50)
    print("""
  <!-- เพิ่มใน Camera & Color Detection card -->
  <hr />
  <h4>Detection Mode</h4>
  <p>โหมดปัจจุบัน: <span id="detection-mode" class="data-display">HSV</span></p>
  <button class="button button-success" onclick="toggleDetectionMode()">
    สลับโหมด
  </button>
    """)
    print("  " + "-" * 50)
    print("\n  และเพิ่ม JavaScript:")
    print("  " + "-" * 50)
    print("""
  function toggleDetectionMode() {
    fetch("/toggle_detection_mode")
      .then(response => response.json())
      .then(data => {
        if (data.status === "success") {
          document.getElementById("detection-mode").innerText = data.mode;
          alert("สลับเป็นโหมด " + data.mode);
        } else {
          alert("ไม่สามารถสลับโหมดได้");
        }
      });
  }
    """)
    print("  " + "-" * 50)

# === ขั้นตอนที่ 5: ตรวจสอบ Segmentation Model ===
print("\n[5/5] ตรวจสอบ Segmentation Model...")

model_paths = [
    "runs/segment/plant_segmentation/weights/best.pt",
    "runs/segment/train/weights/best.pt",
    "best.pt",
    "model.pt"
]

model_found = False
model_path = None

for path in model_paths:
    if os.path.exists(path):
        model_found = True
        model_path = path
        print("  ✓ พบ Model: " + path)
        break

if not model_found:
    print("  ✗ ไม่พบ Segmentation Model")
    print("\n  โปรดเทรน Model ก่อนโดยรัน:")
    print("    python train_segmentation.py")
    print("\n  หรือดาวน์โหลด Pre-trained Model มาวางไว้")
else:
    print("\n  Model พร้อมใช้งาน!")

# === สรุป ===
print("\n" + "=" * 60)
print("สรุปผลการ Migration")
print("=" * 60)

print("\n✓ สิ่งที่ทำสำเร็จ:")
print("  - สำรองไฟล์เดิมที่: " + backup_folder)

if answer.lower() == 'y':
    print("  - อัพเดท flask_controller.py")
else:
    print("  - (ยังไม่ได้แทนที่ flask_controller.py)")

if model_found:
    print("  - พบ Segmentation Model: " + model_path)

print("\n! สิ่งที่ต้องทำต่อ:")

if not model_found:
    print("  1. เทรน Segmentation Model:")
    print("     python train_segmentation.py")

if "detection-mode" not in html_content:
    print("  2. เพิ่มปุ่มสลับโหมดในหน้าเว็บ (ดูด้านบน)")

print("  3. ทดสอบระบบ:")
print("     python flask_controller.py")

print("  4. ทดสอบ Segmentation:")
print("     python simple_segmentation_demo.py")

print("\n" + "=" * 60)
print("การ Migration เสร็จสมบูรณ์!")
print("=" * 60)

# === บันทึก Log ===
log_file = os.path.join(backup_folder, "migration_log.txt")
with open(log_file, 'w', encoding='utf-8') as f:
    f.write("Migration Log\n")
    f.write("=" * 60 + "\n")
    f.write("Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n")
    f.write("Backup Folder: " + backup_folder + "\n")
    f.write("\nFiles Backed Up:\n")
    for file in files_to_backup:
        f.write("  - " + file + "\n")
    f.write("\nModel Found: " + str(model_found) + "\n")
    if model_found:
        f.write("Model Path: " + model_path + "\n")

print("\nLog บันทึกที่: " + log_file)
