import pygame
import serial
import sys
import time

# --- CONFIGURARE ---
MEGA_PORT = 'COM5'  # <--- VERIFICA PORTUL
ESP_PORT = 'COM6'  # <--- VERIFICA PORTUL
BAUD_RATE = 115200

BLOCK_SIZE = 30
GRID_W = 20
GRID_H = 10
UI_HEIGHT = 60  # Inaltime bara Scor

# CULORI
BLACK = (0, 0, 0);
WHITE = (255, 255, 255);
GREEN = (0, 255, 0);
RED = (255, 0, 0);
BLUE = (50, 50, 255);
CYAN = (0, 255, 255);
MAGENTA = (255, 0, 255);
YELLOW = (255, 255, 0);
DARK_GRAY = (30, 30, 30);
GRAY = (50, 50, 50);
ORANGE = (255, 165, 0)

CURRENT_SNAKE_COLOR = GREEN

pygame.init()
window_width = GRID_W * BLOCK_SIZE
window_height = (GRID_H * BLOCK_SIZE) + UI_HEIGHT
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Snake IoT - Ultimate")
font = pygame.font.SysFont("arial", 20)
big_font = pygame.font.SysFont("arial", 40, bold=True)
notif_font = pygame.font.SysFont("arial", 28, bold=True)


# --- CONEXIUNI ---
def init_connections():
    mega = None;
    esp = None
    try:
        mega = serial.Serial(MEGA_PORT, BAUD_RATE, timeout=0.1)
        print(f"✅ MEGA conectat")
    except:
        sys.exit()
    try:
        esp = serial.Serial(ESP_PORT, BAUD_RATE, timeout=1)
        esp.dtr = False;
        esp.rts = False
        print(f"✅ ESP32 conectat")
    except:
        pass
    return mega, esp


