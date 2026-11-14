import sys, json, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
k = Kokoro(sys.argv[1]+"/kokoro-v1.0.int8.onnx", sys.argv[1]+"/voices-v1.0.bin")
LINES = {
 "intro": ("Quotable Nights. Episode one. ... Silence, is also an answer.", 0.95),
 "a": ("We used to talk until three a.m. Then the replies got shorter. Haha. Okay. Sure.", 0.9),
 "b": ("I typed a paragraph. Deleted it. Typed, hey. Deleted that too. ... No reply. ... That was the reply.", 0.88),
 "outro": ("Have you ever waited for a reply that never came? Tell me in the comments.", 0.95),
}
out = {}
for key, (txt, sp) in LINES.items():
    s, sr = k.create(txt, voice=sys.argv[3], speed=sp, lang="en-us")
    sf.write(f"{sys.argv[2]}/{key}.wav", s, sr); out[key] = round(len(s)/sr, 2)
print(json.dumps(out))
