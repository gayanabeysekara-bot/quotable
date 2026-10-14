# Don't Tell the Cake — 10s vertical cartoon

`dont-tell-the-cake.mp4` — 1080×1920 (9:16), 30 fps, exactly 10.0 s, H.264 + AAC stereo.

One locked-off shot of Mom and Dad in the kitchen, drawn in code (Canvas 2D) to match the
supplied character sheets, with lip sync driven by the real voice audio.

| Time | Beat |
|---|---|
| 0.0–2.5 | Fridge open. Dad leans toward the cake. Mom, eyebrow raised: "Why are you whispering in the kitchen?" |
| 2.5–4.8 | Dad turns, cups his mouth, whispers "I don't want the cake to hear me." — glances back at the cake |
| 4.8–5.4 | Mom tilts her head: "Why?" |
| 5.4–6.5 | Dad, proud, whispers "I'm on a diet." |
| 6.5–8.0 | Dad slowly closes the fridge (seal thump), hand stays on the handle; Mom turns away |
| 8.0–10.0 | Dad checks Mom, cracks the door open, peers at the cake. Mom looks back, one eyebrow up. Dad freezes (comic pluck). Hold. |

## Pipeline
- `voice.py` — trims the Kokoro TTS takes (`out/vo/raw*.wav`) and turns Dad's lines into a true whisper
  via LPC resynthesis (vocal-tract envelope kept, voicing replaced with breath noise).
- `mix.py` — places the lines on the timeline, synthesizes room tone, fridge hum (louder while open),
  door seal, reopen pop and a Karplus-Strong pluck; exports `out/audio.wav` + `lips.js` (per-frame mouth openness).
- `cake.js` — the animation (pure function of time; 3-sample motion blur). `index.html` previews it.
- `render.cjs` — renders frames with Playwright and muxes with ffmpeg.

```bash
python3 voice.py && python3 mix.py && node render.cjs
```
Voices: Kokoro v1.0 (`af_heart` for Mom, `am_michael` for Dad), generated locally.
