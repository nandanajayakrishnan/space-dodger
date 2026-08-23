import pygame
import sys
import random
import math

pygame.init()

# Screen settings
WIDTH, HEIGHT = 480, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Dodger")

clock = pygame.time.Clock()
FPS = 60

# Colors
BG_TOP = (8, 8, 24)
BG_BOTTOM = (20, 15, 45)
CYAN = (100, 230, 255)
CYAN_DARK = (40, 150, 190)
RED = (255, 100, 110)
ROCK_DARK = (150, 50, 60)
WHITE = (245, 245, 245)
GRAY = (160, 160, 175)
YELLOW = (255, 210, 90)
PINK = (255, 150, 200)

# Player settings
player_width, player_height = 36, 46
player_x = WIDTH // 2 - player_width // 2
player_y = HEIGHT - player_height - 20
player_speed = 6

# Asteroid settings
asteroid_size = 30
asteroid_speed = 4
asteroid_spawn_timer = 0
asteroid_spawn_delay = 40
asteroids = []  # [x, y, rotation]

# Score & difficulty
score = 0
difficulty_timer = 0
high_score = 0

# Fonts
font_big = pygame.font.SysFont("arial", 52, bold=True)
font_med = pygame.font.SysFont("arial", 34, bold=True)
font_small = pygame.font.SysFont("arial", 24)

# Game states
START, PLAYING, GAME_OVER = "start", "playing", "game_over"
state = START

# Starfield: (x, y, size, twinkle_speed, twinkle_offset)
stars = []
for _ in range(70):
    stars.append([
        random.randint(0, WIDTH),
        random.randint(0, HEIGHT),
        random.choice([1, 1, 2]),
        random.uniform(0.02, 0.06),
        random.uniform(0, math.pi * 2)
    ])

frame_count = 0


def draw_background():
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    for star in stars:
        x, y, size, speed, offset = star
        brightness = 150 + int(100 * math.sin(frame_count * speed + offset))
        brightness = max(80, min(240, brightness))  # capped at 240 so +15 stays <= 255
        pygame.draw.circle(screen, (brightness, brightness, brightness + 15), (x, y), size)


def move_stars():
    for star in stars:
        star[1] += 1
        if star[1] > HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, WIDTH)


def draw_rocket(x, y):
    """Draw a cute rocket mascot centered in the player's bounding box."""
    cx = x + player_width // 2
    top = y

    # Flame (animated flicker)
    flame_h = 10 + (frame_count % 6)
    pygame.draw.polygon(screen, YELLOW, [
        (cx - 8, y + player_height),
        (cx + 8, y + player_height),
        (cx, y + player_height + flame_h)
    ])
    pygame.draw.polygon(screen, (255, 150, 60), [
        (cx - 4, y + player_height),
        (cx + 4, y + player_height),
        (cx, y + player_height + flame_h - 4)
    ])

    # Body (rounded rocket shape)
    body_rect = pygame.Rect(x + 6, top + 10, player_width - 12, player_height - 14)
    pygame.draw.ellipse(screen, WHITE, body_rect)
    pygame.draw.rect(screen, WHITE, (x + 6, top + 22, player_width - 12, player_height - 24))

    # Nose cone
    pygame.draw.polygon(screen, CYAN, [
        (cx - 12, top + 14),
        (cx + 12, top + 14),
        (cx, top)
    ])

    # Side fins
    pygame.draw.polygon(screen, CYAN_DARK, [
        (x + 4, top + player_height - 16),
        (x - 4, top + player_height - 2),
        (x + 10, top + player_height - 10)
    ])
    pygame.draw.polygon(screen, CYAN_DARK, [
        (x + player_width - 4, top + player_height - 16),
        (x + player_width + 4, top + player_height - 2),
        (x + player_width - 10, top + player_height - 10)
    ])

    # Window / face
    pygame.draw.circle(screen, CYAN, (cx, top + 22), 8)
    pygame.draw.circle(screen, (255, 255, 255), (cx, top + 22), 8, 1)
    # Little eyes in the window
    pygame.draw.circle(screen, (10, 10, 20), (cx - 3, top + 21), 1)
    pygame.draw.circle(screen, (10, 10, 20), (cx + 3, top + 21), 1)


def draw_asteroid(x, y, rot):
    """Draw a chunky asteroid with craters."""
    cx, cy = x + asteroid_size // 2, y + asteroid_size // 2
    points = []
    for i in range(8):
        angle = rot + i * (math.pi * 2 / 8)
        r = asteroid_size // 2 + random.Random(i + int(x)).randint(-3, 2)
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(screen, RED, points)
    pygame.draw.polygon(screen, ROCK_DARK, points, 2)
    pygame.draw.circle(screen, ROCK_DARK, (cx - 5, cy - 3), 3)
    pygame.draw.circle(screen, ROCK_DARK, (cx + 4, cy + 5), 2)


