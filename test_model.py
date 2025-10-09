# โค้ดสำหรับทดลองใช้ Model Segmentation ที่เทรนเสร็จแล้ว

from ultralytics import YOLO
import cv2
import os

# ===== ตั้งค่า =====
MODEL_PATH = "runs/segment/plant_segmentation/weights/best.pt"  # ตำแหน่ง Model
TEST_IMAGE = "test_image.jpg"  # ภาพที่ต้องการทดสอบ
CONFIDENCE = 0.5  # ความมั่นใจขั้นต่ำ (0.0-1.0)

# ===== ตรวจสอบว่ามี Model หรือไม่ =====
if not os.path.exists(MODEL_PATH):
    print("ไม่พบ Model ที่: " + MODEL_PATH)
    print("โปรดเทรน Model ก่อน โดยรัน train_segmentation.py")
    exit()

# ===== โหลด Model =====
print("=" * 50)
print("กำลังโหลด Model...")
print("=" * 50)

model = YOLO(MODEL_PATH)
print("โหลด Model สำเร็จ!")

# ===== แสดงข้อมูล Model =====
print("\nข้อมูล Model:")
print("Class ทั้งหมด: " + str(model.names))

# ===== ตรวจสอบว่ามีภาพทดสอบหรือไม่ =====
if not os.path.exists(TEST_IMAGE):
    print("\nไม่พบภาพทดสอบ: " + TEST_IMAGE)
    print("โปรดใส่ภาพที่ต้องการทดสอบในโฟลเดอร์เดียวกัน")

    # ใช้ภาพจาก webcam แทน
    print("\nกำลังเปิด Webcam...")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ไม่สามารถเปิด Webcam ได้")
        exit()

    print("กดปุ่ม 'q' เพื่อออก")

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        # ทำนายผล
        results = model.predict(frame, conf=CONFIDENCE, verbose=False)

        # วาดผลลัพธ์
        annotated = results[0].plot()

        # นับจำนวนแต่ละ Class
        class_counts = {}
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]

            if class_name in class_counts:
                class_counts[class_name] = class_counts[class_name] + 1
            else:
                class_counts[class_name] = 1

        # แสดงจำนวนบนภาพ
        y = 30
        for class_name, count in class_counts.items():
            text = class_name + ": " + str(count)
            cv2.putText(annotated, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            y = y + 30

        # แสดงผล
        cv2.imshow("Plant Detection (Press 'q' to quit)", annotated)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

else:
    # ===== ทำนายผลจากภาพ =====
    print("\n" + "=" * 50)
    print("กำลังทำนายผล...")
    print("=" * 50)

    # อ่านภาพ
    image = cv2.imread(TEST_IMAGE)

    # ทำนายผล
    results = model.predict(TEST_IMAGE, conf=CONFIDENCE, save=True)

    # ===== แสดงผลลัพธ์ =====
    print("\nผลการทำนาย:")
    print("-" * 50)

    # นับจำนวนวัตถุที่พบ
    total_objects = len(results[0].boxes)
    print("จำนวนวัตถุที่พบ: " + str(total_objects))

    if total_objects == 0:
        print("ไม่พบวัตถุใดๆ ในภาพ")
        print("ลองลด CONFIDENCE หรือตรวจสอบว่าภาพถูกต้อง")
    else:
        # นับจำนวนแต่ละ Class
        class_counts = {}

        print("\nรายละเอียด:")
        for i, box in enumerate(results[0].boxes):
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            confidence = float(box.conf[0])

            # นับ
            if class_name in class_counts:
                class_counts[class_name] = class_counts[class_name] + 1
            else:
                class_counts[class_name] = 1

            # แสดงผล
            print("วัตถุที่ " + str(i+1) + ":")
            print("  - ชนิด: " + class_name)
            print("  - ความมั่นใจ: " + str(round(confidence * 100, 2)) + "%")

        # สรุป
        print("\n" + "-" * 50)
        print("สรุปผล:")
        for class_name, count in class_counts.items():
            print(class_name + ": " + str(count) + " ชิ้น")

        # วิเคราะห์สุขภาพพืช
        print("\n" + "=" * 50)
        print("การวิเคราะห์สุขภาพพืช:")
        print("=" * 50)

        yellow_count = class_counts.get("yellow_leaf", 0)
        green_count = class_counts.get("green_leaf", 0)
        purple_count = class_counts.get("purple_leaf", 0)

        total = yellow_count + green_count + purple_count

        if total == 0:
            print("ไม่พบใบพืช")
        else:
            # คำนวณเปอร์เซ็นต์
            green_percent = (green_count * 100.0) / total
            yellow_percent = (yellow_count * 100.0) / total
            purple_percent = (purple_count * 100.0) / total

            print("ใบเขียว (ปกติ): " + str(green_count) + " ชิ้น (" + str(round(green_percent, 1)) + "%)")
            print("ใบเหลือง (ขาดไนโตรเจน): " + str(yellow_count) + " ชิ้น (" + str(round(yellow_percent, 1)) + "%)")
            print("ใบม่วง (ขาดฟอสฟอรัส): " + str(purple_count) + " ชิ้น (" + str(round(purple_percent, 1)) + "%)")

            print("\nคำแนะนำ:")
            if green_percent >= 80:
                print("✓ พืชมีสุขภาพดี")
            elif yellow_percent > 30:
                print("✗ พืชขาดไนโตรเจน - ควรใส่ปุ๋ยยูเรีย")
            elif purple_percent > 30:
                print("✗ พืชขาดฟอสฟอรัส - ควรใส่ปุ๋ยฟอสเฟต")
            else:
                print("! พืชมีสุขภาพปานกลาง - ควรติดตามต่อไป")

    # ===== แสดงภาพ =====
    print("\n" + "=" * 50)
    print("กำลังแสดงภาพผลลัพธ์...")
    print("กดปุ่มใดก็ได้เพื่อปิด")
    print("=" * 50)

    # วาดผลลัพธ์
    annotated = results[0].plot()

    # แสดงภาพ
    cv2.imshow("Result", annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print("\nภาพผลลัพธ์บันทึกที่: runs/segment/predict")

print("\nเสร็จสิ้น!")
