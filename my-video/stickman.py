"""Stick-figure explainer (9:16) for Holy Family Catholic Primary School, Karama.

Usage: python3 stickman.py  ->  writes holy-family-stickman-9x16.mp4
Story: a morning welcome, then one short scene each for Courage, Respect and
Mercy, then a cheering finale. Frames are drawn at 2x and downscaled for
smooth (anti-aliased) lines.
"""
import math
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont

W, H, FPS, S = 1080, 1920, 30, 2  # S = supersample factor
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "holy-family-stickman-9x16.mp4")

FD = "/usr/share/fonts/truetype"
SERIF_B = f"{FD}/dejavu/DejaVuSerif-Bold.ttf"
SANS = f"{FD}/liberation/LiberationSans-Regular.ttf"
SANS_B = f"{FD}/liberation/LiberationSans-Bold.ttf"
EMOJI = f"{FD}/noto/NotoColorEmoji.ttf"

PAPER = (250, 247, 240)
INK = (30, 30, 36)
GREY = (120, 120, 130)
GOLD = (236, 176, 40)
NAVY = (22, 52, 104)
BLUE = (70, 140, 220)
RED = (220, 70, 70)
GROUND = 1420

_fonts = {}


def font(path, size):
    k = (path, int(size))
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(path, int(size))
    return _fonts[k]


_emo = {}


def emoji(ch, size):
    if ch not in _emo:
        im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((80, 80), ch, font=ImageFont.truetype(EMOJI, 109),
                                embedded_color=True, anchor="mm")
        _emo[ch] = im.crop(im.getbbox())
    b = _emo[ch]
    k = size * S / max(b.size)
    return b.resize((max(1, int(b.width * k)), max(1, int(b.height * k))), Image.LANCZOS)


# ---------- timing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def seg(t, a, b):
    return clamp((t - a) / (b - a))


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def back(x):
    x = clamp(x)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, k):
    return a + (b - a) * k


def within(t, a, b):
    return a <= t < b


# ---------- drawing primitives (coords in 1x units) ----------
def P(x, y):
    return (x * S, y * S)


def line(d, a, b, w, col=INK):
    d.line([P(*a), P(*b)], fill=col, width=int(w * S))
    r = w * S / 2
    for x, y in (a, b):
        d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=col)


def text(d, xy, s, size, col=INK, f=SANS_B, anchor="mm"):
    if size < 2:
        return
    d.text(P(*xy), s, font=font(f, size * S), fill=col, anchor=anchor)


def paste_emoji(img, ch, xy, size):
    if size <= 2:
        return
    e = emoji(ch, size)
    img.paste(e, (int(xy[0] * S - e.width / 2), int(xy[1] * S - e.height / 2)), e)


def bubble(d, xy, s, k, tail, size=44):
    """Speech bubble centred at xy that pops in with progress k."""
    if k <= 0:
        return
    sc = back(k)
    size *= sc
    if size < 2:
        return
    f = font(SANS_B, size * S)
    tw = d.textlength(s, font=f) / S
    pw, ph = tw / 2 + 26 * sc, size * 0.5 + 22 * sc
    x, y = xy
    d.polygon([P(x - 18 * sc, y + ph - 4), P(x + 18 * sc, y + ph - 4), P(*tail)],
              fill=(255, 255, 255), outline=INK, width=int(4 * S))
    d.rounded_rectangle((*P(x - pw, y - ph), *P(x + pw, y + ph)), radius=int(28 * S * sc),
                        fill=(255, 255, 255), outline=INK, width=int(4 * S))
    # cover the tail's top edge so tail and bubble join cleanly
    d.rectangle((*P(x - 15 * sc, y + ph - 8), *P(x + 15 * sc, y + ph - 1)), fill=(255, 255, 255))
    d.text(P(x, y), s, font=f, fill=INK, anchor="mm")


def say(d, who, s, k, dx=0, size=44):
    hx, hy = who["head"]
    top = hy - who["r"] - 18
    bubble(d, (hx + dx, top - 95), s, k, (hx + dx * 0.25, top), size)


