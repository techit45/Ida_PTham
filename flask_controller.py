# ===================================
# โปรเจค: ระบบตรวจสอบพืชและรดน้ำอัตโนมัติ
# ระบบ: ESP32 + กล้อง + มอเตอร์ 2 แกน
# ===================================

from flask import Flask, render_template, jsonify, request, Response
from datetime import datetime
import cv2
import numpy as np
import serial
import threading
import time
import serial.tools.list_ports
import csv
import os

app = Flask(__name__)

# ===================================
# ส่วนที่ 1: กล้อง (ตรวจจับสีพืช)
# ===================================
class Camera:
    def __init__(self):
        # ตัวแปรพื้นฐาน
        self.cam = None
        self.running = False

        # ตัวแปรเก็บสถานะสี (True/False)
        self.yellow = False  # สีเหลือง
        self.green = False   # สีเขียว
        self.purple = False  # สีม่วง
        self.brown = False   # สีน้ำตาล

        # ตัวแปรนับจำนวนสี
        self.yellow_count = 0
        self.green_count = 0
        self.purple_count = 0
        self.brown_count = 0

        # สถานะพืช
        self.plant_status = "ไม่พบพืช"

    def start(self):
        """เปิดกล้อง"""
        try:
            # เปิดกล้อง index 1 (Windows)
            self.cam = cv2.VideoCapture(1, cv2.CAP_DSHOW)

            if self.cam.isOpened():
                # ตั้งค่าขนาดภาพ
                self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.running = True
                print("กล้องเปิดสำเร็จ!")
                return True
            else:
                print("เปิดกล้องไม่ได้")
                return False
        except Exception as e:
            print("ผิดพลาด: " + str(e))
            return False

    def get_frame(self):
        """อ่านภาพจากกล้องและตรวจจับสี"""
        # เช็คว่ากล้องพร้อมหรือไม่
        if not self.cam:
            return None
        if not self.cam.isOpened():
            return None

        # อ่านภาพจากกล้อง
        ret, frame = self.cam.read()
        if not ret:
            return None

        # แปลงภาพเป็น HSV (สำหรับตรวจจับสี)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # --- ตรวจจับสีเหลือง (ขาดไนโตรเจน) ---
        yellow_low = np.array([20, 100, 100])   # ค่าต่ำสุด HSV
        yellow_high = np.array([30, 255, 255])  # ค่าสูงสุด HSV
        yellow_mask = cv2.inRange(hsv, yellow_low, yellow_high)
        yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # --- ตรวจจับสีเขียว (พืชปกติ) ---
        green_low = np.array([40, 80, 80])
        green_high = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, green_low, green_high)
        green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # --- ตรวจจับสีม่วง (ขาดฟอสฟอรัส) ---
        purple_low = np.array([125, 100, 100])
        purple_high = np.array([155, 255, 255])
        purple_mask = cv2.inRange(hsv, purple_low, purple_high)
        purple_contours, _ = cv2.findContours(purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # --- ตรวจจับสีน้ำตาล (ขาดโพแทสเซียม) ---
        brown_low = np.array([8, 50, 50])
        brown_high = np.array([19, 255, 200])
        brown_mask = cv2.inRange(hsv, brown_low, brown_high)
        brown_contours, _ = cv2.findContours(brown_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # --- นับและวาดกรอบสีเหลือง ---
        self.yellow_count = 0
        for c in yellow_contours:
            area = cv2.contourArea(c)
            if area > 500:  # ถ้าพื้นที่ > 500 ถึงจะนับ
                self.yellow_count = self.yellow_count + 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)  # วาดกรอบสีเหลือง
                cv2.putText(frame, 'YELLOW', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # --- นับและวาดกรอบสีเขียว ---
        self.green_count = 0
        for c in green_contours:
            area = cv2.contourArea(c)
            if area > 500:
                self.green_count = self.green_count + 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, 'GREEN', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # --- นับและวาดกรอบสีม่วง ---
        self.purple_count = 0
        for c in purple_contours:
            area = cv2.contourArea(c)
            if area > 500:
                self.purple_count = self.purple_count + 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 255), 2)
                cv2.putText(frame, 'PURPLE', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

        # --- นับและวาดกรอบสีน้ำตาล ---
        self.brown_count = 0
        for c in brown_contours:
            area = cv2.contourArea(c)
            if area > 500:
                self.brown_count = self.brown_count + 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (42, 42, 165), 2)
                cv2.putText(frame, 'BROWN', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (42, 42, 165), 2)

        # --- อัปเดตสถานะสี (True/False) ---
        self.yellow = (self.yellow_count > 0)
        self.green = (self.green_count > 0)
        self.purple = (self.purple_count > 0)
        self.brown = (self.brown_count > 0)

        # --- วิเคราะห์สถานะพืช ---
        # ถ้าเจอสีที่แสดงการขาดธาตุ (ไม่สนใจว่ามีสีเขียวหรือไม่)
        deficiencies = []
        if self.yellow:
            deficiencies.append("ไนโตรเจน")
        if self.purple:
            deficiencies.append("ฟอสฟอรัส")
        if self.brown:
            deficiencies.append("โพแทสเซียม")

        # ถ้าขาดธาตุอย่างใดอย่างหนึ่ง
        if len(deficiencies) > 0:
            self.plant_status = "ขาด" + "+".join(deficiencies)

        # ถ้าเจอเฉพาะสีเขียว = พืชปกติ
        elif self.green:
            self.plant_status = "พืชปกติ"

        # ถ้าไม่เจออะไร = ไม่พบพืช
        else:
            self.plant_status = "ไม่พบพืช"

        # --- แสดงข้อมูลบนภาพ ---
        text1 = "Y:" + str(self.yellow_count) + " G:" + str(self.green_count) + " P:" + str(self.purple_count) + " B:" + str(self.brown_count)
        cv2.putText(frame, text1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, self.plant_status, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame

    def stop(self):
        """ปิดกล้อง"""
        self.running = False
        if self.cam:
            self.cam.release()
            self.cam = None

# ===================================
# ส่วนที่ 2: Arduino (เชื่อมต่อ ESP32)
# ===================================
class Arduino:
    def __init__(self):
        # ตัวแปรเชื่อมต่อ Serial
        self.ser = None
        self.connected = False
        self.port = None

        # ตัวแปรเก็บตำแหน่ง Encoder
        self.encoder_x = 0
        self.encoder_y = 0

        # สถานะการอ่านข้อมูล
        self.reading = False

    def get_ports(self):
        """หา COM Port ทั้งหมด (Windows)"""
        ports = ['COM4']  # ให้ COM4 เป็นตัวเลือกแรก
        try:
            all_ports = serial.tools.list_ports.comports()
            for port in all_ports:
                if port.device not in ports:
                    ports.append(port.device)
        except:
            pass
        return ports

    def connect(self, port=None):
        """เชื่อมต่อ Arduino ผ่าน Serial"""
        # ถ้าระบุ port มา ใช้ port นั้น ถ้าไม่ระบุ ใช้ COM4
        if port:
            ports = [port]
        else:
            ports = ['COM4']

        # ลองเชื่อมต่อทีละ port
        for p in ports:
            try:
                print("กำลังเชื่อมต่อ " + p + "...")

                # เปิด Serial Port (ความเร็ว 115200)
                self.ser = serial.Serial(p, 115200, timeout=1)
                time.sleep(2)  # รอให้ Arduino พร้อม

                # ล้างข้อมูลเก่าทิ้ง
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()

                # ลองส่ง PING 2 ครั้ง
                success = False
                for _ in range(2):
                    self.ser.write(b"PING\n")
                    time.sleep(0.5)

                    # ถ้ามีข้อมูลตอบกลับมา
                    if self.ser.in_waiting > 0:
                        data = self.ser.readline()
                        response = data.decode('utf-8', errors='ignore').strip()
                        print("ได้รับ: " + response)

                        # ถ้าได้ PONG กลับมา = เชื่อมต่อสำเร็จ
                        if "PONG" in response:
                            self.connected = True
                            self.port = p
                            self.reading = True

                            # เริ่ม thread อ่านข้อมูลจาก Arduino
                            t = threading.Thread(target=self.read_loop, daemon=True)
                            t.start()

                            print("เชื่อมต่อสำเร็จ: " + p)
                            success = True
                            break

                if success:
                    return True
                else:
                    self.ser.close()

            except Exception as e:
                print("ผิดพลาด: " + str(e))
                try:
                    self.ser.close()
                except:
                    pass

        print("ไม่พบ Arduino - ใช้โหมดจำลอง")
        return False

    def read_loop(self):
        """อ่านข้อมูลจาก Arduino ตลอดเวลา (ทำงานใน Thread แยก)"""
        while self.reading and self.connected:
            try:
                # ถ้ามีข้อมูลมาจาก Arduino
                if self.ser and self.ser.in_waiting > 0:
                    # อ่านข้อมูล 1 บรรทัด
                    _ = self.ser.readline()
                    data = _.decode('utf-8', errors='ignore').strip()

                    # ถ้าเป็นข้อมูล STATUS (ตำแหน่ง Encoder)
                    if data.startswith("STATUS:"):
                        # ตัดคำว่า STATUS: ออก
                        data = data.replace("STATUS:", "")

                        # แยกข้อมูลด้วย ,
                        parts = data.split(",")

                        # หาค่า X และ Y
                        for part in parts:
                            if "X=" in part:
                                value = part.split("=")[1]
                                self.encoder_x = int(value)
                            elif "Y=" in part:
                                value = part.split("=")[1]
                                self.encoder_y = int(value)

                time.sleep(0.1)
            except:
                pass

    def send(self, cmd):
        """ส่งคำสั่งไป Arduino"""
        if self.connected and self.ser:
            try:
                self.ser.write(cmd.encode())
                return True
            except:
                self.connected = False
        return False

    def close(self):
        """ปิดการเชื่อมต่อ"""
        self.reading = False
        self.connected = False
        if self.ser:
            self.ser.close()

# ===================================
# ส่วนที่ 3: บันทึกข้อมูล CSV
# ===================================
class DataLogger:
    def __init__(self):
        # สร้างชื่อไฟล์ตามวันที่ (เช่น plant_data_20250115.csv)
        self.csv_filename = "plant_data_" + datetime.now().strftime('%Y%m%d') + ".csv"
        self.csv_path = os.path.join(os.getcwd(), self.csv_filename)
        self.init_csv()

    def init_csv(self):
        """สร้างไฟล์ CSV และใส่ header"""
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # เขียน Header
                writer.writerow([
                    'Timestamp', 'Position_X', 'Position_Y', 'Position_Name',
                    'Green_Count', 'Yellow_Count', 'Purple_Count', 'Brown_Count',
                    'Plant_Status', 'Diagnosis', 'Notes'
                ])
            print("สร้างไฟล์ CSV: " + self.csv_path)

    def log_data(self, position_name, position_x=0, position_y=0, notes=""):
        """บันทึกข้อมูลพืชลง CSV"""
        # เวลาขณะนี้
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # วิเคราะห์สถานะพืช
        diagnosis = self.analyze_plant_status()

        # เขียนข้อมูลลงไฟล์ CSV
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, position_x, position_y, position_name,
                camera.green_count, camera.yellow_count, camera.purple_count, camera.brown_count,
                camera.plant_status, diagnosis, notes
            ])

        print("บันทึกข้อมูล: " + position_name + " -> " + diagnosis)
        return True

    def analyze_plant_status(self):
        """วิเคราะห์สถานะธาตุอาหารของพืช"""
        yellow = camera.yellow_count
        purple = camera.purple_count
        brown = camera.brown_count
        green = camera.green_count

        # สร้างรายการธาตุที่ขาด (ไม่สนใจว่ามีสีเขียวหรือไม่)
        deficiencies = []
        if yellow > 0:
            deficiencies.append("ไนโตรเจน")
        if purple > 0:
            deficiencies.append("ฟอสฟอรัส")
        if brown > 0:
            deficiencies.append("โพแทสเซียม")

        # ถ้าขาดธาตุอย่างใดอย่างหนึ่ง
        if len(deficiencies) > 0:
            return "ขาด" + "+".join(deficiencies)

        # ถ้าเจอเฉพาะสีเขียว = ปกติ
        elif green > 0:
            return "ปกติ"

        # ไม่เจอพืช
        else:
            return "ไม่พบพืช"

