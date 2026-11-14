#!/usr/bin/env python3
"""Framed 'late-night film' social edit: clip inside an animated film frame
with bokeh backdrop, audio-reactive waveform, scene counter and light leaks.
usage: render2.py <input.mp4> <output.mp4> [--preview t1,t2,...]
"""
import sys, subprocess, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

SRC, OUT = sys.argv[1], sys.argv[2]
PREVIEW = [float(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None

W, H, FPS = 1080, 1920, 30
DUR = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", SRC], capture_output=True, text=True).stdout) - 0.05
N = int(DUR * FPS)

# palette
BG_TOP, BG_BOT = (16, 12, 30), (34, 14, 30)
BLUSH = (255, 168, 188)
CREAM = (250, 240, 226)
AMBER = (255, 190, 120)

FD = "/usr/share/fonts/"
F_SERIF_I = FD + "truetype/freefont/FreeSerifItalic.ttf"
F_SERIF_BI = FD + "truetype/freefont/FreeSerifBoldItalic.ttf"
F_SANS = FD + "opentype/inter/Inter-SemiBold.otf"
F_SANS_B = FD + "opentype/inter/InterDisplay-Bold.otf"
_fc = {}
def font(p, s):
    k = (p, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(p, int(s))
    return _fc[k]

CUTS = [1.6016, 3.7037, 5.90591, 7.60761, 9.84318, 12.1455, 15.2486, 18.4184, 20.0534,
        23.1899, 26.0594, 27.7611, 30.7975, 34.1341, 36.2362, 37.8378, 39.6063, 41.6083,
        47.5809, 49.3827, 51.4848, 56.1562, 60.2603]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo3(x): x = clamp(x); return 1 - (1 - x) ** 3
def eoexpo(x): x = clamp(x); return 1 if x == 1 else 1 - 2 ** (-10 * x)
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def eoback(x, s=1.7): x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1
def since_cut(t):
    p = [c for c in CUTS if c <= t]; return t - p[-1] if p else 99.0
def scene_no(t): return 1 + sum(1 for c in CUTS if c <= t)

def with_alpha(img, a):
    if a >= 0.999: return img
    img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * a))); return img

def text_img(txt, fnt, fill, tracking=0, shadow=True):
    widths = [fnt.getlength(c) + tracking for c in txt] if tracking else None
    tw = int(sum(widths) - tracking if tracking else fnt.getlength(txt)) + 4
    asc, desc = fnt.getmetrics(); pad = 24
    img = Image.new("RGBA", (tw + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    sh = img.copy()
    for layer, col in ((sh, (0, 0, 0, 160)), (img, fill)):
        d = ImageDraw.Draw(layer)
        if tracking:
            x = pad
            for c, w in zip(txt, widths): d.text((x, pad), c, font=fnt, fill=col); x += w
        else:
            d.text((pad, pad), txt, font=fnt, fill=col)
    if not shadow: return img
    return Image.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)), img)
_tc = {}
def T(*a, **k):
    key = (a, tuple(sorted(k.items())))
    if key not in _tc: _tc[key] = text_img(*a, **k)
    return _tc[key]

def put(c, im, cx, cy, a=1.0, scale=1.0):
    if a <= 0.01: return
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    c.alpha_composite(with_alpha(im, a), (int(cx - im.width / 2), int(cy - im.height / 2)))

# ---------- precomputed layers ----------
rng = random.Random(3)
BG = Image.new("RGBA", (W, H))
bd = ImageDraw.Draw(BG)
for y in range(H):
    k = y / H
    bd.line([(0, y), (W, y)], fill=tuple(int(BG_TOP[i] * (1 - k) + BG_BOT[i] * k) for i in range(3)) + (255,))

BOKEH_H = H * 2
BOKEH = Image.new("RGBA", (W, BOKEH_H), (0, 0, 0, 0))
bk = ImageDraw.Draw(BOKEH)
for _ in range(110):
    x, y, r = rng.uniform(0, W), rng.uniform(0, BOKEH_H), rng.uniform(8, 46)
    col = rng.choice([AMBER, BLUSH, (255, 220, 160), (255, 140, 120)])
    bk.ellipse([x - r, y - r, x + r, y + r], fill=col + (rng.randint(40, 120),))
