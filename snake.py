import pygame
import serial
import sys
import time

# ==========================================
#               CONFIGURARE
# ==========================================
MEGA_PORT = 'COM5'  # Verifica in Device Manager!
ESP_PORT = 'COM6'  # Verifica in Device Manager!
BAUD_RATE = 115200

# Setari Grafica Initiale (Se vor modifica de pe telefon)
BLOCK_SIZE = 30
GRID_W = 20
GRID_H = 10

# Culori
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (50, 50, 50)
BLUE = (50, 50, 255)

# Inițializare Pygame
pygame.init()
window_width = GRID_W * BLOCK_SIZE
window_height = GRID_H * BLOCK_SIZE
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Snake IoT - Ultimate Controller")
font = pygame.font.SysFont("arial", 20)
big_font = pygame.font.SysFont("arial", 40, bold=True)


# ==========================================
#          FUNCTII DE CONECTARE
# ==========================================
def init_connections():
    mega = None
    esp = None

    # 1. MEGA
    try:
        mega = serial.Serial(MEGA_PORT, BAUD_RATE, timeout=0.1)
        print(f"✅ MEGA conectat pe {MEGA_PORT}")
    except:
        print(f"❌ EROARE MEGA - Verifică portul {MEGA_PORT}!")
        sys.exit()

    # 2. ESP32
    try:
        esp = serial.Serial(ESP_PORT, BAUD_RATE, timeout=1)
        # CRITIC: Previne intrarea in mod programare (Download Mode)
        esp.dtr = False
        esp.rts = False
        print(f"✅ ESP32 conectat pe {ESP_PORT}")
    except:
        print(f"⚠️ ESP32 lipsă - se va juca offline")

    return mega, esp


