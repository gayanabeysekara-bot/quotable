# "Rules Nobody Tells You" — animated episode template

Fully original, 100% generated video: three.js 3D notebook + fountain pen writing the rules,
Kokoro TTS narrator, synthesized SFX and lo-fi music. No external footage.

Edit `script.json` (voice, rules, page titles, intro/outro lines), then:

1. Setup: `npm i three@0.187.0` inside `three/` (Playwright + Chromium required);
   `pip install kokoro-onnx soundfile`; get `kokoro-v1.0.int8.onnx` + `voices-v1.0.bin`
   from the kokoro-onnx GitHub releases into `tts/`; put `Caveat.ttf`, `Playfair.ttf`,
   `PlayfairItalic.ttf` (Google Fonts, OFL) in `three/` and in `fonts/`.
2. `mkdir -p ep/vo ep/three && cp script.json ep/ && cp three/* ep/three/`
3. `python scripts/tts2.py tts ep` — voiceover + durations
4. `python scripts/timeline2.py ep && cp ep/timeline.json ep/three/` — timing for everything
5. `python scripts/render4.py ep video.mp4` (use `--preview 3,10,25` for a quick contact sheet)
6. `python scripts/mix4.py ep audio.wav`
7. `ffmpeg -i video.mp4 -i audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest final.mp4`

Render time is ~25 min for 60 s (software WebGL).
