import pygame
import serial
import sys

# === CONFIGURARE ===
SERIAL_PORT = 'COM5'
BAUD_RATE = 115200
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
pygame.display.set_caption("Snake Arduino Display")
font = pygame.font.SysFont("arial", 20)

# Inițializare Serial
try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
    print(f"Conectat la {SERIAL_PORT}")
except Exception as e:
    print(f"Eroare conectare serial: {e}")
    sys.exit()

running = True
current_score = 0
game_over_state = False

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- CITIRE DATE DE LA ARDUINO ---
    if ser.in_waiting > 0:
        try:
            # Citim linia și eliminăm spațiile/newline
            line = ser.readline().decode('utf-8', errors='ignore').strip()

            # Verificăm dacă e pachetul nostru de date
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
                    # Transformăm lista (x,y,x,y...) în tupluri [(x,y), (x,y)...]
                    if len(snake_raw) >= 2:
                        for i in range(0, len(snake_raw), 2):
                            if i + 1 < len(snake_raw):
                                snake_body.append((int(snake_raw[i]), int(snake_raw[i + 1])))

                    # 3. Scor și Game Over
                    current_score = int(parts[3])
                    game_over_state = int(parts[4]) == 1

                    # --- DESENARE (Doar după ce avem date noi) ---
                    screen.fill(BLACK)

                    # Desenăm mâncarea
                    pygame.draw.rect(screen, RED, (food_x * BLOCK_SIZE, food_y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))

                    # Desenăm șarpele
                    for segment in snake_body:
                        pygame.draw.rect(screen, GREEN,
                                         (segment[0] * BLOCK_SIZE, segment[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
                        # Contur mic pentru a vedea segmentele
                        pygame.draw.rect(screen, BLACK,
                                         (segment[0] * BLOCK_SIZE, segment[1] * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

                    # Desenăm scorul
                    score_text = font.render(f"Scor: {current_score}", True, WHITE)
                    screen.blit(score_text, (10, 10))

                    # Mesaj Game Over
                    if game_over_state:
                        over_text = font.render("GAME OVER - Misca joystick pt Reset", True, WHITE)
                        text_rect = over_text.get_rect(center=(window_width / 2, window_height / 2))
                        screen.blit(over_text, text_rect)

                    pygame.display.update()

        except Exception as e:
            pass

pygame.quit()
ser.close()