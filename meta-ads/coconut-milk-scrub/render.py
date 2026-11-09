#!/usr/bin/env python3
"""Meta ad v2 (Arabic, premium-minimal): Laurus Aroma Coconut Milk Body Scrub. 1080x1920 @30fps."""
import subprocess, sys, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, "fonts")
W, H, FPS, SR = 1080, 1920, 30, 44100

AR_XB = os.path.join(FONTS, "almarai-arabic-800-normal.woff")
AR_B = os.path.join(FONTS, "almarai-arabic-700-normal.woff")
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"

CREAM = (250, 245, 236)
INK = (30, 25, 20)
GOLD = (190, 150, 80)

SP = 1.08  # gentle pace-up of her real speech (pitch preserved)
# One continuous story: her opening before/after line + one unbroken demo take, then end card.
EDL = [
    dict(a=0.00, b=2.35, sp=SP, voice=True, kind="hook"),
    dict(a=33.07, b=52.22, sp=SP, voice=True, kind="demo"),
    dict(a=136.40, b=139.60, sp=1.0, voice=False, kind="end"),
]
t = 0.0
for s in EDL:
    s["nf"] = int(round((s["b"] - s["a"]) / s["sp"] * FPS)); s["t0"] = t; t += s["nf"] / FPS
TOTAL, TOTAL_F = t, int(round(t * FPS))
print(f"total {TOTAL:.2f}s")

def src_to_demo(ts):  # source second -> local seconds inside demo segment
    return (ts - EDL[1]["a"]) / SP

clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ text
_fc = {}
def F(p, s):
    if (p, s) not in _fc:
        _fc[(p, s)] = ImageFont.truetype(p, s, layout_engine=ImageFont.Layout.RAQM)
    return _fc[(p, s)]

def line_img(txt, fp, size, fill=CREAM, ar=True):
    f = F(fp, size)
    kw = dict(direction="rtl", language="ar") if ar else {}
    bb = f.getbbox(txt, **kw)
    im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 24), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], 12 - bb[1]), txt, font=f, fill=fill, **kw)
    return im

