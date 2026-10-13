# DistilBook — 40s motion showreel

A fully code-driven motion graphics piece about [DistilBook](https://distilbook.com), the AI tool that
turns any document (PDF, Word, Markdown, images, links, prompts) into a narrated explainer video.

**Output:** `distilbook-showreel.mp4` — 1920×1080, 30 fps, 40 s, H.264 + AAC stereo.

No stock footage, no templates, no After Effects: every pixel comes from `reel.js` (Canvas 2D) and
every sample of the soundtrack from `audio.py` (numpy).

## Structure (120 BPM — every cut lands on the beat)

| Time | Scene | Moves |
|---|---|---|
| 0–4s | **Cold open** | Ink drop falls → shockwave + splash physics, counter "312 pages.", strike-through on the snare, iris wipe |
| 4–8s | **The pile** | 18 documents (PDF/DOCX/MD/URL/PNG/TXT/PROMPT) land on 16th notes, slot-machine headline, vortex suck-out |
| 8–11s | **Distillation** | 720 glyph particles spiral through counter-rotating rings into a glowing core, HUD progress, implosion + silence |
| 11–15s | **Logo slam** | Flash frame, chromatic split, overshoot glyphs, sunburst, beat rings, zoom *through* the "o" |
| 15–24s | **How it works** | Amber field collapses into a sidebar; UI card with 3D flips: upload → script typed + approved → whiteboard drawn by a marker with 12 fps line boil |
| 24–30s | **19 styles** | Eighth-note hard cuts through styles, camera pull-back into a live 20-tile grid, beat ripple, diagonal flip-out |
| 30–34s | **20+ languages** | 1,100-point rotating dot globe, great-circle flight arcs, greetings in 12 scripts |
| 34–37s | **Every format** | Frame morphs 16:9 → 9:16 → 1:1 with live art inside, use-case marquee, collapses into a drop |
| 37–40s | **End card** | Bookend drop + ripple, "Don't read it. / Watch it.", wordmark lockup with glyph-clipped light sweep |

Finishing: 4-sample 180° shutter motion blur, camera shake and flash frames on impacts, film grain, vignette.

Style names in the styles section are illustrative of the range (whiteboard + motion graphics), not
DistilBook's exact catalogue. The colour palette is original to this piece.

## Rebuild

```bash
python3 audio.py                 # -> out/soundtrack.wav
node render.cjs                  # -> distilbook-showreel.mp4 (WORKERS=4 by default)
node render.cjs --stills 11,24.6 # proof individual frames into out/
```

Open `index.html` in a browser for a live, scrubbable preview.

Requires Node + Playwright (Chromium), ffmpeg (libx264), Python 3 + numpy, and the Inter / Inter Display fonts.
