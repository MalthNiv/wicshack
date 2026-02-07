import pygame
import time
import math
import json

with open("stocks_daily_prices.json", "r") as f:
    data = json.load(f)

# The array of SDs
sd_array = data["standard_deviations"]

# Find JP Morgan's SD
jpm_sd = next(item["standard_deviation"] for item in sd_array if item["name"] == "Bumble")
print(jpm_sd)

standard_deviation_current = jpm_sd

def sd_to_score_nonlinear(sd, sd_min=0.016, sd_max=0.048, score_min=10, score_max=100, gamma=2):
    # Clip SD
    sd = max(min(sd, sd_max), sd_min)
    # Nonlinear mapping
    fraction = (sd_max - sd) / (sd_max - sd_min)
    score = score_min + (score_max - score_min) * (fraction ** gamma)
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
beat_time = sd_to_score_nonlinear(standard_deviation_current) / bpm  # seconds per beat step
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