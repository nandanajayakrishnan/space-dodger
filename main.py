import pygame
import sys
import random
import math
import sounds

pygame.init()

# Screen settings
WIDTH, HEIGHT = 480, 640
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Dodger")

clock = pygame.time.Clock()
FPS = 60

# Deep space palette
BG_TOP = (5, 4, 20)
BG_MID = (18, 10, 40)
BG_BOTTOM = (30, 12, 45)
NEBULA_PURPLE = (120, 70, 200)
NEBULA_BLUE = (60, 110, 220)
NEBULA_PINK = (200, 90, 170)
STAR_WHITE = (235, 235, 255)
ELECTRIC_CYAN = (100, 230, 255)
VIOLET = (170, 130, 255)
WHITE = (245, 245, 250)
GRAY = (160, 160, 180)
GOLD = (255, 200, 100)

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
asteroids = []

# Score & difficulty
score = 0
difficulty_timer = 0
high_score = 0

# Fonts
font_big = pygame.font.SysFont("arial", 50, bold=True)
font_med = pygame.font.SysFont("arial", 32, bold=True)
font_small = pygame.font.SysFont("arial", 24, bold=True)

# Game states
START, PLAYING, GAME_OVER = "start", "playing", "game_over"
state = START

# Trail particles behind the rocket: [x, y, life]
trail = []

# Stars: (x, y, size, twinkle_speed, twinkle_offset)
stars = []
for _ in range(90):
    stars.append([
        random.randint(0, WIDTH),
        random.randint(0, HEIGHT),
        random.choice([1, 1, 2]),
        random.uniform(0.02, 0.06),
        random.uniform(0, math.pi * 2)
    ])

# Nebula clouds: (x, y, radius, color, drift_speed)
nebula_clouds = [
    (80, 120, 130, NEBULA_PURPLE),
    (380, 200, 110, NEBULA_BLUE),
    (200, 420, 150, NEBULA_PINK),
    (420, 500, 100, NEBULA_PURPLE),
    (60, 550, 90, NEBULA_BLUE),
]

frame_count = 0


def draw_background():
    # Deep space vertical gradient
    for y in range(HEIGHT):
        t = y / HEIGHT
        if t < 0.5:
            local_t = t / 0.5
            r = int(BG_TOP[0] + (BG_MID[0] - BG_TOP[0]) * local_t)
            g = int(BG_TOP[1] + (BG_MID[1] - BG_TOP[1]) * local_t)
            b = int(BG_TOP[2] + (BG_MID[2] - BG_TOP[2]) * local_t)
        else:
            local_t = (t - 0.5) / 0.5
            r = int(BG_MID[0] + (BG_BOTTOM[0] - BG_MID[0]) * local_t)
            g = int(BG_MID[1] + (BG_BOTTOM[1] - BG_MID[1]) * local_t)
            b = int(BG_MID[2] + (BG_BOTTOM[2] - BG_MID[2]) * local_t)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

    # Soft glowing nebula clouds
    for cx, cy, radius, color in nebula_clouds:
        cloud_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        for i in range(radius, 0, -6):
            alpha = int(14 * (i / radius))
            pygame.draw.circle(cloud_surf, (*color, alpha), (radius, radius), i)
        screen.blit(cloud_surf, (cx - radius, cy - radius))

    # Twinkling stars
    for star in stars:
        x, y, size, speed, offset = star
        brightness = 170 + int(85 * math.sin(frame_count * speed + offset))
        brightness = max(120, min(255, brightness))
        pygame.draw.circle(screen, (brightness, brightness, min(255, brightness + 10)), (x, y), size)


def move_stars():
    for star in stars:
        star[1] += 0.6
        if star[1] > HEIGHT:
            star[1] = 0
            star[0] = random.randint(0, WIDTH)


def draw_glow_text(text, font, color, center, glow_radius=6):
    """Render text with a soft glow behind it."""
    base = font.render(text, True, color)
    for offset in range(glow_radius, 0, -2):
        glow_surf = font.render(text, True, color)
        glow_surf.set_alpha(25)
        rect = glow_surf.get_rect(center=center)
        for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset)]:
            screen.blit(glow_surf, rect.move(dx, dy))
    rect = base.get_rect(center=center)
    screen.blit(base, rect)


def update_trail():
    if state == PLAYING or state == GAME_OVER:
        trail.append([player_x + player_width // 2, player_y + player_height + 4, 20])
    for p in trail[:]:
        p[2] -= 1
        if p[2] <= 0:
            trail.remove(p)


def draw_trail():
    for p in trail:
        x, y, life = p
        alpha = max(0, int(life / 20 * 170))
        radius = max(1, int(life / 20 * 6))
        glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*VIOLET, alpha), (radius, radius), radius)
        screen.blit(glow_surf, (x - radius, y - radius))