# ===================================
# ส่วนที่ 4: สร้าง Object ต่างๆ
# ===================================
camera = Camera()           # Object กล้อง
arduino = Arduino()         # Object Arduino
data_logger = DataLogger()  # Object บันทึก CSV

class System:
    """ระบบควบคุมทั่วไป"""
    def __init__(self):
        # ตำแหน่ง
        self.x = 0
        self.y = 0
        self.moving = False

        # โหมด
        self.mode = "manual"  # manual หรือ auto_sequence
        self.step = 0

        # Alarm 3 ตัว (ตั้งเวลารดน้ำ)
        self.alarms = []
        self.alarms.append({"isEnabled": False, "time": ""})
        self.alarms.append({"isEnabled": False, "time": ""})
        self.alarms.append({"isEnabled": False, "time": ""})

        # กล้อง
        self.cam_on = False

        # ปั๊มน้ำ
        self.pump_duration = 5  # เปิดปั๊ม 5 วินาที

system = System()

# ===================================
# ฟังก์ชันช่วย (Helper Functions)
# ===================================

def send_color_loop():
    """ส่งข้อมูลสีไป Arduino ทุกๆ 1 วินาที"""
    last = 0
    while camera.running:
        try:
            # ถ้าผ่านไป 1 วินาทีแล้ว
            if time.time() - last >= 1.0:
                # ถ้าเจอสีอย่างใดอย่างหนึ่ง
                if camera.yellow or camera.green or camera.purple or camera.brown:
                    # สร้างคำสั่ง COLOR (สถานะ 4 สี + จำนวน 4 สี)
                    cmd = "COLOR:" + str(int(camera.yellow)) + "," + str(int(camera.green)) + ","
                    cmd = cmd + str(int(camera.purple)) + "," + str(int(camera.brown)) + ","
                    cmd = cmd + str(camera.yellow_count) + "," + str(camera.green_count) + ","
                    cmd = cmd + str(camera.purple_count) + "," + str(camera.brown_count) + "\n"
                    arduino.send(cmd)
                last = time.time()
            time.sleep(0.1)
        except:
            time.sleep(1)