BOKEH = BOKEH.filter(ImageFilter.GaussianBlur(7))
BOKEH = Image.alpha_composite(BOKEH, BOKEH.crop((0, 0, W, BOKEH_H)))  # (no-op keeps type)

# video window geometry
VW, VH = 800, 1422
VX, VY = (W - VW) // 2, 262
RAD = 34
MASK = Image.new("L", (VW, VH), 0)
ImageDraw.Draw(MASK).rounded_rectangle([0, 0, VW - 1, VH - 1], radius=RAD, fill=255)
BORDER = 10
FRAME = Image.new("RGBA", (VW + 2 * BORDER + 120, VH + 2 * BORDER + 120), (0, 0, 0, 0))
fsh = Image.new("RGBA", FRAME.size, (0, 0, 0, 0))
ImageDraw.Draw(fsh).rounded_rectangle([60, 80, 60 + VW + 2 * BORDER, 80 + VH + 2 * BORDER],
                                      radius=RAD + BORDER, fill=(0, 0, 0, 200))
fsh = fsh.filter(ImageFilter.GaussianBlur(26))
FRAME.alpha_composite(fsh)
ImageDraw.Draw(FRAME).rounded_rectangle([60, 60, 60 + VW + 2 * BORDER - 1, 60 + VH + 2 * BORDER - 1],
                                        radius=RAD + BORDER, fill=CREAM + (255,))

# film sprocket strips
STRIP_W, PITCH = 70, 64
STRIP = Image.new("RGBA", (STRIP_W, H + PITCH * 2), (0, 0, 0, 0))
sd = ImageDraw.Draw(STRIP)
sd.rectangle([0, 0, STRIP_W - 1, STRIP.height], fill=(10, 8, 14, 235))
for y in range(0, STRIP.height, PITCH):
    sd.rounded_rectangle([20, y + 18, STRIP_W - 20, y + 46], radius=6, fill=CREAM + (210,))

# light leak blob
LEAK = Image.new("RGBA", (700, 1600), (0, 0, 0, 0))
ImageDraw.Draw(LEAK).ellipse([100, 100, 600, 1500], fill=(255, 150, 90, 150))
LEAK = LEAK.filter(ImageFilter.GaussianBlur(90))

# ---------- audio analysis for waveform ----------
NB = 24
def audio_bands():
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", SRC, "-ac", "1", "-ar", "24000",
                          "-f", "s16le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    spf = 24000 // FPS
    edges = np.geomspace(2, 600, NB + 1).astype(int)
    out = np.zeros((N + 2, NB), np.float32)
    win = np.hanning(spf * 2)
    for i in range(N + 2):
        seg = a[i * spf: i * spf + spf * 2]
        if len(seg) < spf * 2: break
        sp = np.abs(np.fft.rfft(seg * win))
        out[i] = [sp[edges[b]:max(edges[b] + 1, edges[b + 1])].mean() for b in range(NB)]
    out = np.log1p(out * 4)
    out /= np.percentile(out, 98) + 1e-6
    sm = out.copy()  # temporal smoothing (fast attack, slow release)
    for i in range(1, len(sm)):
        sm[i] = np.maximum(out[i], sm[i - 1] * 0.82)
    return np.clip(sm, 0, 1.2)
BANDS = audio_bands()

def fmt(s): s = int(s); return f"{s // 60:02d}:{s % 60:02d}"

