import json
import numpy as np
from midiutil import MIDIFile

# -----------------------------
# 1) Pull stock data from JSON
# -----------------------------
DATA_PATH = "stocks_daily_prices.json"
TICKER = "TTD"  # choose your stock (must be in the JSON)
STOCK_NAME = "The Trade Desk"  # for file naming and rotation seeds
LAST_N = None  # or None for all

with open(DATA_PATH, "r", encoding="utf-8") as f:
    rows = json.load(f)  # list of dicts

# filter to ticker (and make sure price exists)
prices = [float(r["price"]) for r in rows if r.get("ticker") == TICKER and "price" in r]

# keep only last N (based on file order)
if LAST_N is not None:
    prices = prices[-LAST_N:]

print("Loaded", len(prices), "prices for", TICKER)

# -----------------------------
# 2) Techno settings
# -----------------------------
stock_steps_per_bar = 8   # 8 trading days per bar (volatility window)

steps_per_bar = 16        # 16th-note grid
bpm = 150
step_beats = 0.25         # 16 * 0.25 = 4 beats

W = 40
root_midi = 48            # C3
octaves = 3

# C natural minor: C D Eb F G Ab Bb
SCALE_OFFSETS = np.array([0, 2, 3, 5, 7, 8, 10], dtype=int)

k_min, k_max = 4, 16          # allow full 16ths in extreme volatility
density_gamma = 0.45          # ramps to dense faster
gate = 0.85                  # base gate (we’ll tighten more per-bar)
lead_vmin, lead_vmax = 50, 120

# Instruments (General MIDI)
LEAD_PROGRAM = 87         # 84 = Lead 5 (charang) (edgy)
BASS_PROGRAM = 39         # 38 = Synth Bass 1 (rounder)

# Drum kit channel
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

# Bass degrees for minor techno feel: i, bVII, bVI, v
BASS_DEG_OFFSETS = np.array([0, 10, 8, 7], dtype=int)

def pick_bass_note(v: float, bar_ret: float, root_bass: int) -> int:
    base = 0 if bar_ret >= 0 else 1
    shift = 0 if v < 0.35 else (1 if v < 0.70 else 2)
    idx = (base + shift) % len(BASS_DEG_OFFSETS)
    note = root_bass + int(BASS_DEG_OFFSETS[idx])
    if v > 0.80 and np.random.random() < 0.30:
        note -= 12
    return note

def v_to_bass_k(v: float, kmin: int = 4, kmax: int = 12) -> int:
    gamma = 0.75
    vv = float(np.clip(v, 0.0, 1.0)) ** gamma
    return int(round(kmin + (kmax - kmin) * vv))

def vol_to_01(bar_vol: np.ndarray) -> np.ndarray:
    lo = np.percentile(bar_vol, 10)
    hi = np.percentile(bar_vol, 90)
    if hi <= lo:
        hi = lo + 1e-9
    return np.clip((bar_vol - lo) / (hi - lo), 0.0, 1.0)

def v_to_k(v: float, kmin: int, kmax: int, gamma: float = 0.7) -> int:
    vv = float(np.clip(v, 0.0, 1.0)) ** gamma
    return int(round(kmin + (kmax - kmin) * vv))

def stock_rotation(name: str, mod: int) -> int:
    return abs(hash(name)) % mod

def accent_vel(base: int, boost: int, on: bool) -> int:
    return int(np.clip(base + (boost if on else 0), 1, 127))

def clamp127(x: int) -> int:
    return int(np.clip(x, 1, 127))

def chaos_amount(v: float) -> float:
    """
    Map volatility v in [0,1] -> chaos in [0,1], mostly only above ~0.6.
    Keeps calm bars stable.
    """
    return float(np.clip((v - 0.60) / 0.40, 0.0, 1.0))

def maybe_transpose_octaves(note: int, v: float) -> int:
    """
    Musical chaos: occasional octave jumps in high volatility.
    """
    c = chaos_amount(v)
    if c <= 0:
        return note
    # modest octave-up chance, bigger when very chaotic
    if np.random.random() < (0.08 + 0.25 * c):
        note += 12
    # rare +2 octave spike (very chaotic)
    if np.random.random() < (0.01 + 0.08 * c):
        note += 12
    return note

