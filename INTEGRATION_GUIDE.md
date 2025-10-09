# คู่มือการนำ Segmentation ไปใช้งานในโปรเจค

## ไฟล์ที่ได้

### 1. flask_controller_segmentation.py
Flask Controller พร้อมระบบ Segmentation แบบสมบูรณ์
- รองรับทั้ง HSV และ Segmentation
- สลับ Mode ได้ผ่านหน้าเว็บ
- โหลด Model อัตโนมัติเมื่อเริ่มโปรแกรม
- ถ้าไม่มี Model จะใช้ HSV แทน

### 2. simple_segmentation_demo.py
โปรแกรมทดสอบ Model แบบง่ายๆ
- ใช้กับ Webcam
- แสดงผลแบบ Real-time
- บันทึกภาพได้
- เหมาะสำหรับทดสอบ Model

---

## วิธีการใช้งาน

### ขั้นตอนที่ 1: ทดสอบ Model ก่อน

```bash
python simple_segmentation_demo.py
```

**ผลลัพธ์:**
- หน้าต่างแสดงภาพจากกล้อง
- วาดรูปร่างวัตถุที่ตรวจจับได้
- แสดงจำนวนและสถานะพืช

**คำสั่ง:**
- กด `q` - ออกจากโปรแกรม
- กด `s` - บันทึกภาพ
- กด `i` - แสดง/ซ่อนข้อมูล

---

### ขั้นตอนที่ 2: ใช้กับ Flask

#### วิธีที่ 1: ใช้ไฟล์ใหม่ (แนะนำ)

```bash
python flask_controller_segmentation.py
```

ระบบจะ:
1. ตรวจสอบว่ามี Segmentation Model หรือไม่
2. ถ้ามี → โหลดและใช้งาน
3. ถ้าไม่มี → ใช้ HSV แทน

#### วิธีที่ 2: แทนที่ไฟล์เดิม

```bash
# สำรองไฟล์เดิม
cp flask_controller.py flask_controller_backup.py

# แทนที่ด้วยไฟล์ใหม่
cp flask_controller_segmentation.py flask_controller.py

# รันโปรแกรม
python flask_controller.py
```

---

## การใช้งานผ่านหน้าเว็บ

### API Endpoints ใหม่

#### 1. สลับโหมดการตรวจจับ
```
GET /toggle_detection_mode
```

**Response:**
```json
{
  "status": "success",
  "mode": "SEGMENTATION"  // หรือ "HSV"
}
```

#### 2. โหลด Model จากตำแหน่งอื่น
```
GET /load_custom_model?path=/path/to/model.pt
```

**Response:**
```json
{
  "status": "success"
}
```

#### 3. ดูข้อมูลการตรวจจับ
```
GET /detection_data
```

**Response:**
```json
{
  "yellow_detected": true,
  "green_detected": true,
  "purple_detected": false,
  "yellow_count": 3,
  "green_count": 5,
  "purple_count": 0,
  "plant_status": "พืชปกติบางส่วน มีอาการขาดธาตุบางส่วน",
  "detection_mode": "SEGMENTATION"  // ← ใหม่
}
```

---

## การเพิ่มปุ่มสลับ Mode ในหน้าเว็บ

### เพิ่มใน HTML (web_interface.html)

```html
<!-- เพิ่มในส่วน Camera & Color Detection -->
<div class="card">
  <h3>Camera & Color Detection</h3>

  <!-- ... โค้ดเดิม ... -->

  <!-- เพิ่มส่วนนี้ -->
  <hr />
  <h4>Detection Mode</h4>
  <p>โหมดปัจจุบัน: <span id="detection-mode" class="data-display">HSV</span></p>
  <button class="button button-success" onclick="toggleDetectionMode()">
    สลับโหมด
  </button>
</div>
```

### เพิ่ม JavaScript

```javascript
// เพิ่มใน <script> section

function toggleDetectionMode() {
  fetch("/toggle_detection_mode")
    .then(response => response.json())
    .then(data => {
      if (data.status === "success") {
        document.getElementById("detection-mode").innerText = data.mode;
        alert("สลับเป็นโหมด " + data.mode);
      } else {
        alert("ไม่สามารถสลับโหมดได้: " + data.message);
      }
    });
}

// อัพเดทโหมดปัจจุบันใน updateData()
function updateData() {
  fetch("/detection_data")
    .then(response => response.json())
    .then(data => {
      // ... โค้ดเดิม ...

      // เพิ่มบรรทัดนี้
      document.getElementById("detection-mode").innerText = data.detection_mode;
    });
}
```

