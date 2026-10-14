#!/usr/bin/env python3
"""Mix dialogue + SFX for "Don't Tell the Cake" and export lip-sync envelopes.

Writes out/audio.wav (44.1k stereo, exactly 10.0 s) and lips.js
(window.LIPS = {mom:[...], dad:[...]} — mouth openness 0..1 per frame at 30 fps).
"""
import json
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SR, DUR, FPS = 44100, 10.0, 30
N = int(SR * DUR)
rng = np.random.default_rng(5)

# (file, speaker, start time) — lines never overlap
LINES = [('line0.wav', 'mom', 0.35), ('line1.wav', 'dad', 2.65),
         ('line2.wav', 'mom', 4.90), ('line3.wav', 'dad', 5.45)]
# door timeline (must match cake.js): seal at end of close, unseal at crack-open, freeze pluck
T_SEAL, T_UNSEAL, T_FREEZE = 7.88, 8.42, 9.15


def read(p):
    with wave.open(p) as w:
        sr, n = w.getframerate(), w.getnframes()
        a = np.frombuffer(w.readframes(n), '<i2').astype(float) / 32768
    return a, sr


def resample(a, sr):
    t = np.arange(int(len(a) * SR / sr)) / SR
    return np.interp(t, np.arange(len(a)) / sr, a)


def band(sig, lo, hi):
    f = np.fft.rfft(sig)
    fr = np.fft.rfftfreq(len(sig), 1 / SR)
    f[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(f, len(sig))


L = np.zeros(N)
R = np.zeros(N)


def add(t0, sig, g=1.0, pan=0.0):
    i0 = int(t0 * SR)
    n = min(len(sig), N - i0)
    L[i0:i0 + n] += sig[:n] * g * np.cos((pan + 1) * np.pi / 4) * 1.414
    R[i0:i0 + n] += sig[:n] * g * np.sin((pan + 1) * np.pi / 4) * 1.414


# ---- dialogue + lip envelopes
frames = int(DUR * FPS)
lips = {'mom': np.zeros(frames), 'dad': np.zeros(frames)}
for f, who, t0 in LINES:
    a, sr = read(os.path.join(HERE, 'out', 'vo', f))
    a = resample(a, sr)
    # Mom stage-left, Dad stage-right; Dad's whisper sits a touch closer to mic
    add(t0, a, 0.62 if who == 'mom' else 0.72, -0.25 if who == 'mom' else 0.25)
    hop = SR // FPS
    for k in range(len(a) // hop):
        fi = int(round(t0 * FPS)) + k
        if fi < frames:
            lips[who][fi] = np.sqrt(np.mean(a[k * hop:(k + 1) * hop] ** 2))
for who in lips:
    v = lips[who]
    v = v / (v.max() + 1e-9)
    v = np.where(v > 0.08, v, 0) ** 0.6
    v = np.convolve(v, [0.25, 0.5, 0.25], 'same')            # soften frame-to-frame jitter
    lips[who] = np.round(np.clip(v, 0, 1), 3)

# ---- room tone + fridge hum (louder while the door is open)
t = np.arange(N) / SR
room = band(rng.standard_normal(N), 80, 3000) * 0.004
hum = (np.sin(2 * np.pi * 60 * t) * 0.6 + np.sin(2 * np.pi * 120 * t) * 0.3 + np.sin(2 * np.pi * 180 * t) * 0.1)
hum += band(rng.standard_normal(N), 90, 400) * 0.6
open_amt = np.interp(t, [0, 6.6, 7.88, 8.42, 8.75, 10], [1, 1, 0, 0, 0.55, 0.55])
hum *= 0.010 + 0.016 * open_amt
add(0, room + hum, 1.0)

# ---- door seal (soft rubbery thump) when it closes fully
n = int(0.35 * SR)
tt = np.arange(n) / SR
seal = np.sin(2 * np.pi * (70 + 40 * np.exp(-tt / 0.03)) * tt) * np.exp(-tt / 0.07) * 0.9
seal += band(rng.standard_normal(n), 150, 900) * np.exp(-tt / 0.045) * 0.45
add(T_SEAL, seal, 0.55, 0.45)

# ---- gentle reopen: suction pop + light rattle of nothing
n = int(0.25 * SR)
tt = np.arange(n) / SR
pop = band(rng.standard_normal(n), 300, 1800) * np.exp(-tt / 0.02) * 0.5
pop += np.sin(2 * np.pi * 220 * tt * (1 + tt * 2)) * np.exp(-tt / 0.03) * 0.25
add(T_UNSEAL, pop, 0.38, 0.45)

# ---- one comic pluck on the freeze (Karplus-Strong pizzicato, slight downward bend)
f0 = 98.0                                                    # G2
n = int(1.1 * SR)
period = int(SR / f0)
buf = rng.uniform(-1, 1, period)
out = np.zeros(n)
for i in range(n):
    p = int(period * (1 + 0.04 * min(1, i / (0.4 * SR))))   # bend down ~4%
    j = i % period
    out[i] = buf[j]
    buf[j] = 0.5 * (buf[j] + buf[(j + 1) % period]) * 0.996
out = band(out, 60, 3500) * np.exp(-np.arange(n) / SR / 0.45)
add(T_FREEZE, out / np.max(np.abs(out)), 0.42, 0.0)

# ---- master
peak = max(np.abs(L).max(), np.abs(R).max())
L, R = L / peak * 0.89, R / peak * 0.89
fade = np.ones(N)
fade[:int(0.04 * SR)] = np.linspace(0, 1, int(0.04 * SR))
fade[-int(0.25 * SR):] = np.linspace(1, 0, int(0.25 * SR))
L *= fade
R *= fade
with wave.open(os.path.join(HERE, 'out', 'audio.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.stack([L, R], 1) * 32767).astype('<i2').tobytes())
with open(os.path.join(HERE, 'lips.js'), 'w') as f:
    f.write('window.LIPS = ' + json.dumps({k: v.tolist() for k, v in lips.items()}) + ';\n')
print('wrote out/audio.wav and lips.js')