def draw_rocket(x, y):
    """Cute rocket mascot with cosmic color scheme."""
    cx = x + player_width // 2
    top = y

    flame_h = 12 + (frame_count % 6)
    pygame.draw.polygon(screen, ELECTRIC_CYAN, [
        (cx - 8, y + player_height),
        (cx + 8, y + player_height),
        (cx, y + player_height + flame_h)
    ])
    pygame.draw.polygon(screen, WHITE, [
        (cx - 4, y + player_height),
        (cx + 4, y + player_height),
        (cx, y + player_height + flame_h - 5)
    ])

    body_rect = pygame.Rect(x + 6, top + 10, player_width - 12, player_height - 14)
    pygame.draw.ellipse(screen, WHITE, body_rect)
    pygame.draw.rect(screen, WHITE, (x + 6, top + 22, player_width - 12, player_height - 24))

    pygame.draw.polygon(screen, VIOLET, [
        (cx - 12, top + 14),
        (cx + 12, top + 14),
        (cx, top)
    ])

    pygame.draw.polygon(screen, NEBULA_BLUE, [
        (x + 4, top + player_height - 16),
        (x - 4, top + player_height - 2),
        (x + 10, top + player_height - 10)
    ])
    pygame.draw.polygon(screen, NEBULA_BLUE, [
        (x + player_width - 4, top + player_height - 16),
        (x + player_width + 4, top + player_height - 2),
        (x + player_width - 10, top + player_height - 10)
    ])

    pygame.draw.circle(screen, ELECTRIC_CYAN, (cx, top + 22), 8)
    pygame.draw.circle(screen, WHITE, (cx, top + 22), 8, 1)
    pygame.draw.circle(screen, (20, 10, 30), (cx - 3, top + 21), 1)
    pygame.draw.circle(screen, (20, 10, 30), (cx + 3, top + 21), 1)


def draw_asteroid(x, y, rot):
    """Chunky rocky asteroid with craters."""
    cx, cy = x + asteroid_size // 2, y + asteroid_size // 2
    points = []
    for i in range(8):
        angle = rot + i * (math.pi * 2 / 8)
        r = asteroid_size // 2 + random.Random(i + int(x)).randint(-3, 2)
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    pygame.draw.polygon(screen, (150, 110, 90), points)
    pygame.draw.polygon(screen, (90, 60, 55), points, 2)
    pygame.draw.circle(screen, (90, 60, 55), (cx - 5, cy - 3), 3)
    pygame.draw.circle(screen, (90, 60, 55), (cx + 4, cy + 5), 2)


def draw_logo(cx, cy, scale=1.0):
    pygame.draw.circle(screen, ELECTRIC_CYAN, (cx, cy), int(34 * scale), 2)
    r_w, r_h = int(14 * scale), int(20 * scale)
    top = cy - r_h // 2
    pygame.draw.ellipse(screen, WHITE, (cx - r_w // 2, top + 6, r_w, r_h))
    pygame.draw.polygon(screen, VIOLET, [
        (cx - r_w // 2, top + 8), (cx + r_w // 2, top + 8), (cx, top)
    ])
    pygame.draw.circle(screen, ELECTRIC_CYAN, (cx, top + 12), int(3 * scale))


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
    trail.clear()
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
                    sounds.start_sound.play()
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
                    sounds.hit_sound.play()

        update_trail()

        # Draw
        draw_background()
        move_stars()

        if state == START:
            draw_logo(WIDTH // 2, HEIGHT // 2 - 150, scale=1.6)

            pulse = 1 + 0.03 * math.sin(frame_count * 0.05)
            title_surf = font_big.render("SPACE DODGER", True, GOLD)
            title_surf = pygame.transform.rotozoom(title_surf, 0, pulse)
            title_rect = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 55))
            screen.blit(title_surf, title_rect)

            draw_glow_text("Press SPACE to Start", font_med, WHITE, (WIDTH // 2, HEIGHT // 2 + 15))

            hint = font_small.render("Arrow keys to move  ·  dodge the asteroids", True, ELECTRIC_CYAN)
            hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
            screen.blit(hint, hint_rect)

            draw_trail()
            draw_rocket(WIDTH // 2 - player_width // 2, HEIGHT - 140)

        elif state == PLAYING:
            draw_trail()
            for asteroid in asteroids:
                draw_asteroid(asteroid[0], asteroid[1], asteroid[2])
            draw_rocket(player_x, player_y)

            score_text = font_small.render(f"★ {score // 10}", True, WHITE)
            screen.blit(score_text, (14, 14))

        elif state == GAME_OVER:
            draw_trail()
            for asteroid in asteroids:
                draw_asteroid(asteroid[0], asteroid[1], asteroid[2])
            draw_rocket(player_x, player_y)

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((5, 4, 20, 170))
            screen.blit(overlay, (0, 0))

            draw_glow_text("GAME OVER", font_big, GOLD, (WIDTH // 2, HEIGHT // 2 - 50), glow_radius=8)

            score_line = font_med.render(f"Score {score // 10}   Best {high_score}", True, ELECTRIC_CYAN)
            score_rect = score_line.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
            screen.blit(score_line, score_rect)

            restart_text = font_small.render("Press R to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55))
            screen.blit(restart_text, restart_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()