#!/usr/bin/env python3
"""Meta ad edit renderer: Laurus Aroma Coconut Milk Body Scrub (9:16, 1080x1920, 30fps)."""
import subprocess, sys, math, random, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC = sys.argv[1]
OUT = sys.argv[2]
WORK = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
SR = 44100

BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
XBOLD = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"
SEMI = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SERIF_R = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"

GOLD = (214, 172, 92)
CREAM = (250, 244, 232)
INK = (24, 20, 16)

# ---------------------------------------------------------------- edit list
# src_in, src_out, speed, voice(bool), zoom_from, zoom_to, anchor(y 0..1), text cue, kind
HOOK_SPEED = None
EDL = [
    # ---- HOOK (0-3s): result first, pattern interrupt, SFX-driven
    dict(a=52.45, b=53.75, sp=1.30, voice=False, z=(1.55, 1.18), ay=0.55, kind="h1"),   # glossy hand, pointing at shine
    dict(a=35.05, b=36.35, sp=1.30, voice=False, z=(1.15, 1.40), ay=0.55, kind="h2"),   # pulling scrub from labelled jar
    dict(a=41.00, b=43.50, sp=2.50, voice=False, z=(1.30, 1.10), ay=0.65, kind="h3"),   # scrub melting into glossy skin
    # ---- BODY (voice, cut on natural pauses, 1.1x)
    dict(a=0.00, b=2.35, sp=1.10, voice=True, z=(1.00, 1.06), ay=0.45, kind="b1"),
    dict(a=20.12, b=24.77, sp=1.10, voice=True, z=(1.00, 1.05), ay=0.40, kind="b2"),
    dict(a=25.07, b=31.60, sp=1.10, voice=True, z=(1.12, 1.18), ay=0.50, kind="b3"),
    dict(a=47.67, b=52.22, sp=1.10, voice=True, z=(1.05, 1.13), ay=0.55, kind="b4"),
    dict(a=114.49, b=116.68, sp=1.10, voice=True, z=(1.10, 1.02), ay=0.45, kind="b5"),
    dict(a=135.30, b=140.22, sp=1.10, voice=True, z=(1.00, 1.08), ay=0.50, kind="end"),
]
t = 0.0
for s in EDL:
    s["dur"] = (s["b"] - s["a"]) / s["sp"]
    s["nf"] = int(round(s["dur"] * FPS))
    s["t0"] = t
    t += s["nf"] / FPS
TOTAL = t
TOTAL_F = int(round(TOTAL * FPS))
print(f"total {TOTAL:.2f}s, {TOTAL_F} frames")
for s in EDL:
    print(f"  {s['kind']:4s} {s['t0']:6.2f}-{s['t0']+s['nf']/FPS:6.2f}  src {s['a']}-{s['b']} x{s['sp']}")

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))
def ease_out(x):
    x = clamp(x); return 1 - (1 - x) ** 3
def ease_inout(x):
    x = clamp(x); return x * x * (3 - 2 * x)
def back_out(x, s=2.2):
    x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1

# ---------------------------------------------------------------- text layers
_cache = {}
def font(p, size):
    k = (p, size)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(p, size)
    return _cache[k]

