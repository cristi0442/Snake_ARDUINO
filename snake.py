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
BLUE = (50, 50, 255)  # Culoare pentru Highscore

# Variabile Joc
high_score = 0  # Aici vom stoca recordul venit de pe net

# Inițializare Pygame
pygame.init()
window_width = GRID_W * BLOCK_SIZE
window_height = GRID_H * BLOCK_SIZE
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Snake IoT - Highscore System")
font = pygame.font.SysFont("arial", 20)

# --- 1. CONECTARE ARDUINO MEGA ---
try:
    mega_ser = serial.Serial(MEGA_PORT, BAUD_RATE, timeout=0.1)
    print(f"✅ Conectat la MEGA pe {MEGA_PORT}")
except Exception as e:
    print(f"❌ Eroare conectare MEGA ({MEGA_PORT}): {e}")
    sys.exit()

# --- 2. CONECTARE ESP32 ---
esp_ser = None
try:
    esp_ser = serial.Serial(ESP_PORT, BAUD_RATE, timeout=1)

    # FORTAM pinii de control sa fie opriti (ca sa nu intre in Download Mode)
    esp_ser.dtr = False
    esp_ser.rts = False

    print(f"✅ ESP32 conectat pe {ESP_PORT}")
    print("⏳ Asteptam 10 secunde ca ESP32 sa porneasca...")
    time.sleep(10)

    # Curatam bufferul ca sa nu citim gunoaie vechi
    esp_ser.reset_input_buffer()

    # === CEREM HIGHSCORE-UL LA PORNIRE ===
    print("📥 Cer Highscore-ul din cloud...")
    esp_ser.write(b"GET_HIGHSCORE\n")

    print("🚀 GATA! Poti juca.")

except Exception as e:
    print(f"⚠️ ATENTIE: Nu m-am putut conecta la ESP32 pe {ESP_PORT}.")
    print(f"   Eroare: {e}")

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
            line = mega_ser.readline().decode('utf-8', errors='ignore').strip()

            # CAZUL A: Primim date de desenare (DATA:...)
            if line.startswith("DATA:"):
                try:
                    content = line.split("DATA:")[1]
                    parts = content.split(";")

                    if len(parts) >= 5:
                        # 1. Parsing date
                        food_coords = parts[0].split(',')
                        food_x = int(food_coords[0])
                        food_y = int(food_coords[1])

                        snake_len = int(parts[1])
                        snake_raw = parts[2].split(',')
                        snake_body = []
                        if len(snake_raw) >= 2:
                            for i in range(0, len(snake_raw), 2):
                                if i + 1 < len(snake_raw):
                                    snake_body.append((int(snake_raw[i]), int(snake_raw[i + 1])))

                        current_score = int(parts[3])
                        game_over_state = int(parts[4]) == 1

                        # 2. Desenare
                        screen.fill(BLACK)

                        # Mâncare
                        pygame.draw.rect(screen, RED,
                                         (food_x * BLOCK_SIZE, food_y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

                        # Șarpe
                        for segment in snake_body:
                            pygame.draw.rect(screen, GREEN,
                                             (segment[0] * BLOCK_SIZE, segment[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                            pygame.draw.rect(screen, BLACK,
                                             (segment[0] * BLOCK_SIZE, segment[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE),
                                             1)

                        # Text Scor Curent (Stanga)
                        score_text = font.render(f"Scor: {current_score}", True, WHITE)
                        screen.blit(score_text, (10, 10))

                        # === Text High Score (Dreapta) ===
                        hs_text = font.render(f"Best: {high_score}", True, BLUE)
                        screen.blit(hs_text, (window_width - 100, 10))
                        # =================================

                        # Game Over Overlay
                        if game_over_state:
                            over_text = font.render("GAME OVER", True, WHITE)
                            text_rect = over_text.get_rect(center=(window_width / 2, window_height / 2))
                            screen.blit(over_text, text_rect)

                        pygame.display.update()
                except:
                    pass

            # CAZUL B: Primim comanda de scor la final de joc (SET_SCORE:...)
            elif line.startswith("SET_SCORE:"):
                print(f"🎯 Primit de la Mega: {line}")

                # Parsam scorul primit
                try:
                    valoare_primita = int(line.split(":")[1])
                except:
                    valoare_primita = 0

                # === LOGICA DE COMPARARE ===
                if valoare_primita > high_score:
                    print(f"🏆 RECORD NOU! ({valoare_primita} > {high_score}) -> Trimit la Cloud...")

                    if esp_ser:
                        mesaj_complet = line + "\n"
                        esp_ser.write(mesaj_complet.encode('utf-8'))
                        esp_ser.flush()

                        # Actualizam local recordul imediat
                        high_score = valoare_primita
                    else:
                        print("❌ Nu pot trimite (ESP32 deconectat)")
                else:
                    print(f"📉 Scor prea mic pentru upload. (Record actual: {high_score})")
                # ===========================

        except Exception as e:
            pass

    # --- Verificam daca ESP32 ne raspunde (Highscore sau confirmare upload) ---
    if esp_ser and esp_ser.in_waiting > 0:
        try:
            esp_line = esp_ser.readline().decode('utf-8', errors='ignore').strip()
            if esp_line:
                print(f"[ESP32 Răspunde]: {esp_line}")

                # Daca primim Highscore-ul de la ESP (la pornire)
                if esp_line.startswith("HIGHSCORE:"):
                    try:
                        val = int(esp_line.split(":")[1])
                        high_score = val
                        print(f"✅ Highscore actualizat din cloud: {high_score}")
                    except:
                        pass
        except:
            pass

pygame.quit()
mega_ser.close()
if esp_ser:
    esp_ser.close()