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
        if not self.cam:
            return None
        if not self.cam.isOpened():
            return None

        ret, frame = self.cam.read()
        if not ret:
            return None

        # แปลงเป็นสี HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # หาสีเหลือง (เพิ่ม Saturation และ Value เพื่อไม่ให้เจอพื้นมืด)
        yellow_low = np.array([20, 100, 100])
        yellow_high = np.array([30, 255, 255])
        yellow_mask = cv2.inRange(hsv, yellow_low, yellow_high)
        yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # หาสีเขียว (เพิ่ม Saturation และ Value เพื่อไม่ให้เจอพื้นมืด)
        green_low = np.array([40, 80, 80])
        green_high = np.array([80, 255, 255])
        green_mask = cv2.inRange(hsv, green_low, green_high)
        green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # หาสีม่วง (เพิ่ม Saturation และ Value เพื่อไม่ให้เจอพื้นมืด)
        purple_low = np.array([125, 100, 100])
        purple_high = np.array([155, 255, 255])
        purple_mask = cv2.inRange(hsv, purple_low, purple_high)
        purple_contours, _ = cv2.findContours(purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # นับสีเหลือง
        self.yellow_count = 0
        for c in yellow_contours:
            area = cv2.contourArea(c)
            if area > 500:
                self.yellow_count = self.yellow_count + 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 255), 2)
                cv2.putText(frame, 'YELLOW', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # นับสีเขียว
        self.green_count = 0
        for c in green_contours:
            area = cv2.contourArea(c)
            if area > 500:
                self.green_count = self.green_count + 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, 'GREEN', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # นับสีม่วง
        self.purple_count = 0
        for c in purple_contours:
            area = cv2.contourArea(c)
            if area > 500:
                self.purple_count = self.purple_count + 1
                x, y, w, h = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 255), 2)
                cv2.putText(frame, 'PURPLE', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 255), 2)

        # เช็คว่าพบสีหรือไม่
        if self.yellow_count > 0:
            self.yellow = True
        else:
            self.yellow = False

        if self.green_count > 0:
            self.green = True
        else:
            self.green = False

        if self.purple_count > 0:
            self.purple = True
        else:
            self.purple = False

        # ดูสภาพพืช
        if self.yellow == True and self.green == False and self.purple == False:
            self.plant_status = "ขาดไนโตรเจน"
        elif self.purple == True and self.green == False and self.yellow == False:
            self.plant_status = "ขาดฟอสฟอรัส"
        elif self.yellow == True and self.purple == True:
            self.plant_status = "ขาดไนโตรเจนและฟอสฟอรัส"
        elif self.green == True and self.yellow == False and self.purple == False:
            self.plant_status = "พืชปกติ"
        elif self.green == True:
            self.plant_status = "พืชปกติบางส่วน มีอาการขาดธาตุบางส่วน"
        else:
            self.plant_status = "ไม่พบพืช"

        # เขียนข้อความบนภาพ
        text1 = "Y:" + str(self.yellow_count) + " G:" + str(self.green_count) + " P:" + str(self.purple_count)
        cv2.putText(frame, text1, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, self.plant_status, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

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
        # เตรียม port ที่จะลอง
        if port:
            ports = [port]
        else:
            ports = self.get_ports()

        # ลองเชื่อมต่อแต่ละ port
        for p in ports:
            try:
                print("กำลังเชื่อมต่อ " + p + "...")

                # เปิด port
                self.ser = serial.Serial(p, 115200, timeout=1)
                time.sleep(2)

                # ลบข้อมูลเก่า
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()

                # ลอง PING 2 ครั้ง
                success = False
                for i in range(2):
                    self.ser.write(b"PING\n")
                    time.sleep(0.5)

                    # ดูว่ามีข้อมูลกลับมาไหม
                    if self.ser.in_waiting > 0:
                        data = self.ser.readline()
                        response = data.decode('utf-8', errors='ignore').strip()
                        print("ได้: " + response)

                        # ถ้าได้ PONG กลับมา
                        if "PONG" in response:
                            self.connected = True
                            self.port = p
                            self.reading = True

                            # เริ่ม thread อ่านข้อมูล
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

        print("หา Arduino ไม่เจอ")
        return False

    def read_loop(self):
        # อ่านข้อมูลจาก Arduino ตลอดเวลา
        while self.reading == True and self.connected == True:
            try:
                # ถ้ามีข้อมูล
                if self.ser and self.ser.in_waiting > 0:
                    # อ่านข้อมูล
                    line = self.ser.readline()
                    data = line.decode('utf-8', errors='ignore').strip()

                    # ถ้าเป็นข้อมูล STATUS
                    if data.startswith("STATUS:"):
                        # ตัดคำว่า STATUS: ออก
                        data = data.replace("STATUS:", "")

                        # แยกด้วย ,
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
        # สร้าง alarm 3 ตัว
        self.alarms = []
        self.alarms.append({"isEnabled": False, "time": ""})
        self.alarms.append({"isEnabled": False, "time": ""})
        self.alarms.append({"isEnabled": False, "time": ""})
        self.cam_on = False

system = System()

# ฟังก์ชันส่งข้อมูลสี
def send_color_loop():
    last = 0
    while camera.running:
        try:
            if time.time() - last >= 1.0:
                if camera.yellow or camera.green or camera.purple:
                    # สร้างคำสั่งส่งข้อมูลสี
                    cmd = "COLOR:" + str(int(camera.yellow)) + "," + str(int(camera.green)) + "," + str(int(camera.purple)) + "," + str(camera.yellow_count) + "," + str(camera.green_count) + "," + str(camera.purple_count) + "\n"
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

# === เริ่มโปรแกรม ===
if __name__ == '__main__':
    print("\n" + "="*40)
    print("ESP32 Controller")
    print("="*40)

    camera.start()
    arduino.connect()

    # เริ่ม alarm checker
    start_alarm_check()

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