def text_block(lines, pad=(46, 26), radius=26, gap=10):
    """lines: list of (text, fontpath, size, fill, box_fill or None, stroke)"""
    imgs = []
    for txt, fp, size, fill, box, stroke in lines:
        f = font(fp, size)
        bb = f.getbbox(txt, stroke_width=stroke)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        px, py = pad if box else (stroke + 4, stroke + 4)
        im = Image.new("RGBA", (tw + 2 * px, th + 2 * py), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        if box:
            d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=radius, fill=box)
        d.text((px - bb[0], py - bb[1]), txt, font=f, fill=fill,
               stroke_width=stroke, stroke_fill=(0, 0, 0, 255) if stroke else None)
        imgs.append(im)
    w = max(i.width for i in imgs)
    h = sum(i.height for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i in imgs:
        out.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height + gap
    # soft drop shadow
    sh = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    a = out.split()[3].point(lambda v: int(v * 0.45))
    blk = Image.new("RGBA", out.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk, (30, 38)); sh = sh.filter(ImageFilter.GaussianBlur(14))
    sh.alpha_composite(out, (30, 30))
    return sh

def place(frame, layer, cx, cy, scale=1.0, alpha=1.0, rot=0.0):
    if alpha <= 0.01 or scale <= 0.01:
        return
    L = layer
    if abs(scale - 1) > 1e-3:
        L = L.resize((max(1, int(L.width * scale)), max(1, int(L.height * scale))), Image.BICUBIC)
    if rot:
        L = L.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1:
        a = L.split()[3].point(lambda v: int(v * alpha)); L = L.copy(); L.putalpha(a)
    frame.alpha_composite(L, (int(cx - L.width / 2), int(cy - L.height / 2)))

def pop(frame, layer, lt, cx, cy, dur=None, inn=0.22, out=0.15, rot=0.0):
    """scale-overshoot entrance, quick fade/scale exit"""
    if lt < 0 or (dur is not None and lt > dur):
        return
    s = 0.55 + 0.45 * back_out(lt / inn)
    a = clamp(lt / 0.08)
    if dur is not None and lt > dur - out:
        k = (dur - lt) / out; a *= k; s *= 0.9 + 0.1 * k
    place(frame, layer, cx, cy, s, a, rot)

def slide(frame, layer, lt, cx, cy, dur, dy=60, inn=0.28, out=0.18):
    if lt < 0 or lt > dur:
        return
    k = ease_out(lt / inn)
    a = k
    if lt > dur - out:
        a *= (dur - lt) / out
    place(frame, layer, cx, cy + (1 - k) * dy, 1.0, a)

# Hook copy: big kinetic words, keyword in gold box
HOOK1 = text_block([("THIS GLOW?", BLACK, 150, CREAM, None, 10)])
HOOK1b = text_block([("NO FILTER", BLACK, 80, INK, GOLD + (255,), 0)], pad=(34, 16), radius=18)
HOOK2a = text_block([("JUST", BLACK, 96, CREAM, None, 8)])
HOOK2b = text_block([("1 SCOOP", BLACK, 170, INK, GOLD + (255,), 0)], pad=(44, 14), radius=30)
HOOK3 = text_block([("WATCH IT", BLACK, 120, CREAM, None, 9), ("MELT", BLACK, 210, CREAM, None, 12)], gap=-6)

B1 = text_block([("DRY, DULL SKIN?", BLACK, 104, CREAM, None, 8)])
B1s = text_block([("you need to see this", SEMI, 60, INK, (255, 255, 255, 235), 0)], pad=(32, 14), radius=40)
B2a = text_block([("LAURUS AROMA", SERIF_R, 34, (120, 92, 44), None, 0), ("Coconut Milk", SERIF, 96, INK, None, 0), ("BODY SCRUB", BLACK, 74, INK, None, 0)], gap=2)
B2bg = None
B3 = text_block([("+ DEAD SEA MINERALS", BLACK, 76, INK, GOLD + (255,), 0)], pad=(36, 18), radius=22)
B3s = text_block([("+ COCONUT MILK", BLACK, 76, INK, (255, 255, 255, 240), 0)], pad=(36, 18), radius=22)
B4 = text_block([("MASSAGE IN...", BLACK, 92, CREAM, None, 8)])
B4b = text_block([("INSTANT GLOW", BLACK, 112, INK, GOLD + (255,), 0)], pad=(40, 16), radius=26)
B5 = [text_block([(w, BLACK, 128, CREAM, None, 9)]) for w in ("SOFT.", "SMOOTH.", "GLOWING.")]

# card behind B2 product name
def card(w, h, fill=(250, 244, 232, 238), r=36):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=fill)
    return im
B2card = card(B2a.width + 30, B2a.height - 20)
B2tag = text_block([("by LAURUS AROMA", SEMI, 40, (110, 84, 40), None, 0)])
B2tag_line = text_block([("Ideal for dry skin", SEMI, 46, CREAM, (0, 0, 0, 150), 0)], pad=(28, 12), radius=30)

END_title = text_block([("Coconut Milk", SERIF, 104, INK, None, 0), ("BODY SCRUB", BLACK, 84, INK, None, 0)], gap=2)
END_sub = text_block([("with Dead Sea Minerals  •  Ideal for dry skin", SEMI, 38, (90, 70, 40), None, 0)])
END_brand = text_block([("LAURUS AROMA", SERIF_R, 46, (120, 92, 44), None, 0)])

def cta_button(scale_pulse=1.0):
    f = font(BLACK, 74)
    txt = "SHOP NOW  →"
    bb = f.getbbox(txt)
    w, h = bb[2] - bb[0] + 130, bb[3] - bb[1] + 66
    im = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], radius=h // 2, fill=INK + (255,))
    d.text((20 + 65 - bb[0], 20 + 33 - bb[1]), txt, font=f, fill=CREAM)
    return im
