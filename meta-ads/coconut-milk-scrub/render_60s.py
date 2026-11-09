#!/usr/bin/env python3
"""Meta ad v4 (Arabic, ~60s): Laurus Aroma scrub + body butter routine.
Cut only on word boundaries found by transcription (whisper large-v3-turbo); her speech is never trimmed.
Graphics are synced to the words she says instead of full subtitles."""
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
CREAM, INK, GOLD = (250, 245, 236), (30, 25, 20), (201, 162, 92)

# ------------------------------------------------------------------ edit list (source seconds, her words)
EDL = [  # every boundary sits in the middle of a real silence (>=140ms) at the end of a sentence
    dict(k="hook",  a=34.89,  b=37.34,  z=(1.55, 1.18)),  # "وعمركن شفتوا سكراب بهالقوام؟"
    dict(k="story", a=3.45,   b=31.80,  z=(1.00, 1.04)),  # problem -> 2-step routine -> Laurus Aroma -> coconut milk (one unbroken take)
    dict(k="proof", a=114.36, b=141.30, z=(1.04, 1.00)),  # hands comparison -> her full CTA to the last word (one unbroken take)
    dict(k="end",   a=139.04, b=141.30, z=(1.06, 1.08), mute=True),
]
# punch-ins at her natural pauses inside the long takes (source time, zoom)
PUNCH = {"story": [(11.52, 1.08), (15.45, 1.00), (20.02, 1.10), (24.92, 1.00), (28.0, 1.08)],
         "proof": [(116.83, 1.00), (119.0, 1.08), (122.14, 1.00), (126.66, 1.10), (131.42, 1.00), (135.19, 1.07)]}
t = 0.0
for s in EDL:
    s["nf"] = int(round((s["b"] - s["a"]) * FPS)); s["t0"] = t; t += s["nf"] / FPS
TOTAL = t
print(f"total {TOTAL:.2f}s")

clamp = lambda x, a=0.0, b=1.0: max(a, min(b, x))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def bo(x, s=1.7): x = clamp(x) - 1; return x * x * ((s + 1) * x + s) + 1

# ------------------------------------------------------------------ typography / graphics primitives
_fc = {}
def F(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s, layout_engine=ImageFont.Layout.RAQM)
    return _fc[(p, s)]

def txt(s, fp, size, fill=CREAM, ar=True):
    f = F(fp, size); kw = dict(direction="rtl", language="ar") if ar else {}
    bb = f.getbbox(s, **kw)
    im = Image.new("RGBA", (bb[2] - bb[0] + 20, bb[3] - bb[1] + 24), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - bb[0], 12 - bb[1]), s, font=f, fill=fill, **kw); return im

