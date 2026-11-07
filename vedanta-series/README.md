# Who Am I? — Vedanta in 90 seconds

A 7-part vertical (9:16, 1080×1920) animated series that teaches Advaita Vedanta through its classic
stories. Each episode is 74–98 seconds, opens with a hook, and ends by teasing the next episode.

Everything is generated from code, with no paid tools or stock assets:

- **Animation:** SVG motion graphics drawn per frame in Chromium (`engine/`, `episodes/`)
- **Voice:** [Kokoro](https://github.com/thewh1teagle/kokoro-onnx), an open-weight TTS model (Apache-2.0). It handles the narrator plus character voices.
- **Music & SFX:** a tanpura-style drone, gong, chime, splash and the rest, all synthesized from scratch in `tools/music.py`
- **Fonts:** Baloo 2 and Yatra One (SIL Open Font License), bundled in `engine/fonts/`

## Episodes

| # | Title | Story | Source | Big idea |
|---|---|---|---|---|
| 1 | The Snake That Was Never There | A man panics at a "snake" that turns out to be a rope | Shankara's rope-snake (*rajju-sarpa*) | *Adhyāsa*: seeing one thing as another |
| 2 | The Tenth Man | Ten men cross a river and each counts only nine | Traditional Vedanta teaching story | *Daśamas tvam asi*: the seeker is the sought |
| 3 | Salt in the Water | Uddālaka dissolves salt to teach Śvetaketu | Chāndogya Upaniṣad, ch. 6 | *Tat tvam asi*: you are that |
| 4 | The Wave Who Was Afraid | A little wave fears the shore | Classic teaching analogy | Jīva and Brahman; *nāma-rūpa* |
| 5 | The Space in the Pot | Smash a pot: where does its space go? | Gauḍapāda, Māṇḍūkya Kārikā ch. 3 | Ātman = Brahman (*ghaṭākāśa*) |
| 6 | Three Worlds Every Night | Waking, dreaming, deep sleep | Māṇḍūkya Upaniṣad | *Turīya*, the witness (*sākṣī*) |
| 7 | The Boy Who Met Death | Naciketas waits three days at Yama's door | Kaṭha Upaniṣad (1.2.1–2, 1.2.18) | The pleasant vs the good; the Self never dies |

Rendered videos: `out/ep1.mp4` … `out/ep7.mp4`.

## Posting copy (Shorts / Reels / TikTok)

Post one a day, in order. Each video's end card names the next episode.

**Ep 1: The Snake That Was Never There**
Title: `You've been scared of a snake that was never there 🐍 | Who Am I? Ep 1`
Caption: An ancient Indian story about the biggest mistake we make about ourselves. #vedanta #advaita #spirituality #philosophy #shorts

**Ep 2: The Tenth Man**
Title: `10 men crossed a river. Only 9 came out. | Who Am I? Ep 2`
Caption: Why you can't find what you're looking for. #vedanta #advaita #selfinquiry #philosophy #shorts

**Ep 3: Salt in the Water**
Title: `A father, a lump of salt, and the biggest idea in India | Who Am I? Ep 3`
Caption: Tat tvam asi: "you are that." From the Chandogya Upanishad. #vedanta #upanishads #tattvamasi #philosophy #shorts

**Ep 4: The Wave Who Was Afraid**
Title: `A little wave had a panic attack 🌊 | Who Am I? Ep 4`
Caption: What if you're not the wave, but the ocean? #vedanta #advaita #anxiety #mindfulness #shorts

**Ep 5: The Space in the Pot**
Title: `Smash a pot. Where does the space inside go? | Who Am I? Ep 5`
Caption: Gaudapada's famous image of Atman and Brahman. #vedanta #atman #brahman #philosophy #shorts

**Ep 6: Three Worlds Every Night**
Title: `You visit 3 worlds every night. Something follows you. | Who Am I? Ep 6`
Caption: Waking, dreaming, deep sleep, and the fourth. From the Mandukya Upanishad. #vedanta #consciousness #turiya #shorts

**Ep 7: The Boy Who Met Death**
Title: `A boy waited 3 days at Death's door. Then he asked one question. | Who Am I? Ep 7`
Caption: The finale. From the Katha Upanishad. #vedanta #kathaupanishad #nachiketa #spirituality #shorts

## Rebuild / make a new episode

```bash
# one-time: TTS model (≈350 MB) into a folder of your choice
python3 -m venv venv && venv/bin/pip install kokoro-onnx soundfile
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx   # save as kokoro.onnx
curl -LO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin   # save as voices.bin

venv/bin/python tools/tts.py ep1 <model-dir>   # narration + timings
venv/bin/python tools/music.py ep1             # drone + sfx + mix
node tools/render.js ep1 --workers 4           # -> out/ep1.mp4   (needs Playwright + ffmpeg)
tools/sheet.sh ep1 16                          # optional: contact sheet of stills
```

An episode file (`episodes/epN.js`) has two parts:

- **`lines`** holds the script, one entry per spoken line: `s` scene, `t` caption, `say` spoken text if different, `v` voice, `sp` speed, `p` pause after, `sfx`, `color`.
- **`scenes`** holds one draw function per scene. Each gets `{lt, at(k), dl(k)}`, so animation can sync to the start and length of each line.

Captions are generated automatically, karaoke-style, from `t`.