CTA = cta_button()
END_cardbg = card(900, 600, fill=(250, 244, 232, 240), r=48)

# ---------------------------------------------------------------- fx helpers
random.seed(7)
def sparkle_img(size, color=(255, 250, 230)):
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    pts = [(c, 0), (c + s * 0.09, c - s * 0.09), (s, c), (c + s * 0.09, c + s * 0.09),
           (c, s), (c - s * 0.09, c + s * 0.09), (0, c), (c - s * 0.09, c - s * 0.09)]
    d.polygon(pts, fill=color + (255,))
    glow = im.filter(ImageFilter.GaussianBlur(s * 0.12))
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.alpha_composite(glow); out.alpha_composite(glow); out.alpha_composite(im)
    return out
SPARK = sparkle_img(120)

def sparkles(frame, lt, spots, period=0.9):
    for (x, y, sz, ph) in spots:
        k = (lt / period + ph) % 1.0
        a = math.sin(k * math.pi) ** 2
        place(frame, SPARK, x, y, sz * (0.5 + 0.6 * a), a, rot=k * 90)

def shine_sweep(arr, p, width=260, strength=0.35):
    """diagonal light band, p in 0..1"""
    if p <= 0 or p >= 1:
        return arr
    yy, xx = np.mgrid[0:H:4, 0:W:4]
    pos = (xx + yy * 0.45)
    c = -300 + p * (W + H * 0.45 + 600)
    band = np.exp(-((pos - c) / (width / 2)) ** 2) * strength
    band = np.kron(band, np.ones((4, 4)))[:H, :W]
    return np.clip(arr + band[..., None] * 255 * np.array([1.0, 0.96, 0.86]), 0, 255)

def zoom_frame(img, z, ay):
    if z <= 1.0001:
        return img
    cw, ch = W / z, H / z
    x0 = (W - cw) / 2
    y0 = clamp((H - ch) * ay, 0, H - ch)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

# ---------------------------------------------------------------- frame source
VF = ("hflip,scale=1080:1920:flags=lanczos,"
      "eq=contrast=1.07:saturation=1.10:brightness=0.012:gamma=1.02,"
      "colorbalance=rs=0.035:gs=0.01:bs=-0.04:rh=0.02:bh=-0.02,"
      "unsharp=5:5:0.7")

def frames_for(seg):
    vf = f"{VF},setpts=(PTS-STARTPTS)/{seg['sp']},fps={FPS}"
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{seg['a']:.3f}", "-t", f"{seg['b']-seg['a']+0.2:.3f}",
           "-i", SRC, "-vf", vf, "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = 0; last = None
    while n < seg["nf"]:
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        last = buf; n += 1
        yield Image.frombuffer("RGB", (W, H), buf)
    while n < seg["nf"]:  # pad if short
        n += 1; yield Image.frombuffer("RGB", (W, H), last)
    p.stdout.close(); p.wait()

# ---------------------------------------------------------------- overlays per segment
TXT_Y = 1130   # body text centre (above Reels/Feed bottom UI)

