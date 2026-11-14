import pygame
import random
import math
import json
import os
from array import array

# ==========================================
# NEON SNAKE - CYBER ARCADE
# ==========================================

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()

try:
    pygame.mixer.init()
    SOUND_ENABLED = True
except pygame.error:
    SOUND_ENABLED = False

WIDTH, HEIGHT = 1100, 700
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("NEON SNAKE | Cyber Arcade")
clock = pygame.time.Clock()

# Colors
BLACK = (5, 7, 17)
DARK = (10, 15, 30)
CYAN = (0, 240, 255)
GREEN = (0, 255, 140)
PURPLE = (170, 60, 255)
PINK = (255, 50, 180)
WHITE = (240, 245, 255)
GRAY = (110, 125, 150)
RED = (255, 65, 85)
GOLD = (255, 190, 45)

# Fonts
font = pygame.font.SysFont("dejavusans", 23)
small_font = pygame.font.SysFont("dejavusans", 16)
medium_font = pygame.font.SysFont("dejavusans", 34, bold=True)
title_font = pygame.font.SysFont("dejavusans", 68, bold=True)

# Grid
CELL = 25
COLS = 32
ROWS = 22

BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
BOARD_X = (WIDTH - BOARD_W) // 2
BOARD_Y = (HEIGHT - BOARD_H) // 2

# Save file
SAVE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "neon_snake_save.json"
)

# Game variables
game_state = "menu"
difficulty = "NORMAL"

snake = []
direction = (1, 0)
next_direction = (1, 0)

food = None
food_type = "normal"

score = 0
record = 0
game_speed = 8
move_timer = 0

particles = []
stars = []

running = True
menu_animation = 0
screen_shake = 0

# ==========================================
# SAVE SYSTEM
# ==========================================

def load_record():
    global record

    try:
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                record = int(data.get("record", 0))
    except (OSError, ValueError, json.JSONDecodeError):
        record = 0


def save_record():
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as file:
            json.dump({"record": record}, file)
    except OSError:
        pass


load_record()

# ==========================================
# SOUND SYSTEM
# ==========================================

def make_tone(frequency, duration, volume=0.15):
    if not SOUND_ENABLED:
        return None

    sample_rate = 44100
    samples = int(sample_rate * duration)
    data = array("h")

    for i in range(samples):
        t = i / sample_rate

        fade = min(1, i / 400, (samples - i) / 1200)
        wave = math.sin(2 * math.pi * frequency * t)

        value = int(
            32767 * volume * fade * wave
        )

        data.append(value)
        data.append(value)

    try:
        return pygame.mixer.Sound(buffer=data.tobytes())
    except pygame.error:
        return None


eat_sound = make_tone(750, 0.09)
bonus_sound = make_tone(1100, 0.18)
gameover_sound = make_tone(150, 0.35)
click_sound = make_tone(450, 0.06)


def play_sound(sound):
    if SOUND_ENABLED and sound:
        try:
            sound.play()
        except pygame.error:
            pass


# ==========================================
# BACKGROUND
# ==========================================

for _ in range(100):
    stars.append([
        random.randint(0, WIDTH),
        random.randint(0, HEIGHT),
        random.randint(1, 3),
        random.uniform(0.5, 2)
    ])


def draw_background():
    screen.fill(BLACK)

    for star in stars:
        x, y, size, speed = star

        pygame.draw.circle(
            screen,
            (25, 65, 100),
            (int(x), int(y)),
            size
        )

        star[1] += speed * 0.15

        if star[1] > HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, WIDTH)

    # Decorative neon lines
    for x in range(0, WIDTH, 100):
        pygame.draw.line(
            screen,
            (10, 22, 42),
            (x, 0),
            (x, HEIGHT),
            1
        )


# ==========================================
# TEXT AND BUTTONS
# ==========================================

def draw_text(text, font_type, color, x, y, center=False):
    image = font_type.render(str(text), True, color)
    rect = image.get_rect()

    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)

    screen.blit(image, rect)


def draw_button(rect, text, mouse_pos, color=CYAN):
    hovered = rect.collidepoint(mouse_pos)

    fill = (15, 55, 75) if hovered else (10, 25, 45)
    border = WHITE if hovered else color

    pygame.draw.rect(
        screen,
        fill,
        rect,
        border_radius=12
    )

    pygame.draw.rect(
        screen,
        border,
        rect,
        2,
        border_radius=12
    )

    draw_text(
        text,
        font,
        WHITE,
        rect.centerx,
        rect.centery,
        True
    )


