# Quotable Nights — episode template

Builds a vertical (1080×1920) episode: clip in a card + chat-bubble POV story +
three.js kawaii mascot/floaties + free Kokoro TTS voiceover + synthesized SFX.

1. `cd three && npm install` (three.js; Playwright/Chromium must be available)
2. Fonts: put `Fredoka.ttf` and `Nunito.ttf` (Google Fonts, OFL) in `fonts/`
3. Voice: `pip install kokoro-onnx soundfile`, download `kokoro-v1.0.int8.onnx` and
   `voices-v1.0.bin` from the kokoro-onnx GitHub releases into `tts/`, then
   `python scripts/tts.py tts vo af_heart` (edit LINES in tts.py per episode)
4. `python scripts/render3.py clip.mp4 out.mp4 three vo` → silent video `out.mp4.video.mp4`
5. `python scripts/mix3.py clip.mp4 vo audio.wav`, then mux:
   `ffmpeg -i out.mp4.video.mp4 -i audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest final.mp4`

Per episode, edit: `MSGS`, `TYPING_THEM`, `DRAFTS`, `SEEN_AT`, `NOREPLY_AT`, the quote/EP text
in `render3.py`; matching SFX times + VO start times in `mix3.py`; mood times in `three/scene.html`.