def add_ratchet_notes(midi, track, ch, note, start, step_beats, v, vel):
    """
    Add 2–3 fast repeats inside a single step when volatility is high.
    """
    c = chaos_amount(v)
    if c <= 0:
        return

    p = 0.10 + 0.55 * c  # 0.10..0.65
    if np.random.random() > p:
        return

    reps = 2 if np.random.random() < 0.7 else 3
    sub = step_beats / reps
    dur = sub * 0.55

    for r in range(1, reps):
        midi.addNote(track, ch, note, start + r * sub, dur, clamp127(vel - 20))


# -----------------------------
# 5) Returns + bar volatility
# -----------------------------
prices_arr = np.array(prices, dtype=float)
if len(prices_arr) < W + 1:
    raise ValueError(f"Need at least W+1 prices. You gave {len(prices_arr)} and W={W}.")

returns = np.diff(np.log(prices_arr))
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

midi.addProgramChange(bass_track, 1, 0, BASS_PROGRAM)
midi.addProgramChange(lead_track, 0, 0, LEAD_PROGRAM)

# FX sends (CC91 reverb, CC93 chorus)
midi.addControllerEvent(lead_track, 0, 0, 91, 55)
midi.addControllerEvent(lead_track, 0, 0, 93, 35)
midi.addControllerEvent(bass_track, 1, 0, 91, 10)
midi.addControllerEvent(bass_track, 1, 0, 93, 0)

t = 0.0

root_bass = root_midi - 12

# stock-specific rotations computed once
hat_rot  = stock_rotation(STOCK_NAME + "_hat", steps_per_bar)
perc_rot = stock_rotation(STOCK_NAME + "_perc", steps_per_bar)
open_hat_step = (14 if (stock_rotation(STOCK_NAME + "_oh", 2) == 0) else 12)

