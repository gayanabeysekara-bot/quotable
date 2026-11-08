"""Art of War / discipline video. Generate narration with Kokoro-82M (free, Apache-2.0) and write timeline.js for the animation.
Usage: python tts.py <kokoro.onnx> <voices.bin> [voice] [speed]
"""
import json, sys, re, os
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

LINES = [
    ("hook",     "Twenty-five centuries ago, one general proved that discipline is not a feeling. It's a decision."),
    ("king",     "The King of Wu had read Sun Tzu's Art of War, and he wanted a test."),
    ("test",     "Can your methods train anyone? he asked. Even the women of my palace?"),
    ("yes",      "Sun Tzu said yes."),
    ("ranks",    "One hundred and eighty women were lined up in two companies. The king's two favourite concubines were made their captains."),
    ("orders",   "Sun Tzu explained the commands. Face front. Turn left. Turn right. Then he struck the drum."),
    ("laugh1",   "They laughed."),
    ("blame1",   "If the commands are not clear, Sun Tzu said, the fault is the general's."),
    ("repeat",   "So he explained them again. Carefully. And struck the drum."),
    ("laugh2",   "They laughed again."),
    ("blame2",   "But when the commands are clear, and still not obeyed, the fault belongs to the officers."),
    ("execute",  "He ordered the two captains executed."),
    ("king2",    "The king begged him to stop. Sun Tzu refused. A general in the field, he said, cannot accept every order of his sovereign."),
    ("silence",  "New captains were chosen. The drum sounded once more."),
    ("perfect",  "This time, every woman moved in perfect silence."),
    ("drill",    "Left. Right. Kneel. Rise."),
    ("lesson",   "Here is the lesson."),
    ("you",      "You already know the commands. Wake up early. Do the work. Put the phone down."),
    ("captains", "The problem was never clarity. It's the two captains in your head who keep laughing. Comfort. And excuses."),
    ("remove",   "You don't negotiate with them. You remove them."),
    ("drum",     "Then strike the drum again, and watch how fast the rest of you falls in line."),
    ("end",      "Discipline is a decision. Make it today."),
]
GAP = {"hook": 0.7, "yes": 0.6, "orders": 0.5, "laugh1": 0.8, "blame1": 0.5, "repeat": 0.5, "laugh2": 0.8, "blame2": 0.6, "execute": 1.4, "king2": 0.6, "silence": 0.5, "perfect": 0.4, "drill": 0.9, "lesson": 0.6, "captains": 0.5, "remove": 0.9, "drum": 0.6, "XX": 0,"hook1": 0.15, "hook2": 0.35, "name": 0.45, "block": 0.4, "beat": 0.45, "start": 0.3, "s1": 0.35, "s2": 0.35, "s3": 0.35, "s4": 0.45, "rebuild": 0.35}
LEAD_IN, TAIL = 1.0, 3.0

model, voices = sys.argv[1], sys.argv[2]
voice = sys.argv[3] if len(sys.argv) > 3 else "am_michael"
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
    # word timings: split the line into phrases at punctuation and align them to the
    # pauses actually found in the audio; inside a phrase, weight words by length.
    words = text.split()
    wlen = lambda x: len(re.sub(r"[^A-Za-z0-9]", "", x)) + 2
    phrases, cur = [], []
    for x in words:
        cur.append(x)
        if re.search(r"[.,!?]$", x): phrases.append(cur); cur = []
    if cur: phrases.append(cur)
    hop = int(0.01 * sr); e = np.array([np.sqrt(np.mean(audio[i:i + hop] ** 2)) for i in range(0, len(audio) - hop, hop)])
    voiced = e > max(0.012, e.max() * 0.06)
    segs, i = [], 0
    while i < len(voiced):
        if voiced[i]:
            j = i
            while j < len(voiced) and (voiced[j] or (j + 14 < len(voiced) and voiced[j:j + 14].any())): j += 1
            segs.append([i * 0.01, j * 0.01]); i = j
        else: i += 1
    if len(segs) != len(phrases):            # merge the closest segments until counts match
        while len(segs) > len(phrases) and len(segs) > 1:
            gaps = [segs[q + 1][0] - segs[q][1] for q in range(len(segs) - 1)]
            q = int(np.argmin(gaps)); segs[q] = [segs[q][0], segs[q + 1][1]]; del segs[q + 1]
    if len(segs) != len(phrases): segs = None
    if segs:  # reject implausible alignments (too fast / too slow per letter)
        for ph, (a, b) in zip(phrases, segs):
            r = (b - a) / sum(wlen(x) for x in ph)
            if not (0.025 < r < 0.16): segs = None; break
    wt = []
    if segs:
        for ph, (a, b) in zip(phrases, segs):
            tot = sum(wlen(x) for x in ph); acc = 0
            for x in ph:
                wt.append([x, round(t + a + (b - a) * acc / tot, 3), round(t + a + (b - a) * (acc + wlen(x)) / tot, 3)]); acc += wlen(x)
    else:
        w = [wlen(x) + (3 if re.search(r"[.,!?]$", x) else 0) for x in words]
        tot = sum(w); acc = 0
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
