#!/usr/bin/env python3
"""Quotable Nights Ep.01 — clip + chat-bubble story (POV) + three.js kawaii layers + free TTS voice.
usage: render3.py <clip.mp4> <out.mp4> <three_dir> <vo_dir> [--preview t1,t2,...]
"""
import sys, subprocess, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT, THREE_DIR, VO_DIR = sys.argv[1:5]
PREVIEW = [float(x) for x in sys.argv[6].split(",")] if len(sys.argv) > 6 else None
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")

W, H, FPS = 1080, 1920, 30
INTRO, CLIP = 4.5, 61.4
OUTRO_T = INTRO + CLIP
DUR = OUTRO_T + 6.4
N = int(DUR * FPS)

# ---- palette ----
BG_TOP, BG_BOT = (40, 30, 78), (78, 44, 100)
PINK = (255, 182, 213); PINK_D = (255, 127, 174)
LILAC = (217, 194, 255); MINT = (184, 242, 224); BUTTER = (255, 240, 168)
PLUM = (58, 35, 80); WHITE = (255, 255, 255); OFF = (250, 248, 255)
TICK_GREY = (150, 140, 170); TICK_BLUE = (56, 169, 255)

def vf(name, var, size):
    f = ImageFont.truetype(os.path.join(FONT_DIR, name), int(size))
    try: f.set_variation_by_name(var)
    except Exception: pass
    return f
_fc = {}
def F(kind, size):
    k = (kind, int(size))
    if k not in _fc:
        _fc[k] = {"title": lambda s: vf("Fredoka.ttf", "Bold", s),
                  "med": lambda s: vf("Fredoka.ttf", "Medium", s),
                  "semi": lambda s: vf("Fredoka.ttf", "SemiBold", s),
                  "body": lambda s: vf("Nunito.ttf", "SemiBold", s),
                  "bodyb": lambda s: vf("Nunito.ttf", "ExtraBold", s),
                  "small": lambda s: vf("Nunito.ttf", "Bold", s)}[kind](size)
    return _fc[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo3(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def eoback(x, s=1.8): x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1
def lerp(a, b, k): return a + (b - a) * k

def with_alpha(img, a):
    if a >= 0.999: return img
    img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * a))); return img
def put(c, im, cx, cy, a=1.0, scale=1.0):
    if a <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    c.alpha_composite(with_alpha(im, a), (int(cx - im.width / 2), int(cy - im.height / 2)))

_tc = {}
def T(txt, fnt, fill, shadow=True):
    key = (txt, id(fnt), fill, shadow)
    if key in _tc: return _tc[key]
    asc, desc = fnt.getmetrics(); pad = 20
    img = Image.new("RGBA", (int(fnt.getlength(txt)) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img); d.text((pad, pad), txt, font=fnt, fill=fill)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad, pad + 3), txt, font=fnt, fill=(30, 10, 50, 150))
        img = Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)), img)
    _tc[key] = img; return img

# ---------- static layers ----------
BG = np.zeros((H, W, 3), np.float32)
k = np.linspace(0, 1, H)[:, None]
for i in range(3): BG[..., i] = (BG_TOP[i] * (1 - k) + BG_BOT[i] * k) / 255

CW, CH = 600, 1067
CX0, CY0 = (W - CW) // 2, 245
CRAD, CB = 40, 12
CARD = Image.new("RGBA", (CW + 2 * CB + 100, CH + 2 * CB + 100), (0, 0, 0, 0))
g = Image.new("RGBA", CARD.size, (0, 0, 0, 0))
ImageDraw.Draw(g).rounded_rectangle([40, 50, 60 + CW + 2 * CB, 60 + CH + 2 * CB], radius=CRAD + CB, fill=PINK_D + (150,))
CARD.alpha_composite(g.filter(ImageFilter.GaussianBlur(24)))
ImageDraw.Draw(CARD).rounded_rectangle([50, 50, 50 + CW + 2 * CB - 1, 50 + CH + 2 * CB - 1], radius=CRAD + CB, fill=OFF + (255,))
CMASK = Image.new("L", (CW, CH), 0); ImageDraw.Draw(CMASK).rounded_rectangle([0, 0, CW - 1, CH - 1], radius=CRAD, fill=255)