for b in range(num_stock_bars):
    v = float(v_norm[b])

    # Lead Euclid pattern
    k = v_to_k(v, k_min, k_max, gamma=density_gamma)
    lead_pat = rotate(bjorklund(k, steps_per_bar), r=0)

    bar_len = steps_per_bar * step_beats

    # ---- per-bar stock features ----
    bar_slice = returns[b * stock_steps_per_bar:(b + 1) * stock_steps_per_bar]
    bar_ret = float(np.sum(bar_slice))
    up_bar = (bar_ret >= 0)

    # -----------------------------
    # DRUMS (only ONE system now)
    # -----------------------------
    CLAP = 39
    RIM  = 37
    SHAKER = 70
    TOM_LO = 45

    # Kick: constant 4-on-floor
    for s in (0, 4, 8, 12):
        midi.addNote(dr_track, DRUM_CH, KICK, t + s * step_beats, step_beats * 0.5, 120)

    # Backbeat: clap on up bars, snare on down bars
    backbeat_note = CLAP if up_bar else SNARE
    for s in (4, 12):
        midi.addNote(dr_track, DRUM_CH, backbeat_note, t + s * step_beats, step_beats * 0.35, 92)

    # Ghost backbeat on late step when volatile
    if v > 0.6 and np.random.random() < (0.25 + 0.5 * v):
        midi.addNote(dr_track, DRUM_CH, backbeat_note, t + 15 * step_beats, step_beats * 0.2, 45)

    # Hats: Euclidean density
    hat_k = v_to_k(v, kmin=6, kmax=14, gamma=0.65)
    hat_pat = rotate(bjorklund(hat_k, steps_per_bar), hat_rot)

    for s in range(steps_per_bar):
        if hat_pat[s] == 1:
            offbeat = (s % 4 == 2)  # 2,6,10,14
            vel_hat = accent_vel(base=55, boost=20, on=offbeat)
            vel_hat = int(np.clip(vel_hat + 20 * v, 1, 127))
            midi.addNote(dr_track, DRUM_CH, CL_HAT, t + s * step_beats, step_beats * 0.18, vel_hat)

    # Open hat
    if np.random.random() < (0.15 + 0.55 * v):
        midi.addNote(dr_track, DRUM_CH, OP_HAT, t + open_hat_step * step_beats, step_beats * 0.75, 75)

    # Extra percussion (fix: fully inside the if)
    perc_k = v_to_k(v, kmin=0, kmax=7, gamma=0.9)
    if perc_k > 0:
        perc_pat = rotate(bjorklund(perc_k, steps_per_bar), perc_rot)
        perc_note = SHAKER if up_bar else RIM
        for s in range(steps_per_bar):
            if perc_pat[s] == 1:
                midi.addNote(dr_track, DRUM_CH, perc_note, t + s * step_beats, step_beats * 0.12, int(35 + 35 * v))

    # Tiny fill at bar end
    if v > 0.85 and np.random.random() < 0.35:
        for s in (13, 14, 15):
            midi.addNote(dr_track, DRUM_CH, TOM_LO, t + s * step_beats, step_beats * 0.18, 60)

    # -----------------------------
    # BASS: degree + Euclidean rhythm
    # -----------------------------
    bass_note = pick_bass_note(v, bar_ret, root_bass)

    bass_k = v_to_bass_k(v)
    bass_pat = rotate(bjorklund(bass_k, steps_per_bar), r=0)

    bass_dur = step_beats * (0.35 if v < 0.55 else 0.25)
    bass_vel2 = int(np.clip(55 + 45 * v, 1, 127))

    for s in range(steps_per_bar):
        if bass_pat[s] == 1:
            midi.addNote(bass_track, 1, bass_note, t + s * step_beats, bass_dur, bass_vel2)

    # -----------------------------
    # LEAD: Euclidean + musical chaos (fills + ratchets)
    # -----------------------------
    c = chaos_amount(v)

    # When chaotic, sprinkle extra hits onto empty steps (but not everywhere)
    fill_prob = 0.02 + 0.35 * c          # calm ~2%, chaos ~37%
    # Also allow "runs" (short consecutive hits) in very chaotic bars
    run_prob  = 0.00 + 0.20 * c          # up to 20%

    # Build an "expanded" pattern from lead_pat
    expanded = lead_pat[:]  # copy list

    for s in range(steps_per_bar):
        if expanded[s] == 0 and np.random.random() < fill_prob:
            expanded[s] = 1
            # occasionally make a 2-step run (chaos burst)
            if s + 1 < steps_per_bar and expanded[s + 1] == 0 and np.random.random() < run_prob:
                expanded[s + 1] = 1

    # tighter gate when chaotic -> stabbier techno
    local_gate = 0.80 - 0.35 * c   # 0.80 down to 0.45
    local_gate = float(np.clip(local_gate, 0.35, 0.85))

    last_note = None  # motif memory within the bar

    for s in range(steps_per_bar):
        if expanded[s] != 1:
            continue

        day_in_bar = int(round((s / (steps_per_bar - 1)) * (stock_steps_per_bar - 1)))
        idx = b * stock_steps_per_bar + day_in_bar
        if idx < (W - 1) or idx >= num_steps:
            continue

        window = returns[idx - (W - 1): idx + 1]
        q = rolling_quantile_last(window)
        note = quantile_to_midi(q, scale_steps)

        # Motif memory: when adding extra hits, bias toward repeating last note
        # This keeps chaos musical instead of random.
        if last_note is not None and np.random.random() < (0.55 * c):
            note = last_note

        note = maybe_transpose_octaves(note, v)

        vel = int(np.clip(lead_vmin + (lead_vmax - lead_vmin) * (0.35 * q + 0.65 * v), 1, 127))
        # extra "bite" when chaotic
        vel = clamp127(int(vel + 18 * c))

        start = t + s * step_beats
        dur = step_beats * local_gate

        midi.addNote(lead_track, 0, note, start, dur, vel)

        # ratchets: micro-bursts in high volatility
        add_ratchet_notes(midi, lead_track, 0, note, start, step_beats, v, vel)

        last_note = note

    t += bar_len

out_path = f"{STOCK_NAME.replace(' ', '_')}_TECHNO.mid"
with open(out_path, "wb") as f:
    midi.writeFile(f)

print("Wrote:", out_path)
