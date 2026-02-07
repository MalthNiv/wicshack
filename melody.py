import json
import numpy as np
from midiutil import MIDIFile

np.random.seed(123)

# -----------------------------
# 1) Pull stock data from JSON
# -----------------------------
DATA_PATH = "stocks_daily_prices.json"
STOCK_NAME = "JP Morgan"
LAST_N = 220

with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

prices = data["daily_prices"][STOCK_NAME]
if LAST_N is not None:
    prices = prices[-LAST_N:]

print("Loaded", len(prices), "prices for", STOCK_NAME)

# -----------------------------
# 2) Techno settings
# -----------------------------
# Stock-bar logic
stock_steps_per_bar = 8   # 8 trading days per bar (volatility window for rhythm intensity)

# Music grid (techno)
steps_per_bar = 16        # 16th-note grid
bpm = 140                 # techno tempo
step_beats = 0.25         # 16 steps * 0.25 = 4 beats per bar
gate = 0.9

# Pitch mapping (rolling quantile -> scale) using returns history
W = 60
root_midi = 48            # C3
octaves = 2

# C natural minor (techno-friendly): C D Eb F G Ab Bb
SCALE_OFFSETS = np.array([0, 2, 3, 5, 7, 8, 10], dtype=int)

# Lead density range (E(k,16)) driven by volatility
k_min, k_max = 5, 14
density_gamma = 0.65      # <1 ramps density faster

# Instruments (General MIDI programs)
LEAD_PROGRAM = 82         # Lead 2 (sawtooth)
BASS_PROGRAM = 39         # Synth Bass 2 (more aggressive than 38)

# Velocities
lead_vmin, lead_vmax = 60, 110
bass_vel = 70

# Drum kit (Channel 9 in MIDIUtil is channel=9)
DRUM_CH = 9
KICK = 36
SNARE = 38
CL_HAT = 42
OP_HAT = 46

# -----------------------------
# 3) Helpers: scale + quantiles
# -----------------------------
def build_scale_steps(root: int, octaves: int, offsets: np.ndarray) -> np.ndarray:
    steps = []
    for o in range(octaves):
        for off in offsets:
            steps.append(root + 12 * o + int(off))
    return np.array(steps, dtype=int)

def rolling_quantile_last(window_vals: np.ndarray) -> float:
    last = window_vals[-1]
    count_le = np.sum(window_vals <= last)
    return (count_le - 1) / (len(window_vals) - 1)

def quantile_to_midi(q: float, scale_steps: np.ndarray) -> int:
    N = len(scale_steps)
    idx = int(np.round(q * (N - 1)))
    idx = max(0, min(N - 1, idx))
    return int(scale_steps[idx])

