#!/usr/bin/env python3
"""Meta ad v6 (Arabic, 60s): Laurus Aroma scrub + body butter routine.
Audio: 3 unbroken pieces of her speech, cut only inside sentence-end silences (verified by transcription).
Video: B-roll cutaways over her continuous voice, full synced captions, minimal graphics."""
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

# ================================================================== AUDIO SPINE (her voice; cut only in real silences)
SPINE = [  # (src_a, src_b)
    (34.89, 37.34),    # hook: "وعمركن شفتوا سكراب بهالقوام؟"
    (3.45, 31.80),     # problem -> routine -> Laurus Aroma -> coconut milk
    (114.36, 141.30),  # hands proof -> love the moisture -> CTA to her last word
]
END_HOLD = None  # filled so total == 60.0s
# ================================================================== VIDEO: B-roll cutaways over the spine (src audio time -> src video time)
BROLL = [  # (audio_src_a, audio_src_b, video_src_a, tag)
    (11.52, 14.35, 135.40, "jars"),     # "إنتي بس ناقصك منتجين بالروتين" -> both jars
    (14.35, 15.60, 33.07, "scoop"),     # "أولاً بدك تقشّري" -> fingers in the scrub
    (15.60, 16.86, 60.90, "rub"),       # "بعدين ترطّبي" -> glossy hand
    (122.14, 126.55, 47.67, "glow"),    # "عنجد أنا مغرمة بالترطيب..." -> glossy massage close-up
]
# captions: (src_start, src_end, text) - Lebanese Arabic, cleaned from the transcription
CAPS = [
    (3.45, 5.20, "كتير من البنات بتعاني"),
    (5.20, 6.65, "من الخشونة بالجسم"),
    (6.65, 8.05, "وخصوصاً جلد الوزة"),
    (8.05, 9.99, "وأساساً لو بتعمل شيفينغ لجسمها"),
    (9.99, 11.50, "قبل أو بعد جلسة الليزر"),
    (11.52, 14.35, "إنتي بس ناقصك منتجين بالروتين"),
    (14.35, 15.60, "طبعاً أولاً بدك تقشّري"),
    (15.60, 16.86, "بعدين ترطّبي"),
    (16.86, 18.56, "بس مش بأي منتجات"),
    (18.56, 20.80, "منتجات Laurus Aroma"),
    (20.80, 22.30, "تعي قلّك ليش هالمنتجات"),
    (22.30, 23.60, "رح تناسبك كتير"),
    (23.60, 24.85, "إذا بتعاني من هالمشاكل"),
    (25.07, 27.84, "أكتر شي حبّيتو بالسكراب تبعهن"),
    (27.84, 30.77, "إنو بحليب جوز الهند… شوفولي"),
    (30.77, 31.80, "ملمسو!"),
    (114.36, 116.89, "طلعوا إيدي… هاي عملتلها سكراب"),
    (116.89, 118.68, "وحطّيتلها زبدة، وإيدي هاي…"),
    (119.41, 122.14, "واضح معكن قدّيش في فرق بيناتهن؟"),
    (122.14, 124.40, "عنجد أنا مغرمة بالترطيب"),
    (124.40, 126.60, "يلي أخدتو من بعد الزبدة"),
    (126.76, 128.41, "فإذا كنتي بتعاني من الجفاف"),
    (128.41, 131.30, "أو جلد الوزة أو الجلد الزايد عالجسم"),
    (131.51, 133.47, "إنتي بس ناقصك هالمنتجين"),
    (133.47, 136.30, "ولا تنسي تاخديهن من عند Laurus Aroma"),
    (136.30, 139.73, "لأنو حرفياً رح تلاقي السكن تبعك"),
    (139.73, 141.30, "انتقلت لـ level تاني"),
]
# zoom per spine piece at natural pauses (src time, zoom) - gives jump-cut energy without touching audio
PUNCH = [(3.45, 1.00), (6.65, 1.07), (8.05, 1.00), (16.86, 1.06), (20.80, 1.00), (23.60, 1.08), (25.07, 1.00), (27.84, 1.07),
         (114.36, 1.12), (119.41, 1.20), (126.76, 1.00), (128.41, 1.07), (131.51, 1.00), (133.47, 1.04), (136.30, 1.09)]

total_speech = sum(b - a for a, b in SPINE)
END_HOLD = 60.0 - sum(round((b - a) * FPS) for a, b in SPINE) / FPS
TOTAL = 60.0
print(f"speech {total_speech:.2f}s + end hold {END_HOLD:.2f}s")

# output timeline of the spine
TL = []; t = 0.0
for a, b in SPINE:
    nf = int(round((b - a) * FPS)); TL.append(dict(a=a, b=b, t0=t, nf=nf)); t += nf / FPS
def out_t(src):  # source audio time -> output time
    for p in TL:
        if p["a"] - 1e-6 <= src <= p["b"] + 1e-6: return p["t0"] + src - p["a"]
    raise ValueError(src)

