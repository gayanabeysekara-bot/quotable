# Discipline Is a Decision: Sun Tzu and the King's Captains (9:16)

A vertical motivation video, 1:51 at 1080×1920, built with three.js. It's narrated by the free **Kokoro-82M** voice `am_michael` (#6), pitched about 5% deeper with a short echo, and scored with war drums and a low drone made in `mix.py`.

## The story (and the source)
The story isn't in *The Art of War* itself. It comes from Sun Tzu's biography in Sima Qian's *Records of the Grand Historian* (*Shiji*, c. 94 BC). King Helü of Wu tests Sun Tzu by having him drill 180 palace women, with the king's two favourite concubines as captains. They laugh twice. Sun Tzu blames the general (himself) the first time and the officers the second. He has the two captains executed despite the king's plea, saying a general in the field cannot accept every order of his sovereign. With new captains, the drill is carried out perfectly.

Note: the people executed were the **two captains**, not a general. The script follows the source. The execution is shown without any violence: the captains dissolve into embers.

## Script
| Line | Narration |
|---|---|
| hook | Twenty-five centuries ago, one general proved that discipline is not a feeling. It's a decision. |
| king | The King of Wu had read Sun Tzu's Art of War, and he wanted a test. |
| test | Can your methods train anyone? he asked. Even the women of my palace? |
| yes | Sun Tzu said yes. |
| ranks | One hundred and eighty women were lined up in two companies. The king's two favourite concubines were made their captains. |
| orders | Sun Tzu explained the commands. Face front. Turn left. Turn right. Then he struck the drum. |
| laugh1 | They laughed. |
| blame1 | If the commands are not clear, Sun Tzu said, the fault is the general's. |
| repeat | So he explained them again. Carefully. And struck the drum. |
| laugh2 | They laughed again. |
| blame2 | But when the commands are clear, and still not obeyed, the fault belongs to the officers. |
| execute | He ordered the two captains executed. |
| king2 | The king begged him to stop. Sun Tzu refused. A general in the field, he said, cannot accept every order of his sovereign. |
| silence | New captains were chosen. The drum sounded once more. |
| perfect / drill | This time, every woman moved in perfect silence. Left. Right. Kneel. Rise. |
| lesson | Here is the lesson. |
| you | You already know the commands. Wake up early. Do the work. Put the phone down. |
| captains | The problem was never clarity. It's the two captains in your head who keep laughing. Comfort. And excuses. |
| remove | You don't negotiate with them. You remove them. |
| drum | Then strike the drum again, and watch how fast the rest of you falls in line. |
| end | Discipline is a decision. Make it today. |

## Rebuild
```bash
./venv/bin/python tts.py kokoro-v1.0.int8.onnx voices-v1.0.bin am_michael 0.9   # narration + timeline.js
./venv/bin/python mix.py                                                       # drums/drone + cues.js
node render.cjs art-of-war-discipline.mp4 30                                    # ~12 min
```
Model files: `https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/` (`kokoro-v1.0.int8.onnx`, `voices-v1.0.bin`).
Open `index.html` in a browser and click to preview it with audio (`preview-audio.m4a` is written by the render).