def video_stream():
    """ส่งภาพกล้องไปแสดงบนเว็บ (Real-time streaming)"""
    while True:
        try:
            # ถ้ากล้องเปิด แสดงภาพจริง
            if system.cam_on:
                frame = camera.get_frame()
            # ถ้ากล้องปิด แสดงภาพดำ
            else:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, 'Camera Off', (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            # ถ้าไม่มีภาพ สร้างภาพดำ
            if frame is None:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

            # แปลงเป็น JPEG และส่งออกไป
            ret, jpg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg.tobytes() + b'\r\n')
            time.sleep(0.03)  # 30 FPS
        except:
            time.sleep(0.5)

# ===================================
# ส่วนที่ 5: Flask Routes (หน้าเว็บและ API)
# ===================================
# --- หน้าเว็บหลัก ---
@app.route('/')
def index():
    """แสดงหน้าเว็บหลัก"""
    return render_template('web_interface.html')

# --- ส่งภาพกล้อง ---
@app.route('/video_feed')
def video():
    """ส่งภาพ Real-time ไปแสดงบนเว็บ"""
    return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- ควบคุมกล้อง ---
@app.route('/camera_control')
def cam_ctrl():
    """เปิด/ปิดกล้อง"""
    action = request.args.get('action')
    if action == 'start' and not system.cam_on:
        if camera.start():
            system.cam_on = True
            threading.Thread(target=send_color_loop, daemon=True).start()
            return jsonify({"status": "success"})
    elif action == 'stop':
        camera.stop()
        system.cam_on = False
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

