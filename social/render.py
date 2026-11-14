#!/usr/bin/env python3
"""Motion-graphic social edit: beat-synced kinetic type over a graded clip.
usage: render.py <input.mp4> <output.mp4> [--preview t1,t2,...]
"""
import sys, subprocess, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
PREVIEW = None
if len(sys.argv) > 4 and sys.argv[3] == "--preview":
    PREVIEW = [float(x) for x in sys.argv[4].split(",")]

W, H, FPS = 1080, 1920, 30
DUR = 27.3
N = int(DUR * FPS)

GOLD = (255, 196, 61)
WHITE = (255, 255, 255)

F_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_ITAL = "/usr/share/fonts/opentype/inter/InterDisplay-LightItalic.otf"
F_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
import os
for p in (F_BLACK, F_BOLD, F_ITAL):
    if not os.path.exists(p):
        raise SystemExit("missing font " + p)
_fc = {}
def font(path, size):
    k = (path, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]

# Beat / cut markers detected from the clip (scene changes)
CUTS = [6.92, 8.208, 9.327, 10.447, 11.566, 12.644, 13.804, 14.924,
        16.001, 17.162, 18.281, 19.401, 20.603, 21.681, 22.80]

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out_cubic(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_out_back(x, s=1.9):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1
def ease_in_out(x): x = clamp(x); return x * x * (3 - 2 * x)
def ease_out_expo(x): x = clamp(x); return 1 if x == 1 else 1 - 2 ** (-10 * x)

def since_cut(t):
    prev = [c for c in CUTS if c <= t]
    return t - prev[-1] if prev else 99.0

# ---------- text helpers ----------
def text_layer(txt, fnt, fill, stroke=0, stroke_fill=(0, 0, 0), tracking=0):
    """Render text (with optional letter-spacing) to an RGBA image, plus soft shadow."""
    if tracking:
        widths = [fnt.getlength(c) + tracking for c in txt]
        tw = int(sum(widths) - tracking) + stroke * 2 + 4
    else:
        tw = int(fnt.getlength(txt)) + stroke * 2 + 4
    asc, desc = fnt.getmetrics()
    th = asc + desc + stroke * 2 + 4
    pad = 40
    img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    for layer, col in ((sh, (0, 0, 0, 170)), (img, fill)):
        d = ImageDraw.Draw(layer)
        x = pad + stroke
        if tracking:
            for c, w in zip(txt, widths):
                d.text((x, pad + stroke), c, font=fnt, fill=col,
                       stroke_width=stroke, stroke_fill=stroke_fill if layer is img else col)
                x += w
        else:
            d.text((x, pad + stroke), txt, font=fnt, fill=col,
                   stroke_width=stroke, stroke_fill=stroke_fill if layer is img else col)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    out = Image.alpha_composite(sh, img)
    return out

_tc = {}
def cached_text(*a, **k):
    key = (a, tuple(sorted(k.items())))
    if key not in _tc:
        _tc[key] = text_layer(*a, **k)
    return _tc[key]

def paste(canvas, layer, cx, cy, scale=1.0, alpha=1.0, rot=0.0, blur=0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    l = layer
    if abs(scale - 1) > 1e-3:
        l = l.resize((max(1, int(l.width * scale)), max(1, int(l.height * scale))), Image.BICUBIC)
    if rot:
        l = l.rotate(rot, resample=Image.BICUBIC, expand=True)
    if blur:
        l = l.filter(ImageFilter.GaussianBlur(blur))
    if alpha < 1:
        a = l.getchannel("A").point(lambda v: int(v * alpha))
        l = l.copy(); l.putalpha(a)
    canvas.alpha_composite(l, (int(cx - l.width / 2), int(cy - l.height / 2)))

# ---------- timeline ----------
# Section 1 — hook (0 - 2.4s): stacked slam words
HOOK = [("NOBODY", 0.10), ("SAW", 0.45), ("THE", 0.80), ("STRUGGLE.", 1.10)]
# Section 2 — lower-third story line, word by word
STORY = [(2.6, 6.6, "Every day felt like", "walking against the crowd.")]
# Section 3 — beat words, one per cut
BEAT_WORDS = {6.92: "UNTIL", 8.208: "ONE", 9.327: "DAY", 10.447: "IT",
              11.566: "ALL", 12.644: "PAID", 13.804: "OFF."}
# Section 4 — serif lines over the joy montage
LINES = [(14.924, 17.10, "the tears,"), (16.001, 18.20, "the doubt,"),
         (17.162, 19.35, "the waiting —")]
# Section 5 — big statement
BIG = (19.401, 22.75, ["WORTH", "EVERY", "SECOND."])
# Section 6 — outro
OUTRO_T = 22.80

def draw_hook(c, t):
    if t > 2.6: return
    fade = 1 - ease_in_out((t - 2.25) / 0.35)
    y0 = 300
    for i, (w, st) in enumerate(HOOK):
        p = (t - st) / 0.35
        if p < 0: continue
        s = 1.6 - 0.6 * ease_out_expo(p)
        a = clamp(p * 3) * fade
        gold = (w == "STRUGGLE.")
        size = 150 if gold else 120
        lay = cached_text(w, font(F_BLACK, size), GOLD if gold else WHITE, tracking=4)
        paste(c, lay, W / 2, y0 + i * 135 + (25 if gold else 0), scale=s, alpha=a,
              blur=int(max(0, 1 - p * 2.5) * 6))
    # underline swipe under STRUGGLE
    p = (t - 1.45) / 0.4
    if p > 0:
        d = ImageDraw.Draw(c)
        ww = 560 * ease_out_cubic(p)
        a = int(255 * fade)
        d.rectangle([W / 2 - 280, 790, W / 2 - 280 + ww, 802], fill=GOLD + (a,))

def draw_story(c, t):
    for st, en, l1, l2 in STORY:
        if not (st - 0.1 <= t <= en + 0.4): continue
        fade = 1 - ease_in_out((t - en) / 0.35)
        words = [(w, 0) for w in l1.split()] + [(w, 1) for w in l2.split()]
        fnt = font(F_ITAL, 64)
        fntb = font(F_BOLD, 66)
        # layout lines
        y = {0: 1460, 1: 1545}
        # panel
        pa = ease_out_cubic((t - st) / 0.4) * fade
        if pa > 0:
            panel = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            pd = ImageDraw.Draw(panel)
            for yy in range(1300, H):
                k = (yy - 1300) / (H - 1300)
                pd.line([(0, yy), (W, yy)], fill=(0, 0, 0, int(190 * min(1, k * 1.6) * pa)))
            c.alpha_composite(panel)
            d = ImageDraw.Draw(c)
            d.rectangle([90, 1420, 90 + 8, 1420 + int(190 * pa)], fill=GOLD + (int(255 * pa),))
        x_line = {0: 130, 1: 130}
        for i, (w, ln) in enumerate(words):
            wst = st + 0.25 + i * 0.28
            p = (t - wst) / 0.3
            f = fntb if w.startswith("against") or w.startswith("crowd") else fnt
            col = GOLD if f is fntb else WHITE
            lay = cached_text(w, f, col)
            x = x_line[ln]
            x_line[ln] += f.getlength(w + " ")
            if p <= 0: continue
            a = clamp(p) * fade
            dy = (1 - ease_out_cubic(p)) * 40
            c.alpha_composite(_alpha(lay, a), (int(x - 40), int(y[ln] - 40 + dy)))

def _alpha(l, a):
    if a >= 0.999: return l
    l = l.copy(); l.putalpha(l.getchannel("A").point(lambda v: int(v * a))); return l

def draw_beat_words(c, t):
    keys = sorted(BEAT_WORDS)
    for i, k in enumerate(keys):
        end = keys[i + 1] if i + 1 < len(keys) else 14.924
        if not (k <= t < end + 0.15): continue
        p = (t - k) / 0.28
        out = clamp((t - (end - 0.12)) / 0.2)
        w = BEAT_WORDS[k]
        gold = w in ("UNTIL", "OFF.")
        lay = cached_text(w, font(F_BLACK, 230 if len(w) <= 4 else 200), GOLD if gold else WHITE,
                          tracking=6)
        s = 0.55 + 0.45 * ease_out_back(p) + 0.04 * (t - k)  # pop + slow drift
        a = clamp(p * 2.5) * (1 - out)
        # alternate vertical slot, keep faces (centre) mostly clear
        cy = 360 if i % 2 == 0 else 1520
        jitter = (random.Random(int(t * FPS)).uniform(-3, 3) if p < 1 else 0)
        paste(c, lay, W / 2 + jitter, cy, scale=s, alpha=a, blur=int(max(0, 1 - p * 2) * 5))
        # running sentence ticker under it
        built = " ".join(BEAT_WORDS[kk] for kk in keys if kk <= t and kk >= 8.2)
        if built and k >= 8.2 and t < end:
            tk = cached_text(built, font(F_SEMI, 40), (255, 255, 255, 220), tracking=8)
            paste(c, tk, W / 2, cy + (150 if cy < 900 else -150), alpha=0.85 * (1 - out if w == "OFF." else 1))

def draw_lines(c, t):
    for i, (st, en, txt) in enumerate(LINES):
        if not (st <= t <= en + 0.4): continue
        p = (t - st) / 0.5
        fade = 1 - ease_in_out((t - en) / 0.4)
        lay = cached_text(txt, font(F_ITAL, 96), WHITE)
        x = W / 2 + (1 - ease_out_expo(p)) * (300 if i % 2 == 0 else -300)
        paste(c, lay, x, 300 + i * 120, alpha=clamp(p * 2) * fade)

def draw_big(c, t):
    st, en, words = BIG
    if not (st <= t <= en + 0.3): return
    fade = 1 - ease_in_out((t - en) / 0.3)
    for i, w in enumerate(words):
        wst = st + i * 0.45
        p = (t - wst) / 0.4
        if p <= 0: continue
        gold = i == 2
        lay = cached_text(w, font(F_BLACK, 200 if gold else 170), GOLD if gold else WHITE, tracking=4)
        s = 1.35 - 0.35 * ease_out_expo(p) + 0.015 * (t - wst)
        paste(c, lay, W / 2, 1270 + i * 175, scale=s, alpha=clamp(p * 3) * fade,
              blur=int(max(0, 1 - p * 2.5) * 6))

def draw_outro(c, t):
    if t < OUTRO_T: return
    u = t - OUTRO_T
    # dark gradient wash
    a = ease_in_out(u / 0.8)
    wash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    for yy in range(0, H, 4):
        k = abs(yy - H * 0.52) / (H * 0.52)
        wd.rectangle([0, yy, W, yy + 4], fill=(8, 6, 2, int(150 * a * (1 - 0.55 * k))))
    c.alpha_composite(wash)
    l1 = cached_text("Your moment", font(F_ITAL, 110), WHITE)
    l2 = cached_text("IS COMING.", font(F_BLACK, 148), GOLD, tracking=6)
    p1 = (u - 0.15) / 0.5; p2 = (u - 0.55) / 0.45
    paste(c, l1, W / 2, 820 + (1 - ease_out_cubic(p1)) * 50, alpha=clamp(p1 * 2))
    paste(c, l2, W / 2, 980, scale=1.4 - 0.4 * ease_out_expo(p2), alpha=clamp(p2 * 3),
          blur=int(max(0, 1 - p2 * 2.5) * 6))
    d = ImageDraw.Draw(c)
    p3 = (u - 1.0) / 0.5
    if p3 > 0:
        ww = 420 * ease_out_cubic(p3)
        d.rectangle([W / 2 - ww / 2, 1095, W / 2 + ww / 2, 1101], fill=GOLD + (255,))
    # CTA pill
    p4 = (u - 1.6) / 0.45
    if p4 > 0:
        s = ease_out_back(p4)
        cta = cached_text("SAVE THIS FOR THE HARD DAYS", font(F_BOLD, 40), (20, 16, 6), tracking=4)
        pill = Image.new("RGBA", (cta.width - 20, 110), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle([0, 0, pill.width - 1, 109], radius=55, fill=GOLD + (255,))
        pill.alpha_composite(cta.crop((0, 0, cta.width, cta.height)).resize((cta.width - 20, int(cta.height * (cta.width - 20) / cta.width))),
                             (0, int(55 - cta.height * (cta.width - 20) / cta.width / 2)))
        paste(c, pill, W / 2, 1300, scale=s, alpha=clamp(p4 * 2))
    p5 = (u - 2.2) / 0.5
    if p5 > 0:
        h = cached_text("follow for daily motivation  ·  @quotable", font(F_SEMI, 38), (255, 255, 255), tracking=2)
        paste(c, h, W / 2, 1420 + (1 - ease_out_cubic(p5)) * 30, alpha=clamp(p5) * 0.9)

# ---------- persistent chrome ----------
def draw_chrome(c, t):
    d = ImageDraw.Draw(c)
    # progress bar
    d.rectangle([0, 0, W, 10], fill=(255, 255, 255, 50))
    d.rectangle([0, 0, int(W * t / DUR), 10], fill=GOLD + (255,))
    # brand tag
    a = ease_out_cubic((t - 0.3) / 0.5)
    if a > 0 and t < OUTRO_T:
        tag = cached_text("QUOTABLE", font(F_BOLD, 30), (255, 255, 255), tracking=10)
        paste(c, tag, 175, 70, alpha=0.75 * a)
        d.ellipse([46, 63, 60, 77], fill=GOLD + (int(255 * a),))
    # beat flash
    sc = since_cut(t)
    if sc < 0.12:
        c.alpha_composite(Image.new("RGBA", (W, H), (255, 245, 220, int(110 * (1 - sc / 0.12)))))
    # sparkle particles on the joy section
    if 8.2 <= t < OUTRO_T + 5:
        rng = random.Random(7)
        for i in range(36):
            x0 = rng.uniform(0, W); sp = rng.uniform(40, 120); ph = rng.uniform(0, 30)
            y = H - ((t * sp + ph * 60) % (H + 100))
            x = x0 + 20 * math.sin(t * 1.3 + i)
            r = rng.uniform(2, 5)
            tw = 0.5 + 0.5 * math.sin(t * 6 + i)
            d.ellipse([x - r, y - r, x + r, y + r], fill=GOLD + (int(150 * tw),))

# ---------- video base processing ----------
YY, XX = np.mgrid[0:H, 0:W]
VIGN = 1 - 0.55 * (((XX - W / 2) / (W * 0.75)) ** 2 + ((YY - H / 2) / (H * 0.7)) ** 2)
VIGN = np.clip(VIGN, 0.35, 1)[..., None].astype(np.float32)
GRAIN = [np.random.default_rng(i).normal(0, 7, (H // 2, W // 2)).astype(np.float32) for i in range(8)]

def base_frame(arr, t):
    sc = since_cut(t)
    # zoom: slow push-in + punch on each cut
    z = 1.04 + 0.012 * (t % 1.12)
    if sc < 0.35:
        z += 0.09 * (1 - ease_out_cubic(sc / 0.35))
    if t < 0.6:
        z += 0.25 * (1 - ease_out_expo(t / 0.6))
    img = Image.fromarray(arr)
    cw, ch = W / z, H / z
    x0, y0 = (W - cw) / 2, (H - ch) / 2
    img = img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    f = np.asarray(img).astype(np.float32)
    # chromatic split on cut
    if sc < 0.15:
        o = int(14 * (1 - sc / 0.15))
        if o:
            f[..., 0] = np.roll(f[..., 0], o, axis=1)
            f[..., 2] = np.roll(f[..., 2], -o, axis=1)
    f *= VIGN
    g = GRAIN[int(t * FPS) % len(GRAIN)]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    f += g
    # outro: blur-ish darken handled by overlay; intro fade from black
    if t < 0.25:
        f *= t / 0.25
    if t > DUR - 0.4:
        f *= clamp((DUR - t) / 0.4)
    return np.clip(f, 0, 255).astype(np.uint8)

def overlay(t):
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_hook(c, t); draw_story(c, t); draw_beat_words(c, t)
    draw_lines(c, t); draw_big(c, t); draw_outro(c, t); draw_chrome(c, t)
    return c

GRADE = ("eq=contrast=1.12:saturation=1.18:brightness=-0.01,"
         "colorbalance=rs=-0.04:bs=0.06:rh=0.07:gh=0.02:bh=-0.07,"
         "curves=preset=increase_contrast")

def frames_at(times):
    for t in times:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", SRC, "-frames:v", "1",
                              "-vf", f"scale={W}:{H}:flags=lanczos,{GRADE}", "-f", "rawvideo",
                              "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        yield t, np.frombuffer(raw, np.uint8).reshape(H, W, 3)

def compose(arr, t):
    b = Image.fromarray(base_frame(arr, t)).convert("RGBA")
    b.alpha_composite(overlay(t))
    return b.convert("RGB")

if PREVIEW:
    tiles = [compose(a, t).resize((360, 640)) for t, a in frames_at(PREVIEW)]
    sheet = Image.new("RGB", (360 * len(tiles), 640))
    for i, tl in enumerate(tiles): sheet.paste(tl, (360 * i, 0))
    sheet.save(OUT); sys.exit()

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-t", str(DUR), "-vf",
                        f"fps={FPS},scale={W}:{H}:flags=lanczos,{GRADE}", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", SRC,
                        "-map", "0:v", "-map", "1:a", "-t", str(DUR),
                        "-af", f"afade=t=in:d=0.3,afade=t=out:st={DUR-0.6}:d=0.6",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT],
                       stdin=subprocess.PIPE)
fs = W * H * 3
for i in range(N):
    raw = dec.stdout.read(fs)
    if len(raw) < fs: break
    t = i / FPS
    enc.stdin.write(compose(np.frombuffer(raw, np.uint8).reshape(H, W, 3), t).tobytes())
    if i % 90 == 0: print(f"{t:5.1f}s", flush=True)
enc.stdin.close(); enc.wait(); dec.wait()
print("done")