# ---------- the stick figure ----------
TH, SH, TORSO, UA, FA, HEAD, NECK = 105, 100, 160, 90, 85, 40, 10


def pose(**kw):
    p = dict(lean=0.0, aF=(0.15, 0.05), aB=(-0.15, -0.05), lF=(0.08, 0.08), lB=(-0.08, -0.08),
             mood="smile")
    p.update(kw)
    return p


def blend(p1, p2, k):
    out = {}
    for key in p1:
        a, b = p1[key], p2[key]
        if isinstance(a, tuple):
            out[key] = tuple(lerp(x, y, k) for x, y in zip(a, b))
        elif isinstance(a, str):
            out[key] = b if k > 0.5 else a
        else:
            out[key] = lerp(a, b, k)
    return out


STAND = pose()
CHEER = pose(aF=(2.6, 2.9), aB=(-2.6, -2.9))
SIT = pose(lean=-0.15, lF=(1.45, 1.6), lB=(1.35, 1.5), aF=(-0.5, -0.4), aB=(-0.7, -0.5), mood="ouch")


def walk(phase, run=False):
    amp = 0.6 if run else 0.4
    s = math.sin(phase)
    th1, th2 = amp * s, -amp * s
    sh1 = th1 - (0.9 if run else 0.5) * max(0.0, -math.sin(phase + 0.9))
    sh2 = th2 - (0.9 if run else 0.5) * max(0.0, math.sin(phase + 0.9))
    arm = (0.9 if run else 0.45) * s
    return pose(lean=0.18 if run else 0.04, lF=(th1, sh1), lB=(th2, sh2),
                aF=(-arm, -arm + (1.2 if run else 0.35)), aB=(arm, arm + (1.2 if run else 0.35)))


def wave(t):
    return pose(aF=(2.5, 2.9 + 0.45 * math.sin(t * 12)))


def figure(d, x, facing, s, p, jump=0.0, pack=None, lanyard=False, ground=GROUND):
    def v(a, L):
        return (math.sin(a) * facing * L * s, math.cos(a) * L * s)

    def add(a, b):
        return (a[0] + b[0], a[1] + b[1])

    ext = max(TH * math.cos(p["lF"][0]) + SH * math.cos(p["lF"][1]),
              TH * math.cos(p["lB"][0]) + SH * math.cos(p["lB"][1]), 12)
    hip = (x, ground - ext * s - 6 * s - jump)
    lean = p["lean"]
    up = (math.sin(lean) * facing, -math.cos(lean))
    sho = (hip[0] + up[0] * TORSO * s, hip[1] + up[1] * TORSO * s)
    head = (sho[0] + up[0] * (NECK + HEAD) * s, sho[1] + up[1] * (NECK + HEAD) * s)
    lw = 11 * s

    def limb(root, ang, l1, l2):
        j = add(root, v(ang[0], l1))
        e = add(j, v(ang[1], l2))
        line(d, root, j, lw)
        line(d, j, e, lw)
        return e

    arm = (sho[0] - up[0] * 14 * s, sho[1] - up[1] * 14 * s)
    limb(arm, p["aB"], UA, FA)
    limb(hip, p["lB"], TH, SH)
    if pack:
        mid = ((hip[0] + sho[0]) / 2 - facing * 30 * s, (hip[1] + sho[1]) / 2 - 8 * s)
        d.rounded_rectangle((*P(mid[0] - 26 * s, mid[1] - 42 * s), *P(mid[0] + 26 * s, mid[1] + 42 * s)),
                            radius=int(12 * s * S), fill=pack, outline=INK, width=int(5 * s * S))
    line(d, hip, sho, lw)
    if lanyard:
        c = (sho[0] + facing * 2 * s, sho[1] + 50 * s)
        d.rectangle((*P(c[0] - 14 * s, c[1]), *P(c[0] + 14 * s, c[1] + 20 * s)), fill=GOLD,
                    outline=INK, width=int(3 * S))
    limb(hip, p["lF"], TH, SH)
    r = HEAD * s
    d.ellipse((*P(head[0] - r, head[1] - r), *P(head[0] + r, head[1] + r)), fill=(255, 255, 255),
              outline=INK, width=int(lw * S))
    # face looks in the facing direction
    for ex in (6, 24):
        cx, cy = head[0] + facing * ex * s, head[1] - 8 * s
        d.ellipse((*P(cx - 4.5 * s, cy - 4.5 * s), *P(cx + 4.5 * s, cy + 4.5 * s)), fill=INK)
    mx, my = head[0] + facing * 15 * s, head[1] + 10 * s
    box = (*P(mx - 14 * s, my - 10 * s), *P(mx + 14 * s, my + 10 * s))
    if p["mood"] == "ouch":
        d.arc((box[0], box[1] + 14 * s * S, box[2], box[3] + 14 * s * S), 200, 340, fill=INK,
              width=int(4 * s * S))
    else:
        d.arc(box, 20, 160, fill=INK, width=int(4 * s * S))
    limb(arm, p["aF"], UA, FA)
    return {"hip": hip, "sho": sho, "head": head, "r": r}