def overlay(seg, fr, lt, gt):
    k = seg["kind"]; d = seg["nf"] / FPS
    if k == "h1":
        pop(fr, HOOK1, lt - 0.03, W / 2, 760, rot=-2)
        pop(fr, HOOK1b, lt - 0.38, W / 2 + 120, 900, rot=3)
        sparkles(fr, lt, [(640, 1040, 0.9, 0.0), (420, 1250, 0.6, 0.4), (760, 1350, 0.7, 0.7)], 0.7)
    elif k == "h2":
        pop(fr, HOOK2a, lt - 0.02, W / 2, 640)
        pop(fr, HOOK2b, lt - 0.16, W / 2, 790, rot=-3)
    elif k == "h3":
        pop(fr, HOOK3, lt - 0.02, W / 2, 760)
    elif k == "b1":
        slide(fr, B1, lt - 0.05, W / 2, TXT_Y, d - 0.05)
        slide(fr, B1s, lt - 0.45, W / 2, TXT_Y + 120, d - 0.45)
    elif k == "b2":
        if lt > 0.15:
            kk = ease_out((lt - 0.15) / 0.35); a = kk
            if lt > d - 0.2: a *= (d - lt) / 0.2
            cy = 1420 + (1 - kk) * 80
            place(fr, B2card, W / 2, cy, 1, a); place(fr, B2a, W / 2, cy - 4, 1, a)
        pop(fr, B2tag_line, lt - 1.4, W / 2, 1420 - B2card.height / 2 - 50, dur=d - 1.4)
    elif k == "b3":
        pop(fr, B3s, lt - 0.2, W / 2, TXT_Y - 30, dur=d - 0.2, rot=-2)
        pop(fr, B3, lt - 1.6, W / 2, TXT_Y + 90, dur=d - 1.6, rot=2)
    elif k == "b4":
        slide(fr, B4, lt - 0.05, W / 2, TXT_Y - 40, d - 0.05)
        pop(fr, B4b, lt - 1.5, W / 2, TXT_Y + 90, dur=d - 1.5, rot=-2)
        if lt > 1.5:
            sparkles(fr, lt, [(380, 820, 0.7, 0.1), (700, 700, 0.55, 0.5), (560, 980, 0.6, 0.8)], 0.8)
    elif k == "b5":
        step = d / 3
        for i, L in enumerate(B5):
            if lt >= i * step:
                pop(fr, L, lt - i * step, W / 2, 980 + i * 135, dur=d - i * step)
        sparkles(fr, lt, [(300, 700, 0.8, 0.0), (800, 640, 0.6, 0.33), (560, 520, 0.5, 0.66)], 0.8)
    elif k == "end":
        # card slides up from bottom
        kk = ease_out((lt - 0.1) / 0.45)
        cy = 1250 + (1 - kk) * 700
        place(fr, END_cardbg, W / 2, cy, 1, clamp(kk * 1.2))
        place(fr, END_brand, W / 2, cy - 225, 1, kk)
        place(fr, END_title, W / 2, cy - 85, 1, kk)
        place(fr, END_sub, W / 2, cy + 50, 1, kk)
        if lt > 0.6:
            pl = 1.0 + 0.045 * math.sin((lt - 0.6) * 2 * math.pi * 1.4)
            pop(fr, CTA, lt - 0.6, W / 2, cy + 175, rot=0) if lt < 0.85 else place(fr, CTA, W / 2, cy + 175, pl, 1)
        # finger tap cue
        if lt > 1.2:
            bob = 12 * math.sin((lt - 1.2) * 2 * math.pi * 1.4)
            arr_l = text_block([("▼", XBOLD, 64, GOLD, None, 0)])
            place(fr, arr_l, W / 2, cy + 310 + bob, 1, clamp((lt - 1.2) / 0.3))

# ---------------------------------------------------------------- render video
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                        os.path.join(WORK, "video_only.mp4")], stdin=subprocess.PIPE)
gf = 0
for si, seg in enumerate(EDL):
    n = seg["nf"]
    for i, img in enumerate(frames_for(seg)):
        lt = i / FPS; p = i / max(1, n - 1)
        z0, z1 = seg["z"]
        zp = ease_out(p) if seg["kind"].startswith("h") else ease_inout(p)
        z = z0 + (z1 - z0) * zp
        # micro camera shake on hook entrances
        if seg["kind"].startswith("h") and lt < 0.12:
            z += 0.03 * (1 - lt / 0.12)
        img = zoom_frame(img, z, seg["ay"])
        arr = None
        if seg["kind"] == "h1":
            arr = shine_sweep(np.asarray(img, dtype=np.float32), (lt - 0.15) / 0.75)
        if seg["kind"] == "end":
            # soften background under the card
            img = img.filter(ImageFilter.GaussianBlur(min(10, lt * 14)))
        # white flash on hook cuts + first body cut
        fl = 0.0
        if seg["kind"] in ("h1", "h2", "h3", "b1") and lt < 0.1:
            fl = (1 - lt / 0.1) * (0.85 if seg["kind"] == "h1" else 0.55)
        if fl > 0:
            if arr is None: arr = np.asarray(img, dtype=np.float32)
            arr = arr + (255 - arr) * fl
        if arr is not None:
            img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        fr = img.convert("RGBA")
        overlay(seg, fr, lt, gf / FPS)
        # thin progress bar (top) - retention cue
        d = ImageDraw.Draw(fr)
        d.rectangle([0, 0, int(W * (gf + 1) / TOTAL_F), 9], fill=GOLD + (255,))
        enc.stdin.write(fr.convert("RGB").tobytes())
        gf += 1
    print(f"rendered {seg['kind']} ({gf}/{TOTAL_F})", flush=True)
enc.stdin.close(); enc.wait()

# ---------------------------------------------------------------- audio
def read_audio(a, b, sp):
    af = f"atempo={sp}" if abs(sp - 1) > 1e-3 else "anull"
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b-a:.3f}", "-i", SRC,
                          "-vn", "-af", af, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()

