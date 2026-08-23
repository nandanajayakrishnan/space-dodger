import pygame
import numpy as np

pygame.mixer.init()

def make_tone(frequency, duration_ms, volume=0.3, fade_ms=30):
    sample_rate = pygame.mixer.get_init()[0]
    n_samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n_samples, False)
    wave = np.sin(frequency * t * 2 * np.pi)

    # Fade in/out to avoid clicking sound
    fade_samples = int(sample_rate * fade_ms / 1000)
    if fade_samples > 0 and fade_samples < n_samples // 2:
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        wave[:fade_samples] *= fade_in
        wave[-fade_samples:] *= fade_out

    wave = (wave * volume * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    sound = pygame.sndarray.make_sound(stereo_wave)
    return sound

# Pre-made sound effects
hit_sound = make_tone(150, 300, volume=0.4)      # low thud for collision
score_tick_sound = make_tone(880, 60, volume=0.15)  # subtle tick, currently unused but available
start_sound = make_tone(660, 150, volume=0.3)     # rising blip for game start