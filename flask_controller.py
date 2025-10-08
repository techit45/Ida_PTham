from flask import Flask, render_template, jsonify, request, Response
from datetime import datetime
import cv2
import numpy as np
import serial
import threading
import time
import glob

app = Flask(__name__)

# === IMAGE PROCESSOR ===
class ImageProcessor:
    def __init__(self):
        self.camera = None
        self.is_running = False
        self.yellow_detected = False
        self.green_detected = False
        self.detection_results = {"yellow_count": 0, "green_count": 0}

    def initialize_camera(self):
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                return False
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.is_running = True
            print("Camera initialized")
            return True
        except Exception as e:
            print(f"Camera error: {e}")
            return False

    def detect_colors(self, frame):
        if frame is None:
            return frame, False, False

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Color ranges
        yellow_mask = cv2.inRange(hsv, np.array([20, 50, 50]), np.array([30, 255, 255]))
        green_mask = cv2.inRange(hsv, np.array([40, 50, 50]), np.array([80, 255, 255]))

        # Find contours
        yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_area = 500
        yellow_count = green_count = 0

        # Process yellow
        for contour in yellow_contours:
            if cv2.contourArea(contour) > min_area:
                yellow_count += 1
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                cv2.putText(frame, 'YELLOW', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Process green
        for contour in green_contours:
            if cv2.contourArea(contour) > min_area:
                green_count += 1
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, 'GREEN', (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        self.detection_results = {"yellow_count": yellow_count, "green_count": green_count}
        cv2.putText(frame, f"Y:{yellow_count} G:{green_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame, yellow_count > 0, green_count > 0

    def get_frame(self):
        if not self.camera or not self.camera.isOpened():
            return None

        ret, frame = self.camera.read()
        if not ret:
            return None

        processed_frame, self.yellow_detected, self.green_detected = self.detect_colors(frame)
        return processed_frame

    def release_camera(self):
        self.is_running = False
        if self.camera:
            try:
                self.camera.release()
                # Give time for camera to properly release
                time.sleep(0.5)
                print("Camera released")
            except Exception as e:
                print(f"Camera release error: {e}")
            finally:
                self.camera = None

# === ARDUINO CONTROLLER ===
class ArduinoController:
    def __init__(self, baudrate=115200):
        self.port = None
        self.baudrate = baudrate
        self.serial_connection = None
        self.is_connected = False
        self.last_ping = 0

    def find_arduino_port(self):
        try:
            import serial.tools.list_ports
            for port in serial.tools.list_ports.comports():
                desc = port.description.lower()
                if any(x in desc for x in ['arduino', 'ch340', 'cp210']):
                    return port.device
        except:
            pass

        # Fallback patterns
        for pattern in ['/dev/ttyUSB*', '/dev/ttyACM*', '/dev/cu.usbserial*', '/dev/cu.usbmodem*']:
            ports = glob.glob(pattern)
            if ports:
                return ports[0]
        return None

    def connect(self):
        auto_port = self.find_arduino_port()
        ports_to_try = [auto_port] if auto_port else []
        ports_to_try += ['/dev/ttyUSB0', '/dev/ttyACM0', '/dev/cu.usbserial-1410']

        for port in ports_to_try:
            try:
                print(f"Trying {port}...")
                self.serial_connection = serial.Serial(port, self.baudrate, timeout=1)
                time.sleep(2)

                self.serial_connection.write(b"PING\n")
                if self.serial_connection.readline().decode().strip() == "PONG":
                    self.is_connected = True
                    self.port = port
                    self.last_ping = time.time()
                    print(f"Connected to {port}")
                    return True
                self.serial_connection.close()
            except:
                if self.serial_connection:
                    self.serial_connection.close()
                continue

        print("Arduino not found - simulation mode")
        return False

    def send_detection_data(self, yellow, green, y_count, g_count):
        if not self.is_connected or not self.serial_connection:
            return False
        try:
            cmd = f"COLOR:{int(yellow)},{int(green)},{y_count},{g_count}\n"
            self.serial_connection.write(cmd.encode())
            return True
        except:
            self.is_connected = False
            return False

    def send_detection_data(self, yellow_detected, green_detected, yellow_count, green_count):
        """Send color detection data to Arduino"""
        if not self.is_connected or not self.serial_connection:
            return False
        
        try:
            command = f"COLOR:{int(yellow_detected)},{int(green_detected)},{yellow_count},{green_count}\n"
            self.serial_connection.write(command.encode())
            return True
        except Exception as e:
            print(f"Error sending data to Arduino: {e}")
            self.is_connected = False
            return False

    def send_motor_command(self, command):
        if not self.is_connected or not self.serial_connection:
            return False
        try:
            self.serial_connection.write(f"MOTOR:{command}\n".encode())
            return True
        except:
            return False

    def disconnect(self):
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except:
                pass
            self.is_connected = False

# === SYSTEM STATE ===
class SystemState:
    def __init__(self):
        self.encoder_x = 0
        self.encoder_y = 0
        self.is_moving = False
        self.mode = "manual"
        self.timed_sequence_step = 0
        self.alarms = [{"isEnabled": False, "time": ""} for _ in range(3)]
        self.camera_enabled = False
        self.yellow_detected = False
        self.green_detected = False
        self.detection_results = {"yellow_count": 0, "green_count": 0}

    def set_alarm(self, slot, time_str):
        if 0 <= slot < 3:
            self.alarms[slot] = {"isEnabled": True, "time": time_str}

    def cancel_alarm(self, slot):
        if 0 <= slot < 3:
            self.alarms[slot] = {"isEnabled": False, "time": ""}

# === INITIALIZE ===
system = SystemState()
image_processor = ImageProcessor()
arduino_controller = ArduinoController()

def initialize_components():
    if image_processor.initialize_camera():
        system.camera_enabled = True
        # Start background detection thread
        detection_thread = threading.Thread(target=continuous_detection, daemon=True)
        detection_thread.start()
    arduino_controller.connect()

def continuous_detection():
    """Continuous color detection and Arduino communication"""
    last_send_time = 0
    
    while image_processor.is_running:
        try:
            current_time = time.time()
            
            # Get frame and process
            frame = image_processor.get_frame()
            if frame is not None:
                # Update system state with detection results
                system.yellow_detected = image_processor.yellow_detected
                system.green_detected = image_processor.green_detected
                system.detection_results = image_processor.detection_results
                
                # Send data to Arduino every 1 second to avoid flooding
                if current_time - last_send_time >= 1.0:
                    success = arduino_controller.send_detection_data(
                        system.yellow_detected,
                        system.green_detected,
                        system.detection_results["yellow_count"],
                        system.detection_results["green_count"]
                    )
                    if success:
                        last_send_time = current_time
            
            time.sleep(0.1)  # 100ms delay for responsive detection
            
        except Exception as e:
            print(f"Error in continuous detection: {e}")
            time.sleep(1)

def generate_frames():
    """Generate camera frames for streaming"""
    while True:
        try:
            if not system.camera_enabled or not image_processor.is_running:
                # Generate a placeholder frame
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(frame, 'Camera Not Available', (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            else:
                frame = image_processor.get_frame()
                if frame is None:
                    frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(frame, 'Camera Error', (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            else:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in generate_frames: {e}")
            time.sleep(0.5)

def continuous_detection():
    last_send = 0
    while image_processor.is_running:
        try:
            frame = image_processor.get_frame()
            if frame is not None:
                system.yellow_detected = image_processor.yellow_detected
                system.green_detected = image_processor.green_detected
                system.detection_results = image_processor.detection_results

                if time.time() - last_send >= 1.0:
                    if arduino_controller.send_detection_data(
                        system.yellow_detected, system.green_detected,
                        system.detection_results["yellow_count"],
                        system.detection_results["green_count"]):
                        last_send = time.time()
            time.sleep(0.1)
        except:
            time.sleep(1)

def generate_frames():
    while True:
        if system.camera_enabled:
            frame = image_processor.get_frame()
        else:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, 'Camera Off', (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        if frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# === ROUTES ===
@app.route('/')
def index():
    return render_template('web_interface.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera_control')
def camera_control():
    action = request.args.get('action')
    if action == 'start' and not system.camera_enabled:
        if image_processor.initialize_camera():
            system.camera_enabled = True
            threading.Thread(target=continuous_detection, daemon=True).start()
            return jsonify({"status": "success"})
    elif action == 'stop' and system.camera_enabled:
        image_processor.release_camera()
        system.camera_enabled = False
        return jsonify({"status": "success"})
    return jsonify({"status": "error"})

@app.route('/arduino_control')
def arduino_control():
    action = request.args.get('action')
    if action == 'reconnect':
        arduino_controller.disconnect()
        success = arduino_controller.connect()
        return jsonify({"status": "success" if success else "error",
                       "connected": success, "port": arduino_controller.port})
    elif action in ['X_FWD', 'X_BACK', 'Y_FWD', 'Y_BACK', 'STOP']:
        success = arduino_controller.send_motor_command(action)
        return jsonify({"status": "success" if success else "error"})
    return jsonify({"status": "error"})

@app.route('/detection_data')
def get_detection_data():
    return jsonify({
        "yellow_detected": system.yellow_detected,
        "green_detected": system.green_detected,
        "yellow_count": system.detection_results["yellow_count"],
        "green_count": system.detection_results["green_count"],
        "camera_enabled": system.camera_enabled,
        "arduino_connected": arduino_controller.is_connected,
        "arduino_port": arduino_controller.port
    })

@app.route('/data')
def get_data():
    return jsonify({
        "encoderX": system.encoder_x,
        "encoderY": system.encoder_y,
        "isMoving": system.is_moving,
        "mode": system.mode,
        "timedSequenceStep": system.timed_sequence_step,
        "time": datetime.now().strftime("%H:%M:%S"),
        "alarms": system.alarms,
        "camera_enabled": system.camera_enabled,
        "yellow_detected": system.yellow_detected,
        "green_detected": system.green_detected,
        "detection_results": system.detection_results
    })

@app.route('/motor')
def motor_control():
    if system.mode != "manual" or system.is_moving:
        return "Busy", 403

    direction = request.args.get('dir')
    if direction in ['xfwd', 'xback', 'yfwd', 'yback']:
        system.encoder_x += 100 if direction == 'xfwd' else (-100 if direction == 'xback' else 0)
        system.encoder_y += 100 if direction == 'yfwd' else (-100 if direction == 'yback' else 0)
    elif direction == 'stop':
        system.is_moving = False
        system.mode = "manual"
    return "OK"

@app.route('/moveto')
def move_to():
    if system.is_moving:
        return "Busy", 403
    pos = int(request.args.get('pos', 0))
    positions = {1: (0, 0), 2: (0, -4000), 3: (-4000, 0), 4: (-4000, -4000)}
    if pos in positions:
        system.encoder_x, system.encoder_y = positions[pos]
    return "OK"

@app.route('/setmode')
def set_mode():
    mode = request.args.get('mode')
    system.is_moving = False
    system.mode = "auto_sequence" if mode == 'auto_sequence' else "manual"
    system.timed_sequence_step = 0
    return "OK"

@app.route('/set-alarm')
def set_alarm():
    slot = int(request.args.get('slot', 0))
    alarm_time = request.args.get('alarmTime', '')
    system.set_alarm(slot, alarm_time)
    return "OK"

@app.route('/cancel-alarm')
def cancel_alarm():
    slot = int(request.args.get('slot', 0))
    system.cancel_alarm(slot)
    return "OK"

@app.route('/reset')
def reset():
    system.encoder_x = system.encoder_y = 0
    return "OK"

# === MAIN ===
def cleanup_resources():
    """Clean up resources properly"""
    try:
        if system.camera_enabled:
            image_processor.release_camera()
        arduino_controller.disconnect()
        # Force cleanup of OpenCV resources
        cv2.destroyAllWindows()
        print("Resources cleaned up")
    except Exception as e:
        print(f"Cleanup error: {e}")

if __name__ == '__main__':
    initialize_components()
    try:
        app.run(debug=True, host='0.0.0.0', port=5001, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        cleanup_resources()
