# CLAUDE.md — The Compound Mind: Daily Dose for Senior Leaders

## Who this is for
- **Owner:** Gayan Abeysekara, School Business Manager (dual campus, Darwin NT), 19+ years across finance, banking, property, operations and education. Building a COO-track personal brand under Velnox.
- **Audience:** busy senior leaders and aspiring leaders who want to get better but don't have time to read. Smart, time-poor, sceptical of hype.
- **Promise:** *Ideas that compound, for people who lead.* One useful idea a day, under 60 seconds, that you can use in your next meeting.

## The flow
```
Create for myself  →  Daily Dose for senior leaders
(private edition)      (public: 1 video + 1 LinkedIn post per day)
```
The private "Content Edition" newsletter stays the research engine. Every public piece is pulled out of it. Never publish anything that hasn't been through the edition first.

## Content pillars and weekly rotation
| Day | Pillar | Video | Format |
|---|---|---|---|
| Mon | Leadership | Short | 9:16, 45–60s |
| Tue | Finance (numbers for operators) | Short | 9:16, 45–60s |
| Wed | HR / People | Short | 9:16, 45–60s |
| Thu | Investment & wealth (education only) | Short | 9:16, 45–60s |
| Fri | Operator's Case (real lesson from Gayan's week, anonymised) | Short | 9:16, 45–60s |
| Sat | The Weekly Compound (ties Mon–Fri together) | Long-form | 16:9, 5–8 min |
| Sun | Week in One Minute (recap + next week's teaser) | Short | 9:16, ~60s |

**Rule: exactly one video per day.** Never generate a second video for the same date.

Monthly themes (e.g. "Foundations of Compounding") and weekly themes (e.g. "The Compounding Leader") carry across all pillars, so the week reads as one story.

## The daily unit: one idea, one evidence, one move
Every piece follows this structure:
1. **Hook (0–3s):** a surprising claim, number or question. On-screen text, 4 words max.
2. **Idea:** one sentence, in plain English.
3. **Evidence:** one named, checkable source (study, letter, book, data). Cite it.
4. **Move:** one thing the viewer can do this week.
5. **CTA:** one question for the comments, or "Full breakdown on Saturday."

One idea per piece. If it needs two ideas, it's two days.

## Daily output pack
Save to `editions/YYYY-MM-DD/`:
1. `script.md`: video script (Shorts 110–150 words; Saturday long-form 750–1,200 words with chapter markers). Sentences 15–20 words. Data and lists formatted clearly so they render as on-screen text or charts. Add visual cues in brackets, e.g. `[On screen: 1.5% → 0.8%, bar chart]`.
2. `linkedin.md`: same idea as a LinkedIn post. Hook line, short lines, 120–200 words, ends with a question, 3 hashtags max, no external link in the body (put the link in the first comment).
3. `carousel.md`: 5 slides (hook, idea, evidence, move, CTA), ≤20 words per slide. Only for Tue and Thu, or when the idea has data.
4. `youtube.md`: title (≤60 chars) plus 2 alternatives, description (first line includes the keyword), sources as links, 5–8 tags, pinned comment. Chapters on Saturdays only.
5. `sources.md`: every source with URL and access date, plus a "what we are NOT claiming" line.
6. `shots.md`: the Luma shot list (one prompt per scene, with duration and aspect ratio).
7. `video-log.md`: Luma generation IDs per shot, model, status, credits used, voiceover file, final video link.

## Video animation: Luma (Dream Machine / Ray)
Animation is generated with **Luma AI** (Dream Machine, Ray models). Luma makes short animated clips (about 5–10s each) from text or an image. It does **not** add the voiceover or reliable on-screen text, so the daily video is built in three layers:

1. **Voice:** generate the voiceover from `script.md` in Gayan's cloned voice (see "Voice" below). Save as `editions/YYYY-MM-DD/voiceover.mp3`. This sets the timing.
2. **Animation (Luma):** split the script into scenes and write `shots.md`: one Luma prompt per scene, matched to the voiceover timing. A Short needs about 6–9 shots; Saturday long-form uses Luma for chapter openers and key moments only.
3. **Assemble:** cut the Luma clips to the voiceover in the editor (CapCut, Descript or Premiere). Add burned-in captions, data charts, numbers, the logo and chapter cards **in the edit**, not in Luma. AI video garbles text and numbers.

**Steps:**
1. **Shot list:** write `shots.md` from `script.md`. Check every prompt against the brand and compliance rules below before generating anything.
2. **Generate once:** one Luma generation per shot, one set of shots per day. This uses credits. Regenerate a shot only if it failed, shows garbled text or a recognisable face, or breaks a compliance rule. Log every generation in `video-log.md`.
3. **Assemble** the final cut and save the link in `video-log.md`.
4. **Do not publish.** Leave the video and posts ready for Gayan to approve. Publishing to YouTube or LinkedIn needs his explicit OK.

If a Luma connector or API key isn't available in the session, write `shots.md` ready to paste into Dream Machine (lumalabs.ai) and stop there.

**Luma prompt style:**
- Abstract, brand-coloured motion: dark charcoal background, lime #C8F544 accents, slow camera moves, clean geometric shapes, soft light. Keep it consistent so the channel looks like one series.
- One clear action per shot: "a single lime line climbs slowly across a dark grid, camera dollies forward" beats "show growth".
- Use an image reference (a brand frame or last frame of the previous shot) to keep style continuous.
- No people's faces, no real public figures, no logos or brands, no text in the prompt. Avoid stock clichés (handshakes, whiteboards, city timelapses).
- Metaphors for ideas: compounding = a snowball, stacked layers, a growing lime spiral; cost leakage = a dripping tap; focus = a lens pulling into sharp focus.

**Settings:**
- Shorts: 9:16, 45–60s total, burned-in captions, logo as anchor.
- Saturday: 16:9, 5–8 min, chapter cards.
- Keep the same voice every day: Gayan's cloned voice if set up, otherwise the agreed stock voice.

## Voice
- Gayan's cloned voice lives in one tool only (record the tool and voice ID here once set up). Same voice, same settings every day.
- Never use the clone for anything Gayan hasn't approved, and never to say something he wouldn't say on camera.

**Disclosure:** if a video uses an AI avatar, Gayan's cloned voice or realistic AI-generated footage, flag it in `youtube.md` so the YouTube "altered or synthetic content" box gets ticked at upload.

## Brand
- **Name:** The Compound Mind (@CompoundMindYT). *Confirm with Gayan: the private edition uses "My Compound Mind". Use one name in public.*
- **Look:** dark background, lime accent #C8F544, Bebas Neue headings, clean sans body.
- **Tagline:** "Build in silence. Let it compound."
- **Voice:** friendly but direct, like a COO talking to a peer. Australian spelling. No hype words (game-changer, unlock, secret, hack). No "In today's fast-paced world." Confident, specific, a little dry.
- **Sign-off:** "Ideas that compound, for people who lead."

## Accuracy and compliance (non-negotiable)
- **Every fact needs a named source** in `sources.md`. Quote exactly from the original or a reliable transcript. If you can't verify something, cut it.
- **Correlation ≠ causation.** Say "associated with" when the study design calls for it, and say caveats out loud in the script.
- **Thursday / Investment:** education only. Include "General education, not financial advice" on screen and in the description. No stock picks, no "buy/sell", no return promises.
- **Friday / Operator's Case:** fully anonymised. Never name or hint at a student, parent, staff member, school, CENT, or any confidential matter (HR processes, finances, incidents). Use generic framing: "a school I work with", "a team of 30". If in doubt, leave it out.
- **HR content:** general principles only, not legal advice. Note that employment law varies by jurisdiction.
- **Copyright:** short quotes only (under 15 words), one per source. No copyrighted music, characters or footage.
- Label Gayan's own opinions and hypothetical examples as such.

## Quality bar (check before generating)
- [ ] Would a busy director stop scrolling for the hook?
- [ ] Is it exactly one idea?
- [ ] Is the evidence named and verifiable?
- [ ] Can the viewer act on it this week?
- [ ] Short script is ≤150 words?
- [ ] Brand, voice and compliance rules met?
- [ ] Does it link back to the weekly theme?

## Weekly rhythm
- **Sunday (planning):** draft next week's 7 topics against the monthly theme. Save to `plans/YYYY-Www.md`. Get Gayan's OK before the week starts.
- **Daily:** build the pack → plan → generate one video → log → leave it for approval.
- **Saturday:** long-form built from Mon–Fri. Reuse their evidence and add depth.
- **Monthly:** review the top 3 and bottom 3 performers (views, retention, comments) and write `reviews/YYYY-MM.md` with what to repeat and what to drop.

## Don'ts
- Don't publish without approval.
- Don't make more than one video per day (one set of Luma shots per day).
- Don't use real names from Gayan's workplace.
- Don't give personal financial, legal or HR advice.
- Don't invent stats, quotes or sources.