# ---------- people ----------
TEACHER = dict(s=1.35, lanyard=True)
KID1 = dict(s=0.95, pack=GOLD)
KID2 = dict(s=0.95, pack=BLUE)


# ---------- scenery ----------
def ground(d):
    d.line([P(0, GROUND), P(W, GROUND)], fill=INK, width=int(6 * S))
    for gx in range(40, W, 140):  # little grass tufts
        for dx, h in ((-10, 18), (0, 26), (10, 18)):
            line(d, (gx + dx * 0.4, GROUND), (gx + dx, GROUND - h), 4, (90, 160, 90))


def school(d, x0=600, x1=1040):
    top = GROUND - 420
    d.rectangle((*P(x0, top), *P(x1, GROUND)), fill=(255, 255, 255), outline=INK, width=int(6 * S))
    cx = (x0 + x1) / 2
    d.polygon([P(x0 - 30, top), P(x1 + 30, top), P(cx, top - 170)], fill=(255, 238, 200),
              outline=INK, width=int(6 * S))
    line(d, (cx, top - 170), (cx, top - 260), 8)  # cross
    line(d, (cx - 30, top - 230), (cx + 30, top - 230), 8)
    d.rectangle((*P(x0 + 40, top + 40), *P(x1 - 40, top + 110)), fill=NAVY)
    text(d, (cx, top + 75), "HOLY FAMILY", 44, (255, 255, 255))
    for wx in (x0 + 60, x1 - 150):
        d.rectangle((*P(wx, top + 160), *P(wx + 90, top + 250)), fill=(200, 225, 250), outline=INK,
                    width=int(5 * S))
    d.rounded_rectangle((*P(cx - 60, GROUND - 190), *P(cx + 60, GROUND)), radius=int(20 * S),
                        fill=(170, 110, 60), outline=INK, width=int(5 * S))


def title(d, img, word, t, ch=None, col=NAVY, size=96):
    k = back(seg(t, 0.15, 0.75))
    if k <= 0:
        return
    text(d, (W / 2, 300), word, size * k, col, SERIF_B)
    if ch:
        paste_emoji(img, ch, (W / 2, 160), 110 * k)


def caption(d, s, t):
    if t < 0.6:
        return
    f = font(SANS, 46 * S)
    words, lines, cur = s.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if d.textlength(trial, font=f) / S > W - 140:
            lines.append(cur)
            cur = w_
        else:
            cur = trial
    lines.append(cur)
    for i, ln in enumerate(lines):
        text(d, (W / 2, 1560 + i * 64), ln, 46, INK, SANS)


