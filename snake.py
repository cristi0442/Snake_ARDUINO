import pygame
import time
import random
import serial

SERIAL_PORT = 'COM3'
BAUD_RATE = 9600
WIDTH = 600
HEIGHT = 400
SNAKE_BLOCK = 20
SNAKE_SPEED = 10

# Culori
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (213, 50, 80)
GREEN = (0, 255, 0)

# Inițializare Serial
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=.1)
    time.sleep(2)  # Așteaptă stabilirea conexiunii
    print(f"Conectat la {SERIAL_PORT}")
except:
    print("NU s-a putut conecta la Arduino. Verifică portul!")
    arduino = None

# Inițializare Pygame
pygame.init()
dis = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Snake Game cu Arduino Control')
clock = pygame.time.Clock()

font_style = pygame.font.SysFont("bahnschrift", 25)


def message(msg, color):
    mesg = font_style.render(msg, True, color)
    # Centrare text
    text_rect = mesg.get_rect(center=(WIDTH / 2, HEIGHT / 2))
    dis.blit(mesg, text_rect)


def gameLoop():
    game_over = False
    game_close = False

    x1 = WIDTH / 2
    y1 = HEIGHT / 2
    x1_change = 0
    y1_change = 0

    snake_List = []
    Length_of_snake = 1

    foodx = round(random.randrange(0, WIDTH - SNAKE_BLOCK) / 20.0) * 20.0
    foody = round(random.randrange(0, HEIGHT - SNAKE_BLOCK) / 20.0) * 20.0

    current_direction = ""

    while not game_over:

        while game_close == True:
            dis.fill(BLACK)
            message("Ai pierdut! Apasa Q-Quit sau C-Joca din nou", RED)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop()

        if arduino and arduino.in_waiting > 0:
            try:
                data = arduino.readline().decode('utf-8').strip()
                if data == 'L' and current_direction != 'R':
                    x1_change = -SNAKE_BLOCK
                    y1_change = 0
                    current_direction = 'L'
                elif data == 'R' and current_direction != 'L':
                    x1_change = SNAKE_BLOCK
                    y1_change = 0
                    current_direction = 'R'
                elif data == 'U' and current_direction != 'D':
                    y1_change = -SNAKE_BLOCK
                    x1_change = 0
                    current_direction = 'U'
                elif data == 'D' and current_direction != 'U':
                    y1_change = SNAKE_BLOCK
                    x1_change = 0
                    current_direction = 'D'
            except:
                pass

        # --- INPUT DE LA TASTATURĂ (Backup) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True

        # Verificăm limitele ecranului
        if x1 >= WIDTH or x1 < 0 or y1 >= HEIGHT or y1 < 0:
            game_close = True

        x1 += x1_change
        y1 += y1_change
        dis.fill(BLACK)

        # Desenare mâncare
        pygame.draw.rect(dis, RED, [foodx, foody, SNAKE_BLOCK, SNAKE_BLOCK])

        # Logica Șarpelui
        snake_Head = []
        snake_Head.append(x1)
        snake_Head.append(y1)
        snake_List.append(snake_Head)
        if len(snake_List) > Length_of_snake:
            del snake_List[0]

        for x in snake_List[:-1]:
            if x == snake_Head:
                game_close = True

        for x in snake_List:
            pygame.draw.rect(dis, GREEN, [x[0], x[1], SNAKE_BLOCK, SNAKE_BLOCK])

        pygame.display.update()

        if x1 == foodx and y1 == foody:
            foodx = round(random.randrange(0, WIDTH - SNAKE_BLOCK) / 20.0) * 20.0
            foody = round(random.randrange(0, HEIGHT - SNAKE_BLOCK) / 20.0) * 20.0
            Length_of_snake += 1

        clock.tick(SNAKE_SPEED)

    pygame.quit()
    quit()


gameLoop()