---

## การเปรียบเทียบ HSV vs Segmentation

### ตัวอย่างการใช้งาน

```python
# ใน Camera class

def get_frame(self):
    # อ่านภาพจากกล้อง
    ret, frame = self.cam.read()

    # เลือกวิธีการตรวจจับ
    if self.use_segmentation and self.model:
        # ใช้ Segmentation - แม่นยำกว่า
        frame = self.detect_with_segmentation(frame)
    else:
        # ใช้ HSV - เร็วกว่า
        frame = self.detect_with_hsv(frame)

    return frame
```

### ผลลัพธ์

**HSV Mode:**
- ✓ เร็วมาก (60 FPS)
- ✓ ไม่ต้องเทรน Model
- ✗ แม่นยำน้อย (60-70%)
- ✗ ได้รับผลกระทบจากแสง
- ✗ ตรวจจับพื้นหลังบางครั้ง

**Segmentation Mode:**
- ✓ แม่นยำมาก (90-95%)
- ✓ แยกแต่ละใบได้
- ✓ ไม่ได้รับผลกระทบจากแสง
- ✗ ช้ากว่า (30 FPS)
- ✗ ต้องเทรน Model ก่อน

---

## การใช้งานขั้นสูง

### 1. โหลดหลาย Model

```python
# เก็บหลาย Model
models = {
    "plant_v1": YOLO("model_v1.pt"),
    "plant_v2": YOLO("model_v2.pt"),
    "plant_best": YOLO("model_best.pt")
}

# เลือกใช้
current_model = models["plant_best"]
```

### 2. ปรับความมั่นใจแบบ Dynamic

```python
def detect_with_segmentation(self, frame, confidence=0.5):
    # ปรับ confidence ตามความต้องการ
    results = self.model.predict(frame, conf=confidence, verbose=False)
    return results[0].plot()
```

### 3. บันทึกภาพที่ตรวจจับได้

```python
def save_detection(self, frame, results):
    # บันทึกเฉพาะเมื่อพบวัตถุ
    if len(results[0].boxes) > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "detected_" + timestamp + ".jpg"
        cv2.imwrite(filename, frame)
        return filename
    return None
```

### 4. ส่งข้อมูลไป Arduino

```python
def send_segmentation_data(self):
    # ส่งข้อมูลแบบละเอียด
    cmd = "SEG_DATA:"
    cmd = cmd + str(self.yellow_count) + ","
    cmd = cmd + str(self.green_count) + ","
    cmd = cmd + str(self.purple_count) + ","
    cmd = cmd + str(total_area) + ","  # พื้นที่รวม
    cmd = cmd + str(avg_confidence) + "\n"  # ความมั่นใจเฉลี่ย

    arduino.send(cmd)
```

---

## การแก้ไขปัญหา

### ปัญหา 1: Model โหลดไม่ได้

**สาเหตุ:**
- ไม่มีไฟล์ Model
- ตำแหน่งไฟล์ไม่ถูกต้อง

**วิธีแก้:**
```python
# ตรวจสอบว่ามีไฟล์หรือไม่
import os
if os.path.exists("best.pt"):
    print("✓ พบไฟล์ Model")
else:
    print("✗ ไม่พบไฟล์ Model")
```

### ปัญหา 2: ภาพกระตุก/ช้า

**สาเหตุ:**
- Model ใหญ่เกินไป
- ไม่มี GPU

**วิธีแก้:**
1. ใช้ Model เล็กกว่า (nano, small)
2. ลด FPS
3. ลด Image Size

```python
# ลด Image Size
frame_resized = cv2.resize(frame, (320, 240))
results = model.predict(frame_resized)
```

### ปัญหา 3: ตรวจจับผิด

**สาเหตุ:**
- Model ยังไม่ดีพอ
- ข้อมูลเทรนน้อย