# ---------- scenes: fn(img, d, t) ----------
def sc_welcome(img, d, t):
    title(d, img, "Good morning!", t, "☀️", GOLD)
    school(d)
    ground(d)
    # kid walks in from the left and stops
    k = smooth(seg(t, 0.3, 3.6))
    kx = lerp(-120, 230, k)
    kp = walk(kx / 38) if 0 < k < 1 else STAND
    if t > 4.0:
        kp = blend(STAND, wave(t), smooth(seg(t, 4.0, 4.3)) * (1 - smooth(seg(t, 6.6, 6.9))))
    kid = figure(d, kx, 1, p=kp, **KID1)
    tp = STAND
    if t > 2.6:
        tp = blend(STAND, wave(t), smooth(seg(t, 2.6, 2.9)) * (1 - smooth(seg(t, 5.4, 5.7))))
    tch = figure(d, 470, -1, p=tp, **TEACHER)
    if within(t, 2.8, 6.2):
        say(d, tch, "Good morning!", seg(t, 2.8, 3.2), 60)
    if within(t, 4.3, 7.2):
        say(d, kid, "Hi!", seg(t, 4.3, 4.7), -40)
    caption(d, "Every day at Holy Family starts with a warm welcome.", t)


def sc_courage(img, d, t):
    title(d, img, "COURAGE", t, "\U0001F981")
    ground(d)
    # easel whiteboard
    bx0, bx1, by0, by1 = 70, 470, 830, 1110
    line(d, (bx0 + 60, by1), (bx0 + 20, GROUND), 8, GREY)
    line(d, (bx1 - 60, by1), (bx1 - 20, GROUND), 8, GREY)
    d.rectangle((*P(bx0, by0), *P(bx1, by1)), fill=(255, 255, 255), outline=INK, width=int(7 * S))
    text(d, ((bx0 + bx1) / 2 - 50, (by0 + by1) / 2), "7 × 8 =", 64, INK)
    if t > 5.2:
        text(d, (bx1 - 70, (by0 + by1) / 2), "56", 72 * back(seg(t, 5.2, 5.6)), GOLD)
    else:
        text(d, (bx1 - 70, (by0 + by1) / 2), "?", 72, RED)
    # kid: nervous -> listens -> writes -> celebrates
    kx, facing, kp, jump = 560, -1, STAND, 0
    if t < 2.2:
        kx += 4 * math.sin(t * 45) * seg(t, 0.5, 0.8)
        kp = pose(aF=(0.4, 0.3), aB=(-0.1, 0.2), mood="ouch")
    elif t < 4.2:
        facing = 1
    elif t < 5.6:
        kp = pose(lean=0.1, aF=(1.9, 2.2 + 0.3 * math.sin(t * 22)))
    else:
        facing = 1
        kp = CHEER
        jump = 70 * abs(math.sin((t - 5.6) * 5))
    kid = figure(d, kx, facing, p=kp, jump=jump, **KID1)
    tp = STAND
    if within(t, 2.2, 4.8):
        tp = blend(STAND, pose(aF=(1.4, 2.7)), smooth(seg(t, 2.2, 2.5)) * (1 - smooth(seg(t, 4.5, 4.8))))
    if t > 5.6:
        tp = blend(STAND, CHEER, smooth(seg(t, 5.6, 5.9)))
    tch = figure(d, 880, -1, p=tp, **TEACHER)
    if within(t, 0.6, 2.4):
        say(d, kid, "?", seg(t, 0.6, 0.9), 0, size=60)
    if within(t, 2.4, 4.6):
        say(d, tch, "You can do it!", seg(t, 2.4, 2.8), -120)
    if t > 5.8:
        say(d, kid, "I did it!", seg(t, 5.8, 6.2), -60)
    caption(d, "Courage means trying something new, even when it feels hard.", t)


def ball_pos(t):
    """Ball thrown back and forth; returns (x, y, thrower) or None."""
    throws = [(0.5, 330, 760, 1), (1.9, 760, 330, 2), (3.3, 330, 760, 1)]
    for start, x0, x1, who in throws:
        if within(t, start, start + 1.0):
            k = (t - start) / 1.0
            y = (GROUND - 360) - 260 * 4 * k * (1 - k)
            return lerp(x0, x1, k), y, who
    return None