N = int(round(TOTAL * SR)) + SR
voice = np.zeros((N, 2), np.float32)
sfx = np.zeros((N, 2), np.float32)
for seg in EDL:
    if not seg["voice"]:
        continue
    x = read_audio(seg["a"], seg["b"], seg["sp"])
    L = min(len(x), int(seg["nf"] / FPS * SR))
    x = x[:L]
    fi = int(0.012 * SR); fo = int(0.02 * SR)
    if seg["kind"] == "end":
        fi = int(0.15 * SR); fo = int(1.2 * SR)
    x[:fi] *= np.linspace(0, 1, fi)[:, None]
    x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    s0 = int(seg["t0"] * SR)
    voice[s0:s0 + L] += x

rng = np.random.default_rng(3)
def onepole_lp(x, cut):
    y = np.zeros_like(x); acc = 0.0
    for i in range(len(x)):
        a = 1 - math.exp(-2 * math.pi * cut[i] / SR)
        acc += a * (x[i] - acc); y[i] = acc
    return y
def add(sig, t, gain=1.0, pan=0.0):
    s0 = int(t * SR); e = min(N, s0 + len(sig))
    sig = sig[:e - s0] * gain
    sfx[s0:e, 0] += sig * (1 - max(0, pan)); sfx[s0:e, 1] += sig * (1 + min(0, pan))
def whoosh(dur=0.35, f0=300, f1=6000):
    n = int(dur * SR); tt = np.linspace(0, 1, n)
    cut = f0 * (f1 / f0) ** (np.sin(tt * math.pi / 2))
    x = onepole_lp(rng.standard_normal(n), cut)
    x = x - onepole_lp(x, np.full(n, 200.0))
    env = np.sin(np.pi * tt) ** 1.5
    return (x * env / (np.abs(x).max() + 1e-9)).astype(np.float32)
def impact(dur=0.7, f0=110, f1=38):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt * 18)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-tt * 5.5)
    click = rng.standard_normal(n) * np.exp(-tt * 120) * 0.5
    return np.tanh((body + click) * 1.6).astype(np.float32) * 0.9
def pop_sfx(f0=900, f1=420, dur=0.08):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt * 60)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 45)).astype(np.float32)
def shimmer(dur=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for k in range(14):
        st = rng.uniform(0, dur * 0.6); f = rng.uniform(2800, 7000)
        m = tt >= st
        x[m] += np.sin(2 * np.pi * f * (tt[m] - st)) * np.exp(-(tt[m] - st) * 9) * rng.uniform(0.3, 1)
    return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)
def riser(dur):
    n = int(dur * SR); tt = np.linspace(0, 1, n)
    x = onepole_lp(rng.standard_normal(n), 200 * (40 ** tt))
    tone = np.sin(2 * np.pi * np.cumsum(180 * (4 ** tt)) / SR) * 0.25
    return ((x / (np.abs(x).max() + 1e-9) + tone) * tt ** 2).astype(np.float32)

h1, h2, h3, b1 = EDL[0]["t0"], EDL[1]["t0"], EDL[2]["t0"], EDL[3]["t0"]
add(impact(), 0.0, 0.85)
add(shimmer(1.0), 0.12, 0.22, 0.3)
add(pop_sfx(), 0.38, 0.35)
add(whoosh(0.32), h2 - 0.16, 0.45, -0.4)
add(impact(0.4, 160, 60), h2, 0.5)
add(pop_sfx(1100, 500), h2 + 0.16, 0.35)
add(whoosh(0.32), h3 - 0.16, 0.45, 0.4)
add(impact(0.4, 150, 55), h3, 0.5)
add(riser(b1 - h3), h3, 0.16)
add(impact(0.9, 90, 32), b1, 0.6)
for seg in EDL[4:]:
    add(whoosh(0.26, 500, 7000), seg["t0"] - 0.13, 0.22, rng.uniform(-0.5, 0.5))
add(shimmer(1.2), EDL[6]["t0"] + 1.4, 0.16)
add(shimmer(1.2), EDL[7]["t0"] + 0.1, 0.16)
add(pop_sfx(700, 350, 0.1), EDL[8]["t0"] + 0.6, 0.35)

mix = voice + sfx
mix = mix[:int(TOTAL * SR)]
mix.astype(np.float32).tofile(os.path.join(WORK, "mix.f32"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, "video_only.mp4"),
                "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", os.path.join(WORK, "mix.f32"),
                "-af", "highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.0:LRA=9",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT)
