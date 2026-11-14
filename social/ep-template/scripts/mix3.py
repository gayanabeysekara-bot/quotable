#!/usr/bin/env python3
"""Audio for Quotable Nights Ep.01: clip audio (ducked under VO) + Kokoro VO + synthesized kawaii SFX + music box.
usage: mix3.py <clip.mp4> <vo_dir> <out.wav>
"""
import sys, subprocess, numpy as np, wave

SRC, VO, OUT = sys.argv[1:4]
SR = 48000
INTRO, CLIP = 4.5, 61.4
OUTRO_T = INTRO + CLIP
DUR = OUTRO_T + 6.4
L = int(DUR * SR)

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

mix = np.zeros((L, 2), np.float32)
def add(sig, at, gain=1.0):
    i = int(at * SR)
    if sig.ndim == 1: sig = np.stack([sig, sig], 1)
    n = min(len(sig), L - i)
    if n > 0: mix[i:i + n] += sig[:n] * gain

# ---- clip audio with ducking under the voiceover ----
VO_AT = {"intro": 0.4, "a": INTRO + 17.0, "b": INTRO + 48.5, "outro": OUTRO_T + 0.4}
vo = {k: load(f"{VO}/{k}.wav") for k in VO_AT}
clip = load(SRC)[: int(CLIP * SR)]
env = np.ones(len(clip), np.float32)
tt = np.arange(len(clip)) / SR + INTRO
for k in ("a", "b"):
    a, b = VO_AT[k] - 0.3, VO_AT[k] + len(vo[k]) / SR + 0.3
    ramp = np.clip(np.minimum((tt - a) / 0.3, (b - tt) / 0.3), 0, 1)
    env = np.minimum(env, 1 - 0.68 * ramp)
fade = np.clip((INTRO + CLIP - tt) / 0.6, 0, 1) * np.clip((tt - INTRO) / 0.25, 0, 1)
add(clip * (env * fade)[:, None], INTRO, 0.9)
for k, at in VO_AT.items():
    add(vo[k], at, 1.25)

# ---- synth helpers ----
def tone(f0, f1, dur, decay=12.0, harm=(1.0, 0.35, 0.12)):
    t = np.arange(int(dur * SR)) / SR
    f = np.linspace(f0, f1, len(t)); ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(a * np.sin(ph * (i + 1)) for i, a in enumerate(harm))
    e = np.exp(-t * decay) * np.clip(t / 0.004, 0, 1)
    return (s * e).astype(np.float32)
def click(dur=0.012, seed=0):
    rng = np.random.default_rng(seed); n = int(dur * SR)
    return (rng.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 400)).astype(np.float32)

# bubble pops (match the chat timeline in render3.py)
MSGS = [(1.0, "me"), (4.2, "them"), (8.0, "them"), (11.5, "me"), (18.0, "them"), (24.0, "me")]
for c, side in MSGS:
    if side == "me": add(tone(700, 1250, 0.18, 20), INTRO + c, 0.22)
    else: add(tone(620, 470, 0.2, 18), INTRO + c, 0.22)
add(tone(2200, 2200, 0.05, 80), INTRO + 31.5, 0.12)                       # delivered tick
add(tone(1318, 1318, 0.6, 5), INTRO + 44.5, 0.16); add(tone(1046, 1046, 0.9, 4), INTRO + 44.75, 0.16)  # seen chime
add(tone(330, 210, 0.35, 9), INTRO + 52.0, 0.25)                          # no reply bloop
# keyboard taps while drafting / deleting
rng = np.random.default_rng(1)
for a, b in ((35.5, 39.6), (40.1, 41.4), (42.0, 42.7), (43.4, 43.9)):
    t = a
    while t < b:
        add(click(seed=int(t * 1000)), INTRO + t, 0.05); t += rng.uniform(0.07, 0.13)
# typing indicator soft blips
for a, b in ((14.0, 17.6), (57.0, 59.6)):
    add(tone(880, 880, 0.1, 30), INTRO + a, 0.06)

# ---- music box for intro and outro ----
PENTA = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
def musicbox(start, dur, seed):
    r = np.random.default_rng(seed); t = 0.0; seq = [0, 2, 4, 3, 5, 4, 2, 1, 0, 2, 3, 1]
    i = 0
    while t < dur - 0.4:
        f = PENTA[seq[i % len(seq)]]
        add(tone(f, f, 1.2, 3.5, (1.0, 0.0, 0.25, 0.0, 0.08)), start + t, 0.07)
        if i % 4 == 0: add(tone(f / 2, f / 2, 1.6, 2.5, (1.0, 0.2)), start + t, 0.05)
        t += 0.32; i += 1
musicbox(0.0, INTRO + 0.4, 3)
musicbox(OUTRO_T, DUR - OUTRO_T, 4)

# master: gentle limiter + fades
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
tl = np.arange(L) / SR
mix *= np.clip(tl / 0.2, 0, 1)[:, None] * np.clip((DUR - tl) / 0.6, 0, 1)[:, None]
pk = np.abs(mix).max(); mix *= 0.93 / pk if pk > 0.93 else 1
pcm = (mix * 32767).astype(np.int16)
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("audio", DUR, "s")
