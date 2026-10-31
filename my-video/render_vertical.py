"""Vertical 9:16 (1080x1920) version of the Holy Family explainer.

Usage: python3 render_vertical.py  ->  writes holy-family-explainer-9x16.mp4
Reuses the drawing helpers from render.py, with layouts re-done for portrait
(Reels, TikTok, YouTube Shorts, Stories).
"""
import os

from PIL import Image, ImageDraw

import render as R
from render import (GOLD, WHITE, SOFT, SERIF_B, SANS, SANS_B, font, appear, ease_out,
                    ease_back, clamp, put_text, put_emoji, rounded_card, wrap)

W, H = 1080, 1920
R.W, R.H = W, H
R.BG = R.gradient_bg()
R.OUT = os.path.join(R.HERE, "holy-family-explainer-9x16.mp4")
CX = W // 2
_measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))


def heading(L, t, text, y=330, start=0.2, size=78):
    f = font(SERIF_B, size)
    lines = wrap(text, f, W - 120, _measure)
    p = appear(t, start, 0.7)
    step = int(size * 1.25)
    for i, ln in enumerate(lines):
        put_text(L, (CX, y + i * step), ln, f, WHITE, p, dy=(1 - p) * 40)
    uy = y + (len(lines) - 1) * step + int(size * 0.85)
    lw = int(200 * appear(t, start + 0.3, 0.6))
    if lw > 0:
        ImageDraw.Draw(L).rounded_rectangle((CX - lw, uy, CX + lw, uy + 8), radius=4, fill=GOLD + (255,))


def para(L, t, text, y0, start, size=50, color=SOFT, gap=0.35, maxw=W - 140, f=None):
    f = f or font(SANS, size)
    step = int(size * 1.45)
    for i, ln in enumerate(wrap(text, f, maxw, _measure)):
        p = appear(t, start + i * gap, 0.6)
        put_text(L, (CX, y0 + i * step), ln, f, color, p, dy=(1 - p) * 30)