PX0, PY0, PX1, PY1 = 50, 1345, 1030, 1885
PANEL = Image.new("RGBA", (PX1 - PX0, PY1 - PY0), (0, 0, 0, 0))
pd = ImageDraw.Draw(PANEL)
pd.rounded_rectangle([0, 0, PANEL.width - 1, PANEL.height - 1], radius=44, fill=(46, 30, 82, 225), outline=(255, 255, 255, 90), width=3)
pd.line([(30, 92), (PANEL.width - 30, 92)], fill=(255, 255, 255, 50), width=2)
CHAT_TOP, CHAT_BOT = PY0 + 100, PY0 + 440  # visible bubble region (screen coords)
INPUT_Y = PY0 + 478

# ---------- story timeline (clip-relative seconds) ----------
MSGS = [  # (time, side, text, clock)
    (1.0, "me", "we used to talk till 3am", "1:02 AM"),
    (4.2, "them", "haha yes", "1:04 AM"),
    (8.0, "them", "ok", "9:15 PM"),
    (11.5, "me", "are we okay?", "9:16 PM"),
    (18.0, "them", "sure", "11:58 PM"),
    (24.0, "me", "i miss us.", "11:41 PM"),
]
TYPING_THEM = [(14.0, 17.6), (57.0, 59.6)]
DELIVERED_AT, SEEN_AT, NOREPLY_AT = 31.5, 44.5, 52.0
DRAFTS = [  # (start typing, end typing, start delete, end delete, text)
    (35.5, 39.6, 40.1, 41.4, "i'm sorry if i did something wrong, i just"),
    (42.0, 42.7, 43.4, 43.9, "hey"),
]

def tick_state(c, idx):
    """old messages read (blue), last message: single -> double -> blue."""
    if idx < 4: return 2, True
    if idx == 5:
        if c >= SEEN_AT: return 2, True
        return (2 if c >= DELIVERED_AT else 1), False
    return 2, True

def draw_ticks(d, x, y, n, blue, scale=1.0):
    col = (TICK_BLUE if blue else TICK_GREY) + (255,)
    for i in range(n):
        ox = x + i * 11 * scale
        d.line([(ox, y + 8 * scale), (ox + 6 * scale, y + 14 * scale), (ox + 17 * scale, y)], fill=col, width=int(3 * scale), joint="curve")

_bc = {}
def bubble(side, text, clock, n_ticks=0, blue=False):
    key = (side, text, clock, n_ticks, blue)
    if key in _bc: return _bc[key]
    f, fs = F("body", 38), F("small", 22)
    tw = f.getlength(text); meta = clock
    mw = fs.getlength(meta) + (34 if side == "me" else 0)
    w = int(max(tw, 0) + 44 + mw + 16); h = 86
    img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([10, 14, w + 10, h + 12], radius=32, fill=(20, 5, 40, 90))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    fill = PINK if side == "me" else OFF
    d.rounded_rectangle([10, 10, w + 10, h + 10], radius=32, fill=fill + (255,))
    # little tail
    if side == "me": d.polygon([(w - 6, h - 4), (w + 18, h + 14), (w - 30, h + 4)], fill=fill + (255,))
    else: d.polygon([(26, h - 4), (2, h + 14), (50, h + 4)], fill=fill + (255,))
    d.text((32, 26), text, font=f, fill=PLUM)
    mx = 32 + tw + 16
    d.text((mx, 46), meta, font=fs, fill=PLUM + (150,))
    if side == "me" and n_ticks: draw_ticks(d, mx + fs.getlength(meta) + 8, 52, n_ticks, blue, 1.0)
    _bc[key] = img; return img