# -----------------------------
# 4) Euclidean rhythm (Bjorklund)
# -----------------------------
def bjorklund(k: int, n: int) -> list[int]:
    if k <= 0:
        return [0] * n
    if k >= n:
        return [1] * n

    counts = []
    remainders = [k]
    divisor = n - k
    level = 0

    while True:
        counts.append(divisor // remainders[level])
        remainders.append(divisor % remainders[level])
        divisor = remainders[level]
        level += 1
        if remainders[level] <= 1:
            break
    counts.append(divisor)

    def build(level: int) -> list[int]:
        if level == -1:
            return [0]
        if level == -2:
            return [1]
        res = []
        for _ in range(counts[level]):
            res += build(level - 1)
        if remainders[level] != 0:
            res += build(level - 2)
        return res

    return build(level)[:n]

def rotate(pattern: list[int], r: int) -> list[int]:
    if not pattern:
        return pattern
    r %= len(pattern)
    return pattern[r:] + pattern[:r]

def vol_to_01(bar_vol: np.ndarray) -> np.ndarray:
    lo = np.percentile(bar_vol, 10)
    hi = np.percentile(bar_vol, 90)
    if hi <= lo:
        hi = lo + 1e-9
    return np.clip((bar_vol - lo) / (hi - lo), 0.0, 1.0)

def v_to_k(v: float) -> int:
    v2 = float(np.clip(v, 0.0, 1.0)) ** density_gamma
    return int(round(k_min + (k_max - k_min) * v2))

# -----------------------------
# 5) Returns + bar volatility (from 8-day stock bars)
# -----------------------------
prices_arr = np.array(prices, dtype=float)
if len(prices_arr) < W + 1:
    raise ValueError(f"Need at least W+1 prices. You gave {len(prices_arr)} and W={W}.")

returns = np.diff(np.log(prices_arr))  # daily returns
num_steps = len(returns)

num_stock_bars = num_steps // stock_steps_per_bar
if num_stock_bars == 0:
    raise ValueError("Not enough data for even one 8-day stock bar. Increase LAST_N.")

scale_steps = build_scale_steps(root_midi, octaves, SCALE_OFFSETS)

bar_vol = np.array([
    float(np.std(returns[b * stock_steps_per_bar:(b + 1) * stock_steps_per_bar]))
    for b in range(num_stock_bars)
])
v_norm = vol_to_01(bar_vol)

# -----------------------------
# 6) Build MIDI: drums + bass + lead
# -----------------------------
midi = MIDIFile(3)  # 0=drums, 1=bass, 2=lead
dr_track, bass_track, lead_track = 0, 1, 2
midi.addTempo(dr_track, 0, bpm)
midi.addTempo(bass_track, 0, bpm)
midi.addTempo(lead_track, 0, bpm)

# Program changes
midi.addProgramChange(bass_track, 1, 0, BASS_PROGRAM)
midi.addProgramChange(lead_track, 0, 0, LEAD_PROGRAM)

# Lead FX sends
midi.addControllerEvent(lead_track, 0, 0, 91, 55)  # reverb
midi.addControllerEvent(lead_track, 0, 0, 93, 35)  # chorus

# Bass: keep reverb low or it gets muddy
midi.addControllerEvent(bass_track, 1, 0, 91, 10)
midi.addControllerEvent(bass_track, 1, 0, 93, 0)

# Optional: reverb send (CC91)
midi.addControllerEvent(lead_track, 0, 0, 91, 45)
midi.addControllerEvent(bass_track, 1, 0, 91, 20)

t = 0.0  # beats

# Bass note choices: root and fifth (techno simple)
root_bass = root_midi - 12
fifth_bass = root_bass + 7

for b in range(num_stock_bars):
    v = float(v_norm[b])
    k = v_to_k(v)
    lead_pat = rotate(bjorklund(k, steps_per_bar), r=0)

    bar_len = steps_per_bar * step_beats

    # --- DRUMS: 4-on-the-floor + hats; add more hats when volatile ---
    # Kick on 0,4,8,12
    for s in (0, 4, 8, 12):
        midi.addNote(dr_track, DRUM_CH, KICK, t + s * step_beats, step_beats * 0.5, 110)

    # Snare/clap on 4 and 12 (beats 2 and 4)
    for s in (4, 12):
        midi.addNote(dr_track, DRUM_CH, SNARE, t + s * step_beats, step_beats * 0.4, 90)

    # Closed hats on offbeats (every 2 steps: 1,3,5,...,15)
    for s in range(1, steps_per_bar, 2):
        midi.addNote(dr_track, DRUM_CH, CL_HAT, t + s * step_beats, step_beats * 0.25, 65)

    # Extra 16th hats when volatile (fills space)
    extra_hat_prob = 0.10 + 0.60 * v  # calm ~10%, volatile ~70%
    for s in range(steps_per_bar):
        if (s % 2 == 0) and (np.random.random() < extra_hat_prob):
            midi.addNote(dr_track, DRUM_CH, CL_HAT, t + s * step_beats, step_beats * 0.2, 45)

    # Open hat near end of bar sometimes
    if np.random.random() < (0.2 + 0.5 * v):
        midi.addNote(dr_track, DRUM_CH, OP_HAT, t + 14 * step_beats, step_beats * 0.8, 70)

    # --- BASS: simple root pulse with occasional fifth (more movement when volatile) ---
    # Put bass on steps 0,8 (half-notes). In higher vol, add step 4 too.
    bass_steps = [0, 8] + ([4] if v > 0.55 else [])
    bass_note = root_bass if (b % 2 == 0) else fifth_bass
    for s in bass_steps:
        midi.addNote(bass_track, 1, bass_note, t + s * step_beats, step_beats * 3.5, bass_vel)

    # --- LEAD: Euclidean pattern; pitch from rolling quantile ---
    for s in range(steps_per_bar):
        if lead_pat[s] == 1:
            # map this musical step back into the daily-return index inside the stock bar
            # we pick a representative day in this 8-day bar:
            day_in_bar = int(round((s / (steps_per_bar - 1)) * (stock_steps_per_bar - 1)))
            idx = b * stock_steps_per_bar + day_in_bar

            if idx < (W - 1) or idx >= num_steps:
                continue

            window = returns[idx - (W - 1): idx + 1]
            q = rolling_quantile_last(window)
            note = quantile_to_midi(q, scale_steps)

            if v > 0.75 and np.random.random() < 0.35:
                note += 12  # octave up occasionally

            # Velocity: a bit louder in volatile bars + slightly based on q
            vel = int(np.clip(lead_vmin + (lead_vmax - lead_vmin) * (0.4 * q + 0.6 * v), 1, 127))

            midi.addNote(lead_track, 0, note, t + s * step_beats, step_beats * gate, vel)

    t += bar_len

out_path = f"{STOCK_NAME.replace(' ', '_')}_TECHNO.mid"
with open(out_path, "wb") as f:
    midi.writeFile(f)

print("Wrote:", out_path)