# ------------------------------------------------------------------ caption + graphics assets
def wrap_caption(s, size=60, maxw=900):
    im = txt(s, AR_XB, size)
    if im.width <= maxw: lines = [s]
    else:
        w = s.split(" "); h = (len(w) + 1) // 2; lines = [" ".join(w[:h]), " ".join(w[h:])]
    imgs = [txt(l, AR_XB, size) for l in lines]
    bw = max(i.width for i in imgs) + 56; bh = sum(i.height for i in imgs) + 30 + 6 * (len(imgs) - 1)
    box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, bw - 1, bh - 1], 26, fill=(18, 14, 10, 150))
    y = 15
    for i in imgs: box.alpha_composite(i, ((bw - i.width) // 2, y)); y += i.height + 6
    return shadowed(box, 0.25, 14, 4)
CAP_IMG = [(a, b, wrap_caption(s)) for a, b, s in CAPS]
CAP_Y = 1300

HOOK_L1 = big("عمركن شفتوا", 96)
HOOK_L2 = big("سكراب بهالقوام؟", 108)
COCO = pill("حليب جوز الهند", 58, icon=coconut_icon(56))
STEP1 = step_card("١", "تقشير"); STEP2 = step_card("٢", "ترطيب")
LBL_TREATED = pill("سكراب + زبدة", 50, bg=GOLD + (245,))
LBL_BARE = pill("بدون", 50, fg=CREAM, bg=(20, 16, 12, 175))
ROUTINE = pill("سكراب جوز الهند  +  زبدة الجسم", 48)

def spotlight(arr, cx, strength):
    """darken everything except a soft vertical band around cx (hands section)"""
    if strength <= 0: return arr
    xx = np.arange(W, dtype=np.float32)
    m = 1 - strength * (1 - np.exp(-((xx - cx) / 210) ** 2))
    return arr * m[None, :, None]

# ------------------------------------------------------------------ frame sources
VF = ("hflip,scale=1080:1920:flags=lanczos,eq=contrast=1.05:saturation=1.06:brightness=0.015:gamma=1.03,"
      "colorbalance=rs=0.025:bs=-0.03:rh=0.015:bh=-0.015,unsharp=5:5:0.55")
def frames(a, nf):
    p = subprocess.Popen(["ffmpeg", "-v", "quiet", "-ss", f"{a:.3f}", "-t", f"{nf / FPS + 0.3:.3f}", "-i", SRC,
                          "-vf", f"{VF},setpts=PTS-STARTPTS,fps={FPS}", "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         stdout=subprocess.PIPE)
    n, last = 0, None
    while n < nf:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        last = b; n += 1; yield Image.frombuffer("RGB", (W, H), b)
    while n < nf: n += 1; yield Image.frombuffer("RGB", (W, H), last)
    p.kill(); p.wait()

def zoom(img, z, ax=0.5, ay=0.48):
    if z <= 1.0005: return img
    cw, ch = W / z, H / z; x0 = clamp((W - cw) * ax, 0, W - cw); y0 = clamp((H - ch) * ay, 0, H - ch)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

# build the video piece list: spine pieces split by B-roll intervals
PIECES = []  # (out_t0, nf, video_src_a, tag, audio_src_a)
for p in TL:
    cur = p["a"]
    for (aa, ab, va, tag) in sorted(BROLL):
        if p["a"] <= aa < p["b"]:
            if aa > cur: PIECES.append((cur, aa, cur, "sync"))
            PIECES.append((aa, ab, va, tag)); cur = ab
    if cur < p["b"]: PIECES.append((cur, p["b"], cur, "sync" if p["a"] != 34.89 else "hook"))
# convert to frame counts on the output timeline
VP = []; f_acc = 0
for (aa, ab, va, tag) in PIECES:
    f_end = int(round(out_t(ab) * FPS)); nf = f_end - f_acc
    VP.append(dict(aa=aa, va=va, tag=tag, nf=nf, f0=f_acc)); f_acc = f_end
END_NF = int(round(TOTAL * FPS)) - f_acc
VP.append(dict(aa=None, va=139.30, tag="end", nf=END_NF, f0=f_acc))
for v in VP: print(f"  {v['f0']/FPS:6.2f}s {v['tag']:6s} video@{v['va']:.2f} ({v['nf']} f)")

def zoom_for(src_t, tag):
    if tag == "hook": return None
    if tag in ("scoop", "rub", "glow"): return 1.18
    if tag == "jars": return 1.04
    z = 1.0
    for ts, zz in PUNCH:
        if src_t >= ts - 1e-6: z = zz
    return z

enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                        os.path.join(HERE, "v6_video.mp4")], stdin=subprocess.PIPE)
HOOK_LEN = TL[0]["nf"] / FPS
for v in VP:
    for i, img in enumerate(frames(v["va"], v["nf"])):
        gf = v["f0"] + i; T = gf / FPS; lt = i / FPS
        src = None if v["aa"] is None else v["aa"] + lt   # audio-source time currently heard
        tag = v["tag"]
        # ---- camera
        if tag == "hook":
            z = 1.55 + (1.18 - 1.55) * eo(T / HOOK_LEN * 2.2); img = zoom(img, z, 0.48, 0.30)
        elif tag == "end":
            img = zoom(img, 1.06, 0.5, 0.45).filter(ImageFilter.GaussianBlur(8))
        else:
            z = zoom_for(src, tag) + (0.03 * eio(lt / (v["nf"] / FPS)) if tag != "sync" else 0.008 * math.sin(T * 0.7))
            ay = 0.40 if (src is not None and 114.36 <= src <= 122.14) else 0.48
            img = zoom(img, z, 0.5, ay)
        arr = None
        if tag == "hook":
            arr = light_leak(np.asarray(img, np.float32), T / HOOK_LEN)
            if T < 0.08: arr = arr + (255 - arr) * 0.35 * (1 - T / 0.08)
        # ---- hands: spotlight follows what she's talking about
        if src is not None and 114.36 <= src <= 122.14:
            if arr is None: arr = np.asarray(img, np.float32)
            # treated hand (watch) on the right, bare hand on the left of frame
            if src < 116.9:   cx, s_ = 640, 0.58 * eo((src - 114.6) / 0.5)
            elif src < 118.5: cx, s_ = 640 + (230 - 640) * eio((src - 117.6) / 0.6), 0.58
            elif src < 119.4: cx, s_ = 230, 0.58
            else:             cx, s_ = 430, 0.58 * (1 - eo((src - 119.4) / 0.6))
            arr = spotlight(arr, cx, s_)
        if arr is not None: img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
        fr = img.convert("RGBA")
        # ---- graphics (all timed to her words)
        if tag == "hook":
            hs = TL[0]["a"]
            show(fr, HOOK_L1, T, 35.05 - hs, 99, W / 2, 1180, "pop")
            show(fr, HOOK_L2, T, 35.95 - hs, 99, W / 2, 1330, "pop")
        if src is not None:
            ot = lambda s_: out_t(s_)
            # step cards over the B-roll: "أولاً بدك تقشّري / بعدين ترطّبي"
            show(fr, STEP1, T, ot(14.40), ot(16.86), W / 2 + 190, 1060, "pop")
            show(fr, STEP2, T, ot(15.62), ot(16.86), W / 2 - 190, 1060, "pop")
            # brand plate as she names it
            show(fr, BRAND, T, ot(18.70), ot(20.80), W / 2, 1080)
            # coconut milk badge
            show(fr, COCO, T, ot(29.05), ot(31.80), W / 2, 1100, "pop")
            # hands labels
            show(fr, LBL_TREATED, T, ot(115.10), ot(122.14), 640, 1080, "pop")
            show(fr, LBL_BARE, T, ot(118.00), ot(122.14), 230, 1080, "pop")
            # "هالمنتجين" -> routine pill
            show(fr, ROUTINE, T, ot(131.60), ot(133.47), W / 2, 1100, "pop")
            # captions
            for a, b, L in CAP_IMG:
                if a <= src < b:
                    x = src - a; k = eo(x / 0.16)
                    place(fr, L, W / 2, CAP_Y + (1 - k) * 14, 1, clamp(x / 0.12))
        if tag == "end":
            kk = eo(lt / 0.4); cy = 1000 + (1 - kk) * 60
            place(fr, CARD, W / 2, cy, 0.97 + 0.03 * kk, kk)
            kb = eo((lt - 0.25) / 0.3)
            place(fr, BTN, W / 2, cy + 185, (0.9 + 0.1 * kb) * (1 + 0.035 * math.sin(max(0, lt - 0.55) * 2 * math.pi * 1.3)), kb)
        enc.stdin.write(fr.convert("RGB").tobytes())
    print(f"rendered {v['tag']} @ {v['f0']/FPS:.2f}s", flush=True)
enc.stdin.close(); enc.wait()

# ================================================================== AUDIO
N = int(TOTAL * SR) + SR; mix = np.zeros((N, 2), np.float32)
for p in TL:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{p['a']:.3f}", "-t", f"{p['b']-p['a']:.3f}", "-i", SRC,
                          "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()[: int(p["nf"] / FPS * SR)]
    f = int(0.015 * SR); x[:f] *= np.linspace(0, 1, f)[:, None]; x[-f:] *= np.linspace(1, 0, f)[:, None]
    s0 = int(p["t0"] * SR); mix[s0:s0 + len(x)] += x
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
add(whoosh(0.6, 200, 4500), 0.0, 0.10)
for p in TL[1:]: add(whoosh(0.35), p["t0"] - 0.17, 0.09)
for s_ in [35.05, 35.95, 14.40, 15.62, 29.05, 115.10, 118.00, 131.60]:
    add(tick(1300 + 300 * (int(s_ * 10) % 3)), out_t(s_), 0.05)
add(chime(), TL[-1]["t0"] + TL[-1]["nf"] / FPS + 0.25, 0.05)
mix = mix[: int(TOTAL * SR)]; mix.tofile(os.path.join(HERE, "v6_mix.f32"))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "v6_video.mp4"), "-f", "f32le", "-ar", str(SR), "-ac", "2",
                "-i", os.path.join(HERE, "v6_mix.f32"), "-af", "highpass=f=70,loudnorm=I=-14:TP=-1.0:LRA=9",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT)
