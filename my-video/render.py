"""Render an animated explainer video:
"Why Holy Family Catholic Primary School, Karama is a great choice".

Usage: python3 render.py   ->  writes holy-family-explainer.mp4 next to this file.
Frames are drawn with Pillow and piped into ffmpeg.
"""
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1920, 1080, 30
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "holy-family-explainer.mp4")

FONT_DIR = "/usr/share/fonts/truetype"
SERIF_B = f"{FONT_DIR}/dejavu/DejaVuSerif-Bold.ttf"
SANS = f"{FONT_DIR}/liberation/LiberationSans-Regular.ttf"
SANS_B = f"{FONT_DIR}/liberation/LiberationSans-Bold.ttf"
EMOJI = f"{FONT_DIR}/noto/NotoColorEmoji.ttf"

NAVY_TOP = (12, 30, 66)
NAVY_BOT = (28, 68, 128)
GOLD = (242, 190, 66)
WHITE = (255, 255, 255)
SOFT = (210, 222, 240)

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


_emoji_cache = {}


def emoji_img(ch, size):
    """Noto Color Emoji only renders at 109px; draw there, then resize."""
    if ch not in _emoji_cache:
        f = ImageFont.truetype(EMOJI, 109)
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((80, 80), ch, font=f, embedded_color=True, anchor="mm")
        _emoji_cache[ch] = im.crop(im.getbbox())
    base = _emoji_cache[ch]
    scale = size / max(base.size)
    return base.resize((max(1, int(base.width * scale)), max(1, int(base.height * scale))), Image.LANCZOS)


# ---------- easing / timing helpers ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def appear(t, start, dur=0.6):
    return ease_out((t - start) / dur)


# ---------- drawing helpers ----------
def gradient_bg():
    bg = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(bg)
    for y in range(H):
        k = y / H
        c = tuple(int(NAVY_TOP[i] + (NAVY_BOT[i] - NAVY_TOP[i]) * k) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    return bg


BG = gradient_bg()


def wrap(text, f, max_w, draw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textlength(trial, font=f) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_layer(draw_fn):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(layer), layer)
    return layer


def put_text(layer, xy, text, f, fill, alpha, anchor="mm", dy=0):
    if alpha <= 0:
        return
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((xy[0], xy[1] + dy), text, font=f, fill=fill + (255,), anchor=anchor)
    if alpha < 1:
        a = tmp.getchannel("A").point(lambda v: int(v * alpha))
        tmp.putalpha(a)
    layer.alpha_composite(tmp)


def put_emoji(layer, ch, center, size, prog):
    if prog <= 0:
        return
    s = int(size * max(0.05, ease_back(prog)))
    im = emoji_img(ch, s)
    if prog < 1:
        a = im.getchannel("A").point(lambda v: int(v * clamp(prog * 1.5)))
        im.putalpha(a)
    layer.alpha_composite(im, (int(center[0] - im.width / 2), int(center[1] - im.height / 2)))


def rounded_card(layer, box, alpha, fill=(255, 255, 255), opacity=34, outline=GOLD):
    if alpha <= 0:
        return
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).rounded_rectangle(
        box, radius=36, fill=fill + (int(opacity * alpha),), outline=outline + (int(255 * alpha),), width=4
    )
    layer.alpha_composite(tmp)