def start_status_loop():
    def loop():
        while arduino.connected:
            arduino.send("STATUS\n")
            time.sleep(1)
    threading.Thread(target=loop, daemon=True).start()

def start_alarm_check():
    # เช็คเวลาทุก 30 วินาที
    def loop():
        last_triggered_minute = -1  # เก็บนาทีที่ trigger ล่าสุด

        while True:
            try:
                if system.mode == "auto_sequence":
                    now = datetime.now()
                    current_hour = now.hour
                    current_minute = now.minute

                    # ถ้านาทีนี้ trigger ไปแล้ว ข้าม
                    if current_minute == last_triggered_minute:
                        time.sleep(30)
                        continue

                    # เช็คแต่ละ alarm
                    for alarm in system.alarms:
                        if alarm["isEnabled"] and alarm["time"]:
                            # แยกเวลา
                            parts = alarm["time"].split(":")
                            alarm_hour = int(parts[0])
                            alarm_minute = int(parts[1])

                            # ถ้าตรงเวลา
                            if current_hour == alarm_hour and current_minute == alarm_minute:
                                print("ถึงเวลาแล้ว! เริ่ม sequence")
                                arduino.send("START_SEQUENCE\n")
                                last_triggered_minute = current_minute
                                break  # ออกจาก loop ทันที

                time.sleep(30)  # เช็คทุก 30 วินาที
            except:
                time.sleep(30)

    threading.Thread(target=loop, daemon=True).start()

