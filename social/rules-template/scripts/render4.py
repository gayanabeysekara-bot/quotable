#!/usr/bin/env python3
"""'Rules Nobody Tells You' — composite three.js frames + captions/UI overlays, then encode.
usage: render4.py <ep_dir> <out_video.mp4> [--preview t1,t2,...]"""
import sys, os, io, json, struct, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D, OUT = sys.argv[1], sys.argv[2]
PREVIEW = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
TL = json.load(open(f"{D}/timeline.json"))
W, H, FPS = 1080, 1920, 30
END = TL["end"]; N = int(END * FPS)
FD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
GOLD = (240, 196, 92); CREAM = (250, 240, 222); WHITE = (255, 255, 255)

_fc = {}
def F(path, size, var=None):
    k = (path, size, var)
    if k not in _fc:
        f = ImageFont.truetype(path, size)
        if var:
            try: f.set_variation_by_name(var)
            except Exception: pass
        _fc[k] = f
    return _fc[k]
CAP = lambda s: F("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf", s)
SANS = lambda s: F("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", s)
SERIF_I = lambda s: F(os.path.join(FD, "PlayfairItalic.ttf"), s, "Medium Italic")
SERIF = lambda s: F(os.path.join(FD, "Playfair.ttf"), s, "Bold")

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo3(x): x = clamp(x); return 1 - (1 - x) ** 3
def eoback(x, s=1.7): x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)

def text_img(txt, fnt, fill, stroke=0, shadow=True, tracking=0):
    widths = [fnt.getlength(c) + tracking for c in txt] if tracking else None
    tw = int(sum(widths) - tracking if tracking else fnt.getlength(txt)) + 2 * stroke + 4
    asc, desc = fnt.getmetrics(); pad = 28
    img = Image.new("RGBA", (tw + 2 * pad, asc + desc + 2 * stroke + 2 * pad), (0, 0, 0, 0))
    sh = img.copy()
    for layer, col in ((sh, (0, 0, 0, 200)), (img, fill)):
        d = ImageDraw.Draw(layer)
        if tracking:
            x = pad + stroke
            for ch, w in zip(txt, widths):
                d.text((x, pad + stroke), ch, font=fnt, fill=col, stroke_width=stroke, stroke_fill=(10, 8, 6, 255) if layer is img else col); x += w
        else:
            d.text((pad + stroke, pad + stroke), txt, font=fnt, fill=col, stroke_width=stroke, stroke_fill=(10, 8, 6, 255) if layer is img else col)
    if not shadow: return img
    return Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)), img)
_tc = {}
def T(*a, **k):
    key = (a[0], id(a[1]), a[2], tuple(sorted(k.items())))
    if key not in _tc: _tc[key] = text_img(*a, **k)
    return _tc[key]
def with_alpha(img, a):
    if a >= 0.999: return img
    img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * a))); return img
def put(c, im, cx, cy, a=1.0, scale=1.0):
    if a <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 1e-3: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    c.alpha_composite(with_alpha(im, a), (int(cx - im.width / 2), int(cy - im.height / 2)))