def draw_logo(cx, cy, scale=1.0):
    """Small rocket badge logo, used on the start screen."""
    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), int(34 * scale), 2)
    r_w, r_h = int(14 * scale), int(20 * scale)
    top = cy - r_h // 2
    pygame.draw.ellipse(screen, WHITE, (cx - r_w // 2, top + 6, r_w, r_h))
    pygame.draw.polygon(screen, CYAN, [
        (cx - r_w // 2, top + 8), (cx + r_w // 2, top + 8), (cx, top)
    ])
    pygame.draw.circle(screen, CYAN, (cx, top + 12), int(3 * scale))


def spawn_asteroid():
    x = random.randint(0, WIDTH - asteroid_size)
    asteroids.append([x, -asteroid_size, random.uniform(0, math.pi)])


def check_collision(player_rect, asteroid_rect):
    return player_rect.colliderect(asteroid_rect)


def reset_game():
    global player_x, player_y, asteroid_speed, asteroid_spawn_delay
    global score, difficulty_timer
    player_x = WIDTH // 2 - player_width // 2
    player_y = HEIGHT - player_height - 20
    asteroids.clear()
    asteroid_speed = 4
    asteroid_spawn_delay = 40
    score = 0
    difficulty_timer = 0


def main():
    global player_x, player_y, asteroid_spawn_timer, asteroid_speed
    global asteroid_spawn_delay, score, difficulty_timer, state, high_score, frame_count

    running = True

    while running:
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if state == START and event.key == pygame.K_SPACE:
                    reset_game()
                    state = PLAYING
                elif state == GAME_OVER and event.key == pygame.K_r:
                    reset_game()
                    state = PLAYING

        if state == PLAYING:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player_x > 0:
                player_x -= player_speed
            if keys[pygame.K_RIGHT] and player_x < WIDTH - player_width:
                player_x += player_speed
            if keys[pygame.K_UP] and player_y > 0:
                player_y -= player_speed
            if keys[pygame.K_DOWN] and player_y < HEIGHT - player_height:
                player_y += player_speed

            score += 1

            difficulty_timer += 1
            if difficulty_timer >= 300:
                asteroid_speed += 0.5
                if asteroid_spawn_delay > 15:
                    asteroid_spawn_delay -= 3
                difficulty_timer = 0

            asteroid_spawn_timer += 1
            if asteroid_spawn_timer >= asteroid_spawn_delay:
                spawn_asteroid()
                asteroid_spawn_timer = 0

            for asteroid in asteroids[:]:
                asteroid[1] += asteroid_speed
                if asteroid[1] > HEIGHT:
                    asteroids.remove(asteroid)

            player_rect = pygame.Rect(player_x + 4, player_y + 8, player_width - 8, player_height - 8)
            for asteroid in asteroids:
                asteroid_rect = pygame.Rect(asteroid[0], asteroid[1], asteroid_size, asteroid_size)
                if check_collision(player_rect, asteroid_rect):
                    if score // 10 > high_score:
                        high_score = score // 10
                    state = GAME_OVER

        # Draw
        draw_background()
        move_stars()

        if state == START:
            draw_logo(WIDTH // 2, HEIGHT // 2 - 130, scale=1.6)

            pulse = 1 + 0.03 * math.sin(frame_count * 0.05)
            title = font_big.render("SPACE DODGER", True, YELLOW)
            title = pygame.transform.rotozoom(title, 0, pulse)
            title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
            screen.blit(title, title_rect)

            prompt = font_med.render("Press SPACE to Start", True, WHITE)
            prompt_rect = prompt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 30))
            screen.blit(prompt, prompt_rect)

            hint = font_small.render("Arrow keys to move  -  dodge the asteroids", True, GRAY)
            hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 75))
            screen.blit(hint, hint_rect)

            draw_rocket(WIDTH // 2 - player_width // 2, HEIGHT - 140)

        elif state == PLAYING:
            for asteroid in asteroids:
                draw_asteroid(asteroid[0], asteroid[1], asteroid[2])
            draw_rocket(player_x, player_y)

            score_text = font_small.render(f"Score: {score // 10}", True, WHITE)
            screen.blit(score_text, (14, 14))

        elif state == GAME_OVER:
            for asteroid in asteroids:
                draw_asteroid(asteroid[0], asteroid[1], asteroid[2])
            draw_rocket(player_x, player_y)

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 5, 15, 160))
            screen.blit(overlay, (0, 0))

            text = font_big.render("GAME OVER", True, WHITE)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            screen.blit(text, text_rect)

            score_line = font_med.render(f"Score {score // 10}   Best {high_score}", True, YELLOW)
            score_rect = score_line.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 5))
            screen.blit(score_line, score_rect)

            restart_text = font_small.render("Press R to Restart", True, GRAY)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
            screen.blit(restart_text, restart_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()