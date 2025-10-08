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
        self.yellow_count = 0
        self.green_count = 0

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

        # หาสี
        yellow_mask = cv2.inRange(hsv, np.array([20, 50, 50]), np.array([30, 255, 255]))
        green_mask = cv2.inRange(hsv, np.array([40, 50, 50]), np.array([80, 255, 255]))

        yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.yellow_count = 0
        self.green_count = 0

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

        self.yellow = self.yellow_count > 0
        self.green = self.green_count > 0

        cv2.putText(frame, f"Y:{self.yellow_count} G:{self.green_count}", (10, 30),
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

    def get_ports(self):
        # ดึงรายชื่อ COM ports ที่มีอยู่จริง (Windows)
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(port.device)
        return ports

    def connect(self, port=None):
        # เชื่อมต่อกับ port ที่ระบุ หรือหาอัตโนมัติ
        if port:
            ports = [port]
        else:
            ports = self.get_ports()

        for p in ports:
            try:
                print(f"Trying to connect to {p}...")
                self.ser = serial.Serial(p, 115200, timeout=2)
                time.sleep(2)

                # ล้างข้อมูลเก่า
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()

                # ส่ง PING
                self.ser.write(b"PING\n")
                time.sleep(0.5)

                # อ่าน response (รองรับ encoding error)
                response = ""
                try:
                    response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                except:
                    response = ""

                print(f"Response from {p}: '{response}'")

                if "PONG" in response:
                    self.connected = True
                    self.port = p
                    print(f"Arduino connected: {p}")
                    return True
                self.ser.close()
            except Exception as e:
                print(f"Failed to connect to {p}: {e}")
                try:
                    if self.ser and self.ser.is_open:
                        self.ser.close()
                except:
                    pass

        print("Arduino: Not found")
        return False

    def send(self, cmd):
        if self.connected and self.ser:
            try:
                self.ser.write(cmd.encode())
                return True
            except:
                self.connected = False
        return False

    def close(self):
        if self.ser:
            self.ser.close()
        self.connected = False

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
                if camera.yellow or camera.green:
                    cmd = f"COLOR:{int(camera.yellow)},{int(camera.green)},{camera.yellow_count},{camera.green_count}\n"
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
        return jsonify({"status": "success" if ok else "error",
                       "connected": ok, "port": arduino.port})
    elif action == 'disconnect':
        arduino.close()
        return jsonify({"status": "success", "connected": False, "port": None})
    elif action == 'reconnect':
        arduino.close()
        ok = arduino.connect()
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
        "yellow_count": camera.yellow_count,
        "green_count": camera.green_count,
        "camera_enabled": system.cam_on,
        "arduino_connected": arduino.connected,
        "arduino_port": arduino.port
    })

@app.route('/data')
def data():
    return jsonify({
        "encoderX": system.x,
        "encoderY": system.y,
        "isMoving": system.moving,
        "mode": system.mode,
        "timedSequenceStep": system.step,
        "time": datetime.now().strftime("%H:%M:%S"),
        "alarms": system.alarms,
        "camera_enabled": system.cam_on,
        "yellow_detected": camera.yellow,
        "green_detected": camera.green,
        "detection_results": {"yellow_count": camera.yellow_count, "green_count": camera.green_count}
    })

@app.route('/motor')
def motor():
    if system.mode != "manual" or system.moving:
        return "Busy", 403

    d = request.args.get('dir')
    if d == 'xfwd':
        system.x += 100
    elif d == 'xback':
        system.x -= 100
    elif d == 'yfwd':
        system.y += 100
    elif d == 'yback':
        system.y -= 100
    elif d == 'stop':
        system.moving = False
    return "OK"

@app.route('/moveto')
def moveto():
    if system.moving:
        return "Busy", 403
    p = int(request.args.get('pos', 0))
    if p == 1:
        system.x, system.y = 0, 0
    elif p == 2:
        system.x, system.y = 0, -4000
    elif p == 3:
        system.x, system.y = -4000, 0
    elif p == 4:
        system.x, system.y = -4000, -4000
    return "OK"

@app.route('/setmode')
def setmode():
    m = request.args.get('mode')
    system.moving = False
    system.mode = "auto_sequence" if m == 'auto_sequence' else "manual"
    system.step = 0
    return "OK"

@app.route('/set-alarm')
def setalarm():
    s = int(request.args.get('slot', 0))
    t = request.args.get('alarmTime', '')
    if 0 <= s < 3:
        system.alarms[s] = {"isEnabled": True, "time": t}
    return "OK"

@app.route('/cancel-alarm')
def cancelalarm():
    s = int(request.args.get('slot', 0))
    if 0 <= s < 3:
        system.alarms[s] = {"isEnabled": False, "time": ""}
    return "OK"

@app.route('/reset')
def reset():
    system.x = system.y = 0
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
