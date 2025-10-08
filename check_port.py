import serial.tools.list_ports

print("Available COM Ports:")
for port in serial.tools.list_ports.comports():
    print(f"  {port.device} - {port.description}")
