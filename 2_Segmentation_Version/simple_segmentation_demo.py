# ตัวอย่างการใช้ Segmentation Model แบบง่ายๆ
# สำหรับทดสอบกับกล้อง Webcam

from ultralytics import YOLO
import cv2

# === ตั้งค่า ===
MODEL_PATH = "runs/segment/plant_segmentation/weights/best.pt"  # ตำแหน่ง Model
CONFIDENCE = 0.5  # ความมั่นใจขั้นต่ำ (0.0-1.0)

print("=" * 50)
print("Segmentation Model Demo")
print("=" * 50)

# === โหลด Model ===
try:
    print("\nกำลังโหลด Model: " + MODEL_PATH)
    model = YOLO(MODEL_PATH)
    print("✓ โหลด Model สำเร็จ!")
    print("\nClass ทั้งหมด:")
    for class_id, class_name in model.names.items():
        print("  - " + class_name)
except Exception as e:
    print("✗ ไม่สามารถโหลด Model: " + str(e))
    print("\nโปรดเทรน Model ก่อนโดยรัน:")
    print("  python train_segmentation.py")
    exit()

# === เปิด Webcam ===
print("\n" + "=" * 50)
print("กำลังเปิด Webcam...")
print("=" * 50)

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("✗ ไม่สามารถเปิด Webcam ได้")
    exit()

print("✓ เปิด Webcam สำเร็จ!")
print("\nคำสั่ง:")
print("  - กด 'q' เพื่อออก")
print("  - กด 's' เพื่อบันทึกภาพ")
print("  - กด 'i' เพื่อแสดง/ซ่อนข้อมูล")

# ตัวแปรเก็บสถานะ
show_info = True
saved_count = 0

# === Loop หลัก ===
while True:
    ret, frame = cap.read()

    if not ret:
        print("ไม่สามารถอ่านภาพจากกล้อง")
        break

    # ทำนายผล
    results = model.predict(frame, conf=CONFIDENCE, verbose=False)

    # วาดผลลัพธ์
    annotated = results[0].plot()

    # นับจำนวนแต่ละ Class
    class_counts = {}
    total_objects = len(results[0].boxes)

    for box in results[0].boxes:
        class_id = int(box.cls[0])
        class_name = model.names[class_id]
        confidence = float(box.conf[0])

        # นับ
        if class_name in class_counts:
            class_counts[class_name] = class_counts[class_name] + 1
        else:
            class_counts[class_name] = 1

    # แสดงข้อมูลบนภาพ (ถ้าเปิดใช้งาน)
    if show_info:
        y = 30

        # แสดงจำนวนวัตถุทั้งหมด
        text = "Total: " + str(total_objects) + " objects"
        cv2.putText(annotated, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y = y + 35

        # แสดงจำนวนแต่ละ Class
        for class_name, count in class_counts.items():
            text = class_name + ": " + str(count)
            cv2.putText(annotated, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y = y + 30

        # วิเคราะห์สุขภาพพืช (ถ้ามี)
        yellow_count = class_counts.get("yellow_leaf", 0)
        green_count = class_counts.get("green_leaf", 0)
        purple_count = class_counts.get("purple_leaf", 0)

        total_leaves = yellow_count + green_count + purple_count

        if total_leaves > 0:
            y = y + 10

            # คำนวณเปอร์เซ็นต์
            green_percent = (green_count * 100.0) / total_leaves

            # แสดงสถานะ
            if green_percent >= 80:
                status = "Status: Healthy"
                color = (0, 255, 0)  # เขียว
            elif yellow_count > purple_count:
                status = "Status: N-Deficiency"
                color = (0, 255, 255)  # เหลือง
            elif purple_count > yellow_count:
                status = "Status: P-Deficiency"
                color = (255, 0, 255)  # ม่วง
            else:
                status = "Status: Multiple Issues"
                color = (0, 165, 255)  # ส้ม

            cv2.putText(annotated, status, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    # แสดงคำสั่งด้านล่าง
    h = annotated.shape[0]
    cv2.putText(annotated, "Q:Quit | S:Save | I:Info", (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # แสดงผล
    cv2.imshow("Plant Segmentation Demo", annotated)

    # รอการกดปุ่ม
    key = cv2.waitKey(1)

    if key == ord('q'):
        # ออกจากโปรแกรม
        print("\nออกจากโปรแกรม...")
        break

    elif key == ord('s'):
        # บันทึกภาพ
        saved_count = saved_count + 1
        filename = "captured_" + str(saved_count) + ".jpg"
        cv2.imwrite(filename, annotated)
        print("บันทึกภาพ: " + filename)

    elif key == ord('i'):
        # สลับการแสดงข้อมูล
        show_info = not show_info
        if show_info:
            print("เปิดการแสดงข้อมูล")
        else:
            print("ปิดการแสดงข้อมูล")

# === ปิดโปรแกรม ===
cap.release()
cv2.destroyAllWindows()

print("\nสรุป:")
print("  - บันทึกภาพ: " + str(saved_count) + " ภาพ")
print("\nเสร็จสิ้น!")