@app.route('/arduino_control')
def ard_ctrl():
    action = request.args.get('action')
    port = request.args.get('port')

    if action == 'get_ports':
        return jsonify({"status": "success", "ports": arduino.get_ports()})

    if action == 'connect':
        arduino.close()
        ok = arduino.connect(port)
        if ok:
            start_status_loop()
            return jsonify({"status": "success", "connected": True, "port": arduino.port})
        else:
            return jsonify({"status": "error", "connected": False, "port": arduino.port})

    if action == 'disconnect':
        arduino.close()
        return jsonify({"status": "success", "connected": False, "port": None})

    if action == 'reconnect':
        arduino.close()
        ok = arduino.connect()
        if ok:
            start_status_loop()
            return jsonify({"status": "success", "connected": True, "port": arduino.port})
        else:
            return jsonify({"status": "error", "connected": False, "port": arduino.port})

    if action in ['X_FWD', 'X_BACK', 'Y_FWD', 'Y_BACK', 'STOP']:
        cmd = "MOTOR:" + action + "\n"
        if arduino.send(cmd):
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error"})

    return jsonify({"status": "error"})

@app.route('/detection_data')
def detect_data():
    return jsonify({
        "yellow_detected": camera.yellow,
        "green_detected": camera.green,
        "purple_detected": camera.purple,
        "brown_detected": camera.brown,
        "yellow_count": camera.yellow_count,
        "green_count": camera.green_count,
        "purple_count": camera.purple_count,
        "brown_count": camera.brown_count,
        "plant_status": camera.plant_status,
        "camera_enabled": system.cam_on,
        "arduino_connected": arduino.connected,
        "arduino_port": arduino.port
    })

@app.route('/data')
def data():
    return jsonify({
        "encoderX": arduino.encoder_x,
        "encoderY": arduino.encoder_y,
        "isMoving": system.moving,
        "mode": system.mode,
        "timedSequenceStep": system.step,
        "time": datetime.now().strftime("%H:%M:%S"),
        "alarms": system.alarms,
        "camera_enabled": system.cam_on,
        "yellow_detected": camera.yellow,
        "green_detected": camera.green,
        "purple_detected": camera.purple,
        "brown_detected": camera.brown,
        "plant_status": camera.plant_status,
        "detection_results": {
            "yellow_count": camera.yellow_count,
            "green_count": camera.green_count,
            "purple_count": camera.purple_count,
            "brown_count": camera.brown_count
        }
    })

@app.route('/motor')
def motor():
    d = request.args.get('dir')

    if d == 'xfwd':
        arduino.send("MOTOR:X_FWD\n")
    elif d == 'xback':
        arduino.send("MOTOR:X_BACK\n")
    elif d == 'yfwd':
        arduino.send("MOTOR:Y_FWD\n")
    elif d == 'yback':
        arduino.send("MOTOR:Y_BACK\n")
    elif d == 'stop':
        arduino.send("MOTOR:STOP\n")

    return "OK"

@app.route('/moveto')
def moveto():
    """เคลื่อนที่ไปตำแหน่งที่กำหนด (Position 1-4)"""
    p = int(request.args.get('pos', 0))
    if p >= 1 and p <= 4:
        # *** สำคัญ: บันทึกข้อมูลก่อนเคลื่อนที่ในโหมด Auto ***
        if system.mode == "auto_sequence":
            position_name = "Position_" + str(p)
            notes = "Auto sequence - before watering at position " + str(p)
            data_logger.log_data(position_name, arduino.encoder_x, arduino.encoder_y, notes)
            print("บันทึกข้อมูล: " + position_name)

        # ส่งคำสั่งไป Arduino
        cmd = "MOVETO:" + str(p) + "\n"
        arduino.send(cmd)
    return "OK"

