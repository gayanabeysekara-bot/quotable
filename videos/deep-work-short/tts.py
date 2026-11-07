"""Generate narration with Kokoro-82M (free, Apache-2.0) and write timeline.js for the animation.
Usage: python tts.py <kokoro.onnx> <voices.bin> [voice] [speed]
"""
import json, sys, re, os
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

LINES = [
    ("hook1",   "You're not lazy."),
    ("hook2",   "Your focus is being shattered."),
    ("ping",    "Every notification pulls your attention somewhere else."),
    ("residue", "And when you come back, part of your mind is still stuck on the last thing."),
    ("name",    "Researchers call this attention residue."),
    ("day",     "Here's a normal workday."),
    ("chop",    "Every interruption chops your focus into tiny pieces."),
    ("block",   "Deep work flips it. One long, protected block."),
    ("formula", "Because the work you get done is time, multiplied by how hard you focus."),
    ("beat",    "Two deep hours can beat four distracted ones."),
    ("start",   "Here's how to start today."),
    ("s1",      "One. Pick one task."),
    ("s2",      "Two. Put your phone in another room."),
    ("s3",      "Three. Set a timer for sixty minutes."),
    ("s4",      "Four. When you get bored, don't reach for your phone. Stay with the work."),
    ("rebuild", "Do it every day for thirty days, and your focus starts to rebuild."),
    ("cta",     "Follow for my full thirty-day experiment."),
]
GAP = {"hook1": 0.15, "hook2": 0.35, "name": 0.45, "block": 0.4, "beat": 0.45, "start": 0.3, "s1": 0.35, "s2": 0.35, "s3": 0.35, "s4": 0.45, "rebuild": 0.35}
LEAD_IN, TAIL = 0.4, 1.6

model, voices = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "af_heart"
speed = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
k = Kokoro(model, voices)
here = os.path.dirname(os.path.abspath(__file__))

sr = 24000
chunks = [np.zeros(int(LEAD_IN * sr), dtype=np.float32)]
t = LEAD_IN
timeline = []
for key, text in LINES:
    audio, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
    # trim leading/trailing silence
    idx = np.where(np.abs(audio) > 0.01)[0]
    if len(idx):
        audio = audio[max(0, idx[0] - 600): idx[-1] + 1200]
    dur = len(audio) / sr
    # approximate word timings: weight by letters (+ pause weight for punctuation)
    words = text.split()
    w = [len(re.sub(r"[^A-Za-z0-9]", "", x)) + 2 + (3 if re.search(r"[.,!?]$", x) else 0) for x in words]
    tot = sum(w); acc = 0; wt = []
    for word, ww in zip(words, w):
        wt.append([word, round(t + dur * acc / tot, 3), round(t + dur * (acc + ww) / tot, 3)]); acc += ww
    timeline.append({"key": key, "text": text, "start": round(t, 3), "end": round(t + dur, 3), "words": wt})
    gap = GAP.get(key, 0.25)
    chunks += [audio.astype(np.float32), np.zeros(int(gap * sr), dtype=np.float32)]
    t += dur + gap
chunks.append(np.zeros(int(TAIL * sr), dtype=np.float32))
full = np.concatenate(chunks)
sf.write(os.path.join(here, "narration.wav"), full, sr)
total = len(full) / sr
with open(os.path.join(here, "timeline.js"), "w") as f:
    f.write("window.TIMELINE = " + json.dumps({"voice": voice, "duration": round(total, 3), "lines": timeline}, indent=1) + ";\n")
print(f"voice={voice} duration={total:.2f}s")
for l in timeline: print(f'{l["start"]:6.2f}-{l["end"]:6.2f}  {l["key"]:8s} {l["text"]}')