def draw_cursor():
    mx, my = pygame.mouse.get_pos()

    pygame.draw.circle(
        screen,
        CYAN,
        (mx, my),
        10,
        2
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (mx, my),
        2
    )

    pygame.draw.line(
        screen, CYAN,
        (mx - 16, my),
        (mx - 5, my),
        2
    )

    pygame.draw.line(
        screen, CYAN,
        (mx + 5, my),
        (mx + 16, my),
        2
    )

    pygame.draw.line(
        screen, CYAN,
        (mx, my - 16),
        (mx, my - 5),
        2
    )

    pygame.draw.line(
        screen, CYAN,
        (mx, my + 5),
        (mx, my + 16),
        2
    )


# ==========================================
# GAME SETUP
# ==========================================

def spawn_food():
    global food, food_type

    occupied = set(snake)

    available = [
        (x, y)
        for x in range(COLS)
        for y in range(ROWS)
        if (x, y) not in occupied
    ]

    if not available:
        return

    food = random.choice(available)

    if random.random() < 0.15:
        food_type = "bonus"
    else:
        food_type = "normal"


def start_game():
    global snake, direction, next_direction
    global score, game_speed, move_timer
    global particles, screen_shake, game_state

    snake = [
        (COLS // 2, ROWS // 2),
        (COLS // 2 - 1, ROWS // 2),
        (COLS // 2 - 2, ROWS // 2)
    ]

    direction = (1, 0)
    next_direction = (1, 0)

    score = 0
    move_timer = 0
    particles = []
    screen_shake = 0

    if difficulty == "EASY":
        game_speed = 6
    elif difficulty == "HARD":
        game_speed = 12
    else:
        game_speed = 8

    spawn_food()
    game_state = "game"


# ==========================================
# PARTICLES
# ==========================================

def create_particles(x, y, color, amount=16):
    px = BOARD_X + x * CELL + CELL // 2
    py = BOARD_Y + y * CELL + CELL // 2

    for _ in range(amount):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(40, 170)

        particles.append({
            "x": px,
            "y": py,
            "dx": math.cos(angle) * speed,
            "dy": math.sin(angle) * speed,
            "life": random.uniform(0.3, 0.7),
            "max_life": 0.7,
            "color": color,
            "size": random.randint(2, 5)
        })


def update_particles(dt):
    for particle in particles[:]:
        particle["x"] += particle["dx"] * dt
        particle["y"] += particle["dy"] * dt

        particle["life"] -= dt

        if particle["life"] <= 0:
            particles.remove(particle)


def draw_particles():
    for particle in particles:
        ratio = max(
            0,
            particle["life"] / particle["max_life"]
        )

        color = tuple(
            int(channel * ratio)
            for channel in particle["color"]
        )

        pygame.draw.circle(
            screen,
            color,
            (int(particle["x"]), int(particle["y"])),
            max(1, int(particle["size"] * ratio))
        )


# ==========================================
# SNAKE MOVEMENT
# ==========================================

def change_direction(new_direction):
    global next_direction

    if (
        new_direction[0] + direction[0] == 0
        and new_direction[1] + direction[1] == 0
    ):
        return

    next_direction = new_direction


def move_snake():
    global snake, direction, score
    global game_state, record, game_speed, screen_shake

    direction = next_direction

    head_x, head_y = snake[0]

    new_head = (
        head_x + direction[0],
        head_y + direction[1]
    )

    eating = new_head == food

    if not (0 <= new_head[0] < COLS):
        game_over()
        return

    if not (0 <= new_head[1] < ROWS):
        game_over()
        return

    body_to_check = snake if eating else snake[:-1]

    if new_head in body_to_check:
        game_over()
        return

    snake.insert(0, new_head)

    if eating:
        if food_type == "bonus":
            score += 30
            create_particles(
                food[0], food[1], GOLD, 28
            )
            play_sound(bonus_sound)
        else:
            score += 10
            create_particles(
                food[0], food[1], GREEN, 18
            )
            play_sound(eat_sound)

        if score > record:
            record = score
            save_record()

        # Gradually increase speed
        if difficulty == "EASY":
            game_speed = min(15, 6 + score // 100)
        elif difficulty == "NORMAL":
            game_speed = min(20, 8 + score // 100)
        else:
            game_speed = min(25, 12 + score // 100)

        spawn_food()

    else:
        snake.pop()


def game_over():
    global game_state, record

    game_state = "over"
    play_sound(gameover_sound)

    if score > record:
        record = score
        save_record()


# ==========================================
# DRAW GAME
# ==========================================

def draw_board():
    pygame.draw.rect(
        screen,
        (8, 15, 30),
        (
            BOARD_X - 5,
            BOARD_Y - 5,
            BOARD_W + 10,
            BOARD_H + 10
        ),
        border_radius=8
    )

    # Grid
    for x in range(COLS + 1):
        px = BOARD_X + x * CELL

        pygame.draw.line(
            screen,
            (17, 35, 55),
            (px, BOARD_Y),
            (px, BOARD_Y + BOARD_H),
            1
        )

    for y in range(ROWS + 1):
        py = BOARD_Y + y * CELL

        pygame.draw.line(
            screen,
            (17, 35, 55),
            (BOARD_X, py),
            (BOARD_X + BOARD_W, py),
            1
        )

    pygame.draw.rect(
        screen,
        CYAN,
        (
            BOARD_X - 5,
            BOARD_Y - 5,
            BOARD_W + 10,
            BOARD_H + 10
        ),
        2,
        border_radius=8
    )


def draw_glow_circle(x, y, radius, color):
    glow = pygame.Surface(
        (radius * 6, radius * 6),
        pygame.SRCALPHA
    )

    center = radius * 3

    for i in range(4, 0, -1):
        alpha = 15 + i * 8

        pygame.draw.circle(
            glow,
            (*color, alpha),
            (center, center),
            radius * i // 2
        )

    screen.blit(
        glow,
        (int(x - center), int(y - center))
    )


def draw_snake():
    for index, segment in enumerate(reversed(snake)):
        x, y = segment

        px = BOARD_X + x * CELL + CELL // 2
        py = BOARD_Y + y * CELL + CELL // 2

        if index == len(snake) - 1:
            color = GREEN
        else:
            ratio = index / max(1, len(snake))

            color = (
                int(0),
                int(120 + 130 * (1 - ratio)),
                int(170 + 85 * (1 - ratio))
            )

        draw_glow_circle(px, py, 12, color)

        pygame.draw.rect(
            screen,
            color,
            (
                px - 10,
                py - 10,
                20,
                20
            ),
            border_radius=6
        )

    # Eyes
    head_x, head_y = snake[0]

    px = BOARD_X + head_x * CELL + CELL // 2
    py = BOARD_Y + head_y * CELL + CELL // 2

    if direction == (1, 0):
        eyes = [(px + 5, py - 4), (px + 5, py + 4)]
    elif direction == (-1, 0):
        eyes = [(px - 5, py - 4), (px - 5, py + 4)]
    elif direction == (0, -1):
        eyes = [(px - 4, py - 5), (px + 4, py - 5)]
    else:
        eyes = [(px - 4, py + 5), (px + 4, py + 5)]

    for eye in eyes:
        pygame.draw.circle(screen, WHITE, eye, 2)


def draw_food():
    if food is None:
        return

    x, y = food

    px = BOARD_X + x * CELL + CELL // 2
    py = BOARD_Y + y * CELL + CELL // 2

    if food_type == "bonus":
        color = GOLD
        radius = 10
    else:
        color = PINK
        radius = 8

    pulse = math.sin(pygame.time.get_ticks() * 0.006) * 2

    draw_glow_circle(px, py, radius + pulse, color)

    pygame.draw.circle(
        screen,
        color,
        (px, py),
        int(radius + pulse)
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (px - 2, py - 2),
        3
    )


def draw_hud():
    pygame.draw.rect(
        screen,
        (10, 20, 40),
        (30, 25, 220, 75),
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        CYAN,
        (30, 25, 220, 75),
        2,
        border_radius=10
    )

    draw_text("SCORE", small_font, GRAY, 48, 35)
    draw_text(str(score), medium_font, CYAN, 48, 55)

    pygame.draw.rect(
        screen,
        (10, 20, 40),
        (WIDTH - 250, 25, 220, 75),
        border_radius=10
    )

    pygame.draw.rect(
        screen,
        PURPLE,
        (WIDTH - 250, 25, 220, 75),
        2,
        border_radius=10
    )

    draw_text("BEST", small_font, GRAY, WIDTH - 230, 35)
    draw_text(str(record), medium_font, PURPLE, WIDTH - 230, 55)

    draw_text(
        "ESC: PAUSE",
        small_font,
        GRAY,
        WIDTH // 2,
        HEIGHT - 27,
        True
    )


# ==========================================
# MENUS
# ==========================================

def draw_menu():
    draw_background()

    draw_text(
        "NEON SNAKE",
        title_font,
        CYAN,
        WIDTH // 2,
        180,
        True
    )

    draw_text(
        "CYBER ARCADE EXPERIENCE",
        font,
        PURPLE,
        WIDTH // 2,
        250,
        True
    )

    mouse = pygame.mouse.get_pos()

    start_button = pygame.Rect(
        WIDTH // 2 - 145, 330, 290, 65
    )

    settings_button = pygame.Rect(
        WIDTH // 2 - 145, 415, 290, 60
    )

    quit_button = pygame.Rect(
        WIDTH // 2 - 145, 495, 290, 60
    )

    draw_button(start_button, "START GAME", mouse)
    draw_button(settings_button, "SETTINGS", mouse, PURPLE)
    draw_button(quit_button, "QUIT", mouse, RED)

    draw_text(
        f"BEST SCORE: {record}",
        small_font,
        GREEN,
        WIDTH // 2,
        600,
        True
    )


def draw_settings():
    draw_background()

    draw_text(
        "SETTINGS",
        title_font,
        CYAN,
        WIDTH // 2,
        180,
        True
    )

    mouse = pygame.mouse.get_pos()

    if difficulty == "EASY":
        label = "DIFFICULTY: EASY"
    elif difficulty == "HARD":
        label = "DIFFICULTY: HARD"
    else:
        label = "DIFFICULTY: NORMAL"

    difficulty_button = pygame.Rect(
        WIDTH // 2 - 170, 340, 340, 70
    )

    back_button = pygame.Rect(
        WIDTH // 2 - 145, 445, 290, 60
    )

    draw_button(
        difficulty_button,
        label,
        mouse,
        PURPLE
    )

    draw_button(
        back_button,
        "BACK",
        mouse
    )


def draw_pause():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(210)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_text(
        "PAUSED",
        title_font,
        CYAN,
        WIDTH // 2,
        230,
        True
    )

    draw_text(
        "PRESS ESC TO CONTINUE",
        font,
        WHITE,
        WIDTH // 2,
        330,
        True
    )

    draw_text(
        "R: RESTART       Q: MAIN MENU",
        small_font,
        GRAY,
        WIDTH // 2,
        390,
        True
    )


def draw_game_over():
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(210)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))

    draw_text(
        "GAME OVER",
        title_font,
        RED,
        WIDTH // 2,
        220,
        True
    )

    draw_text(
        f"SCORE: {score}",
        medium_font,
        WHITE,
        WIDTH // 2,
        320,
        True
    )

    draw_text(
        f"RECORD: {record}",
        font,
        GOLD,
        WIDTH // 2,
        370,
        True
    )

    draw_text(
        "ENTER: PLAY AGAIN",
        font,
        CYAN,
        WIDTH // 2,
        460,
        True
    )

    draw_text(
        "ESC: MAIN MENU",
        small_font,
        GRAY,
        WIDTH // 2,
        510,
        True
    )


# ==========================================
# MAIN LOOP
# ==========================================

move_timer = 0

while running:

    dt = min(clock.tick(FPS) / 1000, 0.05)

    menu_animation += dt

    mouse = pygame.mouse.get_pos()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                if game_state == "game":
                    game_state = "pause"

                elif game_state == "pause":
                    game_state = "game"

                elif game_state == "settings":
                    game_state = "menu"

                elif game_state == "over":
                    game_state = "menu"

            if game_state == "game":

                if event.key in (pygame.K_UP, pygame.K_w):
                    change_direction((0, -1))

                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    change_direction((0, 1))

                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    change_direction((-1, 0))

                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    change_direction((1, 0))

            if event.key == pygame.K_r:
                if game_state in ("pause", "over"):
                    start_game()

            if event.key == pygame.K_q:
                if game_state == "pause":
                    game_state = "menu"

            if event.key == pygame.K_RETURN:

                if game_state == "menu":
                    start_game()

                elif game_state == "over":
                    start_game()

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if game_state == "menu":

                    if pygame.Rect(
                        WIDTH // 2 - 145, 330, 290, 65
                    ).collidepoint(mouse):
                        start_game()
                        play_sound(click_sound)

                    elif pygame.Rect(
                        WIDTH // 2 - 145, 415, 290, 60
                    ).collidepoint(mouse):
                        game_state = "settings"
                        play_sound(click_sound)

                    elif pygame.Rect(
                        WIDTH // 2 - 145, 495, 290, 60
                    ).collidepoint(mouse):
                        running = False

                elif game_state == "settings":

                    if pygame.Rect(
                        WIDTH // 2 - 170, 340, 340, 70
                    ).collidepoint(mouse):

                        if difficulty == "EASY":
                            difficulty = "NORMAL"
                        elif difficulty == "NORMAL":
                            difficulty = "HARD"
                        else:
                            difficulty = "EASY"

                        play_sound(click_sound)

                    elif pygame.Rect(
                        WIDTH // 2 - 145, 445, 290, 60
                    ).collidepoint(mouse):
                        game_state = "menu"

    # Update
    if game_state == "game":

        move_timer += dt

        interval = 1 / game_speed

        if move_timer >= interval:
            move_timer = 0
            move_snake()

        update_particles(dt)

    else:
        update_particles(dt)

    # Draw
    draw_background()

    if game_state == "menu":
        draw_menu()

    elif game_state == "settings":
        draw_settings()

    elif game_state in ("game", "pause", "over"):

        draw_board()
        draw_food()
        draw_snake()
        draw_particles()
        draw_hud()

        if game_state == "pause":
            draw_pause()

        elif game_state == "over":
            draw_game_over()

    draw_cursor()

    pygame.display.flip()


save_record()

pygame.mouse.set_visible(True)
pygame.quit()