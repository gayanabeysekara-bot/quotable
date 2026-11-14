import sys, json, soundfile as sf
from kokoro_onnx import Kokoro
tts, d = sys.argv[1], sys.argv[2]
S = json.load(open(f"{d}/script.json"))
k = Kokoro(f"{tts}/kokoro-v1.0.int8.onnx", f"{tts}/voices-v1.0.bin")
segs = [("intro", S["intro"])]
for pi, p in enumerate(S["pages"]):
    for ri, r in enumerate(p["rules"]): segs.append((f"p{pi}r{ri}", r))
segs.append(("outro", S["outro"]))
out = {}
for key, txt in segs:
    s, sr = k.create(txt, voice=S["voice"], speed=S["speed"], lang="en-gb" if S["voice"].startswith("b") else "en-us")
    sf.write(f"{d}/vo/{key}.wav", s, sr); out[key] = {"text": txt, "dur": round(len(s) / sr, 3)}
json.dump(out, open(f"{d}/vo/durations.json", "w"), indent=1)
print({k: v["dur"] for k, v in out.items()})
