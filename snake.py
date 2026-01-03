import pygame
import serial
import sys
import time
import math  # Import necesar pentru animatii

# --- CONFIGURARE ---
MEGA_PORT = 'COM5'  # <--- VERIFICA PORTUL
ESP_PORT = 'COM6'  # <--- VERIFICA PORTUL
BAUD_RATE = 115200

BLOCK_SIZE = 30
GRID_W = 20
GRID_H = 10
UI_HEIGHT = 70  # Inaltime bara Scor

# CULORI MODERNE
BG_COLOR = (20, 20, 25)  # Dark Navy Blue (Fundal)
GRID_COLOR = (40, 40, 50)  # Gri subtil pentru linii
UI_BG_COLOR = (30, 30, 35)  # Bara de sus

BLACK = (0, 0, 0)  # <--- AM ADAUGAT DEFINITIA LIPSA
WHITE = (240, 240, 240)
GREEN = (46, 204, 113)  # Emerald Green
RED = (231, 76, 60)  # Alizarin Red
BLUE = (52, 152, 219)  # Peter River
YELLOW = (241, 196, 15)
CYAN = (0, 220, 220)
MAGENTA = (220, 0, 220)
SHADOW = (0, 0, 0, 100)  # Umbra semitransparenta

CURRENT_SNAKE_COLOR = GREEN

pygame.init()
window_width = GRID_W * BLOCK_SIZE
window_height = (GRID_H * BLOCK_SIZE) + UI_HEIGHT
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Snake IoT - PRO Interface")

# Fonturi Moderne
try:
    font = pygame.font.Font(None, 26)
    big_font = pygame.font.Font(None, 50)
    score_font = pygame.font.Font(None, 34)
except:
    font = pygame.font.SysFont("arial", 20)
    big_font = pygame.font.SysFont("arial", 40, bold=True)
    score_font = pygame.font.SysFont("arial", 30, bold=True)


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


# --- FUNCTII GRAFICE PRO ---

def draw_grid():
    # Deseneaza linii verticale
    for x in range(0, window_width, BLOCK_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (x, UI_HEIGHT), (x, window_height))
    # Deseneaza linii orizontale
    for y in range(UI_HEIGHT, window_height, BLOCK_SIZE):
        pygame.draw.line(screen, GRID_COLOR, (0, y), (window_width, y))


def draw_shadow(rect, offset=4):
    # Deseneaza o umbra sub obiect
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 80), s.get_rect(), border_radius=6)
    screen.blit(s, (rect.x + offset, rect.y + offset))


