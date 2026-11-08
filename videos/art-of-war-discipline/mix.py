"""Build sound design (war drums, impact, low drone) timed to the narration, and cues.js for the animation.
Usage: python mix.py      (reads timeline.js, writes sfx.wav + cues.js)
"""
import json, os, re
import numpy as np, soundfile as sf

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "timeline.js")).read()
TL = json.loads(src[src.index("{"): src.rindex("}") + 1])
L = {l["key"]: l for l in TL["lines"]}
DUR = TL["duration"]

def word(key, pat, which="start", n=0):
    hits = [w for w in L[key]["words"] if re.search(pat, w[0], re.I)]
    w = hits[n]
    return w[1] if which == "start" else w[2]

strikes = [
    (0.45, 1.0), (word("hook", r"^decision") + 0.05, 0.9),
    (word("orders", r"^drum") + 0.1, 1.0),
    (word("repeat", r"^drum") + 0.1, 1.0),
    (word("silence", r"^drum") + 0.1, 1.0),
    (word("drill", r"^Left") , 0.55), (word("drill", r"^Right"), 0.55),
    (word("drill", r"^Kneel"), 0.55), (word("drill", r"^Rise"), 0.7),
    (word("drum", r"^drum") + 0.1, 1.0), (word("drum", r"^line") + 0.1, 0.8),
    (word("end", r"^decision") + 0.05, 0.8), (word("end", r"^today"), 1.0),
]
booms = [word("execute", r"^executed", "end") + 0.15]
embers = {"execute": booms[0], "remove": word("remove", r"^them", "start", 1)}
perfect = {k: word("drill", "^" + k) for k in ["Left", "Right", "Kneel", "Rise"]}
commands = {"front": word("orders", r"^front"), "left": word("orders", r"^left"), "right": word("orders", r"^right")}
yous = {"early": word("you", r"^early"), "work": word("you", r"^work"), "phone": word("you", r"^phone")}
caps = {"comfort": word("captains", r"^Comfort"), "excuses": word("captains", r"^excuses")}
cues = {"strikes": strikes, "booms": booms, "embers": embers, "perfect": perfect, "commands": commands, "you": yous, "caps": caps,
        "decision": word("hook", r"^decision"), "line": word("drum", r"^line")}
with open(os.path.join(here, "cues.js"), "w") as f:
    f.write("window.CUES = " + json.dumps(cues, indent=1) + ";\n")

# ---------------- audio ----------------
SR = 48000
n = int(DUR * SR)
out = np.zeros((n, 2), dtype=np.float64)
rng = np.random.default_rng(3)
t_all = np.arange(n) / SR

def add(sig, at, pan=0.0, gain=1.0):
    i = int(at * SR)
    if i >= n: return
    sig = sig[: n - i] * gain
    out[i:i + len(sig), 0] += sig * (1 - pan) ** 0.5
    out[i:i + len(sig), 1] += sig * (1 + pan) ** 0.5

def lowpass(x, a):
    y = np.empty_like(x); acc = 0.0
    for i, v in enumerate(x):
        acc += a * (v - acc); y[i] = acc
    return y

def taiko(strength=1.0):
    d = 1.6; tt = np.arange(int(d * SR)) / SR
    f = 48 + 70 * np.exp(-tt * 18)                     # pitch drop
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2)
    sub = np.sin(2 * np.pi * 38 * tt) * np.exp(-tt * 2.2) * 0.6
    hit = lowpass(rng.standard_normal(len(tt)), 0.08) * np.exp(-tt * 40) * 2.2
    room = lowpass(rng.standard_normal(len(tt)), 0.02) * np.exp(-tt * 4) * 0.5
    return (body + sub + hit + room) * 0.55 * strength

def boom():
    d = 4.5; tt = np.arange(int(d * SR)) / SR
    f = 30 + 40 * np.exp(-tt * 6)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 0.9)
    rum = lowpass(rng.standard_normal(len(tt)), 0.01) * np.exp(-tt * 1.2) * 1.4
    crack = lowpass(rng.standard_normal(len(tt)), 0.2) * np.exp(-tt * 25)
    return (s * 0.9 + rum + crack * 0.6) * 0.7

for at, s in strikes:
    add(taiko(s), at, pan=0.0)
    add(taiko(s * 0.35), at + 0.11, pan=0.3)            # slap-back from the courtyard walls
for at in booms:
    add(boom(), at)

# low drone: D minor, swells, darker around the execution, opens up for the lesson
def env_at(times, vals):
    return np.interp(t_all, times, vals)
lesson = L["lesson"]["start"]
amp = env_at([0, 3, L["execute"]["start"], L["execute"]["end"] + 0.3, L["king2"]["start"] + 2, lesson, lesson + 3, DUR - 4, DUR],
             [0, 0.8, 1.0, 0.25, 0.8, 0.7, 1.0, 1.0, 0])
drone = (0.09 * np.sin(2 * np.pi * 73.42 * t_all) +
         0.07 * np.sin(2 * np.pi * 110.0 * t_all) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.05 * t_all)) +
         0.045 * np.sin(2 * np.pi * 146.83 * t_all) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t_all + 1)) +
         0.035 * np.sin(2 * np.pi * 174.61 * t_all) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t_all + 2)))
bright = env_at([0, lesson, lesson + 4, DUR], [0, 0, 1, 1])
drone += bright * 0.03 * np.sin(2 * np.pi * 220.0 * t_all) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.09 * t_all))
drone *= amp * 0.8
out[:, 0] += drone; out[:, 1] += drone * 0.97

peak = np.abs(out).max()
out = out / max(peak, 1e-9) * 0.85
sf.write(os.path.join(here, "sfx.wav"), out.astype(np.float32), SR)
print("strikes", len(strikes), "duration", DUR, "peak-normalised from", round(float(peak), 3))