def stack(lines, gap=14, shadow=True):
    imgs = [line_img(*l) for l in lines]
    w = max(i.width for i in imgs); h = sum(i.height for i in imgs) + gap * (len(imgs) - 1)
    body = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for i in imgs:
        body.alpha_composite(i, ((w - i.width) // 2, y)); y += i.height + gap
    if w > 940:
        body = body.resize((940, int(h * 940 / w)), Image.LANCZOS); w, h = body.size
    if not shadow:
        return body
    pad = 50
    out = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = body.split()[3]
    sh = Image.new("RGBA", body.size, (0, 0, 0, 255)); sh.putalpha(a.point(lambda v: int(v * 0.55)))
    soft = Image.new("RGBA", out.size, (0, 0, 0, 0)); soft.alpha_composite(sh, (pad, pad + 4))
    soft = soft.filter(ImageFilter.GaussianBlur(12))
    out.alpha_composite(soft); out.alpha_composite(soft)
    out.alpha_composite(body, (pad, pad))
    return out

def place(fr, L, cx, cy, sc=1.0, al=1.0):
    if al <= 0.01: return
    if abs(sc - 1) > 1e-3:
        L = L.resize((max(1, int(L.width * sc)), max(1, int(L.height * sc))), Image.BICUBIC)
    if al < 1:
        L = L.copy(); L.putalpha(L.split()[3].point(lambda v: int(v * al)))
    fr.alpha_composite(L, (int(cx - L.width / 2), int(cy - L.height / 2)))

def rise(fr, L, lt, cx, cy, dur, inn=0.35, out=0.25, dy=36):
    """premium entrance: fade + small rise + slight settle; fade out"""
    if lt < 0 or lt > dur: return
    k = ease_out(lt / inn); a = k
    if lt > dur - out: a *= clamp((dur - lt) / out)
    place(fr, L, cx, cy + (1 - k) * dy, 0.96 + 0.04 * k, a)

def label(txt, size=88):
    """before/after tag: text + thin underline"""
    t = line_img(txt, AR_XB, size)
    im = Image.new("RGBA", (t.width + 20, t.height + 26), (0, 0, 0, 0))
    im.alpha_composite(t, (10, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([im.width / 2 - 34, t.height + 10, im.width / 2 + 34, t.height + 16], 3, fill=CREAM)
    pad = 40
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 255)); sh.putalpha(im.split()[3].point(lambda v: int(v * 0.6)))
    s2 = Image.new("RGBA", out.size, (0, 0, 0, 0)); s2.alpha_composite(sh, (pad, pad + 3))
    s2 = s2.filter(ImageFilter.GaussianBlur(10)); out.alpha_composite(s2); out.alpha_composite(s2)
    out.alpha_composite(im, (pad, pad)); return out

# copy (Levantine Arabic, matches a Lebanese creator; benefits are what the footage shows + label facts)
HOOK_HEAD = stack([("إيد وحدة بس عليها السكراب", AR_XB, 70), ("شوفي الفرق", AR_XB, 120)], gap=6)
LBL_BEFORE = label("قبل")
LBL_AFTER = label("بعد")

CAPS = [  # (src_start, src_end, layer)
    (33.07, 36.40, stack([("سكراب حليب جوز الهند", AR_XB, 86), ("مع معادن البحر الميت", AR_B, 56)], gap=4)),
    (36.40, 41.20, stack([("قوامه بيدوب على البشرة", AR_XB, 86)])),
    (41.20, 46.40, stack([("بيقشّر وبيرطّب", AR_XB, 92), ("بخطوة وحدة", AR_B, 60)], gap=4)),
    (46.40, 52.22, stack([("والنتيجة؟", AR_B, 64), ("نعومة ولمعة طبيعية", AR_XB, 92)], gap=2)),
]
# punch-in "cuts" at her natural pauses (audio untouched): (src_time, zoom)
ZOOMS = [(33.07, 1.10), (34.90, 1.00), (36.40, 1.12), (41.20, 1.00), (46.40, 1.10), (47.50, 1.18)]

# end card
def end_card():
    w, h = 880, 560
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 44, fill=(250, 245, 236, 242))
    def c(L, y): im.alpha_composite(L, ((w - L.width) // 2, y))
    brand = line_img("LAURUS  AROMA", SERIF, 40, (140, 108, 56), ar=False); c(brand, 52)
    d.line([w / 2 - 60, 120, w / 2 + 60, 120], fill=GOLD + (255,), width=2)
    c(line_img("سكراب حليب جوز الهند", AR_XB, 74, INK), 148)
    c(line_img("مع معادن البحر الميت  •  مثالي للبشرة الجافة", AR_B, 38, (110, 90, 60)), 262)
    return im
CARD = end_card()
def button():
    t = line_img("اطلبيه الآن", AR_XB, 64, CREAM)
    w, h = t.width + 150, t.height + 50
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=INK + (255,))
    im.alpha_composite(t, ((w - t.width) // 2, (h - t.height) // 2 + 2)); return im
BTN = button()

# ------------------------------------------------------------------ video
VF = ("hflip,scale=1080:1920:flags=lanczos,"
      "eq=contrast=1.05:saturation=1.06:brightness=0.015:gamma=1.03,"
      "colorbalance=rs=0.025:bs=-0.03:rh=0.015:bh=-0.015,unsharp=5:5:0.55")

def frames(seg):
    vf = f"{VF},setpts=(PTS-STARTPTS)/{seg['sp']},fps={FPS}"
    p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-ss", f"{seg['a']:.3f}", "-t", f"{seg['b']-seg['a']+0.3:.3f}",
                          "-i", SRC, "-vf", vf, "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    n, last = 0, None
    while n < seg["nf"]:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        last = b; n += 1; yield Image.frombuffer("RGB", (W, H), b)
    while n < seg["nf"]:
        n += 1; yield Image.frombuffer("RGB", (W, H), last)
    p.kill(); p.wait()

def zoom(img, z, ax=0.5, ay=0.5):
    if z <= 1.0005: return img
    cw, ch = W / z, H / z
    x0 = clamp((W - cw) * ax, 0, W - cw); y0 = clamp((H - ch) * ay, 0, H - ch)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

def demo_zoom(lt):
    z = 1.0
    for st, zz in ZOOMS:
        if lt >= src_to_demo(st): z = zz
    # slow push for life
    return z + 0.012 * math.sin(lt * 0.6)

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                        "-pix_fmt", "yuv420p", os.path.join(HERE, "v2_video.mp4")], stdin=subprocess.PIPE)
for seg in EDL:
    d = seg["nf"] / FPS
    for i, img in enumerate(frames(seg)):
        lt = i / FPS
        if seg["kind"] == "hook":
            # open tight on the glossy (treated) hand, pull out to reveal both hands
            k = ease_io(lt / 0.75)
            z = 1.75 + (1.0 - 1.75) * k
            img = zoom(img, z, ax=0.40 + (0.5 - 0.40) * k, ay=0.36 + (0.5 - 0.36) * k)
            fr = img.convert("RGBA")
            rise(fr, HOOK_HEAD, lt, W / 2, 1255, d + 1, inn=0.3, dy=24)
            rise(fr, LBL_BEFORE, lt - 0.75, 150, 720, d, inn=0.3, dy=20)
            rise(fr, LBL_AFTER, lt - 0.95, 455, 720, d, inn=0.3, dy=20)
        elif seg["kind"] == "demo":
            img = zoom(img, demo_zoom(lt), 0.5, 0.48)
            fr = img.convert("RGBA")
            for a, b, L in CAPS:
                s0, s1 = src_to_demo(a), src_to_demo(b)
                rise(fr, L, lt - s0 - 0.08, W / 2, 1250, s1 - s0 - 0.1)
        else:
            img = zoom(img, 1.02 + 0.04 * ease_io(lt / d), 0.5, 0.45)
            img = img.filter(ImageFilter.GaussianBlur(min(9, lt * 18)))
            fr = img.convert("RGBA")
            dim = Image.new("RGBA", (W, H), (20, 14, 8, int(min(70, lt * 140))))
            fr.alpha_composite(dim)
            k = ease_out((lt - 0.05) / 0.5)
            cy = 1080 + (1 - k) * 60
            place(fr, CARD, W / 2, cy, 0.97 + 0.03 * k, clamp(k * 1.1))
            if lt > 0.45:
                kb = ease_out((lt - 0.45) / 0.35)
                pulse = 1 + 0.03 * math.sin(max(0, lt - 0.8) * 2 * math.pi * 1.2)
                place(fr, BTN, W / 2, cy + 175, (0.9 + 0.1 * kb) * pulse, kb)
        enc.stdin.write(fr.convert("RGB").tobytes())
    print("rendered", seg["kind"], flush=True)
enc.stdin.close(); enc.wait()

# ------------------------------------------------------------------ audio: her voice first, minimal sound design
N = int(TOTAL * SR) + SR
mix = np.zeros((N, 2), np.float32)
for seg in EDL:
    if not seg["voice"]: continue
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{seg['a']:.3f}", "-t", f"{seg['b']-seg['a']:.3f}", "-i", SRC,
                          "-vn", "-af", f"atempo={seg['sp']}", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()[: int(seg["nf"] / FPS * SR)]
    fi, fo = int(0.01 * SR), int(0.04 * SR)
    x[:fi] *= np.linspace(0, 1, fi)[:, None]; x[-fo:] *= np.linspace(1, 0, fo)[:, None]
    s0 = int(seg["t0"] * SR); mix[s0:s0 + len(x)] += x

rng = np.random.default_rng(5)
def add(sig, t, g):
    s0 = int(t * SR); e = min(N, s0 + len(sig)); mix[s0:e] += (sig[: e - s0] * g)[:, None]
def lp(x, cut):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        a = 1 - math.exp(-2 * math.pi * cut[i] / SR); acc += a * (x[i] - acc); y[i] = acc
    return y
def whoosh(dur, f0=250, f1=5000):
    n = int(dur * SR); tt = np.linspace(0, 1, n)
    x = lp(rng.standard_normal(n), f0 * (f1 / f0) ** np.sin(tt * math.pi / 2))
    x -= lp(x, np.full(n, 180.0)); x *= np.sin(np.pi * tt) ** 1.6
    return (x / (abs(x).max() + 1e-9)).astype(np.float32)
def chime(dur=1.6):
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for f, g, dl in [(1318.5, 1, 0), (1975.5, .7, .07), (2637, .5, .14)]:
        m = tt >= dl; x[m] += g * np.sin(2 * np.pi * f * (tt[m] - dl)) * np.exp(-(tt[m] - dl) * 3.2)
    return (x / abs(x).max()).astype(np.float32)
def soft_tick(f=1500, dur=0.05):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 90)).astype(np.float32)

add(whoosh(0.7, 200, 4000), 0.0, 0.12)            # reveal pull-out
add(soft_tick(1400), 0.75, 0.10); add(soft_tick(1700), 0.95, 0.10)   # before / after tags
add(whoosh(0.45), EDL[2]["t0"] - 0.22, 0.14)      # into end card
add(chime(), EDL[2]["t0"] + 0.45, 0.07)           # button
mix = mix[: int(TOTAL * SR)]
mix.tofile(os.path.join(HERE, "v2_mix.f32"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "v2_video.mp4"),
                "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", os.path.join(HERE, "v2_mix.f32"),
                "-af", "highpass=f=70,loudnorm=I=-14:TP=-1.0:LRA=9",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
                "-shortest", OUT], check=True)
print("done", OUT)
