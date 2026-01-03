import pygame
import serial
import sys
import time

# === CONFIGURARE ===
MEGA_PORT = 'COM5'
ESP_PORT = 'COM6'
BAUD_RATE = 115200

# Setari Grafica
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
pygame.display.set_caption("Snake IoT - Loading...")
font = pygame.font.SysFont("arial", 20)
big_font = pygame.font.SysFont("arial", 40, bold=True)


# --- FUNCTIE CONECTARE HARDWARE ---
def init_connections():
    mega = None
    esp = None

    # 1. MEGA
    try:
        mega = serial.Serial(MEGA_PORT, BAUD_RATE, timeout=0.1)
        print(f"✅ MEGA conectat")
    except:
        print(f"❌ EROARE MEGA - Verifică portul!")
        sys.exit()

    # 2. ESP32
    try:
        esp = serial.Serial(ESP_PORT, BAUD_RATE, timeout=1)
        esp.dtr = False
        esp.rts = False
        print(f"✅ ESP32 conectat")
    except:
        print(f"⚠️ ESP32 lipsă - se va juca offline")

    return mega, esp


# --- FUNCTIE ECRAN INCARCARE (ANIMATIE) ---
def show_loading_screen(esp_ser):
    loading = True
    found_score = 0
    start_time = time.time()
    last_req_time = time.time()

    # Cerem scorul imediat
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
            status_text = font.render("Conectare la Cloud...", True, WHITE)
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

        # COMUNICARE ESP32
        if esp_ser:
            if esp_ser.in_waiting:
                try:
                    lines = esp_ser.read_all().decode('utf-8', errors='ignore').split('\n')
                    for line in lines:
                        if line.strip().startswith("HIGHSCORE:"):
                            try:
                                found_score = int(line.strip().split(":")[1])
                                print(f"🏆 SCOR GASIT: {found_score}")
                                loading = False
                            except:
                                pass
                except:
                    pass

            if current_time - last_req_time > 2.0:
                print("🔄 Retry connect...")
                esp_ser.write(b"GET_HIGHSCORE\n")
                last_req_time = current_time

        if elapsed > 15.0:  # Timeout redus la 8 secunde
            print("⚠️ Timeout. Jucam cu 0.")
            loading = False

        pygame.display.update()
        pygame.time.delay(30)

    return found_score


# ==========================================
#               MAIN PROGRAM
# ==========================================

mega_ser, esp_ser = init_connections()
high_score = show_loading_screen(esp_ser)

# Configurare joc
pygame.display.set_caption(f"Snake IoT - Best: {high_score}")
print("🚀 GATA! Incepem jocul.")

# CURATAM BUFFERUL MEGA ===

mega_ser.reset_input_buffer()


running = True
current_score = 0
game_over_state = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    # --- A. MEGA (Jocul) ---
    if mega_ser.in_waiting:
        try:
            line = mega_ser.readline().decode('utf-8', errors='ignore').strip()

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

                        # === DESENARE ===
                        screen.fill(BLACK)

                        # Mâncare
                        pygame.draw.rect(screen, RED, (food_x * 30, food_y * 30, 30, 30))

                        # Sarpe (REPARAT: Acum desenam un patrat PLIN, nu doar contur)
                        for s in snake_body:
                            # 1. Patratul Verde (Plin)
                            pygame.draw.rect(screen, GREEN, (s[0] * 30, s[1] * 30, 30, 30))
                            # 2. Contur Negru (pentru aspect)
                            pygame.draw.rect(screen, BLACK, (s[0] * 30, s[1] * 30, 30, 30), 1)

                        # HUD
                        score_txt = font.render(f"Scor: {current_score}", True, WHITE)
                        hs_txt = font.render(f"Best: {high_score}", True, BLUE)
                        screen.blit(score_txt, (10, 10))
                        screen.blit(hs_txt, (window_width - 100, 10))

                        if game_over_state:
                            msg = font.render("GAME OVER", True, WHITE)
                            screen.blit(msg, (window_width // 2 - 50, window_height // 2))

                        pygame.display.update()
                except Exception as e:
                    pass

            elif line.startswith("SET_SCORE:"):
                try:
                    val = int(line.split(":")[1])
                    if val > high_score:
                        if esp_ser:
                            print(f"🏆 RECORD NOU: {val}")
                            esp_ser.write((line + "\n").encode())
                            high_score = val
                except:
                    pass

        except:
            pass

    # --- B. ESP32 (Update) ---
    if esp_ser and esp_ser.in_waiting:
        try:
            r = esp_ser.readline().decode().strip()
            if r.startswith("HIGHSCORE:"):
                high_score = int(r.split(":")[1])
        except:
            pass

pygame.quit()
mega_ser.close()
if esp_ser:
    esp_ser.close()