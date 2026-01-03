import serial
import time
import threading

# --- CONFIGURARE PORTURI (MODIFICA AICI!) ---
# Vezi in Arduino IDE ce porturi COM au fiecare
mega_port = 'COM5'   # Exemplu: Unde e conectat Mega
esp_port = 'COM4'    # Exemplu: Unde e conectat ESP32
baud_rate = 115200

print(f"Conectez Arduino Mega pe {mega_port} si ESP32 pe {esp_port}...")

try:
    mega = serial.Serial(mega_port, baud_rate, timeout=0.1)
    esp = serial.Serial(esp_port, baud_rate, timeout=0.1)
    print("Conexiune reusita! Podul e activ. (Apasa Ctrl+C pentru oprire)")
except Exception as e:
    print(f"Eroare la conectare: {e}")
    exit()

def read_from_mega():
    while True:
        if mega.in_waiting:
            try:
                line = mega.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"[MEGA -> ESP]: {line}")
                    # Trimitem la ESP
                    esp.write((line + '\n').encode('utf-8'))
            except:
                pass

def read_from_esp():
    while True:
        if esp.in_waiting:
            try:
                line = esp.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"[ESP -> MEGA]: {line}")
                    # Trimitem inapoi la Mega (daca e cazul, ex: highscore)
                    mega.write((line + '\n').encode('utf-8'))
            except:
                pass

# Pornim doua "fire" de executie paralele
t1 = threading.Thread(target=read_from_mega)
t2 = threading.Thread(target=read_from_esp)
t1.daemon = True
t2.daemon = True
t1.start()
t2.start()

# Tinem programul deschis
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nOprire...")
    mega.close()
    esp.close()