def typing_bubble(t):
    img = Image.new("RGBA", (150, 106), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 10, 140, 96], radius=32, fill=OFF + (255,))
    d.polygon([(26, 92), (2, 110), (50, 100)], fill=OFF + (255,))
    for i in range(3):
        y = 53 - 9 * max(0, math.sin(t * 9 - i * 0.9))
        d.ellipse([42 + i * 26 - 8, y - 8, 42 + i * 26 + 8, y + 8], fill=LILAC + (255,))
    return img

def pill(text, fnt, fg, bg, padx=28, h=60, outline=None):
    tw = fnt.getlength(text)
    img = Image.new("RGBA", (int(tw + 2 * padx), h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, img.width - 1, h - 1], radius=h // 2, fill=bg, outline=outline, width=3 if outline else 0)
    asc, desc = fnt.getmetrics()
    d.text((padx, (h - asc - desc) // 2 + 1), text, font=fnt, fill=fg); return img

def draw_chat(c, t, ca, slide):
    """c = clip time. ca = alpha, slide = vertical offset."""
    layer = PANEL.copy()
    d = ImageDraw.Draw(layer)
    # header (right of the mascot)
    hx = 300
    d.ellipse([hx, 22, hx + 52, 74], fill=LILAC + (255,))
    # tiny heart on avatar
    d.ellipse([hx + 14, 36, hx + 28, 50], fill=PINK_D + (255,)); d.ellipse([hx + 24, 36, hx + 38, 50], fill=PINK_D + (255,))
    d.polygon([(hx + 15, 46), (hx + 37, 46), (hx + 26, 60)], fill=PINK_D + (255,))
    d.text((hx + 68, 18), "them", font=F("semi", 34), fill=WHITE)
    online = c < SEEN_AT
    if online:
        d.ellipse([hx + 70, 62, hx + 82, 74], fill=(120, 230, 160, 255))
        d.text((hx + 90, 56), "online", font=F("small", 22), fill=(255, 255, 255, 190))
    else:
        d.text((hx + 70, 56), "last seen 11:47 PM", font=F("small", 22), fill=(255, 255, 255, 190))
    ep = pill("EP.01", F("semi", 24), PLUM, BUTTER + (255,), 18, 44)
    layer.alpha_composite(ep, (layer.width - ep.width - 30, 26))

    # ---- bubbles: stack from bottom upward ----
    items = []  # (img, side, appear_time)
    for i, (mt, side, txt, clock) in enumerate(MSGS):
        if c < mt: continue
        nt, blue = tick_state(c, i) if side == "me" else (0, False)
        items.append((bubble(side, txt, clock, nt, blue), side, mt, i))
    for (a, b) in TYPING_THEM:
        if a <= c < b: items.append((typing_bubble(t), "them", a, -1))
    extras = []
    if c >= SEEN_AT:
        extras.append((pill("Seen 11:47 PM", F("small", 22), (255, 255, 255, 230), (255, 255, 255, 40), 18, 40), "me", SEEN_AT))
    if c >= NOREPLY_AT:
        extras.append((pill("no reply.", F("semi", 30), PLUM, BUTTER + (255,), 30, 56), "center", NOREPLY_AT))
    seq = items + [(e[0], e[1], e[2], -2) for e in extras]
    seq.sort(key=lambda x: x[2])
    region = Image.new("RGBA", (layer.width, CHAT_BOT - CHAT_TOP), (0, 0, 0, 0))
    y = region.height
    for img, side, at, idx in reversed(seq):
        p = (c - at) / 0.35
        hgt = (img.height + 4) * eo3(p * 1.4)
        y -= hgt
        if y + img.height < -10: break
        s = eoback(p)
        if side == "me": x = layer.width - img.width - 28
        elif side == "them": x = 28
        else: x = (layer.width - img.width) // 2
        if s < 0.999:
            sc = max(0.01, s)
            im2 = img.resize((max(1, int(img.width * sc)), max(1, int(img.height * sc))), Image.BICUBIC)
            ax = x + (img.width - im2.width if side == "me" else 0 if side == "them" else (img.width - im2.width) // 2)
            region.alpha_composite(with_alpha(im2, clamp(p * 3)), (int(ax), int(y + img.height - im2.height)))
        else:
            region.alpha_composite(img, (int(x), int(y)))
    # bump on delivered / seen ticks
    layer.alpha_composite(region, (0, CHAT_TOP - PY0))

    # ---- input bar ----
    iy = INPUT_Y - PY0
    d.rounded_rectangle([28, iy - 34, layer.width - 110, iy + 34], radius=34, fill=(255, 255, 255, 235))
    d.ellipse([layer.width - 96, iy - 34, layer.width - 28, iy + 34], fill=PINK_D + (255,))
    ax0 = layer.width - 62
    d.polygon([(ax0 - 14, iy - 14), (ax0 + 16, iy), (ax0 - 14, iy + 14), (ax0 - 8, iy)], fill=WHITE + (255,))
    draft = ""
    for a, b, dl0, dl1, txt in DRAFTS:
        if a <= c < b: draft = txt[:int(len(txt) * (c - a) / (b - a))]
        elif b <= c < dl0: draft = txt
        elif dl0 <= c < dl1: draft = txt[:int(len(txt) * (1 - (c - dl0) / (dl1 - dl0)))]
    fi = F("body", 32)
    if draft:
        maxw = layer.width - 200
        shown = draft
        while fi.getlength(shown) > maxw: shown = shown[1:]
        d.text((58, iy - 22), shown, font=fi, fill=PLUM)
        if (t * 2) % 1 < 0.6:
            cx = 58 + fi.getlength(shown) + 3
            d.line([(cx, iy - 18), (cx, iy + 20)], fill=PINK_D + (255,), width=3)
    else:
        d.text((58, iy - 22), "message...", font=fi, fill=(150, 140, 170))
    return with_alpha(layer, ca), slide

# ---------- three.js layers ----------
B_BYTES, F_BYTES, FG = 540 * 960 * 4, 640 * 640 * 4, 640
def three_proc(times=None):
    args = ["node", os.path.join(THREE_DIR, "driver.cjs")] + (["--range", str(N), str(FPS)] if times is None else [",".join(map(str, times))])
    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
def read_three(p):
    bg = np.frombuffer(p.stdout.read(B_BYTES), np.uint8).reshape(960, 540, 4)[::-1]
    fg = np.frombuffer(p.stdout.read(F_BYTES), np.uint8).reshape(FG, FG, 4)[::-1]
    return bg, fg

def premul_over(base, rgba, x, y):
    """composite premultiplied rgba (uint8) onto float base at x,y with clipping"""
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(base.shape[1], x + w), min(base.shape[0], y + h)
    if x1 <= x0 or y1 <= y0: return
    s = rgba[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32) / 255
    base[y0:y1, x0:x1] = s[..., :3] + base[y0:y1, x0:x1] * (1 - s[..., 3:4])

def mascot_pose(t):
    """centre (x,y) and size in px of the mascot viewport."""
    corner = (165, 1240, 600)
    big_in = (540, 1050, 1180)
    big_out = (540, 1130, 1060)
    if t < 3.9: return big_in
    if t < 4.7: k = eio((t - 3.9) / 0.8); return tuple(lerp(a, b, k) for a, b in zip(big_in, corner))
    if t < OUTRO_T + 0.2: return corner
    k = eio((t - OUTRO_T - 0.2) / 0.8); return tuple(lerp(a, b, k) for a, b in zip(corner, big_out))

def compose(vid, t, bg3, fg3):
    c = t - INTRO
    base = BG.copy()
    bgu = np.asarray(Image.fromarray(bg3, "RGBA").resize((W, H), Image.BICUBIC))
    premul_over(base, bgu, 0, 0)
    canvas = Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

    # ---- intro title ----
    if t < 4.8:
        out = eio((t - 3.8) / 0.7)
        a = clamp(t / 0.4) * (1 - out)
        p1 = eoback((t - 0.2) / 0.6)
        put(canvas, pill("EPISODE 01", F("semi", 34), PLUM, BUTTER + (255,), 30, 64), W / 2, 250, a, p1)
        for i, (w, col) in enumerate((("QUOTABLE", WHITE), ("NIGHTS", PINK))):
            p = (t - 0.35 - i * 0.25) / 0.5
            put(canvas, T(w, F("title", 150), col), W / 2, 380 + i * 150 + 40 * (1 - eo3(p)), a * clamp(p * 2), lerp(1.3, 1, eo3(p)))
        q = "Silence is also an answer."
        n = int(len(q) * clamp((t - 2.15) / 1.6))
        if n:
            put(canvas, T(q[:n], F("med", 58), WHITE), W / 2, 1640, a * (1 - eio((t - 3.7) / 0.3)))
        # underline sparkle
        if t > 3.8 - 0.1:
            pass

    # ---- header during clip ----
    ha = eo3((t - 4.1) / 0.6) * (1 - eio((t - OUTRO_T) / 0.5))
    if ha > 0:
        put(canvas, pill("QUOTABLE NIGHTS  ·  EP. 01", F("semi", 28), PLUM, BUTTER + (255,), 26, 54), W / 2, 78, ha)
        ql = T("Silence is also an ", F("med", 52), WHITE); qr = T("answer.", F("title", 54), PINK)
        tot = ql.width + qr.width - 40
        canvas.alpha_composite(with_alpha(ql, ha), (int(W / 2 - tot / 2), 140))
        canvas.alpha_composite(with_alpha(qr, ha), (int(W / 2 - tot / 2 + ql.width - 40), 138))

    # ---- video card ----
    cin = eoback((t - 4.0) / 0.6, 1.4)
    cout = eio((t - OUTRO_T) / 0.6)
    if t >= 4.0 and cout < 1 and vid is not None:
        v = Image.fromarray(vid).convert("RGBA"); v.putalpha(CMASK)
        card = CARD.copy(); card.alpha_composite(v, (50 + CB, 50 + CB))
        # "seen" moment: soft blue glow pulse on card border
        if 0 <= c - SEEN_AT < 1.2:
            k2 = math.sin((c - SEEN_AT) / 1.2 * math.pi)
            gl = Image.new("RGBA", card.size, (0, 0, 0, 0))
            ImageDraw.Draw(gl).rounded_rectangle([44, 44, card.width - 44, card.height - 44], radius=CRAD + CB + 6, outline=TICK_BLUE + (int(200 * k2),), width=10)
            card.alpha_composite(gl.filter(ImageFilter.GaussianBlur(6)))
        dy = 5 * math.sin(t * 1.2)
        s = max(0.01, cin) * (1 - 0.15 * cout)
        put(canvas, card, W / 2, CY0 - 50 - CB + card.height / 2 + dy + cout * 120, clamp((t - 4.0) / 0.25) * (1 - cout), s)

    # ---- chat panel ----
    pin = eo3((t - 4.3) / 0.6)
    if pin > 0 and cout < 1:
        layer, _ = draw_chat(c, t, pin * (1 - cout), 0)
        canvas.alpha_composite(layer, (PX0, int(PY0 + (1 - pin) * 200 + cout * 200)))

    # ---- mascot (three.js foreground) ----
    mx, my, ms = mascot_pose(t)
    fgi = Image.fromarray(fg3, "RGBA").resize((int(ms), int(ms)), Image.BICUBIC)
    arr = np.asarray(canvas).astype(np.float32) / 255
    rgb = arr[..., :3].copy()
    premul_over(rgb, np.asarray(fgi), int(mx - ms / 2), int(my - ms / 2))
    canvas = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8)).convert("RGBA")

    # ---- outro ----
    if t >= OUTRO_T:
        u = t - OUTRO_T
        lines = ["Have you ever waited", "for a reply that", "never came?"]
        for i, ln in enumerate(lines):
            p = (u - 0.5 - i * 0.3) / 0.5
            put(canvas, T(ln, F("title", 82), PINK if i == 2 else WHITE), W / 2, 300 + i * 100 + 30 * (1 - eo3(p)), clamp(p * 2))
        p = (u - 1.8) / 0.5
        if p > 0:
            put(canvas, pill("tell me in the comments", F("semi", 40), PLUM, PINK + (255,), 36, 84), W / 2, 1640, clamp(p * 2), eoback(p))
            d = ImageDraw.Draw(canvas)
            by = 1730 + 10 * abs(math.sin(u * 5))
            d.polygon([(W / 2 - 22, by), (W / 2 + 22, by), (W / 2, by + 24)], fill=PINK + (int(255 * clamp(p)),))
        p = (u - 2.6) / 0.5
        if p > 0:
            put(canvas, T("Ep. 02 tomorrow night  ·  follow @quotable", F("small", 34), (255, 255, 255, 220)), W / 2, 1810, clamp(p))

    out = np.asarray(canvas.convert("RGB")).astype(np.float32)
    if t < 0.3: out *= t / 0.3
    if t > DUR - 0.5: out *= clamp((DUR - t) / 0.5)
    return out.astype(np.uint8)

VF = f"scale={CW}:{CH}:flags=lanczos,eq=contrast=1.04:saturation=1.06"

def clip_frame_at(c):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0, c):.3f}", "-i", SRC, "-frames:v", "1", "-vf", VF,
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(CH, CW, 3) if raw else None