@app.route('/setmode')
def setmode():
    m = request.args.get('mode')

    if m == 'auto_sequence':
        system.mode = "auto_sequence"
        arduino.send("MODE:AUTO\n")
    else:
        system.mode = "manual"
        arduino.send("MODE:MANUAL\n")

    system.step = 0
    return "OK"

@app.route('/set-alarm')
def setalarm():
    s = int(request.args.get('slot', 0))
    t = request.args.get('alarmTime', '')

    if s >= 0 and s < 3:
        system.alarms[s] = {"isEnabled": True, "time": t}
        cmd = "ALARM:" + str(s) + "," + t + "\n"
        arduino.send(cmd)

    return "OK"

@app.route('/cancel-alarm')
def cancelalarm():
    s = int(request.args.get('slot', 0))

    if s >= 0 and s < 3:
        system.alarms[s] = {"isEnabled": False, "time": ""}
        cmd = "CANCEL:" + str(s) + "\n"
        arduino.send(cmd)

    return "OK"

@app.route('/reset')
def reset():
    arduino.send("RESET\n")
    return "OK"

@app.route('/pump')
def pump():
    """ควบคุมปั๊มน้ำ (เปิด/ปิด)"""
    action = request.args.get('action')
    position = request.args.get('position', 'Current')

    if action == 'on':
        # *** สำคัญ: บันทึกข้อมูลก่อนรดน้ำ ***
        position_name = "Pump_" + position
        data_logger.log_data(position_name, arduino.encoder_x, arduino.encoder_y, "Before watering")
        print("บันทึกข้อมูลก่อนรดน้ำ")

        # เปิดปั๊ม
        arduino.send("PUMP:ON\n")
    elif action == 'off':
        # ปิดปั๊ม
        arduino.send("PUMP:OFF\n")

    return "OK"

@app.route('/set-pump-duration')
def setpumpduration():
    # ตั้งเวลาปั๊มน้ำ (วินาที)
    duration = int(request.args.get('duration', 5))

    if duration > 0:
        system.pump_duration = duration
        # แปลงเป็นมิลลิวินาทีส่งไป Arduino
        duration_ms = duration * 1000
        cmd = "PUMP_DURATION:" + str(duration_ms) + "\n"
        arduino.send(cmd)

    return "OK"

# --- ดาวน์โหลด CSV ---
@app.route('/download_csv')
def download_csv():
    """ดาวน์โหลดไฟล์ CSV"""
    from flask import send_file
    try:
        return send_file(data_logger.csv_path, as_attachment=True, download_name=data_logger.csv_filename)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# --- สถานะ CSV ---
@app.route('/csv_status')
def csv_status():
    """ดูสถานะไฟล์ CSV (มีหรือไม่ จำนวน record)"""
    file_exists = os.path.exists(data_logger.csv_path)
    file_size = 0
    record_count = 0

    if file_exists:
        file_size = os.path.getsize(data_logger.csv_path)
        # นับจำนวน record (ลบ header 1 บรรทัด)
        try:
            with open(data_logger.csv_path, 'r', encoding='utf-8') as f:
                record_count = sum(1 for _ in f) - 1
        except:
            pass

    return jsonify({
        "file_exists": file_exists,
        "filename": data_logger.csv_filename,
        "file_size": file_size,
        "record_count": record_count,
        "file_path": data_logger.csv_path
    })

# ===================================
# ส่วนที่ 6: เริ่มโปรแกรม
# ===================================
if __name__ == '__main__':
    print("\n" + "="*40)
    print("ระบบตรวจสอบพืชและรดน้ำอัตโนมัติ")
    print("="*40)

    # เปิดกล้อง
    camera.start()

    # เชื่อมต่อ Arduino (COM4)
    arduino.connect('COM4')

    # เริ่ม Alarm Checker (ตรวจสอบเวลารดน้ำ)
    start_alarm_check()

    print("="*40)
    print("เว็บเซิร์ฟเวอร์: http://localhost:5001")
    print("="*40 + "\n")

    try:
        # เริ่ม Flask Server
        app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nกำลังหยุดโปรแกรม...")
    finally:
        # ปิดกล้องและ Arduino
        camera.stop()
        arduino.close()
        print("เสร็จสิ้น!")