def heading(layer, t, text, y=200, start=0.2):
    p = appear(t, start, 0.7)
    put_text(layer, (W // 2, y), text, font(SERIF_B, 84), WHITE, p, dy=(1 - p) * 40)
    # gold underline grows from the centre
    lw = int(260 * appear(t, start + 0.3, 0.6))
    if lw > 0:
        ImageDraw.Draw(layer).rounded_rectangle(
            (W // 2 - lw, y + 62, W // 2 + lw, y + 70), radius=4, fill=GOLD + (255,)
        )


def body_lines(layer, t, lines, y0, start, gap=0.45, size=50, color=SOFT, step=78):
    f = font(SANS, size)
    for i, ln in enumerate(lines):
        p = appear(t, start + i * gap, 0.6)
        put_text(layer, (W // 2, y0 + i * step), ln, f, color, p, dy=(1 - p) * 30)


# ---------- scenes ----------
# Each scene: (duration_seconds, caption, draw(layer, t))
# Facts are limited to what public listings agree on; see README.md.


def s_title(L, t):
    put_emoji(L, "⛪", (W // 2, 250), 170, appear(t, 0.1, 0.8))
    p = appear(t, 0.6, 0.8)
    put_text(L, (W // 2, 470), "Why Holy Family", font(SERIF_B, 110), WHITE, p, dy=(1 - p) * 50)
    p = appear(t, 0.9, 0.8)
    put_text(L, (W // 2, 600), "Catholic Primary School?", font(SERIF_B, 90), GOLD, p, dy=(1 - p) * 50)
    p = appear(t, 1.6, 0.8)
    put_text(L, (W // 2, 740), "Karama  ·  Darwin, Northern Territory", font(SANS, 52), SOFT, p)


def s_history(L, t):
    heading(L, t, "A school with heart since 1983")
    put_emoji(L, "\U0001F3EB", (W // 2, 470), 220, appear(t, 0.7, 0.8))
    years = int(43 * ease_out((t - 1.2) / 1.6)) if t > 1.2 else 0
    p = appear(t, 1.2, 0.5)
    put_text(L, (W // 2, 700), f"{years}+ years", font(SERIF_B, 110), GOLD, p)
    body_lines(L, t, ["of educating and caring for Karama families"], 810, 2.4)


def s_values(L, t):
    heading(L, t, "Built on three values", y=170)
    items = [("\U0001F981", "Courage", "Trying new things and\nstanding up for what's right"),
             ("\U0001F91D", "Respect", "Valuing every person,\nevery culture, every voice"),
             ("❤️", "Mercy", "Kindness, forgiveness and\ncare for one another")]
    cw, ch, gap = 500, 560, 70
    x0 = (W - (3 * cw + 2 * gap)) // 2
    for i, (emo, name, desc) in enumerate(items):
        st = 0.8 + i * 0.7
        p = appear(t, st, 0.7)
        if p <= 0:
            continue
        dy = int((1 - p) * 80)
        x = x0 + i * (cw + gap)
        top = 320 + dy
        rounded_card(L, (x, top, x + cw, top + ch), p)
        put_emoji(L, emo, (x + cw // 2, top + 130), 140, appear(t, st + 0.2, 0.7))
        put_text(L, (x + cw // 2, top + 280), name, font(SERIF_B, 70), GOLD, p)
        for j, ln in enumerate(desc.split("\n")):
            put_text(L, (x + cw // 2, top + 380 + j * 52), ln, font(SANS, 38), WHITE, p)


def s_faith(L, t):
    heading(L, t, "Faith and learning, side by side")
    put_emoji(L, "\U0001F64F", (W // 2 - 260, 480), 200, appear(t, 0.8, 0.7))
    put_emoji(L, "\U0001F4DA", (W // 2 + 260, 480), 200, appear(t, 1.2, 0.7))
    p = appear(t, 1.5, 0.5)
    put_text(L, (W // 2, 480), "+", font(SANS_B, 140), GOLD, p)
    body_lines(L, t, ["Catholic faith is part of everyday school life,",
                      "helping children grow in mind, heart and spirit."], 720, 2.0)


def s_early(L, t):
    heading(L, t, "Learning starts early at Rainbows")
    put_emoji(L, "\U0001F308", (W // 2, 450), 230, appear(t, 0.7, 0.8))
    bullets = ["•  Early learning for children aged 2½ to 5",
               "•  Play-based, hands-on discovery",
               "•  Guided by the Early Years Learning Framework"]
    body_lines(L, t, bullets, 660, 1.6, gap=0.6, size=50, color=WHITE)


def s_journey(L, t):
    heading(L, t, "From first steps to Year 6")
    stages = [("\U0001F308", "Early\nLearning"), ("\U0001F392", "Transition"),
              ("✏️", "Years\n1 – 3"), ("\U0001F52C", "Years\n4 – 6"),
              ("\U0001F393", "Ready for\nhigh school")]
    n = len(stages)
    xs = [260 + i * (W - 520) // (n - 1) for i in range(n)]
    y = 560
    # line grows along the timeline
    prog = ease_out((t - 0.6) / 3.0)
    d = ImageDraw.Draw(L)
    if prog > 0:
        d.rounded_rectangle((xs[0], y - 6, xs[0] + int((xs[-1] - xs[0]) * prog), y + 6),
                            radius=6, fill=GOLD + (255,))
    for i, (emo, label) in enumerate(stages):
        st = 0.6 + i * 0.65
        p = appear(t, st, 0.6)
        if p <= 0:
            continue
        r = int(95 * ease_back(p))
        d.ellipse((xs[i] - r, y - r, xs[i] + r, y + r), fill=(255, 255, 255, int(255 * p)),
                  outline=GOLD + (255,), width=6)
        put_emoji(L, emo, (xs[i], y), 100, p)
        for j, ln in enumerate(label.split("\n")):
            put_text(L, (xs[i], y + 150 + j * 50), ln, font(SANS_B, 42), WHITE, p)


def s_care(L, t):
    heading(L, t, "Support for busy families")
    items = [("\U0001F558", "After School Care", "Safe, fun care when the bell rings"),
             ("☀️", "Vacation Care", "Activities through the school holidays")]
    cw, ch, gap = 720, 420, 90
    x0 = (W - (2 * cw + gap)) // 2
    for i, (emo, name, desc) in enumerate(items):
        st = 0.8 + i * 0.8
        p = appear(t, st, 0.7)
        if p <= 0:
            continue
        x = x0 + i * (cw + gap) + int((1 - p) * (-80 if i == 0 else 80))
        top = 380
        rounded_card(L, (x, top, x + cw, top + ch), p)
        put_emoji(L, emo, (x + cw // 2, top + 120), 130, appear(t, st + 0.2, 0.7))
        put_text(L, (x + cw // 2, top + 260), name, font(SERIF_B, 60), GOLD, p)
        put_text(L, (x + cw // 2, top + 340), desc, font(SANS, 38), WHITE, p)


def s_community(L, t):
    heading(L, t, "A close-knit community")
    faces = ["\U0001F467\U0001F3FD", "\U0001F466\U0001F3FB", "\U0001F467\U0001F3FF",
             "\U0001F466\U0001F3FE", "\U0001F467\U0001F3FC"]
    for i, f in enumerate(faces):
        put_emoji(L, f, (W // 2 + (i - 2) * 200, 470), 150, appear(t, 0.7 + i * 0.25, 0.6))
    body_lines(L, t, ["Around 250 students, so every child is known by name",
                      "and families feel part of the school family."], 690, 2.2)


def s_cta(L, t):
    put_emoji(L, "\U0001F4AB", (W // 2, 230), 150, appear(t, 0.1, 0.8))
    p = appear(t, 0.4, 0.8)
    put_text(L, (W // 2, 420), "Come and see for yourself", font(SERIF_B, 96), WHITE, p, dy=(1 - p) * 40)
    p = appear(t, 1.0, 0.8)
    put_text(L, (W // 2, 540), "Book a school tour today", font(SANS_B, 60), GOLD, p)
    body_lines(L, t, ["Holy Family Catholic Primary School",
                      "Calytrix Road, Karama NT 0812",
                      "(08) 8927 6188  ·  admin.holyfamily@nt.catholic.edu.au"],
               680, 1.6, gap=0.35, size=46, step=70)


SCENES = [
    (7.0, "Why choose Holy Family Catholic Primary School in Karama?", s_title),
    (8.0, "Holy Family has served Karama families since 1983.", s_history),
    (10.0, "Everything here is built on Courage, Respect and Mercy.", s_values),
    (8.5, "Catholic faith is woven into everyday learning.", s_faith),
    (9.0, "Little learners start at Rainbows Early Learning.", s_early),
    (9.0, "Children can grow with one school all the way to Year 6.", s_journey),
    (8.0, "After School and Vacation Care help working families.", s_care),
    (8.0, "It's a small, welcoming community where everyone belongs.", s_community),
    (9.0, "Come and visit. Book a tour today!", s_cta),
]

FADE = 0.5
TOTAL = sum(s[0] for s in SCENES)


def footer(L, t_global, caption, cap_alpha):
    d = ImageDraw.Draw(L)
    # caption strip
    if cap_alpha > 0:
        f = font(SANS_B, 40)
        tw = d.textlength(caption, font=f)
        box = (W // 2 - tw / 2 - 30, H - 175, W // 2 + tw / 2 + 30, H - 105)
        d.rounded_rectangle(box, radius=20, fill=(0, 0, 0, int(150 * cap_alpha)))
        put_text(L, (W // 2, H - 140), caption, f, WHITE, cap_alpha)
    # brand + progress bar
    put_text(L, (60, H - 50), "Holy Family Catholic Primary School · Karama NT",
             font(SANS, 30), SOFT, 0.8, anchor="lm")
    d.rectangle((0, H - 8, int(W * t_global / TOTAL), H), fill=GOLD + (255,))


def render():
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t_global = 0.0
    for dur, caption, fn in SCENES:
        frames = int(round(dur * FPS))
        for i in range(frames):
            t = i / FPS
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            fn(layer, t)
            # scene fade in / out
            k = min(clamp(t / FADE), clamp((dur - t) / FADE))
            if k < 1:
                layer.putalpha(layer.getchannel("A").point(lambda v, k=k: int(v * k)))
            frame = BG.convert("RGBA")
            frame.alpha_composite(layer)
            cap_a = min(appear(t, 0.8, 0.5), clamp((dur - t) / FADE))
            footer(frame, t_global + t, caption, cap_a)
            proc.stdin.write(frame.convert("RGB").tobytes())
        t_global += dur
    proc.stdin.close()
    proc.wait()
    print(f"Wrote {OUT} ({TOTAL:.0f}s)")


if __name__ == "__main__":
    render()
