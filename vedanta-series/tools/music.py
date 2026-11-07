"""Synthesize a tanpura-style drone + sound effects and mix them under the narration.

usage: python music.py <episode-id>      -> out/<id>/mix.wav
All sound is generated here from scratch (no samples), so it is free to use.
"""
import json, os, sys
import numpy as np, soundfile as sf

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ep_id = sys.argv[1]
out = os.path.join(ROOT, "out", ep_id)
SR = 24000
nar, _ = sf.read(os.path.join(out, "narration.wav"), dtype="float32")
TL = json.load(open(os.path.join(out, "timings.json")))
N = len(nar); T = np.arange(N) / SR
rs = np.random.default_rng(int(''.join(c for c in ep_id if c.isdigit()) or 1))

def pluck(f0, dur=5.0, amp=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    y = np.zeros(n, np.float32)
    for h in range(1, 16):
        # jawari: upper harmonics bloom then fade, giving the tanpura "buzz"
        bloom = (1 - np.exp(-t * (1.5 + h * .25))) * np.exp(-t * (0.35 + h * 0.09))
        a = (1 / h ** 0.75) * bloom * (1 + 0.25 * np.sin(2 * np.pi * (0.3 + h * .05) * t))
        y += (a * np.sin(2 * np.pi * f0 * h * t * (1 + 0.0007 * h))).astype(np.float32)
    att = np.minimum(1, t / 0.01)
    return (y * att * amp / 4).astype(np.float32)

def tanpura(total, sa=138.59):
    pa = sa * 1.5 / 2  # low Pa
    seq = [pa, sa * 2, sa * 2, sa]
    y = np.zeros(int(total * SR) + 6 * SR, np.float32)
    step, i, t0 = 0.95, 0, 0.0
    while t0 < total:
        p = pluck(seq[i % 4] * (1 if seq[i % 4] != sa else 1), 5.5, 1.0 if i % 4 != 3 else 1.25)
        o = int(t0 * SR); y[o:o + len(p)] += p
        t0 += step if i % 4 != 3 else step * 1.6
        i += 1
    return y[:int(total * SR)]

def pad(total, sa=138.59):
    t = np.arange(int(total * SR)) / SR
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t)
    y = (np.sin(2 * np.pi * sa / 2 * t) + 0.5 * np.sin(2 * np.pi * sa * 0.75 * t) + 0.25 * np.sin(2 * np.pi * sa * t * 1.002)) * lfo
    return (y * 0.12).astype(np.float32)

def env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)

def lowpass(x, k):  # simple one-pole
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)): acc += k * (x[i] - acc); y[i] = acc
    return y

def sfx(name):
    if name == "chime":
        n = int(3.5 * SR); t = np.arange(n) / SR
        y = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in
                [(1046.5, 1, 1.2), (1568, .6, 1.6), (2093, .4, 2.2), (2637, .25, 3), (3136, .15, 4)])
        return (y * 0.35).astype(np.float32)
    if name == "gong":
        n = int(5 * SR); t = np.arange(n) / SR
        y = sum(a * np.sin(2 * np.pi * f * t + 3 * np.sin(2 * np.pi * 0.7 * t)) * np.exp(-t * d) for f, a, d in
                [(110, 1, .6), (166, .7, .8), (231, .5, 1), (352, .3, 1.4)])
        return (y * env(n, .01, 9) * 0.5).astype(np.float32)
    if name == "boom":
        n = int(1.6 * SR); t = np.arange(n) / SR
        f = 90 * np.exp(-t * 2.5) + 38
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)
        return (y * 0.9).astype(np.float32)
    if name == "whoosh":
        n = int(0.9 * SR); t = np.arange(n) / SR
        x = rs.standard_normal(n).astype(np.float32)
        y = lowpass(x, 0.08) * np.sin(np.pi * t / t[-1]) ** 2
        return (y * 1.6).astype(np.float32)
    if name == "pop":
        n = int(0.18 * SR); t = np.arange(n) / SR
        y = np.sin(2 * np.pi * (500 + 900 * t / t[-1]) * t) * env(n, .002, .05)
        return (y * 0.45).astype(np.float32)
    if name == "splash":
        n = int(1.2 * SR); t = np.arange(n) / SR
        x = rs.standard_normal(n).astype(np.float32)
        y = lowpass(x, 0.25) * env(n, .005, .25)
        return (y * 0.9).astype(np.float32)
    if name == "hiss":
        n = int(1.0 * SR); t = np.arange(n) / SR
        x = rs.standard_normal(n).astype(np.float32)
        y = (x - lowpass(x, 0.3)) * np.sin(np.pi * t / t[-1])
        return (y * 0.35).astype(np.float32)
    if name == "heartbeat":
        out = np.zeros(int(2.4 * SR), np.float32)
        for k, st in enumerate([0, .28, .9, 1.18, 1.8, 2.08]):
            n = int(.25 * SR); t = np.arange(n) / SR
            b = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 18) * (1 if k % 2 == 0 else .7)
            o = int(st * SR); out[o:o + n] += b[:len(out) - o]
        return out * 1.1
    if name == "crack":
        n = int(0.8 * SR); t = np.arange(n) / SR
        x = rs.standard_normal(n).astype(np.float32)
        y = x * env(n, .001, .06) + 0.5 * lowpass(x, .1) * env(n, .001, .2)
        return (y * 0.8).astype(np.float32)
    raise ValueError(name)

total = N / SR
music = tanpura(total) * 0.16 + pad(total)
music = np.pad(music, (0, max(0, N - len(music))))[:N]
# duck the music under the voice
voice_env = np.convolve(np.abs(nar), np.ones(int(.25 * SR)) / int(.25 * SR), mode="same")
duck = 1 - 0.45 * np.clip(voice_env / 0.03, 0, 1)
fade = np.minimum(1, T / 1.5) * np.minimum(1, (total - T) / 2.0)
music = music[:N] * duck * fade

fx = np.zeros(N, np.float32)
for L in TL["lines"]:
    for name in (L.get("sfx") or "").split():
        if not name: continue
        at = 0.0
        if "@" in name: name, at = name.split("@"); at = float(at)
        s = sfx(name); o = int((L["start"] + at) * SR)
        if name in ("boom", "whoosh"): o = max(0, o - int(0.15 * SR))
        fx[o:o + len(s)] += s[:max(0, N - o)]

mix = nar * 1.0 + music * 0.55 + fx * 0.5
mix = mix / max(1e-6, np.abs(mix).max()) * 0.92
sf.write(os.path.join(out, "mix.wav"), mix.astype(np.float32), SR)
print(f"{ep_id}: mixed {total:.1f}s")
