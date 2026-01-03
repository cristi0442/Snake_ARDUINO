import pygame
import serial
import sys
import time


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

# Inițializare Pygame
pygame.init()
window_width = GRID_W * BLOCK_SIZE
window_height = GRID_H * BLOCK_SIZE
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Snake IoT - Mega & ESP32 Bridge")
font = pygame.font.SysFont("arial", 20)

# --- 1. CONECTARE ARDUINO MEGA ---
try:
    mega_ser = serial.Serial(MEGA_PORT, BAUD_RATE, timeout=0.1)
    print(f"✅ Conectat la MEGA pe {MEGA_PORT}")
except Exception as e:
    print(f"❌ Eroare conectare MEGA ({MEGA_PORT}): {e}")
    print("Verifica cablul sau portul!")
    sys.exit()

# --- 2. CONECTARE ESP32 ---
esp_ser = None
try:
    esp_ser = serial.Serial(ESP_PORT, BAUD_RATE, timeout=1)

    # 2. FORTAM pinii de control sa fie opriti (ca sa nu intre in Download Mode)
    esp_ser.dtr = False
    esp_ser.rts = False

    print(f"✅ ESP32 conectat pe {ESP_PORT}")

    print("⏳ Asteptam 4 secunde ca ESP32 sa porneasca...")
    time.sleep(4)

    print("🚀 GATA! Poti juca.")
except Exception as e:
    print(f"⚠️ ATENTIE: Nu m-am putut conecta la ESP32 pe {ESP_PORT}.")
    print(f"   Eroare: {e}")
    print("   Jocul va merge, dar scorul NU se va salva online.")

running = True
current_score = 0
game_over_state = False

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- CITIRE DATE DE LA ARDUINO MEGA ---
    if mega_ser.in_waiting > 0:
        try:
            # Citim linia
            line = mega_ser.readline().decode('utf-8', errors='ignore').strip()

            # CAZUL A: Primim date de desenare (DATA:...)
            if line.startswith("DATA:"):
                # Eliminăm prefixul "DATA:"
                content = line.split("DATA:")[1]
                parts = content.split(";")

                # Format: FoodXY; Len; SnakeCoords; Score; GameOver
                if len(parts) >= 5:
                    # 1. Mâncarea
                    food_coords = parts[0].split(',')
                    food_x = int(food_coords[0])
                    food_y = int(food_coords[1])

                    # 2. Șarpele
                    snake_len = int(parts[1])
                    snake_raw = parts[2].split(',')
                    snake_body = []
                    if len(snake_raw) >= 2:
                        for i in range(0, len(snake_raw), 2):
                            if i + 1 < len(snake_raw):
                                snake_body.append((int(snake_raw[i]), int(snake_raw[i + 1])))

                    # 3. Scor și Game Over
                    current_score = int(parts[3])
                    game_over_state = int(parts[4]) == 1

                    # --- DESENARE ---
                    screen.fill(BLACK)

                    # Mâncare
                    pygame.draw.rect(screen, RED, (food_x * BLOCK_SIZE, food_y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

                    # Șarpe
                    for segment in snake_body:
                        pygame.draw.rect(screen, GREEN,
                                         (segment[0] * BLOCK_SIZE, segment[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                        pygame.draw.rect(screen, BLACK,
                                         (segment[0] * BLOCK_SIZE, segment[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

                    # Text Scor
                    score_text = font.render(f"Scor: {current_score}", True, WHITE)
                    screen.blit(score_text, (10, 10))

                    # Text Game Over
                    if game_over_state:
                        over_text = font.render("GAME OVER", True, WHITE)
                        text_rect = over_text.get_rect(center=(window_width / 2, window_height / 2))
                        screen.blit(over_text, text_rect)

                        sub_text = font.render("Scorul se trimite in cloud...", True, GRAY)
                        screen.blit(sub_text, (window_width / 2 - 100, window_height / 2 + 30))

                    pygame.display.update()

            # CAZUL B: Primim comanda de scor (SET_SCORE:...)
            elif line.startswith("SET_SCORE:"):
                print(f"🎯 Primit de la Mega: {line}")

                if esp_ser:
                    mesaj_complet = line + "\n"

                    print(f"📡 Trimit la ESP32: {mesaj_complet.strip()}")
                    esp_ser.write(mesaj_complet.encode('utf-8'))
                    esp_ser.flush()  # Fortam trimiterea imediata din buffer

                    # Asteptam putin raspunsul pentru debug
                    time.sleep(0.5)
                else:
                    print("❌ Nu pot trimite la cloud (ESP32 deconectat)")


        except Exception as e:
            # Erori de citire serială ocazionale
            pass

    # --- Verificam daca ESP32 ne raspunde ---
    if esp_ser and esp_ser.in_waiting > 0:
        try:
            esp_line = esp_ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"[ESP32 Răspunde]: {esp_line}")
        except:
            pass

pygame.quit()
mega_ser.close()
if esp_ser:
    esp_ser.close()