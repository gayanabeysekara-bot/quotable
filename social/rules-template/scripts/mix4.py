#!/usr/bin/env python3
"""Audio for 'Rules Nobody Tells You': Kokoro VO + synthesized pen scratch, page turns,
cover thump and a lo-fi electric-piano bed with vinyl crackle. All generated here.
usage: mix4.py <ep_dir> <out.wav>"""
import sys, json, subprocess, wave
import numpy as np

D, OUT = sys.argv[1:3]
TL = json.load(open(f"{D}/timeline.json"))
SR = 48000; END = TL["end"]; L = int(END * SR)
rng = np.random.default_rng(7)
mix = np.zeros((L, 2), np.float32)

def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
def add(sig, at, gain=1.0, pan=0.0):
    i = int(at * SR)
    if sig.ndim == 1: sig = np.stack([sig * (1 - max(0, pan)), sig * (1 + min(0, pan))], 1)
    n = min(len(sig), L - i)
    if n > 0 and i >= 0: mix[i:i + n] += sig[:n] * gain
def bandpass(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= ((f >= lo) & (f <= hi)) * 1.0; return np.fft.irfft(X, len(x)).astype(np.float32)

# ---- voiceover ----
vo_times = [("intro", TL["intro_vo"])] + [(f"p{pi}r{ri}", r["vo"]) for pi, p in enumerate(TL["pages"]) for ri, r in enumerate(p["rules"])] + [("outro", TL["outro_vo"])]
vo_mask = np.zeros(L, np.float32)
for key, at in vo_times:
    s = load(f"{D}/vo/{key}.wav"); add(s, at, 1.3)
    a, b = int(at * SR), min(L, int(at * SR) + len(s)); vo_mask[a:b] = 1

# ---- pen scratch: band-passed noise with stroke rhythm ----
def scratch(dur, under=False):
    n = int(dur * SR); t = np.arange(n) / SR
    x = bandpass(rng.normal(0, 1, n).astype(np.float32), 2500 if not under else 1800, 9000)
    if under: env = np.clip(t / 0.05, 0, 1) * np.clip((dur - t) / 0.08, 0, 1) * 0.8
    else:
        strokes = 0.55 + 0.45 * np.sin(2 * np.pi * (7 + rng.uniform(-1, 1)) * t + rng.uniform(0, 6)) ** 2
        gaps = (np.sin(2 * np.pi * 1.3 * t + rng.uniform(0, 6)) > -0.75).astype(np.float32)
        env = strokes * gaps * np.clip(t / 0.03, 0, 1) * np.clip((dur - t) / 0.05, 0, 1)
    return x * env
for p in TL["pages"]:
    for r in p["rules"]:
        add(scratch(r["write"][1] - r["write"][0]), r["write"][0], 0.045, 0.25)
        add(scratch(r["underline"][1] - r["underline"][0], True), r["underline"][0], 0.05, 0.25)

# ---- page turn: paper swish + flutter ----
def page_turn(dur=1.4):
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.normal(0, 1, n).astype(np.float32)
    lo = bandpass(x, 300, 2500); hi = bandpass(x, 3000, 10000)
    env = np.exp(-((t - dur * 0.45) / (dur * 0.22)) ** 2)
    flutter = 0.7 + 0.3 * np.sin(2 * np.pi * 23 * t) ** 2
    return (lo * 0.7 + hi * 0.5) * env * flutter
for p in TL["pages"]:
    if p["turn"]: add(page_turn(p["turn"][1] - p["turn"][0]), p["turn"][0], 0.16, -0.2)
# cover opening: creak swish + soft thump when it lands
add(page_turn(1.9), TL["cover"][0], 0.1)
tt = np.arange(int(0.5 * SR)) / SR
add((np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 14) + bandpass(rng.normal(0, 1, len(tt)).astype(np.float32), 80, 600) * np.exp(-tt * 30) * 0.5), TL["cover"][1] - 0.05, 0.35)
# pen laid down at the end
tt = np.arange(int(0.25 * SR)) / SR
add(np.sin(2 * np.pi * 900 * tt) * np.exp(-tt * 40) * 0.5 + bandpass(rng.normal(0, 1, len(tt)).astype(np.float32), 1000, 6000) * np.exp(-tt * 60), TL["outro"] + 1.35, 0.12)

# ---- lo-fi electric piano bed ----
BPM = 72; beat = 60 / BPM
def note(f, dur, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    trem = 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
    s = (np.sin(2 * np.pi * f * t) + 0.32 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 3) + 0.08 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 6))
    env = np.clip(t / 0.012, 0, 1) * np.exp(-t * 1.1) * np.clip((dur - t) / 0.3, 0, 1)
    return (s * env * trem * vel).astype(np.float32)
mid = lambda m: 440 * 2 ** ((m - 69) / 12)
CHORDS = [[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]]  # Fmaj7 Em7 Dm7 Cmaj7
MEL = [72, None, 71, 69, None, 67, 69, None, 64, None, 67, 65, None, 64, None, None]
bar = 4 * beat; t0 = 0.2; i = 0
bed = np.zeros((L, 2), np.float32)
def badd(sig, at, gain, pan=0):
    k = int(at * SR); n = min(len(sig), L - k)
    if n > 0: bed[k:k + n, 0] += sig[:n] * gain * (1 - max(0, pan)); bed[k:k + n, 1] += sig[:n] * gain * (1 + min(0, pan))
while t0 < END:
    ch = CHORDS[i % 4]
    for j, m in enumerate(ch): badd(note(mid(m), bar + 0.8, 0.8), t0 + j * 0.03 + rng.uniform(0, 0.02), 0.06, (j - 1.5) * 0.15)
    badd(note(mid(ch[0] - 12), bar, 1.0), t0, 0.07)
    for k in range(4):
        m = MEL[(i * 4 + k) % len(MEL)]
        if m and rng.random() > 0.25: badd(note(mid(m), beat * 1.6, 0.6), t0 + k * beat + rng.uniform(0, 0.03), 0.035, 0.2)
    # soft brushed hat on off-beats
    for k in range(8):
        h = bandpass(rng.normal(0, 1, int(0.06 * SR)).astype(np.float32), 6000, 14000) * np.exp(-np.arange(int(0.06 * SR)) / SR * 60)
        badd(h, t0 + k * beat / 2 + beat / 4, 0.012 if k % 2 else 0.006)
    t0 += bar; i += 1
# vinyl crackle
cr = np.zeros(L, np.float32); idx = rng.integers(0, L, int(END * 25)); cr[idx] = rng.uniform(-1, 1, len(idx))
cr = bandpass(cr, 1500, 9000) * 0.6 + bandpass(rng.normal(0, 1, L).astype(np.float32), 200, 4000) * 0.01
bed[:, 0] += cr * 0.05; bed[:, 1] += cr * 0.05
# duck bed under VO (smoothed)
k = int(0.25 * SR); sm = np.convolve(vo_mask, np.ones(k) / k, mode="same")
tl = np.arange(L) / SR
bed *= (1 - 0.35 * sm)[:, None] * np.clip(tl / 1.5, 0, 1)[:, None]
mix += bed

mix = np.tanh(mix * 1.15) / np.tanh(1.15)
mix *= np.clip((END - tl) / 1.2, 0, 1)[:, None]
pk = np.abs(mix).max(); mix *= 0.92 / pk if pk > 0.92 else 1
with wave.open(OUT, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("audio", round(END, 2), "s")
