"""Narrate an episode line by line with Kokoro and write timings.json + narration.wav.

usage: python tts.py <episode-id> <kokoro-model-dir>
Each line in the episode: {s: scene, t: caption, say?: spoken text, v?: voice, sp?: speed, p?: pause after, sfx?: name}
"""
import hashlib, json, os, subprocess, sys
import numpy as np, soundfile as sf
from kokoro_onnx import Kokoro

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ep_id, model_dir = sys.argv[1], sys.argv[2]
ep = json.loads(subprocess.check_output(["node", "-e",
    f"const E=require({json.dumps(os.path.join(ROOT, 'episodes', ep_id + '.js'))});"
    "console.log(JSON.stringify({num:E.num,voice:E.voice,speed:E.speed||1,lines:E.lines}))"]))
out = os.path.join(ROOT, "out", ep_id); os.makedirs(out, exist_ok=True)
k = Kokoro(os.path.join(model_dir, "kokoro.onnx"), os.path.join(model_dir, "voices.bin"))
SR = 24000
LEAD, TAIL, GAP = 0.45, 1.6, 0.32

def trim(a, thr=0.012):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx): return a
    return a[max(0, idx[0] - 240): min(len(a), idx[-1] + 1200)]

cache_dir = os.path.join(out, "lines"); os.makedirs(cache_dir, exist_ok=True)
clips, lines, cur = [], [], LEAD
for i, L in enumerate(ep["lines"]):
    voice = L.get("v", ep["voice"]); speed = L.get("sp", ep["speed"])
    say = L.get("say", L["t"])
    key = f"{i:02d}_" + hashlib.md5(f"{say}|{voice}|{speed}".encode()).hexdigest()[:10] + ".wav"
    fp = os.path.join(cache_dir, key)
    if os.path.exists(fp):
        a, _ = sf.read(fp, dtype="float32")
    else:
        a, sr = k.create(say, voice=voice, speed=speed, lang=L.get("lang", "en-gb" if voice.startswith("b") else "en-us"))
        a = trim(a.astype(np.float32)); sf.write(fp, a, SR)
    dur = len(a) / SR
    pause = L.get("p", GAP)
    clips.append((cur, a))
    lines.append({"i": i, "scene": L["s"], "text": L["t"], "start": round(cur, 3), "dur": round(dur, 3),
                  "pause": pause, "sfx": L.get("sfx"), "color": L.get("color"), "nocap": L.get("nocap", False),
                  "voice": voice})
    cur += dur + pause
total = cur + TAIL
buf = np.zeros(int(total * SR) + SR, dtype=np.float32)
for st, a in clips:
    o = int(st * SR); buf[o:o + len(a)] += a
sf.write(os.path.join(out, "narration.wav"), buf[:int(total * SR)], SR)
TLJ = {"total": round(total, 3), "lines": lines}
json.dump(TLJ, open(os.path.join(out, "timings.json"), "w"), indent=1)
open(os.path.join(out, "timings.js"), "w").write("window.TIMINGS = " + json.dumps(TLJ) + ";")
print(f"{ep_id}: {len(lines)} lines, {total:.1f}s")
