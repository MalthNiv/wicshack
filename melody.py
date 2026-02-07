import os
import time
import numpy as np
import fluidsynth

# -----------------------------
# 0) Point Python to FluidSynth DLLs (Windows)
# -----------------------------
# os.add_dll_directory(r"C:\tools\fluidsynth\bin")

# -----------------------------
# 1) Provide your dummy prices
# -----------------------------
prices = [100, 101, 99, 102, 103, 101, 104, 103, 105, 106, 108, 107, 109, 110, 108, 111, 112, 114, 113, 115, 116, 118, 117, 119, 120, 118, 121, 122, 124, 123, 125]

# -----------------------------
# 2) Settings
# -----------------------------
W = 5                 # rolling window size
root_midi = 48  # C3
octaves = 2
note_seconds = 0.25

SOUNDFONT = r"C:\tools\soundfonts\FluidR3_GM.sf2"

# Instrument (General MIDI program numbers)
PIANO = 0
NYLON_GUITAR = 24
STEEL_GUITAR = 25
E_GUITAR_CLEAN = 27

INSTRUMENT = PIANO     # change to NYLON_GUITAR, etc.

# -----------------------------
# 3) Init FluidSynth once
# -----------------------------
fs = fluidsynth.Synth()

# Call these AFTER fs.start(...)
try:
    fs.set_gain(0.6)  # overall volume
except Exception:
    pass

# roomsize, damping, width, level
try:
    fs.set_reverb(0.55, 0.35, 0.90, 0.22)
except Exception as e:
    print("Reverb setup failed:", e)

# nr, level, speed, depth_ms, type (0=sine, 1=triangle)
try:
    fs.set_chorus(3, 0.8, 0.30, 4.0, 0)
except Exception as e:
    print("Chorus setup failed:", e)

# Disable MIDI input (we call noteon/noteoff directly)
try:
    fs.setting("midi.driver", "none")
except Exception:
    fs.setting("midi.driver", "null")

# Start audio driver (Windows)
for driver in ("dsound", "wasapi", "winmm"):
    try:
        fs.start(driver=driver)
        print("Audio driver:", driver)
        break
    except Exception as e:
        print("Failed driver:", driver, "|", e)
else:
    raise RuntimeError("No working audio driver found (dsound/wasapi/winmm).")

sfid = fs.sfload(SOUNDFONT)
fs.program_select(0, sfid, 0, INSTRUMENT)  # channel 0

# channel 1 = bass (GM program 32 = Acoustic Bass)
BASS_PROGRAM = 32
fs.program_select(1, sfid, 0, BASS_PROGRAM)

# ----------------------
# Music Helpers
# ----------------------

def bass_note_for_step(step_index: int) -> int:
    # Alternating C2 and G1 gives a solid foundation in C
    C2 = 36
    G1 = 31
    return C2 if (step_index % 2 == 0) else G1

release_tail = 0.1
def play_midi(midi_note: int, seconds: float, velocity: int = 100):
    fs.noteon(0, midi_note, velocity)
    time.sleep(seconds)
    fs.noteoff(0, midi_note)
    time.sleep(release_tail)

# -----------------------------
# 4) Mapping helpers
# -----------------------------
PENT_OFFSETS = np.array([0, 2, 4, 7, 9], dtype=int)  # C D E G A

def build_c_pentatonic_steps(root: int, octaves: int) -> np.ndarray:
    steps = []
    for o in range(octaves):
        for off in PENT_OFFSETS:
            steps.append(root + 12 * o + off)
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

# Optional: map q to velocity so higher quantile feels “stronger”
def quantile_to_velocity(q: float, vmin: int = 60, vmax: int = 115) -> int:
    v = vmin + (vmax - vmin) * q
    return int(max(1, min(127, round(v))))

def smooth_value(new_val: float, prev_val: float | None, alpha: float = 0.15) -> float:
    """
    Exponential smoothing (low-pass filter).
    Smaller alpha = slower/smoother velocity changes.
    """
    return new_val if prev_val is None else (alpha * new_val + (1 - alpha) * prev_val)

def limit_step(target: int, current: int | None, max_step: int = 4) -> int:
    """
    Slew limiter: caps how fast velocity can change per note.
    Smaller max_step = slower changes.
    """
    if current is None:
        return target
    if target > current:
        return min(target, current + max_step)
    return max(target, current - max_step)

# -----------------------------
# 5) Pipeline: prices -> returns -> rolling quantiles -> notes -> play
# -----------------------------
prices_arr = np.array(prices, dtype=float)
if len(prices_arr) < W + 1:
    raise ValueError(f"Need at least W+1 prices. You gave {len(prices_arr)} and W={W}.")

returns = np.diff(np.log(prices_arr))
scale_steps = build_c_pentatonic_steps(root_midi, octaves)

try:
    time.sleep(0.25)  # let the audio driver settle

    # Prime the synth (quiet note) so the first real note doesn't get clipped
    fs.noteon(0, 60, 1)
    time.sleep(0.03)
    fs.noteoff(0, 60)
    time.sleep(0.10)

    q_smooth = None
    prev_vel = None
    bass_current = None

    fs.cc(0, 64, 127)
    for i in range(W - 1, len(returns)):
        # Changing pedal sustain
        if (i % 8) == 0:
            fs.cc(0, 64, 0)    # sustain OFF (clears held notes)
            time.sleep(0.05)
            fs.cc(0, 64, 127)  # sustain ON 
            
         # Bass: change every 2 melody notes, hold longer
        if i % 2 == 0:
            if bass_current is not None:
                fs.noteoff(1, bass_current)
            bass_current = bass_note_for_step(i // 2)
            fs.noteon(1, bass_current, 35)  # bass velocity

        # Main melody note
        window = returns[i - (W - 1): i + 1]
        q = rolling_quantile_last(window)
        midi_note = quantile_to_midi(q, scale_steps)
        q_smooth = smooth_value(q, q_smooth, alpha=0.5)   # try 0.08–0.20
        target_vel = quantile_to_velocity(q_smooth, vmin=70, vmax=105)
        vel = limit_step(target_vel, prev_vel, max_step=6)  # try 2–6
        prev_vel = vel

        # print(f"t={i:02d} return={returns[i]: .5f} q={q: .2f} qS={q_smooth: .2f} midi={midi_note} vel={vel}")
        play_midi(midi_note, note_seconds, velocity=vel)

    # turn off bass at end + let reverb tail ring
    if bass_current is not None:
        fs.noteoff(1, bass_current)
    time.sleep(0.3)

finally:
    fs.delete()