# ---------- compose ----------
def compose(vid, t):
    fi = int(t * FPS)
    c = BG.copy()
    # drifting bokeh, gently breathing
    off = int((t * 22) % H)
    bok = BOKEH.crop((0, off, W, off + H))
    c.alpha_composite(with_alpha(bok, 0.75 + 0.25 * math.sin(t * 0.8)))

    # sprocket strips scrolling opposite directions
    s1 = int((t * 90) % PITCH); s2 = int((-t * 90) % PITCH)
    intro = eo3(t / 1.0)
    c.alpha_composite(with_alpha(STRIP.crop((0, s1, STRIP_W, s1 + H)), intro), (int(-STRIP_W + (STRIP_W + 25) * intro) if intro < 1 else 25, 0))
    c.alpha_composite(with_alpha(STRIP.crop((0, s2, STRIP_W, s2 + H)), intro), (int(W - 25 - STRIP_W + (1 - intro) * (STRIP_W + 25)), 0))

    # ---- the framed video ----
    v = Image.fromarray(vid).convert("RGBA")
    sc = since_cut(t)
    # light leak sweep after each cut
    if sc < 0.9:
        p = sc / 0.9
        lx = int(-700 + p * (VW + 700))
        lk = with_alpha(LEAK, math.sin(p * math.pi) * 0.9)
        layer = Image.new("RGBA", (VW, VH), (0, 0, 0, 0)); layer.alpha_composite(lk, (lx, -90))
        v = Image.alpha_composite(v, layer)
    v.putalpha(MASK)
    card = FRAME.copy()
    card.alpha_composite(v, (60 + BORDER, 60 + BORDER))
    # outro dim + end card inside frame
    if t > DUR - 4.0:
        u = t - (DUR - 4.0)
        dim = Image.new("RGBA", (VW, VH), (12, 8, 20, int(185 * eio(u / 0.6))))
        dim.putalpha(ImageChops.multiply(dim.getchannel("A"), MASK))
        card.alpha_composite(dim, (60 + BORDER, 60 + BORDER))
        cx, cy = card.width / 2, card.height / 2
        p1, p2, p3 = (u - 0.3) / 0.6, (u - 0.7) / 0.6, (u - 1.3) / 0.5
        put(card, T("Tag someone", font(F_SERIF_I, 96), CREAM), cx, cy - 120 + 30 * (1 - eo3(p1)), clamp(p1 * 2))
        put(card, T("who needed this", font(F_SERIF_BI, 88), BLUSH), cx, cy - 10 + 30 * (1 - eo3(p2)), clamp(p2 * 2))
        put(card, T("tonight.", font(F_SERIF_I, 96), CREAM), cx, cy + 95 + 30 * (1 - eo3(p2)), clamp((p2 - 0.3) * 2))
        if p3 > 0:
            pill = Image.new("RGBA", (360, 96), (0, 0, 0, 0))
            ImageDraw.Draw(pill).rounded_rectangle([0, 0, 359, 95], radius=48, outline=BLUSH + (255,), width=4)
            lab = T("@quotable", font(F_SANS_B, 40), CREAM, tracking=2, shadow=False)
            pill.alpha_composite(lab, ((360 - lab.width) // 2, (96 - lab.height) // 2))
            put(card, pill, cx, cy + 250, clamp(p3 * 2), scale=eoback(p3))
    # intro: frame drops in with a slight tilt that settles
    if t < 1.2:
        p = eoback(t / 1.0, 1.3)
        s = 1.18 - 0.18 * p
        rot = 5 * (1 - eo3(t / 1.1))
        cc = card.resize((int(card.width * s), int(card.height * s)), Image.BICUBIC).rotate(rot, Image.BICUBIC, expand=True)
        put(c, cc, W / 2, VY - 60 - BORDER + card.height / 2, clamp(t / 0.35))
    else:
        # subtle float
        dy = 4 * math.sin(t * 1.1)
        c.alpha_composite(card, (VX - 60 - BORDER, int(VY - 60 - BORDER + dy)))

    d = ImageDraw.Draw(c)
    # ---- header ----
    a0 = eo3((t - 0.4) / 0.6)
    lw = 70 * a0
    put(c, T("A  LATE-NIGHT  STORY", font(F_SANS, 26), BLUSH, tracking=6), W / 2, 74, a0)
    d.line([(W / 2 - 230 - lw, 76), (W / 2 - 230, 76)], fill=BLUSH + (int(200 * a0),), width=2)
    d.line([(W / 2 + 230, 76), (W / 2 + 230 + lw, 76)], fill=BLUSH + (int(200 * a0),), width=2)
    title = "Some goodbyes don't make a sound.".split()
    f = font(F_SERIF_I, 60)
    x = W / 2 - f.getlength(" ".join(title)) / 2
    for i, w in enumerate(title):
        p = (t - 0.8 - i * 0.16) / 0.45
        img = T(w, f, CREAM if w not in ("sound.",) else BLUSH)
        if p > 0:
            c.alpha_composite(with_alpha(img, clamp(p)), (int(x - 24), int(150 - 24 + 18 * (1 - eo3(p)))))
        x += f.getlength(w + " ")

    # ---- footer: scene counter, timecode, waveform, progress ----
    fy = VY + VH + 46
    fa = eo3((t - 0.9) / 0.6)
    n = scene_no(t)
    roll = eo3(sc / 0.35) if sc < 0.35 else 1
    lab = T("SCENE", font(F_SANS, 24), (255, 255, 255, 170), tracking=5)
    c.alpha_composite(with_alpha(lab, fa), (VX - 24, fy - 24))
    num = T(f"{n:02d}", font(F_SANS_B, 34), BLUSH)
    numc = Image.new("RGBA", (num.width, 50), (0, 0, 0, 0))
    numc.alpha_composite(num, (0, int(-24 + (1 - roll) * 40)))
    if roll < 1:
        prev = T(f"{n - 1:02d}", font(F_SANS_B, 34), BLUSH)
        numc.alpha_composite(prev, (0, int(-24 - roll * 40)))
    c.alpha_composite(with_alpha(numc, fa), (VX + 105, fy - 12))
    tc = T(f"{fmt(t)} / {fmt(DUR)}", font(F_SANS, 26), (255, 255, 255, 200), tracking=2)
    c.alpha_composite(with_alpha(tc, fa), (VX + VW - tc.width + 24, fy - 22))

    # audio-reactive bars
    band = BANDS[min(fi, len(BANDS) - 1)]
    bw, gap = 10, 6
    total = NB * 2 * (bw + gap) - gap
    bx0 = W / 2 - total / 2
    cyb = fy + 78
    order = list(band[::-1]) + list(band)  # mirrored
    for i, v_ in enumerate(order):
        h = (6 + 46 * float(v_)) * fa
        x = bx0 + i * (bw + gap)
        mix = i / (len(order) - 1)
        col = tuple(int(BLUSH[k] * (1 - abs(mix - 0.5) * 2) + AMBER[k] * abs(mix - 0.5) * 2) for k in range(3))
        d.rounded_rectangle([x, cyb - h / 2, x + bw, cyb + h / 2], radius=6, fill=col + (int(230 * fa),))
    # progress
    py = cyb + 62
    d.rounded_rectangle([VX, py - 2, VX + VW, py + 2], radius=2, fill=(255, 255, 255, int(60 * fa)))
    px = VX + VW * t / DUR
    d.rounded_rectangle([VX, py - 2, px, py + 2], radius=2, fill=BLUSH + (int(255 * fa),))
    d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=CREAM + (int(255 * fa),))

    out = np.asarray(c.convert("RGB")).astype(np.float32)
    if t < 0.3: out *= t / 0.3
    if t > DUR - 0.5: out *= clamp((DUR - t) / 0.5)
    return out.astype(np.uint8)

VF = f"scale={VW}:{VH}:flags=lanczos,eq=contrast=1.05:saturation=1.08"

if PREVIEW:
    tiles = []
    for t in PREVIEW:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", SRC, "-frames:v", "1",
                              "-vf", VF, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        tiles.append(Image.fromarray(compose(np.frombuffer(raw, np.uint8).reshape(VH, VW, 3), t)).resize((360, 640)))
    sheet = Image.new("RGB", (360 * len(tiles), 640))
    for i, tl in enumerate(tiles): sheet.paste(tl, (360 * i, 0))
    sheet.save(OUT); sys.exit()

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-vf", f"fps={FPS},{VF}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", SRC, "-map", "0:v", "-map", "1:a",
                        "-t", f"{DUR:.3f}", "-af", f"afade=t=in:d=0.3,afade=t=out:st={DUR - 0.8:.2f}:d=0.8",
                        "-c:v", "libx264", "-preset", "slow", "-b:v", "7M", "-maxrate", "9M", "-bufsize", "14M",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", OUT],
                       stdin=subprocess.PIPE)
fs = VW * VH * 3
for i in range(N):
    raw = dec.stdout.read(fs)
    if len(raw) < fs: break
    enc.stdin.write(compose(np.frombuffer(raw, np.uint8).reshape(VH, VW, 3), i / FPS).tobytes())
    if i % 300 == 0: print(f"{i / FPS:5.1f}s", flush=True)
enc.stdin.close(); enc.wait(); dec.kill()
print("done")
