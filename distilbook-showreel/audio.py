#!/usr/bin/env python3
"""Procedural soundtrack for the DistilBook showreel.

120 BPM, A minor (Am - F - C - G, one chord per 2s bar). Every hit, whoosh and
UI sound is placed on the same timeline as reel.js. Writes out/soundtrack.wav.
"""
import os
import wave

import numpy as np

SR = 44100
DUR = 40.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
L = np.zeros(N)
R = np.zeros(N)
VERB_L = np.zeros(N)
VERB_R = np.zeros(N)
BEAT = 0.5


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(dur):
    return np.arange(int(dur * SR)) / SR


def add(t0, sig, gain=1.0, pan=0.0, verb=0.0):
    i0 = int(round(t0 * SR))
    if i0 >= N:
        return
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    n = min(len(sig), N - i0)
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    s = sig[:n] * gain
    L[i0:i0 + n] += s * gl * 1.414
    R[i0:i0 + n] += s * gr * 1.414
    if verb:
        VERB_L[i0:i0 + n] += s * gl * verb
        VERB_R[i0:i0 + n] += s * gr * verb


def band(sig, lo, hi):
    f = np.fft.rfft(sig)
    fr = np.fft.rfftfreq(len(sig), 1 / SR)
    f[(fr < lo) | (fr > hi)] = 0
    return np.fft.irfft(f, len(sig))


def noise(dur):
    return rng.uniform(-1, 1, int(dur * SR))


# ---------------------------------------------------------------- instruments
def kick(big=False):
    t = tt(0.5)
    f = 44 + 120 * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.22 if big else 0.15))
    s += noise(0.5) * np.exp(-t / 0.003) * 0.25
    return np.tanh(s * 1.6)


def clap():
    t = tt(0.35)
    e = sum(np.exp(-np.clip(t - d, 0, None) / 0.007) * (t >= d) for d in (0, 0.011, 0.023))
    e += 0.5 * np.exp(-t / 0.09)
    return band(noise(0.35), 900, 6000) * e * 1.6


def hat(open_=False):
    t = tt(0.25)
    return band(noise(0.25), 7000, 18000) * np.exp(-t / (0.09 if open_ else 0.022))


def bass(freq, dur):
    t = tt(dur)
    env = np.minimum(1, t / 0.005) * np.exp(-t / (dur * 0.9))
    s = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t)
    return np.tanh(2.2 * s) * env


def pluck(freq, dur=0.5, bright=1.0):
    t = tt(dur)
    s = np.zeros_like(t)
    for k in range(1, 12):
        if freq * k > 16000:
            break
        s += np.sin(2 * np.pi * freq * k * t * (1 + 0.0007 * k)) / k * np.exp(-t * (4 + k * 3.2 / bright))
    return s * np.minimum(1, t / 0.002)


def pad(midis, dur, att=0.5, rel=0.8):
    t = tt(dur + rel)
    s = np.zeros_like(t)
    for m in midis:
        f = mtof(m)
        for det in (-0.12, 0.0, 0.11):
            fd = f * 2 ** (det / 12)
            ph = rng.uniform(0, 2 * np.pi)
            for k in range(1, 7):
                s += np.sin(2 * np.pi * fd * k * t + ph * k) / k ** 1.4
    env = np.minimum(1, t / att) * np.where(t > dur, np.exp(-(t - dur) / (rel / 3)), 1)
    return s * env / (len(midis) * 6)


def impact(big=1.0):
    t = tt(2.5)
    f = 28 + 45 * np.exp(-t / 0.25)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.7 * big))
    crack = band(noise(2.5), 80, 3500) * np.exp(-t / 0.18)
    return np.tanh(1.4 * sub + 0.7 * crack)


def sweep(dur, f0, f1, shape='up', chunks=24):
    """Band-limited noise whose band moves f0 -> f1; envelope rises (riser) or swells (whoosh)."""
    out = np.zeros(int(dur * SR))
    seg = len(out) // chunks
    win = np.hanning(2 * seg)
    for i in range(chunks + 1):
        c = f0 * (f1 / f0) ** (min(i, chunks - 1) / (chunks - 1))
        part = band(rng.uniform(-1, 1, 2 * seg), c * 0.6, c * 1.6) * win
        i0 = (i - 1) * seg + seg // 2
        a, b = max(0, i0), min(len(out), i0 + 2 * seg)
        if b > a:
            out[a:b] += part[a - i0:b - i0]
    x = np.linspace(0, 1, len(out))
    env = x ** 2.2 if shape == 'up' else np.sin(np.pi * x) ** 2
    return out * env


