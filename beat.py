import pygame
import time
import math

#Takes volatility and transfers it to beat

standard_deviation_current = 100

def sd_to_score_log(sd, sd_min=0.35, sd_max=355, score_min=10, score_max=100):
    """
    Logarithmic inverse mapping: compresses large SDs for better spread
    """
    # Clip SD to avoid math errors
    sd = max(min(sd, sd_max), sd_min)
    score = score_min + (score_max - score_min) * (math.log(sd_max) - math.log(sd)) / (math.log(sd_max) - math.log(sd_min))
    return score

# Initialize audio engine
pygame.mixer.init()
# Load sounds
kick = pygame.mixer.Sound("sounds/KICK.wav")
snare = pygame.mixer.Sound("sounds/SNARE.wav")
hihat = pygame.mixer.Sound("sounds/HIHAT.mp3")
# Define beat patterns (8 steps)
kick_pattern = [1, 0, 0, 0, 1, 0, 0, 0]
snare_pattern = [0, 0, 1, 0, 0, 0, 1, 0]
hihat_pattern = [1, 1, 1, 1, 1, 1, 1, 1]
# Tempo control
bpm = 120
beat_time = sd_to_score_log(standard_deviation_current) / bpm  # seconds per beat step
# Main loop
while True:
    for i in range(8):
        if kick_pattern[i]:
            kick.play()
        if snare_pattern[i]:
            snare.play()
        if hihat_pattern[i]:
            hihat.play()
        time.sleep(beat_time)