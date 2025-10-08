from flask import Flask, render_template, jsonify, request, Response
from datetime import datetime
import cv2
import numpy as np
import serial
import threading
import time
import serial.tools.list_ports

app = Flask(__name__)

# === กล้อง ===
class Camera:
    def __init__(self):
        self.cam = None
        self.running = False
        self.yellow = False
        self.green = False
        self.purple = False
        self.yellow_count = 0
        self.green_count = 0
        self.purple_count = 0
        self.plant_status = "ไม่พบพืช"

    def start(self):
        try:
            # Windows เท่านั้น
            self.cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

            if self.cam.isOpened():
                self.cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.running = True
                print("Camera: OK")
                return True
        except:
            pass
        print("Camera: Failed")
        return False

    def get_frame(self):
        if not self.cam or not self.cam.isOpened():
            return None

        ret, frame = self.cam.read()
        if not ret:
            return None

        # แปลงเป็น HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # หาสี 3 แบบ (เพิ่ม Saturation และ Value ขั้นต่ำ เพื่อไม่เจอสีเข้ม/ดำ)
        yellow_mask = cv2.inRange(hsv, np.array([20, 80, 80]), np.array([30, 255, 255]))
        green_mask = cv2.inRange(hsv, np.array([40, 60, 60]), np.array([80, 255, 255]))
        purple_mask = cv2.inRange(hsv, np.array([125, 80, 80]), np.array([155, 255, 255]))

        yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        purple_contours, _ = cv2.findContours(purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.yellow_count = 0
        self.green_count = 0
        self.purple_count = 0

        # วาดกรอบสีเหลือง
        for c in yellow_contours:
            if cv2.contourArea(c) > 500:
                self.yellow_count += 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                cv2.putText(frame, 'YELLOW', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # วาดกรอบสีเขียว
        for c in green_contours:
            if cv2.contourArea(c) > 500:
                self.green_count += 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, 'GREEN', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # วาดกรอบสีม่วง
        for c in purple_contours:
            if cv2.contourArea(c) > 500:
                self.purple_count += 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 255), 2)
                cv2.putText(frame, 'PURPLE', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

        self.yellow = self.yellow_count > 0
        self.green = self.green_count > 0
        self.purple = self.purple_count > 0

        # ตรวจสอบสภาพพืช
        if self.yellow and not self.green and not self.purple:
            self.plant_status = "ขาดไนโตรเจน"
        elif self.purple and not self.green and not self.yellow:
            self.plant_status = "ขาดฟอสฟอรัส"
        elif self.yellow and self.purple:
            self.plant_status = "ขาดไนโตรเจนและฟอสฟอรัส"
        elif self.green and not self.yellow and not self.purple:
            self.plant_status = "พืชปกติ"
        elif self.green and (self.yellow or self.purple):
            self.plant_status = "พืชปกติบางส่วน มีอาการขาดธาตุบางส่วน"
        else:
            self.plant_status = "ไม่พบพืช"

        # แสดงสถานะ
        cv2.putText(frame, f"Y:{self.yellow_count} G:{self.green_count} P:{self.purple_count}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, self.plant_status, (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame

    def stop(self):
        self.running = False
        if self.cam:
            self.cam.release()
            self.cam = None

# === Arduino ===
class Arduino:
    def __init__(self):
        self.ser = None
        self.connected = False
        self.port = None
        self.encoder_x = 0
        self.encoder_y = 0
        self.reading = False

    def get_ports(self):
        # หา COM port ทั้งหมด
        ports = []
        all_ports = serial.tools.list_ports.comports()
        for port in all_ports:
            ports.append(port.device)
        return ports

    def connect(self, port=None):
        # เชื่อมต่อ Arduino
        if port:
            # ใช้ port ที่เลือก
            ports = [port]
        else:
            # หาอัตโนมัติ
            ports = self.get_ports()

        for p in ports:
            try:
                print(f"กำลังเชื่อมต่อ {p}...")

                # เปิด port
                self.ser = serial.Serial(p, 115200, timeout=1)
                time.sleep(2)

                # ลบข้อมูลเก่า
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                time.sleep(0.5)

                # ส่ง PING
                self.ser.write(b"PING\n")
                time.sleep(0.5)

                # อ่าน response
                if self.ser.in_waiting > 0:
                    data = self.ser.readline()
                    response = data.decode('utf-8', errors='ignore').strip()
                    print(f"ได้: {response}")

                    if "PONG" in response:
                        self.connected = True
                        self.port = p
                        print(f"เชื่อมต่อสำเร็จ: {p}")
                        # เริ่ม thread อ่านข้อมูล
                        self.reading = True
                        threading.Thread(target=self.read_loop, daemon=True).start()
                        return True

                # ลองอีกครั้ง
                self.ser.write(b"PING\n")
                time.sleep(0.5)

                if self.ser.in_waiting > 0:
                    data = self.ser.readline()
                    response = data.decode('utf-8', errors='ignore').strip()
                    print(f"ได้: {response}")

                    if "PONG" in response:
                        self.connected = True
                        self.port = p
                        print(f"เชื่อมต่อสำเร็จ: {p}")
                        # เริ่ม thread อ่านข้อมูล
                        self.reading = True
                        threading.Thread(target=self.read_loop, daemon=True).start()
                        return True

                print(f"ไม่ได้รับ PONG จาก {p}")
                self.ser.close()

            except Exception as e:
                print(f"ผิดพลาด: {e}")
                if self.ser:
                    try:
                        self.ser.close()
                    except:
                        pass

        print("หา Arduino ไม่เจอ")
        return False

    def read_loop(self):
        # อ่านข้อมูลจาก Arduino ตลอดเวลา
        while self.reading and self.connected:
            try:
                if self.ser and self.ser.in_waiting > 0:
                    line = self.ser.readline()
                    data = line.decode('utf-8', errors='ignore').strip()

                    # แยกข้อมูล STATUS
                    if data.startswith("STATUS:"):
                        parts = data.replace("STATUS:", "").split(",")
                        for part in parts:
                            if "X=" in part:
                                self.encoder_x = int(part.split("=")[1])
                            elif "Y=" in part:
                                self.encoder_y = int(part.split("=")[1])

                time.sleep(0.1)
            except:
                pass

    def send(self, cmd):
        if self.connected and self.ser:
            try:
                self.ser.write(cmd.encode())
                return True
            except:
                self.connected = False
        return False

    def close(self):
        self.reading = False
        self.connected = False
        if self.ser:
            self.ser.close()

# === ระบบ ===
camera = Camera()
arduino = Arduino()

class System:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.moving = False
        self.mode = "manual"
        self.step = 0
        self.alarms = [{"isEnabled": False, "time": ""} for i in range(3)]
        self.cam_on = False

system = System()

# ฟังก์ชันส่งข้อมูลสี
def send_color_loop():
    last = 0
    while camera.running:
        try:
            if time.time() - last >= 1.0:
                if camera.yellow or camera.green or camera.purple:
                    cmd = f"COLOR:{int(camera.yellow)},{int(camera.green)},{int(camera.purple)},{camera.yellow_count},{camera.green_count},{camera.purple_count}\n"
                    arduino.send(cmd)
                last = time.time()
            time.sleep(0.1)
        except:
            time.sleep(1)

# ฟังก์ชันส่งภาพ
def video_stream():
    while True:
        try:
            if system.cam_on:
                frame = camera.get_frame()
            else:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, 'Camera Off', (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

            if frame is None:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

            ret, jpg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpg.tobytes() + b'\r\n')
            time.sleep(0.03)
        except:
            time.sleep(0.5)

# === หน้าเว็บ ===
@app.route('/')
def index():
    return render_template('web_interface.html')

@app.route('/video_feed')
def video():
    return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera_control')
def cam_ctrl():
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

@app.route('/arduino_control')
def ard_ctrl():
    action = request.args.get('action')
    port = request.args.get('port')

    if action == 'get_ports':
        ports = arduino.get_ports()
        return jsonify({"status": "success", "ports": ports})
    elif action == 'connect':
        arduino.close()
        ok = arduino.connect(port)
        if ok:
            # ขอ STATUS ทุก 1 วินาที
            def request_status():
                while arduino.connected:
                    arduino.send("STATUS\n")
                    time.sleep(1)
            threading.Thread(target=request_status, daemon=True).start()
        return jsonify({"status": "success" if ok else "error",
                       "connected": ok, "port": arduino.port})
    elif action == 'disconnect':
        arduino.close()
        return jsonify({"status": "success", "connected": False, "port": None})
    elif action == 'reconnect':
        arduino.close()
        ok = arduino.connect()
        if ok:
            # ขอ STATUS ทุก 1 วินาที
            def request_status():
                while arduino.connected:
                    arduino.send("STATUS\n")
                    time.sleep(1)
            threading.Thread(target=request_status, daemon=True).start()
        return jsonify({"status": "success" if ok else "error",
                       "connected": ok, "port": arduino.port})
    elif action in ['X_FWD', 'X_BACK', 'Y_FWD', 'Y_BACK', 'STOP']:
        ok = arduino.send(f"MOTOR:{action}\n")
        return jsonify({"status": "success" if ok else "error"})
    return jsonify({"status": "error"})

@app.route('/detection_data')
def detect_data():
    return jsonify({
        "yellow_detected": camera.yellow,
        "green_detected": camera.green,
        "purple_detected": camera.purple,
        "yellow_count": camera.yellow_count,
        "green_count": camera.green_count,
        "purple_count": camera.purple_count,
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
        "plant_status": camera.plant_status,
        "detection_results": {
            "yellow_count": camera.yellow_count,
            "green_count": camera.green_count,
            "purple_count": camera.purple_count
        }
    })

@app.route('/motor')
def motor():
    # Manual control ผ่าน Arduino
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
    # ส่งคำสั่งไป Arduino ให้ไปตำแหน่ง
    p = int(request.args.get('pos', 0))
    if p >= 1 and p <= 4:
        arduino.send(f"MOVETO:{p}\n")
    return "OK"

@app.route('/setmode')
def setmode():
    # เปลี่ยนโหมด
    m = request.args.get('mode')
    system.mode = "auto_sequence" if m == 'auto_sequence' else "manual"
    system.step = 0

    # ส่งไป Arduino
    if m == 'auto_sequence':
        arduino.send("MODE:AUTO\n")
    else:
        arduino.send("MODE:MANUAL\n")

    return "OK"

@app.route('/set-alarm')
def setalarm():
    # ตั้งเวลา
    s = int(request.args.get('slot', 0))
    t = request.args.get('alarmTime', '')
    if 0 <= s < 3:
        system.alarms[s] = {"isEnabled": True, "time": t}
        # ส่งไป Arduino
        arduino.send(f"ALARM:{s},{t}\n")
    return "OK"

@app.route('/cancel-alarm')
def cancelalarm():
    # ยกเลิกเวลา
    s = int(request.args.get('slot', 0))
    if 0 <= s < 3:
        system.alarms[s] = {"isEnabled": False, "time": ""}
        # ส่งไป Arduino
        arduino.send(f"CANCEL:{s}\n")
    return "OK"

@app.route('/reset')
def reset():
    # รีเซ็ต encoder
    arduino.send("RESET\n")
    return "OK"

# === เริ่มโปรแกรม ===
if __name__ == '__main__':
    print("\n" + "="*40)
    print("ESP32 Controller")
    print("="*40)

    camera.start()
    arduino.connect()

    print("="*40 + "\n")
    print("Server: http://localhost:5001")
    print("="*40 + "\n")

    try:
        app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        camera.stop()
        arduino.close()
        print("Done.")