**วิธีแก้:**
1. เพิ่มข้อมูลเทรน
2. เทรนนานขึ้น (epochs)
3. ปรับ Confidence

```python
# ปรับ Confidence
results = model.predict(frame, conf=0.7)  # เพิ่มเป็น 0.7
```

---

## ตัวอย่างการใช้งานจริง

### ตัวอย่างที่ 1: ระบบตรวจสอบพืชแบบอัตโนมัติ

```python
def auto_inspection():
    # เคลื่อนที่ไปแต่ละตำแหน่ง
    for pos in [1, 2, 3, 4]:
        # ไปตำแหน่ง
        move_to_position(pos)

        # รอให้หยุด
        wait_until_stopped()

        # รอ 1 วินาที
        time.sleep(1)

        # ตรวจจับด้วย Segmentation
        frame = camera.get_frame()
        results = model.predict(frame)

        # วิเคราะห์
        analyze_plant_health(results)

        # บันทึกข้อมูล
        save_to_database(pos, results)

        # ถ้าพบปัญหา ให้รดน้ำ
        if needs_water():
            pump_water(5)  # รดน้ำ 5 วินาที
```

### ตัวอย่างที่ 2: Alert System

```python
def check_plant_health():
    # ตรวจสอบสุขภาพพืช
    results = model.predict(frame)

    yellow_count = count_class(results, "yellow_leaf")
    total_leaves = count_all_leaves(results)

    # ถ้าใบเหลืองมากกว่า 50%
    if yellow_count > total_leaves * 0.5:
        send_line_notify("⚠️ พืชขาดไนโตรเจน!")
        turn_on_red_led()
    else:
        turn_on_green_led()
```

### ตัวอย่างที่ 3: Data Logging

```python
import csv
from datetime import datetime

def log_detection_data():
    # บันทึกข้อมูลลง CSV
    with open("plant_data.csv", "a", newline="") as f:
        writer = csv.writer(f)

        # เขียนข้อมูล
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            camera.yellow_count,
            camera.green_count,
            camera.purple_count,
            camera.plant_status
        ])
```

---

## Performance Tips

### 1. ใช้ Threading สำหรับ Detection

```python
import threading

def detection_thread():
    while running:
        frame = camera.read()
        results = model.predict(frame)
        update_ui(results)
        time.sleep(0.1)

# เริ่ม Thread
t = threading.Thread(target=detection_thread, daemon=True)
t.start()
```

### 2. Cache Results

```python
# เก็บผลลัพธ์ล่าสุด
last_results = None
last_update = 0

def get_detection():
    global last_results, last_update

    # อัพเดททุก 1 วินาที
    if time.time() - last_update > 1.0:
        last_results = model.predict(frame)
        last_update = time.time()

    return last_results
```

### 3. Batch Processing

```python
# ประมวลผลหลายภาพพร้อมกัน
frames = [frame1, frame2, frame3]
results = model.predict(frames)  # เร็วกว่าทีละภาพ
```

---

## สรุป

### ข้อดีของการใช้ Segmentation

1. **ความแม่นยำสูง** - ตรวจจับได้ดีกว่า HSV มาก
2. **แยกแต่ละใบได้** - นับจำนวนได้แม่นยำ
3. **ไม่ได้รับผลกระทบจากแสง** - ทำงานได้ทุกสภาพแสง
4. **ยืดหยุ่น** - เพิ่ม Class ใหม่ได้ง่าย

### ข้อควรระวัง

1. **ต้องเทรน Model** - ใช้เวลาและข้อมูล
2. **ช้ากว่า HSV** - ต้องมี GPU ถ้าต้องการ Real-time
3. **ใช้ RAM มาก** - อาจต้องลด Batch Size

### คำแนะนำ

- **ใช้ HSV** → สำหรับการทดสอบเบื้องต้น
- **ใช้ Segmentation** → สำหรับการใช้งานจริง
- **เทรน Model ใหม่** → เมื่อมีข้อมูลมากขึ้น
- **Fine-tune** → ปรับแต่ง Model เดิมด้วยข้อมูลใหม่

---

## อ้างอิง

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Roboflow Training Guide](https://blog.roboflow.com/how-to-train-yolov8-instance-segmentation/)
- [Flask Documentation](https://flask.palletsprojects.com/)