# --- LOADING SCREEN ---
def show_loading_screen(esp_ser):
    loading = True;
    found_score = 0;
    start_time = time.time();
    last_req_time = time.time()
    if esp_ser: esp_ser.reset_input_buffer(); esp_ser.write(b"GET_HIGHSCORE\n")
    snake_anim_x = -30

    while loading:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        elapsed = time.time() - start_time

        screen.fill(BLACK)
        screen.blit(big_font.render("SNAKE IoT", True, CURRENT_SNAKE_COLOR),
                    (window_width // 2 - 90, window_height // 2 - 80))

        if esp_ser:
            screen.blit(font.render("Sincronizare Cloud...", True, WHITE),
                        (window_width // 2 - 80, window_height // 2 + 50))
            if esp_ser.in_waiting:
                try:
                    lines = esp_ser.read_all().decode('utf-8', errors='ignore').split('\n')
                    for line in lines:
                        if line.strip().startswith("HIGHSCORE:"):
                            found_score = int(line.split(":")[1])
                            loading = False
                        elif "IP PENTRU TELEFON" in line:
                            print(f"📡 {line}")
                except:
                    pass
            if time.time() - last_req_time > 2.0:
                esp_ser.write(b"GET_HIGHSCORE\n");
                last_req_time = time.time()
        else:
            time.sleep(1);
            return 0

        snake_anim_x += 5;
        if snake_anim_x > window_width: snake_anim_x = -30
        pygame.draw.rect(screen, GRAY, (50, window_height // 2, window_width - 100, 20), 2)
        pygame.draw.rect(screen, CURRENT_SNAKE_COLOR,
                         (50 + (elapsed * 50) % (window_width - 150), window_height // 2 + 2, 40, 16))

        if elapsed > 10.0: loading = False
        pygame.display.update();
        pygame.time.delay(30)
    return found_score


# ================= MAIN =================
mega_ser, esp_ser = init_connections()
high_score = show_loading_screen(esp_ser)
pygame.display.set_caption(f"Snake IoT - Best: {high_score}")
mega_ser.reset_input_buffer()

# Variabile Notificare
notif_text = "";
notif_start = 0;
notif_dur = 2.0

running = True
current_score = 0
last_sent_score = -1
current_speed = 300
is_paused = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False

    # A. MEGA
    if mega_ser.in_waiting:
        try:
            line = mega_ser.readline().decode('utf-8', errors='ignore').strip()

            # EVENIMENT VITEZA
            if line == "EVENT:SPEED_UP":
                notif_text = "VITEZA A CRESCUT!"
                notif_start = time.time()
                print("⚡ VITEZA UP")

            # DATE JOC
            elif line.startswith("DATA:"):
                try:
                    content = line.split("DATA:")[1]
                    parts = content.split(";")
                    if len(parts) >= 7:
                        food_x, food_y = map(int, parts[0].split(','))
                        snake_body = [(int(parts[2].split(',')[i]), int(parts[2].split(',')[i + 1])) for i in
                                      range(0, len(parts[2].split(',')), 2)]
                        current_score = int(parts[3])
                        game_over = int(parts[4]) == 1
                        current_speed = int(parts[5])
                        is_paused = int(parts[6]) == 1

                        # Trimitem date la ESP32
                        if esp_ser:
                            if current_score != last_sent_score:
                                esp_ser.write(f"LIVE:{current_score}\n".encode())
                                last_sent_score = current_score
                            # Trimitem viteza mereu ca sa se vada live
                            esp_ser.write(f"LIVE_SPEED:{current_speed}\n".encode())

                        # DESENARE
                        screen.fill(BLACK)

                        # HUD
                        pygame.draw.rect(screen, DARK_GRAY, (0, 0, window_width, UI_HEIGHT))
                        pygame.draw.line(screen, GRAY, (0, UI_HEIGHT), (window_width, UI_HEIGHT), 2)
                        screen.blit(font.render(f"SCOR: {current_score}", True, WHITE), (20, 20))
                        screen.blit(font.render(f"BEST: {high_score}", True, BLUE), (window_width - 140, 20))

                        # JOC
                        pygame.draw.rect(screen, RED,
                                         (food_x * BLOCK_SIZE, food_y * BLOCK_SIZE + UI_HEIGHT, BLOCK_SIZE, BLOCK_SIZE))
                        for s in snake_body:
                            pygame.draw.rect(screen, CURRENT_SNAKE_COLOR,
                                             (s[0] * BLOCK_SIZE, s[1] * BLOCK_SIZE + UI_HEIGHT, BLOCK_SIZE, BLOCK_SIZE))
                            pygame.draw.rect(screen, BLACK,
                                             (s[0] * BLOCK_SIZE, s[1] * BLOCK_SIZE + UI_HEIGHT, BLOCK_SIZE, BLOCK_SIZE),
                                             1)

                        # OVERLAYS
                        if is_paused:
                            s = pygame.Surface((window_width, window_height));
                            s.set_alpha(150);
                            s.fill(BLACK)
                            screen.blit(s, (0, 0))
                            pause_txt = big_font.render("PAUZA", True, YELLOW)
                            screen.blit(pause_txt, (window_width // 2 - 60, window_height // 2))

                        elif game_over:
                            over_txt = big_font.render("GAME OVER", True, WHITE)
                            screen.blit(over_txt, (window_width // 2 - 100, window_height // 2))

                        # NOTIFICARE
                        if time.time() - notif_start < notif_dur:
                            n_s = notif_font.render(notif_text, True, ORANGE)
                            screen.blit(n_s, (window_width // 2 - n_s.get_width() // 2, UI_HEIGHT + 20))

                        pygame.display.update()
                except:
                    pass

            elif line.startswith("SET_SCORE:"):
                try:
                    val = int(line.split(":")[1])
                    if val > high_score:
                        if esp_ser: esp_ser.write((line + "\n").encode()); high_score = val
                except:
                    pass
        except:
            pass

    # B. ESP32 (SETARI)
    if esp_ser and esp_ser.in_waiting:
        try:
            r = esp_ser.readline().decode('utf-8', errors='ignore').strip()
            if r.startswith("CONFIG:"):
                try:
                    parts = r.split(";")
                    spd = parts[1].split("=")[1]
                    grid = parts[2].split("=")[1]
                    color_name = parts[3].split("=")[1]
                    walls = parts[4].split("=")[1]

                    if color_name == "CYAN":
                        CURRENT_SNAKE_COLOR = CYAN
                    elif color_name == "MAGENTA":
                        CURRENT_SNAKE_COLOR = MAGENTA
                    elif color_name == "YELLOW":
                        CURRENT_SNAKE_COLOR = YELLOW
                    else:
                        CURRENT_SNAKE_COLOR = GREEN

                    mega_ser.write(f"SET_SPEED:{spd}\n".encode());
                    time.sleep(0.05)
                    mega_ser.write(f"SET_GRID:{grid}\n".encode());
                    time.sleep(0.05)
                    mega_ser.write(f"SET_WALLS:{walls}\n".encode())

                    GRID_W, GRID_H = map(int, grid.split(","))
                    window_width = GRID_W * BLOCK_SIZE
                    window_height = (GRID_H * BLOCK_SIZE) + UI_HEIGHT
                    screen = pygame.display.set_mode((window_width, window_height))

                    esp_ser.write(b"GET_HIGHSCORE\n")
                    high_score = 0;
                    last_sent_score = -1
                    time.sleep(0.1);
                    mega_ser.reset_input_buffer()
                except Exception as e:
                    print(e)
            elif r.startswith("HIGHSCORE:"):
                high_score = int(r.split(":")[1])
            elif "IP PENTRU TELEFON" in r:
                print(f"🌐 {r}")
        except:
            pass

pygame.quit()
mega_ser.close()
if esp_ser: esp_ser.close()