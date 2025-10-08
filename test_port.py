import serial
import time

# ทดสอบเปิด COM4
try:
    print("กำลังทดสอบเปิด COM4...")
    ser = serial.Serial('COM4', 115200, timeout=1)
    print("✓ เปิด COM4 ได้")

    time.sleep(2)
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    print("ส่ง PING...")
    ser.write(b"PING\n")
    time.sleep(1)

    if ser.in_waiting > 0:
        response = ser.readline().decode('utf-8', errors='ignore').strip()
        print(f"ตอบ: {response}")
    else:
        print("ไม่มีข้อมูลกลับมา")

    ser.close()
    print("ปิด COM4 แล้ว")

except Exception as e:
    print(f"✗ ผิดพลาด: {e}")
