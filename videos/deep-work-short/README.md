# Deep Work: vertical Short (9:16)

A 49-second three.js explainer at 1080×1920. It's narrated by **Kokoro-82M**, a free, open-source TTS model (Apache-2.0), and has word-by-word captions.

| File | What it is |
|---|---|
| `deep-work-short.mp4` | Final video, ready for YouTube Shorts / Reels / TikTok |
| `narration.wav` | Voiceover on its own (Kokoro, voice `af_heart`) |
| `timeline.js` | Line and word timings generated from the voiceover |
| `index.html` | The animation. Open it in a browser and click to play it with audio |
| `tts.py` | Script: edit `LINES` to change what is said |
| `render.cjs` | Frame-by-frame renderer (Playwright + ffmpeg) |

## Changing the voice or script
```bash
python -m venv venv && ./venv/bin/pip install kokoro-onnx soundfile
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
./venv/bin/python tts.py kokoro-v1.0.int8.onnx voices-v1.0.bin am_michael 1.0   # voice, speed
node render.cjs deep-work-short.mp4 30
```
Other free voices include `af_heart`, `af_bella` and `af_nicole` (US female); `am_michael`, `am_fenrir` and `am_puck` (US male); `bf_emma` (UK female); and `bm_george` (UK male).
The scenes follow the timeline automatically, so a new voice or speed stays in sync. If you rename or remove a line key, update the matching scene in `index.html`.