def sc_respect(img, d, t):
    title(d, img, "RESPECT", t, "\U0001F91D")
    ground(d)
    bp = ball_pos(t)
    k = smooth(seg(t, 4.6, 5.6))
    x1, x2 = lerp(260, 465, k), lerp(830, 615, k)
    throw = pose(aF=(2.3, 2.6))
    catch = pose(aF=(1.4, 1.6), aB=(1.2, 1.5))
    p1 = p2 = STAND
    if bp:
        p1, p2 = (throw, catch) if bp[2] == 1 else (catch, throw)
    if 0 < k < 1:
        p1, p2 = walk(x1 / 36), walk(-x2 / 36)
    if t >= 5.6:
        hf = smooth(seg(t, 5.6, 5.9))
        p1 = p2 = blend(STAND, pose(aF=(2.4, 2.75)), hf)
    a = figure(d, x1, 1, p=p1, **KID1)
    b = figure(d, x2, -1, p=p2, **KID2)
    if bp:
        x, y, _ = bp
        d.ellipse((*P(x - 28, y - 28), *P(x + 28, y + 28)), fill=RED, outline=INK, width=int(5 * S))
        line(d, (x - 26, y), (x + 26, y), 3, (255, 255, 255))
    elif t < 4.6:  # ball resting in a hand between throws
        hx = 330 if (1.5 <= t < 1.9 or t >= 4.3) else 760
        if t < 0.5:
            hx = 330
        d.ellipse((*P(hx - 28, GROUND - 388), *P(hx + 28, GROUND - 332)), fill=RED, outline=INK,
                  width=int(5 * S))
    if within(t, 1.9, 3.3):
        say(d, b, "Your turn!", seg(t, 1.9, 2.3), -40)
    if within(t, 3.3, 4.6):
        say(d, a, "Thanks!", seg(t, 3.3, 3.7), 40)
    if t > 5.85:  # high-five sparkle
        kk = back(seg(t, 5.85, 6.3))
        cx, cy = 540, a["sho"][1] - 175
        for a in range(0, 360, 45):
            r0, r1 = 30 * kk, 75 * kk
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            line(d, (cx + ca * r0, cy + sa * r0), (cx + ca * r1, cy + sa * r1), 7, GOLD)
    caption(d, "Respect means taking turns and valuing everyone.", t)


def sc_mercy(img, d, t):
    title(d, img, "MERCY", t, "❤️", RED)
    ground(d)
    # kid2 runs, trips, sits, is helped up
    k = seg(t, 0.2, 1.7)
    x2 = lerp(-100, 640, k)
    f2 = 1
    if t < 1.7:
        p2 = walk(x2 / 28, run=True)
    elif t < 2.0:
        p2 = blend(walk(640 / 28, run=True), SIT, smooth(seg(t, 1.7, 2.0)))
    elif t < 5.0:
        p2, f2 = SIT, -1
    else:
        p2, f2 = blend(SIT, STAND, smooth(seg(t, 5.0, 5.7))), -1
        if t > 5.4:
            p2 = dict(p2, mood="smile")
    if 4.2 < t < 5.6:
        p2 = dict(p2, aF=(1.4, 1.5))
    # kid1 walks over and offers a hand
    k1 = smooth(seg(t, 2.2, 3.9))
    x1 = lerp(-120, 455, k1)
    p1 = walk(x1 / 38) if 0 < k1 < 1 else STAND
    if t > 3.9:
        p1 = blend(STAND, pose(lean=0.3, aF=(1.2, 1.5)), smooth(seg(t, 3.9, 4.3)) *
                   (1 - smooth(seg(t, 5.5, 5.9))))
    a = figure(d, x1, 1, p=p1, **KID1)
    b = figure(d, x2, f2, p=p2, **KID2)
    if within(t, 1.9, 3.8):
        say(d, b, "Ouch!", seg(t, 1.9, 2.2), 60)
        for i in range(3):  # little dust puffs
            r = 14 + 22 * seg(t, 1.9, 2.6)
            dx = 560 + i * 90
            d.ellipse((*P(dx - r, GROUND - r), *P(dx + r, GROUND + 4)), outline=GREY, width=int(4 * S))
    if within(t, 3.9, 5.6):
        say(d, a, "Are you OK?", seg(t, 3.9, 4.3), -30)
    if t > 5.9:
        say(d, b, "Thank you!", seg(t, 5.9, 6.3), 120)
        paste_emoji(img, "❤️", (548, 900 - 40 * seg(t, 5.9, 7.2)), 90 * back(seg(t, 5.9, 6.3)))
    caption(d, "Mercy means kindness, forgiveness and caring for one another.", t)


