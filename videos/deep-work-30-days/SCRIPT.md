# I Tried Deep Work for 30 Days: narration script

Length: 1:42 · 1920×1080 · 30 fps. Each timestamp lines up with a scene in `deep-work-30-days.mp4`.
The on-screen captions match this script word for word, so you can record the voiceover over the video as it is.

| Time | Scene | Narration |
|---|---|---|
| 0:00 | Notification swarm | Every day, hundreds of tiny interruptions steal your focus. |
| 0:04 | Swarm collapses into the focus orb, title | So I tried an experiment: thirty days of Deep Work. |
| 0:08 | Pings hit the orb | Every ping, every tab, every "quick check" pulls your attention away. |
| 0:14 | "~23 min" stat | Research by Gloria Mark found it can take around 23 minutes to fully get back on task. |
| 0:20 | Orb jumps from Task A to Task B | And even when you switch back, part of your mind stays behind. |
| 0:25 | Particles left behind | Psychologist Sophie Leroy calls this attention residue. |
| 0:30 | Work = Time × Focus | Cal Newport's idea is simple: what you produce equals time multiplied by intensity of focus. |
| 0:36 | Tall focus block rises | Two focused hours can beat four distracted ones. |
| 0:42 | 4 pillars | His book boils it down to four rules. |
| 0:44 | Pillar 1 | One: work deeply. |
| 0:47 | Pillar 2 | Two: embrace boredom. |
| 0:51 | Pillar 3 | Three: quit social media, or at least use it on purpose. |
| 0:54 | Pillar 4 | Four: drain the shallows. Shrink the busywork. |
| 0:58 | 30-tile calendar | Here's the 30-day plan. |
| 1:02 | Week 1 lights up | Week one: one 60-minute deep-work block a day, phone in another room. |
| 1:06 | Week 2 | Week two: two hours a day, and a fixed shutdown time. |
| 1:10 | Week 3 | Week three: two and a half hours, and no phone when I'm bored. |
| 1:14 | Days 22–30 | Final stretch: three hours a day, with shallow work batched into one slot. |
| 1:20 | Tower of hours, 65.5 hrs | That adds up to about sixty-five hours of deep work. |
| 1:25 | | The real test is what that time produces. |
| 1:30 | Quote and ring | "Who you are, what you think, feel, and do, what you love, is the sum of what you focus on." (Winifred Gallagher, quoted in *Deep Work*) |
| 1:36 | CTA | Try it for 30 days, track your hours, and tell me your results in the comments. |

## Before publishing
- **Run the experiment for real.** The title says "I tried". This animation is the explainer and plan section. Add your own talking-head footage or real results (hours logged, what you shipped, what was hard) between 1:25 and 1:30. Viewers will forgive rough footage but not a fake experiment.
- The audio is a **placeholder synth pad**. Replace it with your voiceover and a licensed music track.
- Sources: Gloria Mark (UC Irvine) on interruption recovery time; Sophie Leroy (2009), *Why is it so hard to do my work?*, on attention residue; Cal Newport, *Deep Work* (2016).

## Editing / re-rendering
- Open `index.html` in a browser to preview it live. Click to pause; ← and → seek 5 s.
- Text, timings and captions live in `index.html` (`txt(...)` calls and the `CAPS` array).
- Re-render: `node render.cjs deep-work-30-days.mp4 30`. This needs Playwright and ffmpeg and takes about 6 minutes.