def draw_apple(x, y):
    center_x = x * BLOCK_SIZE + BLOCK_SIZE // 2
    center_y = y * BLOCK_SIZE + UI_HEIGHT + BLOCK_SIZE // 2
    radius = BLOCK_SIZE // 2 - 4

    # Umbra
    pygame.draw.circle(screen, (0, 0, 0), (center_x + 2, center_y + 4), radius)

    # Corpul marului (Rosu)
    pygame.draw.circle(screen, RED, (center_x, center_y), radius)

    # Reflexie (Luciu - il face sa para 3D)
    pygame.draw.circle(screen, (255, 100, 100), (center_x - 4, center_y - 4), radius // 3)

    # Codița
    pygame.draw.line(screen, GREEN, (center_x, center_y - radius), (center_x + 4, center_y - radius - 6), 3)


def draw_snake_segment(x, y, color, is_head=False):
    rect = pygame.Rect(x * BLOCK_SIZE + 2, y * BLOCK_SIZE + UI_HEIGHT + 2, BLOCK_SIZE - 4, BLOCK_SIZE - 4)

    # 1. Umbra
    draw_shadow(rect, offset=3)

    # 2. Corpul
    pygame.draw.rect(screen, color, rect, border_radius=8)

    # 3. Detaliu interior (Gradient simplu)
    inner_rect = rect.inflate(-6, -6)
    lighter_color = (min(color[0] + 30, 255), min(color[1] + 30, 255), min(color[2] + 30, 255))
    pygame.draw.rect(screen, lighter_color, inner_rect, border_radius=4)

    # 4. Daca e CAPUL, desenam ochi
    if is_head:
        # Ochii (Alb)
        eye_radius = 4
        left_eye = (rect.x + 8, rect.y + 8)
        right_eye = (rect.x + rect.width - 8, rect.y + 8)

        pygame.draw.circle(screen, WHITE, left_eye, eye_radius)
        pygame.draw.circle(screen, WHITE, right_eye, eye_radius)

        # Pupile (Negru) - AICI ERA EROAREA (Acum BLACK e definit)
        pygame.draw.circle(screen, BLACK, left_eye, 2)
        pygame.draw.circle(screen, BLACK, right_eye, 2)


# --- LOADING SCREEN ---
def show_loading_screen(esp_ser):
    loading = True;
    found_score = 0;
    start_time = time.time();
    last_req_time = time.time()
    if esp_ser: esp_ser.reset_input_buffer(); esp_ser.write(b"GET_HIGHSCORE\n")

    while loading:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        elapsed = time.time() - start_time

        screen.fill(BG_COLOR)
        draw_grid()

        # Titlu Animat
        title_surf = big_font.render("SNAKE IoT", True, CURRENT_SNAKE_COLOR)
        screen.blit(title_surf, (window_width // 2 - title_surf.get_width() // 2, window_height // 2 - 60))

        if esp_ser:
            status_text = "Se conecteaza la Cloud..."
            dots = "." * (int(elapsed * 2) % 4)
            info_surf = font.render(status_text + dots, True, WHITE)
            screen.blit(info_surf, (window_width // 2 - info_surf.get_width() // 2, window_height // 2 + 20))

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

        # Bara de progres
        bar_width = 200
        pygame.draw.rect(screen, GRID_COLOR, (window_width // 2 - 100, window_height // 2 + 60, bar_width, 10),
                         border_radius=5)
        fill_width = (math.sin(elapsed * 3) + 1) / 2 * bar_width
        pygame.draw.rect(screen, CURRENT_SNAKE_COLOR,
                         (window_width // 2 - 100, window_height // 2 + 60, fill_width, 10), border_radius=5)

        if elapsed > 10.0: loading = False
        pygame.display.update();
        pygame.time.delay(30)
    return found_score


# ================= MAIN =================
mega_ser, esp_ser = init_connections()
high_score = show_loading_screen(esp_ser)
pygame.display.set_caption(f"Snake IoT - Best: {high_score}")
mega_ser.reset_input_buffer()

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

            if line == "EVENT:SPEED_UP":
                notif_text = "VITEZA A CRESCUT! ⚡"
                notif_start = time.time()
                print("⚡ VITEZA UP")

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

                        if esp_ser:
                            if current_score != last_sent_score:
                                esp_ser.write(f"LIVE:{current_score}\n".encode())
                                last_sent_score = current_score
                            esp_ser.write(f"LIVE_SPEED:{current_speed}\n".encode())

                        # --- DESENARE PROFESIONALA ---
                        screen.fill(BG_COLOR)
                        draw_grid()

                        # HUD
                        pygame.draw.rect(screen, UI_BG_COLOR, (0, 0, window_width, UI_HEIGHT))
                        pygame.draw.line(screen, (50, 50, 60), (0, UI_HEIGHT), (window_width, UI_HEIGHT), 2)

                        s_surf = score_font.render(f"SCOR: {current_score}", True, WHITE)
                        screen.blit(s_surf, (20, UI_HEIGHT // 2 - s_surf.get_height() // 2))

                        hs_surf = score_font.render(f"BEST: {high_score}", True, BLUE)
                        screen.blit(hs_surf, (window_width - 20 - hs_surf.get_width(),
                                              UI_HEIGHT // 2 - hs_surf.get_height() // 2))

                        # JOC
                        draw_apple(food_x, food_y)

                        for i, s in enumerate(snake_body):
                            is_head = (i == 0)
                            draw_snake_segment(s[0], s[1], CURRENT_SNAKE_COLOR, is_head)

                        # OVERLAYS
                        if is_paused:
                            s = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
                            s.fill((0, 0, 0, 150))
                            screen.blit(s, (0, 0))

                            pause_box = pygame.Rect(window_width // 2 - 100, window_height // 2 - 40, 200, 80)
                            pygame.draw.rect(screen, UI_BG_COLOR, pause_box, border_radius=10)
                            pygame.draw.rect(screen, WHITE, pause_box, 2, border_radius=10)

                            pause_txt = big_font.render("PAUZĂ", True, YELLOW)
                            screen.blit(pause_txt, (window_width // 2 - pause_txt.get_width() // 2,
                                                    window_height // 2 - pause_txt.get_height() // 2))

                        elif game_over:
                            over_txt = big_font.render("GAME OVER", True, RED)
                            over_shadow = big_font.render("GAME OVER", True, (0, 0, 0))
                            screen.blit(over_shadow,
                                        (window_width // 2 - over_txt.get_width() // 2 + 2, window_height // 2 + 2))
                            screen.blit(over_txt, (window_width // 2 - over_txt.get_width() // 2, window_height // 2))

                        # NOTIFICARE
                        if time.time() - notif_start < notif_dur:
                            n_txt = font.render(notif_text, True, (0, 0, 0))
                            padding = 10
                            n_bg = pygame.Rect(0, 0, n_txt.get_width() + padding * 2, n_txt.get_height() + padding * 2)
                            n_bg.center = (window_width // 2, UI_HEIGHT + 40)

                            pygame.draw.rect(screen, (255, 165, 0), n_bg, border_radius=15)
                            screen.blit(n_txt, (n_bg.x + padding, n_bg.y + padding))

                        pygame.display.update()
                except Exception as e:
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