def shadowed(body, alpha=0.55, blur=12, off=4):
    pad = 48
    out = Image.new("RGBA", (body.width + 2 * pad, body.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", body.size, (0, 0, 0, 255)); sh.putalpha(body.split()[3].point(lambda v: int(v * alpha)))
    s2 = Image.new("RGBA", out.size, (0, 0, 0, 0)); s2.alpha_composite(sh, (pad, pad + off))
    s2 = s2.filter(ImageFilter.GaussianBlur(blur)); out.alpha_composite(s2); out.alpha_composite(s2)
    out.alpha_composite(body, (pad, pad)); return out

def big(s, size=104, fill=CREAM, fp=None):
    return shadowed(txt(s, fp or AR_XB, size, fill))

def pill(s, size=58, fg=INK, bg=CREAM + (240,), padx=40, pady=18, icon=None):
    t = txt(s, AR_XB, size, fg)
    iw = 0 if icon is None else icon.width + 14
    w, h = t.width + 2 * padx + iw, t.height + 2 * pady
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=bg)
    im.alpha_composite(t, (padx, pady + 2))
    if icon is not None: im.alpha_composite(icon, (padx + t.width + 8, (h - icon.height) // 2))
    return shadowed(im, 0.35, 16, 6)

def coconut_icon(d=64):
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    g.ellipse([2, 2, d - 3, d - 3], fill=(120, 82, 48, 255))
    g.ellipse([10, 10, d - 11, d - 11], fill=(252, 249, 240, 255))
    g.ellipse([d * .40, d * .40, d * .60, d * .60], fill=(235, 228, 212, 255))
    return im

def step_card(num, label, active=True, w=330, h=150):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    g.rounded_rectangle([0, 0, w - 1, h - 1], 34, fill=(CREAM + (242,)) if active else (250, 245, 236, 150))
    g.ellipse([w - 92, 36, w - 22, 106], fill=GOLD + (255,))
    n = txt(num, AR_XB, 46, CREAM); im.alpha_composite(n, (w - 57 - n.width // 2, 71 - n.height // 2))
    l = txt(label, AR_XB, 56, INK); im.alpha_composite(l, (w - 110 - l.width, (h - l.height) // 2 + 2))
    return shadowed(im, 0.35, 16, 6)

def brand_plate(sub=None):
    b = txt("LAURUS  AROMA", SERIF, 58, CREAM, ar=False)
    w = max(b.width, 420) + 40
    im = Image.new("RGBA", (w, b.height + (80 if sub else 30)), (0, 0, 0, 0))
    im.alpha_composite(b, ((w - b.width) // 2, 0))
    ImageDraw.Draw(im).line([w / 2 - 90, b.height + 8, w / 2 + 90, b.height + 8], fill=GOLD + (255,), width=3)
    if sub:
        s = txt(sub, AR_B, 40, CREAM); im = im.resize(im.size)  # keep
        canvas = Image.new("RGBA", (max(w, s.width + 20), im.height + s.height - 10), (0, 0, 0, 0))
        canvas.alpha_composite(im, ((canvas.width - w) // 2, 0))
        canvas.alpha_composite(s, ((canvas.width - s.width) // 2, b.height + 22)); im = canvas
    return shadowed(im, 0.6, 12, 3)

def place(fr, L, cx, cy, sc=1.0, al=1.0, rot=0.0):
    if al <= 0.01 or sc <= 0.01: return
    if abs(sc - 1) > 1e-3: L = L.resize((max(1, int(L.width * sc)), max(1, int(L.height * sc))), Image.BICUBIC)
    if rot: L = L.rotate(rot, Image.BICUBIC, expand=True)
    if al < 1: L = L.copy(); L.putalpha(L.split()[3].point(lambda v: int(v * al)))
    fr.alpha_composite(L, (int(cx - L.width / 2), int(cy - L.height / 2)))

def show(fr, L, lt, t_in, t_out, cx, cy, mode="rise", dy=34):
    """t_in/t_out in segment-local seconds"""
    if lt < t_in or lt > t_out: return
    x = lt - t_in
    a = clamp(x / 0.18) * clamp((t_out - lt) / 0.22)
    if mode == "pop":
        place(fr, L, cx, cy, 0.6 + 0.4 * bo(x / 0.32), a)
    else:
        k = eo(x / 0.38); place(fr, L, cx, cy + (1 - k) * dy, 0.97 + 0.03 * k, a)

def draw_ring(fr, cx, cy, r, p, width=9, col=CREAM):
    """hand-drawn style ring stroke, p = 0..1 drawn"""
    if p <= 0: return
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(lay)
    end = -100 + 380 * eo(p)
    pts = []
    for a in np.linspace(-100, end, 90):
        rr = r * (1 + 0.04 * math.sin(math.radians(a) * 3))
        pts.append((cx + rr * math.cos(math.radians(a)), cy + rr * 0.86 * math.sin(math.radians(a))))
    g.line(pts, fill=col + (255,), width=width, joint="curve")
    sh = lay.filter(ImageFilter.GaussianBlur(6)); fr.alpha_composite(sh); fr.alpha_composite(lay)

def draw_vline(fr, x, y0, y1, p, col=GOLD, width=6):
    if p <= 0: return
    g = ImageDraw.Draw(fr); ym = y0 + (y1 - y0) * eo(p)
    g.line([(x, y0), (x, ym)], fill=col + (255,), width=width)

def strike(fr, L, cx, cy, p):
    place(fr, L, cx, cy)
    if p > 0:
        g = ImageDraw.Draw(fr); w = (L.width - 96) * eo(p)
        x0 = cx + (L.width - 96) / 2  # RTL: strike from right to left
        g.line([(x0, cy + 6), (x0 - w, cy + 6)], fill=GOLD + (255,), width=12)

def light_leak(arr, p, strength=0.28):
    """warm soft glow drifting across (hook)"""
    if p <= 0 or p >= 1: return arr
    yy, xx = np.mgrid[0:H:8, 0:W:8].astype(np.float32)
    cx = -200 + p * (W + 400); cy = 500 + 300 * p
    g = np.exp(-(((xx - cx) / 520) ** 2 + ((yy - cy) / 760) ** 2)) * strength * math.sin(p * math.pi)
    g = np.kron(g, np.ones((8, 8), np.float32))[:H, :W]
    return np.clip(arr + g[..., None] * np.array([255, 200, 140], np.float32), 0, 255)

# ------------------------------------------------------------------ graphic assets
HOOK_L1 = big("عمركن شفتوا", 96)
HOOK_L2 = big("سكراب بهالقوام؟", 108)
LBL_BEFORE = big("قبل", 92); LBL_AFTER = big("بعد", 92, GOLD)
CHIP_ROUGH = pill("خشونة الجسم"); CHIP_KP = pill("جلد الوزة"); CHIP_LASER = pill("بعد الشيفينغ أو الليزر", 50)
STEP1 = step_card("١", "تقشير"); STEP2 = step_card("٢", "ترطيب"); STEP2_IDLE = step_card("٢", "ترطيب", False)
ARROW = shadowed(txt("←", "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", 80, ar=False))
BRAND = brand_plate()
COCO = pill("حليب جوز الهند", 62, icon=coconut_icon(60))
ROUGH = big("ملمس خشن", 112)
FORGET = big("انسيه", 96, GOLD)
STEP2_BUTTER = step_card("٢", "زبدة الجسم", w=420)
LBL_TREATED = pill("سكراب + زبدة", 50, bg=GOLD + (245,))
LBL_BARE = pill("بدون", 50, fg=CREAM, bg=(20, 16, 12, 170))
ROUTINE = pill("سكراب حليب جوز الهند  +  زبدة الجسم", 46)
BRAND_SUB = brand_plate()

def end_card():
    w, h = 880, 520
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); g = ImageDraw.Draw(im)
    g.rounded_rectangle([0, 0, w - 1, h - 1], 44, fill=(250, 245, 236, 244))
    def c(L, y): im.alpha_composite(L, ((w - L.width) // 2, y))
    c(txt("LAURUS  AROMA", SERIF, 42, (140, 108, 56), ar=False), 46)
    g.line([w / 2 - 60, 112, w / 2 + 60, 112], fill=GOLD + (255,), width=2)
    c(txt("روتين النعومة", AR_XB, 80, INK), 138)
    c(txt("سكراب حليب جوز الهند + زبدة الجسم", AR_B, 42, (110, 90, 60)), 250)
    b = txt("اطلبيه الآن", AR_XB, 62, CREAM)
    bw, bh = b.width + 140, b.height + 46
    btn = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    ImageDraw.Draw(btn).rounded_rectangle([0, 0, bw - 1, bh - 1], bh // 2, fill=INK + (255,))
    btn.alpha_composite(b, ((bw - b.width) // 2, (bh - b.height) // 2 + 2))
    return shadowed(im, 0.35, 20, 8), shadowed(btn, 0.4, 14, 6)
CARD, BTN = end_card()

# ------------------------------------------------------------------ per-segment graphics (times = source seconds -> local)
def overlay(seg, fr, lt):
    k, A = seg["k"], seg["a"]; d = seg["nf"] / FPS
    L = lambda ts: ts - A
    if k == "hook":
        show(fr, HOOK_L1, lt, L(35.05), 99, W / 2, 1180, "pop")
        show(fr, HOOK_L2, lt, L(35.95), 99, W / 2, 1330, "pop")
    elif k == "story":
        # "كتير من البنات بتعاني من الخشونة بالجسم، خصوصاً جلد الوزة، وأساساً لو بتعمل shaving... قبل أو بعد الليزر"
        show(fr, CHIP_ROUGH, lt, L(4.45), L(11.3), W / 2, 1150, "pop")
        show(fr, CHIP_KP, lt, L(6.75), L(11.3), W / 2, 1290, "pop")
        show(fr, CHIP_LASER, lt, L(9.2), L(11.3), W / 2, 1430, "pop")
        # "أولاً بدك تقشري، بعدين ترطبي"
        show(fr, STEP1, lt, L(15.45), L(19.85), W / 2 + 190, 1220, "pop")
        show(fr, ARROW, lt, L(16.2), L(19.85), W / 2, 1220)
        show(fr, STEP2, lt, L(16.4), L(19.85), W / 2 - 190, 1220, "pop")
        # "منتجات Laurus Aroma"
        show(fr, BRAND, lt, L(20.15), L(24.8), W / 2, 1220)
        # "...إنو بحليب جوز الهند، شوفولي ملمسو"
        show(fr, COCO, lt, L(29.1), d, W / 2, 1230, "pop")
    elif k == "proof":
        # "طلعوا إيدي، هاي عملتلها سكراب وحطيتلها زبدة، وإيدي هاي... واضح قديش في فرق بيناتهن"
        draw_vline(fr, 300, 260, 1100, (lt - L(116.9)) / 0.5)
        show(fr, LBL_TREATED, lt, L(115.2), L(122.1), 640, 1240, "pop")
        show(fr, LBL_BARE, lt, L(117.4), L(122.1), 170, 1240, "pop")
        # "إنتي بس ناقصك هالمنتجين"
        show(fr, ROUTINE, lt, L(133.4), L(135.6), W / 2, 1250, "pop")
        # "ولا تنسي تاخديهن من عند Laurus Aroma"
        show(fr, BRAND_SUB, lt, L(135.7), L(139.75), W / 2, 1250)
        if lt >= L(139.8):
            x = lt - L(139.8); kk = eo(x / 0.45); cy = 1040 + (1 - kk) * 60
            place(fr, CARD, W / 2, cy, 0.97 + 0.03 * kk, kk)
            kb = eo((x - 0.3) / 0.3); place(fr, BTN, W / 2, cy + 185, 0.9 + 0.1 * kb, kb)
    elif k == "end":
        place(fr, CARD, W / 2, 1040)
        pulse = 1 + 0.035 * math.sin(lt * 2 * math.pi * 1.3); place(fr, BTN, W / 2, 1225, pulse)

# ------------------------------------------------------------------ video
VF = ("hflip,scale=1080:1920:flags=lanczos,eq=contrast=1.05:saturation=1.06:brightness=0.015:gamma=1.03,"
      "colorbalance=rs=0.025:bs=-0.03:rh=0.015:bh=-0.015,unsharp=5:5:0.55")
def frames(seg):
    p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-ss", f"{seg['a']:.3f}", "-t", f"{seg['b']-seg['a']+0.3:.3f}", "-i", SRC,
                          "-vf", f"{VF},setpts=PTS-STARTPTS,fps={FPS}", "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    n, last = 0, None
    while n < seg["nf"]:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        last = b; n += 1; yield Image.frombuffer("RGB", (W, H), b)
    while n < seg["nf"]: n += 1; yield Image.frombuffer("RGB", (W, H), last)
    p.kill(); p.wait()

def zoom(img, z, ax=0.5, ay=0.48):
    if z <= 1.0005: return img
    cw, ch = W / z, H / z; x0 = clamp((W - cw) * ax, 0, W - cw); y0 = clamp((H - ch) * ay, 0, H - ch)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                        os.path.join(HERE, "v5_video.mp4")], stdin=subprocess.PIPE)
for seg in EDL:
    n = seg["nf"]; z0, z1 = seg["z"]
    for i, img in enumerate(frames(seg)):
        lt = i / FPS; p = i / max(1, n - 1)
        z = z0 + (z1 - z0) * (eo(p * 2.2) if seg["k"] == "hook" else eio(p))
        for ts, zz in PUNCH.get(seg["k"], []):
            if lt >= ts - seg["a"]: z = zz + 0.01 * math.sin(lt * 0.7)
        ax, ay = 0.5, 0.48
        if seg["k"] == "hook": ax, ay = 0.48, 0.30
        if seg["k"] == "ba": ax, ay = 0.40, 0.40
        img = zoom(img, z, ax, ay)
        if seg["k"] == "end":
            img = img.filter(ImageFilter.GaussianBlur(8))
        if seg["k"] == "hook":
            arr = light_leak(np.asarray(img, np.float32), lt / (n / FPS))
            if lt < 0.08: arr = arr + (255 - arr) * 0.35 * (1 - lt / 0.08)
            img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        fr = img.convert("RGBA")
        if seg["k"] == "end":
            fr.alpha_composite(Image.new("RGBA", (W, H), (20, 14, 8, 60)))
        overlay(seg, fr, lt)
        enc.stdin.write(fr.convert("RGB").tobytes())
    print("rendered", seg["k"], f"{seg['t0']:.2f}s", flush=True)
enc.stdin.close(); enc.wait()

# ------------------------------------------------------------------ audio: her words untouched, light sound design
N = int(TOTAL * SR) + SR; mix = np.zeros((N, 2), np.float32)
for seg in EDL:
    if seg.get("mute"): continue
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{seg['a']:.3f}", "-t", f"{seg['b']-seg['a']:.3f}", "-i", SRC,
                          "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()[: int(seg["nf"] / FPS * SR)]
    f = int(0.015 * SR); x[:f] *= np.linspace(0, 1, f)[:, None]; x[-f:] *= np.linspace(1, 0, f)[:, None]
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
    x = lp(rng.standard_normal(n), f0 * (f1 / f0) ** np.sin(tt * math.pi / 2)); x -= lp(x, np.full(n, 180.0))
    x *= np.sin(np.pi * tt) ** 1.6; return (x / (abs(x).max() + 1e-9)).astype(np.float32)
def tick(f=1500, dur=0.06):
    tt = np.arange(int(dur * SR)) / SR; return (np.sin(2 * np.pi * f * tt) * np.exp(-tt * 70)).astype(np.float32)
def chime():
    tt = np.arange(int(1.4 * SR)) / SR; x = np.zeros_like(tt)
    for f, g, dl in [(1318.5, 1, 0), (1975.5, .7, .07), (2637, .5, .14)]:
        m = tt >= dl; x[m] += g * np.sin(2 * np.pi * f * (tt[m] - dl)) * np.exp(-(tt[m] - dl) * 3.5)
    return (x / abs(x).max()).astype(np.float32)
def seg_t(k, src_t):
    s = next(s for s in EDL if s["k"] == k); return s["t0"] + src_t - s["a"]
add(whoosh(0.6, 200, 4500), 0.0, 0.10)
add(whoosh(0.35), seg_t("story", 3.45) - 0.17, 0.10)
add(whoosh(0.35), seg_t("proof", 114.36) - 0.17, 0.10)
for k, ts in [("hook", 35.05), ("hook", 35.95), ("story", 4.45), ("story", 6.75), ("story", 9.2), ("story", 15.45),
              ("story", 16.4), ("story", 29.1), ("proof", 115.2), ("proof", 117.4), ("proof", 133.4)]:
    add(tick(1300 + 300 * (int(ts * 10) % 3)), seg_t(k, ts), 0.06)
add(chime(), seg_t("proof", 139.8) + 0.3, 0.05)
mix = mix[: int(TOTAL * SR)]; mix.tofile(os.path.join(HERE, "v5_mix.f32"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "v5_video.mp4"), "-f", "f32le", "-ar", str(SR), "-ac", "2",
                "-i", os.path.join(HERE, "v5_mix.f32"), "-af", "highpass=f=70,loudnorm=I=-14:TP=-1.0:LRA=9",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT)