CONFETTI = [((i * 137) % W, (i * 271) % 900, (GOLD, BLUE, RED, NAVY)[i % 4], 0.7 + (i % 5) * 0.15)
            for i in range(60)]


def sc_finale(img, d, t):
    for x, y0, col, sp in CONFETTI:
        y = (y0 + t * 260 * sp) % 880 + 520
        xx = x + 20 * math.sin(t * 3 + y0)
        d.rectangle((*P(xx - 8, y - 14), *P(xx + 8, y + 14)), fill=col)
    k = back(seg(t, 0.2, 0.8))
    text(d, (W / 2, 250), "Holy Family", 104 * k, NAVY, SERIF_B)
    text(d, (W / 2, 370), "Catholic Primary School", 60 * k, GOLD, SERIF_B)
    text(d, (W / 2, 450), "Karama NT", 48 * k, GREY, SANS_B)
    ground(d)
    for x, who, ph in ((250, KID1, 0.0), (540, TEACHER, 0.6), (830, KID2, 1.2)):
        j = 60 * max(0.0, math.sin(t * 5 + ph)) if t > 0.6 else 0
        figure(d, x, 1 if x < 540 else -1, p=CHEER if t > 0.6 else STAND, jump=j, **who)
    if t > 1.2:
        kk = back(seg(t, 1.2, 1.7))
        text(d, (W / 2, 1550), "Courage · Respect · Mercy", 56 * kk, NAVY, SERIF_B)
    if t > 2.0:
        kk = back(seg(t, 2.0, 2.5))
        d.rounded_rectangle((*P(W / 2 - 330 * kk, 1640), *P(W / 2 + 330 * kk, 1740)),
                            radius=int(50 * S), fill=GOLD)
        text(d, (W / 2, 1690), "Book a tour today!", 52 * kk, INK)


SCENES = [(7.5, sc_welcome), (7.5, sc_courage), (7.0, sc_respect), (7.8, sc_mercy), (7.0, sc_finale)]
TOTAL = sum(s[0] for s in SCENES)
FADE = 0.35


def frame(scene_fn, t, dur, tg):
    img = Image.new("RGB", (W * S, H * S), PAPER)
    d = ImageDraw.Draw(img)
    scene_fn(img, d, t)
    out = img.resize((W, H), Image.LANCZOS)
    k = min(clamp(t / FADE), clamp((dur - t) / FADE))
    if k < 1:
        out = Image.blend(Image.new("RGB", (W, H), PAPER), out, k)
    od = ImageDraw.Draw(out)
    od.text((W / 2, H - 70), "Holy Family Catholic Primary School · Karama NT",
            font=font(SANS, 30), fill=GREY, anchor="mm")
    od.rectangle((0, H - 10, int(W * (tg + t) / TOTAL), H), fill=GOLD)
    return out


def render():
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
           "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    tg = 0.0
    for dur, fn in SCENES:
        for i in range(int(round(dur * FPS))):
            proc.stdin.write(frame(fn, i / FPS, dur, tg).tobytes())
        tg += dur
    proc.stdin.close()
    proc.wait()
    print(f"Wrote {OUT} ({TOTAL:.1f}s)")


if __name__ == "__main__":
    render()