if PREVIEW:
    p = three_proc(PREVIEW)
    tiles = []
    for t in PREVIEW:
        bg3, fg3 = read_three(p)
        vid = clip_frame_at(t - INTRO) if INTRO <= t < OUTRO_T + 0.6 else None
        if vid is None and t >= 4.0: vid = clip_frame_at(min(CLIP - 0.1, max(0, t - INTRO)))
        tiles.append(Image.fromarray(compose(vid, t, bg3, fg3)).resize((360, 640)))
    sheet = Image.new("RGB", (360 * len(tiles), 640))
    for i, tl in enumerate(tiles): sheet.paste(tl, (360 * i, 0))
    sheet.save(OUT); sys.exit()

# ---------- full render ----------
SILENT = f"{OUT}.video.mp4"
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"fps={FPS},{VF}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "slow", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M",
                        "-pix_fmt", "yuv420p", SILENT], stdin=subprocess.PIPE)
tp = three_proc()
fs = CW * CH * 3
first = last = pre = None
for i in range(N):
    t = i / FPS
    bg3, fg3 = read_three(tp)
    if INTRO <= t:
        if pre is not None: raw, pre = pre, None
        else: raw = dec.stdout.read(fs) if t < OUTRO_T else b""
        if len(raw) == fs:
            last = np.frombuffer(raw, np.uint8).reshape(CH, CW, 3)
            if first is None: first = last
    vid = last
    if t < INTRO and t >= 4.0:
        if first is None:
            pre = dec.stdout.read(fs); first = last = np.frombuffer(pre, np.uint8).reshape(CH, CW, 3)
        vid = first
    enc.stdin.write(compose(vid, t, bg3, fg3).tobytes())
    if i % 300 == 0: print(f"{t:5.1f}s", flush=True)
enc.stdin.close(); enc.wait(); dec.kill(); tp.wait()
print("video done")