# ==========================================
#          ECRAN DE INCARCARE
# ==========================================
def show_loading_screen(esp_ser):
    loading = True
    found_score = 0
    start_time = time.time()
    last_req_time = time.time()

    # Cerem scorul imediat ce intram
    if esp_ser:
        esp_ser.reset_input_buffer()
        esp_ser.write(b"GET_HIGHSCORE\n")

    snake_anim_x = -30

    while loading:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit();
                sys.exit()

        current_time = time.time()
        elapsed = current_time - start_time

        # Desenare Fundal
        screen.fill(BLACK)
        title_text = big_font.render("SNAKE IoT", True, GREEN)
        screen.blit(title_text, (window_width // 2 - 90, window_height // 2 - 80))

        if esp_ser:
            status_text = font.render("Sincronizare Cloud...", True, WHITE)
            ip_hint = font.render("(Verifica IP in consola pentru telefon)", True, GRAY)
            screen.blit(ip_hint, (window_width // 2 - 120, window_height // 2 + 80))
        else:
            status_text = font.render("Mod Offline", True, GRAY)
            pygame.display.update()
            time.sleep(1.5)
            return 0

        screen.blit(status_text, (window_width // 2 - 80, window_height // 2 + 50))

        # Animatie Bara
        snake_anim_x += 5
        if snake_anim_x > window_width: snake_anim_x = -30
        pygame.draw.rect(screen, GRAY, (50, window_height // 2, window_width - 100, 20), 2)
        pygame.draw.rect(screen, GREEN, (50 + (elapsed * 50) % (window_width - 150), window_height // 2 + 2, 40, 16))

        # LOGICA ESP32 (In timpul incarcarii)
        if esp_ser:
            # A. Verificam daca a venit raspunsul
            if esp_ser.in_waiting:
                try:
                    lines = esp_ser.read_all().decode('utf-8', errors='ignore').split('\n')
                    for line in lines:
                        line = line.strip()
                        # Verificam Highscore
                        if line.startswith("HIGHSCORE:"):
                            try:
                                found_score = int(line.split(":")[1])
                                print(f"🏆 SCOR INITIAL GASIT: {found_score}")
                                loading = False
                            except:
                                pass
                        # Afisam IP-ul daca il prindem
                        elif "IP PENTRU TELEFON" in line:
                            print(f"📡 {line}")
                except:
                    pass

            # B. Retry la fiecare 2 secunde
            if current_time - last_req_time > 2.0:
                print("🔄 Retry connect...")
                esp_ser.write(b"GET_HIGHSCORE\n")
                last_req_time = current_time

        # Timeout 10 secunde
        if elapsed > 10.0:
            print("⚠️ Timeout. Jucam cu 0.")
            loading = False

        pygame.display.update()
        pygame.time.delay(30)

    return found_score


# ==========================================
#               MAIN PROGRAM
# ==========================================

# 1. Initializare
mega_ser, esp_ser = init_connections()
high_score = show_loading_screen(esp_ser)

# 2. Configurare Fereastra Joc Initiala
pygame.display.set_caption(f"Snake IoT - Best: {high_score}")
print("🚀 GATA! Incepem jocul.")

# 3. Curatenie Buffer Mega (ca sa nu avem lag la start)
mega_ser.reset_input_buffer()

running = True
current_score = 0
game_over_state = False

# 4. Loop Principal
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    # --- A. CITIM DE LA MEGA (JOCUL) ---
    if mega_ser.in_waiting:
        try:
            line = mega_ser.readline().decode('utf-8', errors='ignore').strip()

            # 1. DATE GRAFICE
            if line.startswith("DATA:"):
                try:
                    content = line.split("DATA:")[1]
                    parts = content.split(";")
                    if len(parts) >= 5:
                        food_coords = parts[0].split(',')
                        food_x, food_y = int(food_coords[0]), int(food_coords[1])

                        snake_len = int(parts[1])
                        snake_raw = list(map(int, parts[2].split(',')))
                        snake_body = [(snake_raw[i], snake_raw[i + 1]) for i in range(0, len(snake_raw), 2)]

                        current_score = int(parts[3])
                        game_over_state = int(parts[4]) == 1

                        # DESENARE
                        screen.fill(BLACK)

                        # Mâncare
                        pygame.draw.rect(screen, RED,
                                         (food_x * BLOCK_SIZE, food_y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

                        # Sarpe (Patrat PLIN + Contur)
                        for s in snake_body:
                            pygame.draw.rect(screen, GREEN,
                                             (s[0] * BLOCK_SIZE, s[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))  # Plin
                            pygame.draw.rect(screen, BLACK,
                                             (s[0] * BLOCK_SIZE, s[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                                             1)  # Contur

                        # HUD (Text)
                        score_txt = font.render(f"Scor: {current_score}", True, WHITE)
                        hs_txt = font.render(f"Best: {high_score}", True, BLUE)
                        screen.blit(score_txt, (10, 10))
                        screen.blit(hs_txt, (window_width - 100, 10))

                        if game_over_state:
                            msg = font.render("GAME OVER", True, WHITE)
                            screen.blit(msg, (window_width // 2 - 50, window_height // 2))

                        pygame.display.update()
                except:
                    pass

            # 2. SALVARE SCOR (GAME OVER)
            elif line.startswith("SET_SCORE:"):
                try:
                    val = int(line.split(":")[1])
                    # Verificam daca e record
                    if val > high_score:
                        if esp_ser:
                            print(f"🏆 RECORD NOU: {val} -> Trimit la Cloud")
                            esp_ser.write((line + "\n").encode())
                            high_score = val  # Update local instant
                    else:
                        print(f"📉 Scor {val} sub recordul {high_score}")
                except:
                    pass

        except:
            pass

    # --- B. CITIM DE LA ESP32 (WEB & DATABASE) ---
    if esp_ser and esp_ser.in_waiting:
        try:
            r = esp_ser.readline().decode('utf-8', errors='ignore').strip()

            # 1. Comanda de pe Telefon (CONFIG:LEVEL=x;SPEED=y;GRID=w,h)
            if r.startswith("CONFIG:"):
                print(f"📲 Setari noi: {r}")
                try:
                    parts = r.split(";")

                    # 1. Extragem valorile
                    # level_part = parts[0].split("=")[1] (Nu ne trebuie in Python, doar pt ESP)
                    speed_part = parts[1].split("=")[1]
                    grid_part = parts[2].split("=")[1]  # "30,20"

                    # 2. Trimitem la Mega (Viteza si Grid)
                    mega_ser.write(f"SET_SPEED:{speed_part}\n".encode())
                    time.sleep(0.1)  # Mica pauza ca sa nu se inece Mega
                    mega_ser.write(f"SET_GRID:{grid_part}\n".encode())

                    # 3. REDIMENSIONAM FEREASTRA PYTHON
                    w_str, h_str = grid_part.split(",")
                    GRID_W = int(w_str)
                    GRID_H = int(h_str)

                    # Recalculam pixelii
                    window_width = GRID_W * BLOCK_SIZE
                    window_height = GRID_H * BLOCK_SIZE

                    # Reconstruim ecranul
                    screen = pygame.display.set_mode((window_width, window_height))
                    print(f"🖥️ Ecran redimensionat la {GRID_W}x{GRID_H}")

                    # 4. Resetam Highscore (pentru noul nivel)
                    esp_ser.write(b"GET_HIGHSCORE\n")
                    high_score = 0

                    # 5. Curatam bufferul Mega ca sa dispara datele vechi de pe harta veche
                    time.sleep(0.1)
                    mega_ser.reset_input_buffer()

                except Exception as e:
                    print(f"Eroare setari: {e}")

            # 2. Primire Highscore Nou
            elif r.startswith("HIGHSCORE:"):
                try:
                    high_score = int(r.split(":")[1])
                    print(f"✅ Highscore incarcat: {high_score}")
                except:
                    pass

            # Debug IP (sa il vezi in consola daca l-ai ratat)
            elif "IP PENTRU TELEFON" in r:
                print(f"🌐 {r}")

        except:
            pass

pygame.quit()
mega_ser.close()
if esp_ser: esp_ser.close()