def tone_sweep(dur, f0, f1):
    t = tt(dur)
    f = f0 * (f1 / f0) ** (t / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * (t / dur) ** 2


def blip(freq, dur=0.12):
    t = tt(dur)
    f = freq * (1 + 0.5 * np.exp(-t / 0.01))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.03)


def tick():
    t = tt(0.03)
    return band(noise(0.03), 2500, 9000) * np.exp(-t / 0.004)


# ---------------------------------------------------------------- harmony
CHORDS = [[57, 60, 64], [53, 57, 60], [55, 60, 64], [55, 59, 62]]   # Am F C/G G
ROOTS = [33, 29, 36, 31]                                            # A1 F1 C2 G1


def chord_at(t):
    return int(t // 2) % 4


# ---------------------------------------------------------------- arrangement
kicks = []


def K(t, g=1.0, big=False):
    kicks.append(t)
    add(t, kick(big), 0.95 * g)


def groove(a, b, kick_every=0.5, clap_on=True, hats=0.25, bass_on=True, hat_gain=0.22):
    t = a
    while t < b - 1e-6:
        K(t)
        t += kick_every
    if clap_on:
        t = a + BEAT
        while t < b - 1e-6:
            add(t, clap(), 0.42, pan=0.05, verb=0.25)
            t += 2 * BEAT
    if hats:
        t, i = a, 0
        while t < b - 1e-6:
            off = (i % 2 == 1)
            add(t, hat(open_=(i % 4 == 2)), hat_gain * (1.0 if off else 0.6), pan=0.3 if i % 2 else -0.25)
            t += hats
            i += 1
    if bass_on:
        t = a
        while t < b - 1e-6:
            r = ROOTS[chord_at(t)]
            m = r + (12 if int(t * 4) % 4 == 3 else 0)
            add(t + 0.25, bass(mtof(m + 12), 0.22), 0.36)       # off-beat bass
            t += BEAT


def arp(a, b, step=0.125, gain=0.16, octave=12, bright=1.0, verb=0.35):
    t, i = a, 0
    while t < b - 1e-6:
        ch = CHORDS[chord_at(t)]
        seq = [ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[0] + 12, ch[1], ch[2] + 12]
        add(t, pluck(mtof(seq[i % 8] + octave), 0.5, bright), gain, pan=0.35 * np.sin(i * 0.9), verb=verb)
        t += step
        i += 1


def pads(a, b, gain=0.22):
    t = a
    while t < b - 1e-6:
        bar_end = min(b, (np.floor(t / 2) + 1) * 2)
        add(t, pad(CHORDS[chord_at(t)], bar_end - t, att=0.3, rel=0.6), gain, verb=0.4)
        t = bar_end


def stab(t, gain=0.3, octave=12):
    for m in CHORDS[chord_at(t)]:
        add(t, pluck(mtof(m + octave), 0.6, 2.5), gain, pan=rng.uniform(-0.4, 0.4), verb=0.5)


def whoosh(t_peak, dur=0.6, gain=0.35):
    add(t_peak - dur * 0.6, sweep(dur, 400, 4000, 'swell'), gain, verb=0.3)


def riser(t_end, dur, gain=0.35):
    add(t_end - dur, sweep(dur, 300, 9000, 'up'), gain, verb=0.25)
    add(t_end - dur, tone_sweep(dur, 220, 1760), gain * 0.18, verb=0.3)


# --- 0-4: cold open
add(0.0, pad([45, 52], 1.0, att=0.8, rel=0.3), 0.25)
add(0.15, tone_sweep(0.85, 1400, 350), 0.06, verb=0.5)  # falling-drop whistle
riser(1.0, 0.9, 0.22)
add(1.0, impact(1.3), 0.95, verb=0.6)
K(1.0, big=True)
add(1.0, pluck(mtof(81), 1.2, 3), 0.35, verb=0.8)
pads(1.0, 4.0, 0.16)
for i in range(16):                                  # number scramble ticks
    add(1.05 + i * 0.035, tick(), 0.25, pan=rng.uniform(-0.5, 0.5))
for t in (2.0, 3.0):
    K(t, 0.8)
add(2.05, blip(880), 0.15, verb=0.4)
add(2.5, clap(), 0.6, verb=0.5)                      # strike-through
add(2.5, impact(0.4), 0.35)
for t in np.arange(1.0, 3.5, 0.25):
    add(t, hat(), 0.12, pan=0.3)
add(3.45, sweep(0.55, 6000, 300, 'up')[::-1], 0.35)  # reverse swell into iris
whoosh(3.95, 0.7, 0.4)

# --- 4-8: the pile
groove(4.0, 7.0)
pads(4.0, 7.0, 0.12)
for i in range(18):                                  # each doc lands = a note
    ch = CHORDS[chord_at(4.0 + i * 0.125)]
    add(4.0 + i * 0.125 + 0.24, pluck(mtof(ch[i % 3] + 12 + 12 * (i // 6)), 0.35, 1.6), 0.15, pan=-0.6 + i * 0.07, verb=0.3)
riser(8.0, 1.1, 0.35)
add(7.0, kick(True), 0.8)
for t in np.arange(7.0, 8.0, 0.125):
    add(t, hat(), 0.08 + 0.12 * (t - 7.0), pan=0.2)

# --- 8-11: distillation (half-time, building)
for t in np.arange(8.0, 10.5, 1.0):
    K(t, 1.0, big=True)
for t in np.arange(8.5, 10.5, 1.0):
    add(t, clap(), 0.4, verb=0.5)
add(8.0, impact(0.6), 0.5, verb=0.5)
pads(8.0, 10.75, 0.2)
arp(8.0, 10.75, 0.125, 0.13, 12, 1.2)
riser(10.75, 2.0, 0.42)
for t in list(np.arange(9.5, 10.0, 0.25)) + list(np.arange(10.0, 10.5, 0.125)) + list(np.arange(10.5, 10.75, 0.0625)):
    add(t, clap(), 0.18 + 0.25 * (t - 9.5), verb=0.2)
for i, t in enumerate(np.arange(8.0, 10.6, 0.0625)):    # glyph sparkle
    if rng.random() < 0.45:
        add(t, blip(mtof(84 + int(rng.integers(0, 12)))), 0.03, pan=rng.uniform(-0.8, 0.8), verb=0.6)
# 10.75-11.0 silence

# --- 11-15: LOGO DROP
add(11.0, impact(1.6), 1.0, verb=0.7)
K(11.0, big=True)
stab(11.0, 0.45)
add(11.0, pad([33, 45, 57, 64], 1.5, att=0.01, rel=1.5), 0.3, verb=0.6)
groove(11.0, 14.25)
arp(11.5, 14.25, 0.125, 0.12)
pads(11.0, 14.25, 0.14)
for t in np.arange(11.0, 14.25, 0.5):               # beat rings
    add(t + 0.002, blip(1760, 0.08), 0.03, verb=0.6)
riser(15.0, 0.75, 0.45)
for t in np.arange(14.25, 15.0, 0.125):
    add(t, kick(), 0.25 + 0.4 * (t - 14.25))

# --- 15-24: how it works
add(15.0, impact(0.8), 0.7, verb=0.5)
K(15.0, big=True)
stab(15.0, 0.3)
groove(15.0, 23.35, hat_gain=0.17)
pads(15.0, 23.35, 0.09)
add(16.35, blip(330, 0.2), 0.4, verb=0.3)           # file lands
add(16.35, kick(), 0.4)
for i, t in enumerate(np.arange(16.5, 17.35, 0.1)):  # progress ticks
    add(t, blip(mtof(76 + i), 0.05), 0.08)
add(17.35, pluck(mtof(88), 0.6, 3), 0.3, verb=0.5)   # "18 key ideas"
add(17.42, pluck(mtof(93), 0.6, 3), 0.25, verb=0.5)
for T in (18.0, 21.0):                                # card flips
    whoosh(T, 0.45, 0.4)
    stab(T, 0.22)
for t in np.arange(18.25, 19.75, 0.045):            # typing
    if rng.random() < 0.8:
        add(t + rng.uniform(0, 0.02), tick(), 0.22, pan=rng.uniform(-0.3, 0.3))
add(20.35, tick(), 0.6)
add(20.35, blip(1200, 0.06), 0.25)
add(20.37, pluck(mtof(81), 0.7, 3), 0.25, verb=0.6)
add(20.45, pluck(mtof(88), 0.7, 3), 0.25, verb=0.6)
arp(21.0, 23.35, 0.25, 0.1, 24, 2.0, 0.5)
scratch = band(noise(2.1), 2000, 7000) * (0.5 + 0.5 * np.abs(np.sin(tt(2.1) * 19)))
add(21.2, scratch, 0.05, pan=0.3)                    # marker on whiteboard
riser(24.0, 0.65, 0.4)

# --- 24-30: 19 styles
for i in range(8):                                    # hard cuts
    t = 24.0 + i * 0.25
    stab(t, 0.18 + 0.02 * i, 12 + (i % 2) * 12)
    add(t, hat(True), 0.15)
add(24.0, impact(0.9), 0.7, verb=0.5)
groove(24.0, 26.0, hats=0.125, hat_gain=0.16)
whoosh(26.6, 1.1, 0.45)
add(27.2, impact(0.7), 0.5, verb=0.5)
groove(27.2, 29.35, hats=0.125, hat_gain=0.18)
arp(27.2, 29.35, 0.125, 0.12)
pads(27.2, 29.6, 0.12)
for i in range(19):                                   # counter 1..19
    add(27.1 + i * 0.058, blip(mtof(72 + i)), 0.07)
add(29.35, sweep(0.65, 6000, 200, 'swell'), 0.35)

# --- 30-34: languages (breakdown)
add(30.0, impact(0.7), 0.55, verb=0.7)
pads(30.0, 34.0, 0.2)
arp(30.0, 34.0, 0.25, 0.11, 24, 2.5, 0.7)
for i in range(12):                                   # greetings
    add(30.35 + i * 0.27, blip(mtof([76, 79, 81, 84][i % 4]), 0.15), 0.12, pan=-0.5 + i / 11, verb=0.6)
groove(32.0, 33.5, hats=0.25, hat_gain=0.12, clap_on=True)
riser(34.0, 0.6, 0.4)

# --- 34-37: formats
add(34.0, impact(0.9), 0.65, verb=0.5)
K(34.0, big=True)
groove(34.0, 36.5, hat_gain=0.18)
arp(34.0, 36.5, 0.125, 0.11)
for T in (35.05, 36.05):
    whoosh(T, 0.4, 0.4)
    stab(T, 0.22)
add(36.55, tone_sweep(0.45, 300, 2400), 0.12, verb=0.4)
riser(37.0, 0.5, 0.35)

# --- 37-40: end card
add(37.0, blip(660, 0.2), 0.3, verb=0.6)              # frame -> drop
add(37.27, impact(0.9), 0.75, verb=0.6)
K(37.27, big=True)
add(37.2, pluck(mtof(69), 0.8, 2), 0.3, verb=0.6)
add(37.7, pluck(mtof(76), 0.8, 2), 0.35, verb=0.6)
for t in np.arange(37.5, 38.5, 0.5):
    K(t, 0.7)
add(38.0, sweep(0.5, 400, 8000, 'up'), 0.35)
add(38.5, impact(2.0), 1.0, verb=0.9)
K(38.5, big=True)
add(38.5, pad([33, 45, 57, 60, 64, 69], 1.2, att=0.01, rel=2.0), 0.45, verb=0.9)
stab(38.5, 0.4, 12)
add(39.0, pluck(mtof(93), 1.0, 3), 0.2, verb=1.0)       # shine sparkle
add(39.15, pluck(mtof(100), 1.0, 3), 0.15, verb=1.0)

# ---------------------------------------------------------------- sidechain + reverb + master
duck = np.ones(N)
for k in kicks:
    i0 = int(k * SR)
    n = min(int(0.3 * SR), N - i0)
    if n > 0:
        duck[i0:i0 + n] = np.minimum(duck[i0:i0 + n], 1 - 0.55 * np.exp(-np.arange(n) / SR / 0.09))


def reverb(x, seconds=2.4, seed=0):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = np.random.default_rng(seed).standard_normal(n) * np.exp(-t / (seconds / 6.5))
    ir[: int(0.012 * SR)] = 0
    ir = band(ir, 200, 9000)
    ir /= np.sqrt(np.sum(ir ** 2))
    m = len(x) + n
    y = np.fft.irfft(np.fft.rfft(x, m) * np.fft.rfft(ir, m), m)[: len(x)]
    return y


wl, wr = reverb(VERB_L, seed=1), reverb(VERB_R, seed=2)
L2 = L + wl * duck * 0.9
R2 = R + wr * duck * 0.9
# gentle glue: soft clip + normalise
mx = max(np.max(np.abs(L2)), np.max(np.abs(R2)))
L2, R2 = np.tanh(1.3 * L2 / mx * 1.4), np.tanh(1.3 * R2 / mx * 1.4)
fade = np.ones(N)
fs = int(0.35 * SR)
fade[-fs:] = np.linspace(1, 0, fs) ** 2
L2 *= fade
R2 *= fade
peak = max(np.max(np.abs(L2)), np.max(np.abs(R2)))
L2, R2 = L2 / peak * 0.89, R2 / peak * 0.89

os.makedirs(os.path.join(os.path.dirname(__file__), 'out'), exist_ok=True)
out = os.path.join(os.path.dirname(__file__), 'out', 'soundtrack.wav')
pcm = (np.stack([L2, R2], axis=1) * 32767).astype('<i2')
with wave.open(out, 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print('wrote', out)