def h_card(L, t, top, emo, name, desc, start, height=300):
    """Horizontal card: emoji on the left, title + description on the right."""
    p = appear(t, start, 0.7)
    if p <= 0:
        return
    x0, x1 = 70, W - 70
    dx = int((1 - p) * 120)
    rounded_card(L, (x0 + dx, top, x1 + dx, top + height), p)
    put_emoji(L, emo, (x0 + dx + 140, top + height // 2), 140, appear(t, start + 0.2, 0.7))
    tx = x0 + dx + 280
    put_text(L, (tx, top + 95), name, font(SERIF_B, 62), GOLD, p, anchor="lm")
    for j, ln in enumerate(wrap(desc, font(SANS, 38), x1 - tx - 30, _measure)):
        put_text(L, (tx, top + 170 + j * 50), ln, font(SANS, 38), WHITE, p, anchor="lm")


# ---------- scenes ----------
def s_title(L, t):
    put_emoji(L, "⛪", (CX, 520), 240, appear(t, 0.1, 0.8))
    p = appear(t, 0.6, 0.8)
    put_text(L, (CX, 800), "Why Holy Family", font(SERIF_B, 100), WHITE, p, dy=(1 - p) * 50)
    p = appear(t, 0.9, 0.8)
    put_text(L, (CX, 940), "Catholic Primary", font(SERIF_B, 92), GOLD, p, dy=(1 - p) * 50)
    put_text(L, (CX, 1060), "School?", font(SERIF_B, 92), GOLD, p, dy=(1 - p) * 50)
    p = appear(t, 1.6, 0.8)
    put_text(L, (CX, 1230), "Karama", font(SANS_B, 56), SOFT, p)
    put_text(L, (CX, 1305), "Darwin, Northern Territory", font(SANS, 50), SOFT, p)


def s_history(L, t):
    heading(L, t, "A school with heart since 1983")
    put_emoji(L, "\U0001F3EB", (CX, 820), 300, appear(t, 0.7, 0.8))
    years = int(43 * ease_out((t - 1.2) / 1.6)) if t > 1.2 else 0
    put_text(L, (CX, 1130), f"{years}+ years", font(SERIF_B, 140), GOLD, appear(t, 1.2, 0.5))
    para(L, t, "of educating and caring for Karama families", 1270, 2.4)


def s_values(L, t):
    heading(L, t, "Built on three values", y=300)
    items = [("\U0001F981", "Courage", "Trying new things and standing up for what's right"),
             ("\U0001F91D", "Respect", "Valuing every person, every culture, every voice"),
             ("❤️", "Mercy", "Kindness, forgiveness and care for one another")]
    for i, (emo, name, desc) in enumerate(items):
        h_card(L, t, 450 + i * 340, emo, name, desc, 0.8 + i * 0.7)


def s_faith(L, t):
    heading(L, t, "Faith and learning, side by side")
    put_emoji(L, "\U0001F64F", (CX - 260, 840), 220, appear(t, 0.8, 0.7))
    put_text(L, (CX, 840), "+", font(SANS_B, 150), GOLD, appear(t, 1.5, 0.5))
    put_emoji(L, "\U0001F4DA", (CX + 260, 840), 220, appear(t, 1.2, 0.7))
    para(L, t, "Catholic faith is part of everyday school life, helping children grow "
               "in mind, heart and spirit.", 1120, 2.0)


def s_early(L, t):
    heading(L, t, "Learning starts early at Rainbows")
    put_emoji(L, "\U0001F308", (CX, 770), 300, appear(t, 0.7, 0.8))
    bullets = [("\U0001F476", "Ages 2½ to 5"),
               ("\U0001F9F8", "Play-based, hands-on discovery"),
               ("\U0001F4D6", "Early Years Learning Framework")]
    for i, (emo, txt) in enumerate(bullets):
        st = 1.6 + i * 0.6
        p = appear(t, st, 0.6)
        y = 1050 + i * 130
        put_emoji(L, emo, (150, y), 80, p)
        put_text(L, (230, y), txt, font(SANS_B, 48), WHITE, p, anchor="lm", dy=(1 - p) * 20)


def s_journey(L, t):
    heading(L, t, "From first steps to Year 6")
    stages = [("\U0001F308", "Early Learning"), ("\U0001F392", "Transition"),
              ("✏️", "Years 1 – 3"), ("\U0001F52C", "Years 4 – 6"),
              ("\U0001F393", "Ready for high school")]
    x, y0, step = 230, 590, 190
    ys = [y0 + i * step for i in range(len(stages))]
    d = ImageDraw.Draw(L)
    prog = ease_out((t - 0.6) / 3.0)
    if prog > 0:
        d.rounded_rectangle((x - 6, ys[0], x + 6, ys[0] + int((ys[-1] - ys[0]) * prog)),
                            radius=6, fill=GOLD + (255,))
    for i, (emo, label) in enumerate(stages):
        p = appear(t, 0.6 + i * 0.65, 0.6)
        if p <= 0:
            continue
        r = int(75 * ease_back(p))
        d.ellipse((x - r, ys[i] - r, x + r, ys[i] + r), fill=(255, 255, 255, int(255 * p)),
                  outline=GOLD + (255,), width=6)
        put_emoji(L, emo, (x, ys[i]), 80, p)
        put_text(L, (x + 130, ys[i]), label, font(SANS_B, 54), WHITE, p, anchor="lm",
                 dy=0)


def s_care(L, t):
    heading(L, t, "Support for busy families")
    h_card(L, t, 640, "\U0001F558", "After School Care", "Safe, fun care when the bell rings", 0.8, 320)
    h_card(L, t, 1040, "☀️", "Vacation Care", "Activities through the school holidays", 1.6, 320)


def s_community(L, t):
    heading(L, t, "A close-knit community")
    faces = ["\U0001F467\U0001F3FD", "\U0001F466\U0001F3FB", "\U0001F467\U0001F3FF",
             "\U0001F466\U0001F3FE", "\U0001F467\U0001F3FC"]
    pos = [(CX - 300, 720), (CX, 720), (CX + 300, 720), (CX - 150, 940), (CX + 150, 940)]
    for i, (f, xy) in enumerate(zip(faces, pos)):
        put_emoji(L, f, xy, 190, appear(t, 0.7 + i * 0.25, 0.6))
    para(L, t, "Around 250 students, so every child is known by name and families "
               "feel part of the school family.", 1160, 2.2)


def s_cta(L, t):
    put_emoji(L, "\U0001F4AB", (CX, 470), 200, appear(t, 0.1, 0.8))
    p = appear(t, 0.4, 0.8)
    put_text(L, (CX, 700), "Come and see", font(SERIF_B, 100), WHITE, p, dy=(1 - p) * 40)
    put_text(L, (CX, 820), "for yourself", font(SERIF_B, 100), WHITE, p, dy=(1 - p) * 40)
    p = appear(t, 1.0, 0.8)
    put_text(L, (CX, 960), "Book a school tour today", font(SANS_B, 60), GOLD, p)
    lines = ["Holy Family Catholic Primary School", "Calytrix Road, Karama NT 0812",
             "(08) 8927 6188", "admin.holyfamily@nt.catholic.edu.au"]
    for i, ln in enumerate(lines):
        p = appear(t, 1.6 + i * 0.35, 0.6)
        put_text(L, (CX, 1110 + i * 72), ln, font(SANS, 46), SOFT, p, dy=(1 - p) * 30)


R.SCENES = [(dur, cap, fn) for (dur, cap, _), fn in zip(R.SCENES, [
    s_title, s_history, s_values, s_faith, s_early, s_journey, s_care, s_community, s_cta])]


def footer(L, t_global, caption, cap_alpha):
    d = ImageDraw.Draw(L)
    if cap_alpha > 0:
        f = font(SANS_B, 44)
        lines = wrap(caption, f, W - 160, _measure)
        top = H - 300 - (len(lines) - 1) * 58
        tw = max(d.textlength(ln, font=f) for ln in lines)
        d.rounded_rectangle((CX - tw / 2 - 34, top - 44, CX + tw / 2 + 34, top + (len(lines) - 1) * 58 + 44),
                            radius=24, fill=(0, 0, 0, int(150 * cap_alpha)))
        for i, ln in enumerate(lines):
            put_text(L, (CX, top + i * 58), ln, f, WHITE, cap_alpha)
    put_text(L, (CX, H - 110), "Holy Family Catholic Primary School · Karama NT",
             font(SANS, 32), SOFT, 0.8)
    d.rectangle((0, H - 10, int(W * t_global / R.TOTAL), H), fill=GOLD + (255,))


R.footer = footer

if __name__ == "__main__":
    R.render()