def pill(text, fnt, fg, bg, padx=26, h=58, outline=None, tracking=0):
    t = T(text, fnt, fg, shadow=False, tracking=tracking)
    img = Image.new("RGBA", (t.width - 56 + 2 * padx, h), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, img.width - 1, h - 1], radius=h // 2, fill=bg, outline=outline, width=2 if outline else 0)
    img.alpha_composite(t, (padx - 28, (h - t.height) // 2)); return img

# ---- caption chunks (<= 3 words, break at punctuation) ----
WORDS = TL["words"]
CHUNKS = []; cur = []
for i, (w, a, b) in enumerate(WORDS):
    cur.append(i)
    nxt_gap = WORDS[i + 1][1] - b if i + 1 < len(WORDS) else 9
    if len(cur) == 3 or w[-1] in ",.?!" or nxt_gap > 0.4: CHUNKS.append(cur); cur = []
if cur: CHUNKS.append(cur)

def draw_captions(c, t):
    for ch in CHUNKS:
        a, b = WORDS[ch[0]][1], WORDS[ch[-1]][2] + 0.25
        if not (a - 0.05 <= t < b): continue
        fnt = CAP(76)
        words = [WORDS[i][0] for i in ch]
        imgs = []
        for i in ch:
            w, wa, wb = WORDS[i]
            active = wa <= t < wb or (i == ch[-1] and t >= wb)
            imgs.append((T(w.upper(), fnt, GOLD if active else WHITE, stroke=5), wa))
        space = 14
        total = sum(im.width - 56 for im, _ in imgs) + space * (len(imgs) - 1)
        fit = min(1.0, 940 / total)
        if fit < 1:
            imgs = [(im.resize((int(im.width * fit), int(im.height * fit)), Image.BICUBIC), wa) for im, wa in imgs]
            space = int(space * fit); total = sum(im.width - int(56 * fit) for im, _ in imgs) + space * (len(imgs) - 1)
        pad = int(56 * fit)
        x = W / 2 - total / 2
        for im, wa in imgs:
            p = (t - wa) / 0.18
            if p <= 0: x += im.width - pad + space; continue
            s = 0.75 + 0.25 * eoback(p)
            put(c, im, x + (im.width - pad) / 2, 1700 + 20 * (1 - eo3(p)), clamp(p * 3), s)
            x += im.width - pad + space
        return

ALL_RULES = [r for p in TL["pages"] for r in p["rules"]]
def rule_now(t):
    n = 0
    for r in ALL_RULES:
        if t >= r["vo"] - 0.2: n = r["n"]
    return n

def draw_ui(c, t):
    d = ImageDraw.Draw(c)
    # top gradient for legibility
    a = eo3((t - 4.8) / 0.6) * (1 - eio((t - TL["outro"]) / 0.6))
    if a > 0:
        put(c, pill("RULES NOBODY TELLS YOU  ·  PART 1", SANS(26), (30, 22, 12, 255), GOLD + (255,), 26, 54, tracking=2), W / 2, 92, a)
        n, tot = rule_now(t), TL["total_rules"]
        lab = T(f"RULE {n:02d} / {tot:02d}", SANS(26), (255, 255, 255, 230), tracking=4)
        put(c, lab, W / 2, 158, a)
        x0 = W / 2 - (tot - 1) * 26 / 2
        for i in range(tot):
            on = i < n
            r = 7 if on else 5
            col = GOLD + (int(255 * a),) if on else (255, 255, 255, int(110 * a))
            d.ellipse([x0 + i * 26 - r, 200 - r, x0 + i * 26 + r, 200 + r], fill=col)
    # intro: bookmark "save this" sticker
    if 1.6 < t < 5.2:
        p = (t - 1.6) / 0.45; out = eio((t - 4.7) / 0.4)
        st = pill("SAVE THIS FOR LATER", SANS(30), (30, 22, 12, 255), GOLD + (255,), 30, 64, tracking=3)
        st = st.rotate(-4, Image.BICUBIC, expand=True)
        put(c, st, W / 2, 250, clamp(p * 2) * (1 - out), eoback(p))
    # outro card
    if t >= TL["outro"] + 0.6:
        u = t - (TL["outro"] + 0.6)
        g = Image.new("RGBA", (W, 760), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        for y in range(760):
            gd.line([(0, y), (W, y)], fill=(8, 5, 3, int(215 * (1 - y / 760) ** 1.2 * eio(u / 0.8))))
        c.alpha_composite(g, (0, 0))
        for i, (ln, col) in enumerate((("Which one did you", CREAM), ("learn the hard way?", GOLD))):
            p = (u - 0.3 - i * 0.35) / 0.6
            put(c, T(ln, SERIF_I(88), col), W / 2, 230 + i * 115 + 30 * (1 - eo3(p)), clamp(p * 2))
        p = (u - 1.4) / 0.5
        if p > 0: put(c, pill("comment the number", SANS(36), (30, 22, 12, 255), GOLD + (255,), 34, 78), W / 2, 470, clamp(p * 2), eoback(p))
        p = (u - 2.1) / 0.5
        if p > 0: put(c, T("Part 2 tomorrow  ·  follow @quotable", SANS(32), (255, 255, 255, 220), tracking=1), W / 2, 570, clamp(p))

# ---- post: vignette + grain ----
yy, xx = np.mgrid[0:H, 0:W]
VIG = np.clip(1 - 0.5 * (((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.66)) ** 2), 0.4, 1)[..., None].astype(np.float32)
GR = [np.random.default_rng(i).normal(0, 5, (H // 2, W // 2)).astype(np.float32) for i in range(6)]

def compose(frame, t):
    f = np.asarray(frame.convert("RGB")).astype(np.float32) * VIG
    g = GR[int(t * FPS) % 6]; f += np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    c = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).convert("RGBA")
    draw_ui(c, t); draw_captions(c, t)
    out = np.asarray(c.convert("RGB")).astype(np.float32)
    if t < 0.4: out *= t / 0.4
    if t > END - 0.6: out *= clamp((END - t) / 0.6)
    return out.astype(np.uint8)

def frames(times_arg):
    p = subprocess.Popen(["node", f"{D}/three/driver.cjs"] + times_arg, stdout=subprocess.PIPE, stderr=sys.stderr)
    while True:
        h = p.stdout.read(4)
        if len(h) < 4: break
        n = struct.unpack("<I", h)[0]
        yield Image.open(io.BytesIO(p.stdout.read(n)))
    p.wait()

if PREVIEW:
    tiles = [Image.fromarray(compose(fr, t)).resize((360, 640)) for fr, t in zip(frames([",".join(map(str, PREVIEW))]), PREVIEW)]
    s = Image.new("RGB", (360 * len(tiles), 640))
    for i, tl in enumerate(tiles): s.paste(tl, (360 * i, 0))
    s.save(OUT); sys.exit()

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M", "-pix_fmt", "yuv420p", OUT],
                       stdin=subprocess.PIPE)
for i, fr in enumerate(frames(["--range", str(N), str(FPS)])):
    enc.stdin.write(compose(fr, i / FPS).tobytes())
    if i % 300 == 0: print(f"{i / FPS:5.1f}s", flush=True)
enc.stdin.close(); enc.wait(); print("video done")
