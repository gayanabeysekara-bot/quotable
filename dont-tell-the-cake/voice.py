#!/usr/bin/env python3
"""Prepare dialogue: trim silence, turn Dad's lines into a real whisper, fit timing.

Whisper = LPC resynthesis: keep each frame's vocal-tract envelope (what makes the
words intelligible) but replace the voiced excitation with breath noise.
"""
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
VO = os.path.join(HERE, 'out', 'vo')


def read(p):
    with wave.open(p) as w:
        sr, n, ch, sw = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        raw = w.readframes(n)
    if sw == 2:
        a = np.frombuffer(raw, '<i2').astype(float) / 32768
    else:
        a = np.frombuffer(raw, '<f4').astype(float)
    return a.reshape(-1, ch).mean(1), sr


def write(p, a, sr):
    with wave.open(p, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(a, -1, 1) * 32767).astype('<i2').tobytes())


def trim(a, sr, db=-42):
    env = np.convolve(np.abs(a), np.ones(int(0.01 * sr)) / int(0.01 * sr), 'same')
    idx = np.where(env > 10 ** (db / 20))[0]
    pad = int(0.02 * sr)
    return a[max(0, idx[0] - pad): idx[-1] + pad]


def lpc(frame, order):
    r = np.correlate(frame, frame, 'full')[len(frame) - 1:len(frame) + order]
    r[0] *= 1.0001
    if r[0] <= 1e-9:
        return np.r_[1, np.zeros(order)], 0.0
    a = np.zeros(order + 1); a[0] = 1; e = r[0]
    for i in range(1, order + 1):
        k = -(r[i] + np.dot(a[1:i], r[i - 1:0:-1])) / e
        a[1:i] = a[1:i] + k * a[i - 1:0:-1]
        a[i] = k
        e *= 1 - k * k
    return a, e


def whisper(x, sr, order=26, seed=3):
    rng = np.random.default_rng(seed)
    n, hop = 1024, 256
    win = np.hanning(n)
    pre = np.append(x[0], x[1:] - 0.9 * x[:-1])          # pre-emphasis
    out = np.zeros(len(x) + n)
    norm = np.zeros(len(x) + n)
    for s in range(0, len(x) - n, hop):
        f = pre[s:s + n] * win
        a, e = lpc(f, order)
        H = 1 / np.abs(np.fft.rfft(a, n))                 # all-pole envelope
        g = np.sqrt(max(e, 0) / n)
        spec = H * g * np.exp(1j * rng.uniform(0, 2 * np.pi, len(H)))
        seg = np.fft.irfft(spec, n) * win
        out[s:s + n] += seg
        norm[s:s + n] += win ** 2
    y = out[:len(x)] / np.maximum(norm[:len(x)], 1e-3)
    for i in range(1, len(y)):                            # de-emphasis
        y[i] += 0.9 * y[i - 1]
    y -= np.convolve(y, np.ones(400) / 400, 'same')       # remove rumble
    return y


def resample_speed(a, factor):
    """Speed up by `factor` (simple, pitch shifts slightly; only used for tiny fits)."""
    idx = np.arange(0, len(a) - 1, factor)
    return np.interp(idx, np.arange(len(a)), a)


def norm(a, peak=0.9):
    return a / (np.max(np.abs(a)) + 1e-9) * peak


SLOTS = [1.95, 2.1, 0.6, 1.1]   # max seconds each line may occupy
for i in range(4):
    a, sr = read(os.path.join(VO, f'raw{i}.wav'))
    a = trim(a, sr)
    if i in (1, 3):
        a = whisper(a, sr)
        a = trim(norm(a), sr, -36)
    d = len(a) / sr
    if d > SLOTS[i]:
        a = resample_speed(a, d / SLOTS[i])
    a = norm(a, 0.9 if i in (1, 3) else 0.8)
    write(os.path.join(VO, f'line{i}.wav'), a, sr)
    print(f'line{i}: {d:.2f}s -> {len(a) / sr:.2f}s')
