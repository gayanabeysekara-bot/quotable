---
name: cartoon-3d-short
description: Use when planning, designing, generating or reviewing a short vertical video (15–70 seconds) in a stylised 3D cartoon look — character bible, style lock, shot list, image and video generator prompts, voice, captions and edit — for YouTube Shorts, Reels or TikTok.
---

# Cartoon 3D Shorts (stylised 3D animated look)

A production recipe for short vertical videos with original, appealing 3D cartoon characters: big expressive eyes, soft rounded shapes, warm cinematic light. The look gets the click, but the story keeps people watching, so pair this with a strong script (for 60-second "true story" Shorts, write the script with the `true-story-shorts` skill first, then use this skill for the visuals).

## 1. Brief (before any generation)
- Length and platform: 15–30s (one gag or one moment) or 45–70s (a full mini-story).
- One-line premise, the hook action for frame 1, and the payoff shot for the last frame.
- Who the audience is and what they should feel at the end (laugh, "aww", "huh, I didn't know that").
- Budget: which tools are available (image generator, image-to-video model, voice tool, editor) and how many credits a Short may use.

## 2. Character bible (one per recurring character)
Consistency across shots matters more than any single beautiful frame. For each character write:
- Name, role, age, personality in three words.
- Silhouette and proportions (e.g. "large head, small body, round belly, short legs").
- Fixed colour palette with 3–4 named colours, plus outfit and one signature prop or feature.
- Expression range: neutral, delighted, smug, shocked, worried.
- A **character anchor prompt**: one paragraph you paste unchanged into every shot prompt.
- A **reference sheet**: generate front, three-quarter and side views on a plain background, pick the best and reuse it as the image reference for every later shot.

Characters must be original. Never copy or name existing studio characters, mascots, franchises or another creator's designs, and don't prompt with studio or film names; describe the qualities you want instead.

## 3. Style lock
Write one **style anchor prompt** and append it to every image prompt, for example:
"stylised 3D animated feature look, soft subsurface skin, rounded shapes, large expressive eyes, warm key light with soft rim light, shallow depth of field, rich saturated but gentle colours, clean background, 9:16 vertical"
- Fix the lighting mood per scene (morning warm, night blue with a warm practical light).
- Keep the same tool, model version and settings for the whole Short. Record the seed when the tool exposes one.
- Negative prompt where supported: text, watermark, extra fingers, distorted face, realistic photo, logo.

## 4. Shot list
- 1080x1920, 30fps (24fps is fine for a filmic feel; keep it consistent).
- A new shot every 2–4 seconds: establishing, medium, close-up reaction, insert of the key object, push-in for the reveal.
- Frame 1 shows the hook action, because the opening frames act as the thumbnail.
- For each shot write: number, timestamp, script line, framing, character action and expression, camera move, and the duration needed.

## 5. Generate (image first, then motion)
1. **Key frame per shot:** character anchor + action + setting + framing + style anchor, with the reference sheet attached as the image reference. Make 2–4 variants and keep the one most on-model.
2. **Check on-model** against the bible: palette, proportions, outfit, prop. Regenerate rather than accept drift.
3. **Animate** each key frame with image-to-video. Keep motion prompts simple: one action plus one camera move ("she gasps and leans back, slow push-in"). 3–6 second clips loop and cut better than long ones.
4. Reject clips with morphing faces, melting hands, flicker or extra limbs. Cut around small glitches instead of re-rendering when possible.
5. Keep a log: shot, prompt, seed, tool, chosen file. It makes fixes and sequels cheap.

## 6. Voice, sound and captions
- Narrator or character voices: the creator's own, or an AI voice they hold the rights to. Record or generate voice before final edit timing.
- Lip-sync only on close-ups where it matters; otherwise favour narration over talking mouths, which hides sync errors.
- Licensed or original music kept under the voice, plus a few cartoon sound effects on actions (whoosh, pop, thud) for punch.
- Burned-in captions one to three words at a time, bold white with a dark outline, lower-centre, kept clear of the platform UI.

## 7. Edit
- Cut on action and on beats in the voice. Trim each clip's first and last few frames, where generators are weakest.
- Add small push-ins or zooms in the editor to keep stills and slow clips alive.
- Colour-match shots so the palette doesn't jump between clips.
- No logo sting, end screen or subscribe card. End on the payoff shot so the video loops.

## 8. Quality gate before publishing
- [ ] Hook action visible in frame 1 and spoken in the first line
- [ ] Every shot on-model (palette, proportions, outfit, prop)
- [ ] No morphing faces, extra fingers, flicker or garbled text in frame
- [ ] Shot changes every 2–4 seconds; total length on brief
- [ ] Captions readable and clear of the platform UI
- [ ] Characters, visuals, voice and music all original or licensed; no studio, franchise or creator look-alikes
- [ ] AI-generated content labelled where the platform requires it
- [ ] Account owner has approved publishing

## 9. Measure
Track views at 24 hours and 7 days, average percentage viewed and the retention drop in the first 3 seconds. If people drop early, fix frame 1 and the hook line; if they drop mid-way, tighten shots. Reuse characters that viewers mention in comments, since a recurring cast compounds.

## Deliverable per Short
The brief, character bible(s) with anchor prompts and reference sheets, the style anchor, the shot list with key-frame and motion prompts, the generation log, voice, music and caption notes, the edit timeline, and the quality-gate result.
