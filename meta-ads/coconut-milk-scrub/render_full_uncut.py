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

def light_leak(arr, p, strength=0.22):
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

MUSIC = sys.argv[4]
AUD_SHIFT = 0.08          # original audio lags the lips by ~70-100ms: play sound 80ms earlier
DUR = 141.565
NF = int(round(DUR * FPS))
def disp(s): return s - AUD_SHIFT   # speech time -> on-screen time

CAPS = [
    (2.56, 3.32, "بالترطيب"),
    (3.45, 5.20, "كتير من البنات بتعاني"),
    (5.20, 6.65, "من الخشونة بالجسم"),
    (6.65, 8.05, "وخصوصاً جلد الوزة"),
    (8.05, 9.99, "وأساساً لو بتعمل شيفينغ لجسمها"),
    (9.99, 11.50, "بعد أو قبل جلسة الليزر"),
    (11.52, 14.35, "إنتي بس ناقصك منتجين بالروتين"),
    (14.35, 16.10, "طبعاً أولاً بدك تقشّري"),
    (16.10, 16.86, "بعدين ترطّبي"),
    (16.86, 18.56, "بس مش بأي منتجات"),
    (18.56, 20.02, "منتجات Laurus Aroma"),
    (20.02, 22.00, "تعي إحكيلك ليش هالمنتجات"),
    (22.00, 23.50, "كتير رح تناسبك"),
    (23.50, 24.85, "لو كنتي بتعاني من هالمشاكل"),
    (25.07, 27.84, "أكتر شي حبّيتو بالسكراب تبعهن"),
    (27.84, 30.77, "إنو بحليب جوز الهند… شوفولي"),
    (30.77, 31.70, "ملمسو!"),
    (31.73, 32.90, "وقوامو… ما أحلاه!"),
    (33.07, 34.73, "شوفولي إنتو بس"),
    (35.05, 37.30, "وعمركن شفتوا سكراب بهالقوام؟"),
    (37.30, 39.88, "وطبعاً هالسكراب بيساعدك تتخلّصي"),
    (39.88, 42.50, "من كل الجلد الميت المتراكم"),
    (42.50, 44.48, "يلي بيكون عالـskin تبعك"),
    (44.48, 45.83, "وبنفس الوقت بيرطّب"),
    (47.41, 49.60, "ملمس البشرة الخشنة؟"),
    (49.60, 51.92, "انسوه من بعد ما تستخدمي هالسكراب"),
    (51.92, 53.07, "طلعوا طلعوا…"),
    (53.07, 55.40, "أحلى قوام على جسمي"),
    (55.59, 58.94, "وإنتي لمّا تضلّك تقشّري جسمك بمقشّر صح"),
    (58.94, 61.23, "شايفين الجلد الميت يلي بيتراكم؟"),
    (61.23, 62.88, "رح يختفي، وحرفياً"),
    (62.88, 65.13, "ودّعي الخشونة"),
    (65.13, 68.09, "وشوفي نعومة جسمك كيف رح تصير"),
    (68.09, 69.90, "أنا شايفة الفرق من هلّأ"),
    (69.95, 72.45, "بالترطيب… وريحتو خفيفة ونضيفة"),
    (72.59, 75.53, "اسمعوا، أنا هلّأ غسلت إيدي"),
    (75.53, 76.86, "ولسّاتني حاسّة بالترطيب والنعومة"),
    (76.86, 78.60, "يلي عطاني ياها لجلدي"),
    (78.60, 79.98, "عنجد هالسكراب خطير"),
    (79.98, 83.00, "تاني وأهم خطوة تعمليها من بعد السكراب"),
    (83.00, 85.80, "خصوصاً لو بشرتك جافة أو حتى فيها خشونة"),
    (85.80, 89.30, "إنك تستخدمي زبدة تكون منيحة لجسمك"),
    (89.30, 91.71, "متل ما رح تستخدمي هالزبدة"),
    (91.92, 94.44, "…بالـskin من بعد استخدامك للسكراب"),
    (94.44, 97.69, "بتحطّي منها على المنطقة بعد ما تكوني"),
    (97.69, 99.39, "استخدمتي مقشّر الجسم"),
    (99.39, 101.60, "طلعوا… طلعوا الترطيب من بعد"),
    (102.29, 104.43, "طلعوا ما أحلى الترطيب!"),
    (104.43, 106.47, "حرفياً طلعوا كيف إيدي متل القطنة"),
    (106.47, 107.72, "واو يا جماعة!"),
    (108.04, 110.53, "وريحة النضافة… بتحسّي حالك"),
    (110.53, 111.30, "طالعة من الحمّام حرفياً"),
    (111.30, 112.34, "طلعوا طلعوا…"),
    (112.34, 113.97, "واو يا جماعة!"),
    (114.36, 116.89, "طلعوا إيدي… هاي عملتلها سكراب"),
    (116.89, 118.68, "وحطّيتلها زبدة، وإيدي هاي…"),
    (119.41, 122.14, "واضح معكن قدّيش في فرق بيناتهن؟"),
    (122.14, 124.40, "عنجد أنا مغرمة بالترطيب"),
    (124.40, 126.60, "يلي أخدتو من بعد السكراب والزبدة"),
    (126.76, 128.41, "فإذا كنتي بتعاني من الجفاف"),
    (128.41, 131.30, "أو جلد الوزة أو الجلد الزايد عالجسم"),
    (131.51, 133.47, "إنتي بس ناقصك هالمنتجين"),
    (133.47, 136.30, "ولا تنسي تاخديهن من عند Laurus Aroma"),
    (136.30, 139.35, "لأنو حرفياً رح تلاقي الـskin تبعك"),
    (139.35, 141.56, "انتقلت من level لـ level تاني"),
]

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

HOOK_L1 = big("أنا شايفة الفرق", 104)
HOOK_L2 = big("من هلّأ", 124)
LBL_BEFORE = pill("قبل", 58); LBL_AFTER = pill("بعد", 58, bg=GOLD + (245,))
COCO = pill("حليب جوز الهند", 58, icon=coconut_icon(56))
STEP1 = step_card("١", "تقشير"); STEP2 = step_card("٢", "ترطيب")
STEP2_BUTTER = step_card("٢", "زبدة الجسم", w=420)
LBL_TREATED = pill("سكراب + زبدة", 50, bg=GOLD + (245,))
LBL_BARE = pill("بدون", 50)
ROUTINE = pill("سكراب جوز الهند  +  زبدة الجسم", 48)
def cta_pill():
    b = txt("اطلبيه الآن", AR_XB, 60, CREAM)
    br = txt("LAURUS  AROMA", SERIF, 30, (225, 200, 150), ar=False)
    w, h = max(b.width, br.width) + 150, b.height + br.height + 46
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], 40, fill=INK + (238,))
    im.alpha_composite(br, ((w - br.width) // 2, 14)); im.alpha_composite(b, ((w - b.width) // 2, 14 + br.height + 4))
    return shadowed(im, 0.4, 16, 6)
CTA = cta_pill()

def spotlight(arr, cx, strength):
    if strength <= 0: return arr
    xx = np.arange(W, dtype=np.float32)
    m = 1 - strength * (1 - np.exp(-((xx - cx) / 210) ** 2))
    return arr * m[None, :, None]
def zoom(img, z, ax=0.5, ay=0.48):
    if z <= 1.0005: return img
    cw, ch = W / z, H / z; x0 = clamp((W - cw) * ax, 0, W - cw); y0 = clamp((H - ch) * ay, 0, H - ch)
    return img.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
def smoothstep_window(t, a, b, r=0.6):
    return eio((t - a) / r) * eio((b - t) / r)

VF = ("hflip,scale=1080:1920:flags=lanczos,eq=contrast=1.05:saturation=1.06:brightness=0.015:gamma=1.03,"
      "colorbalance=rs=0.025:bs=-0.03:rh=0.015:bh=-0.015,unsharp=5:5:0.55")
dec = subprocess.Popen(["ffmpeg", "-v", "quiet", "-i", SRC, "-vf", f"{VF},fps={FPS}", "-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                        "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                        os.path.join(HERE, "v9_video.mp4")], stdin=subprocess.PIPE)
HANDS = (114.36, 122.14)
last = None
for gf in range(NF):
    b = dec.stdout.read(W * H * 3)
    if len(b) < W * H * 3: b = last
    last = b
    img = Image.frombuffer("RGB", (W, H), b)
    T = gf / FPS; sp = T + AUD_SHIFT
    if T < 2.4:
        k = eio(T / 0.85); z = 1.70 + (1.03 - 1.70) * k
        img = zoom(img, z, 0.40 + 0.10 * k, 0.36 + 0.12 * k)
    else:
        hw = smoothstep_window(T, disp(HANDS[0]) - 0.3, disp(HANDS[1]) + 0.3)
        z = 1.03 + 0.02 * math.sin(2 * math.pi * (T - 2.4) / 18) + 0.08 * hw
        img = zoom(img, z, 0.5, 0.48 - 0.08 * hw)
    arr = None
    if T < 2.4:
        arr = light_leak(np.asarray(img, np.float32), T / 2.4)
    if HANDS[0] <= sp <= HANDS[1] + 0.6:
        if arr is None: arr = np.asarray(img, np.float32)
        if sp < 116.9:   cx, s_ = 640, 0.55 * eo((sp - 114.6) / 0.5)
        elif sp < 118.5: cx, s_ = 640 + (230 - 640) * eio((sp - 117.6) / 0.6), 0.55
        elif sp < 119.4: cx, s_ = 230, 0.55
        else:            cx, s_ = 430, 0.55 * (1 - eo((sp - 119.4) / 0.6))
        arr = spotlight(arr, cx, s_)
    if arr is not None: img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    fr = img.convert("RGBA")
    D = disp
    show(fr, HOOK_L1, T, D(0.15), D(2.50), W / 2, 1180, "pop")
    show(fr, HOOK_L2, T, D(1.41), D(2.50), W / 2, 1335, "pop")
    show(fr, LBL_BEFORE, T, 0.85, 2.45, 150, 720)
    show(fr, LBL_AFTER, T, 1.05, 2.45, 455, 720)
    show(fr, STEP1, T, D(14.45), D(17.30), W / 2 + 190, 1080)
    show(fr, STEP2, T, D(16.15), D(17.30), W / 2 - 190, 1080)
    show(fr, BRAND, T, D(19.05), D(20.60), W / 2, 1090)
    show(fr, COCO, T, D(29.05), D(31.70), W / 2, 1090)
    show(fr, STEP2_BUTTER, T, D(86.60), D(91.71), W / 2, 1080)
    show(fr, LBL_TREATED, T, D(115.10), D(122.14), 640, 1080)
    show(fr, LBL_BARE, T, D(118.00), D(122.14), 230, 1080)
    show(fr, ROUTINE, T, D(131.60), D(133.47), W / 2, 1090)
    if T >= D(135.30):
        x = T - D(135.30); k = eo(x / 0.4)
        pulse = 1 + 0.03 * math.sin(max(0, x - 0.5) * 2 * math.pi * 1.2)
        place(fr, CTA, W / 2, 1080 + (1 - k) * 34, (0.97 + 0.03 * k) * pulse, clamp(x / 0.2))
    for a, b2, L in CAP_IMG:
        if D(a) <= T < D(b2):
            x = T - D(a); k = eo(x / 0.16)
            place(fr, L, W / 2, CAP_Y + (1 - k) * 14, 1, clamp(x / 0.12))
    enc.stdin.write(fr.convert("RGB").tobytes())
    if gf % 600 == 0: print(f"frame {gf}/{NF}", flush=True)
dec.kill(); enc.stdin.close(); enc.wait()

# ================================================================== AUDIO
SR2 = 48000; N = int(NF / FPS * SR2)
def load(path, ss=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}"] + (["-t", f"{dur:.3f}"] if dur else []) + \
          ["-i", path, "-vn", "-ac", "2", "-ar", str(SR2), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()
voice = np.zeros((N, 2), np.float32)
v = load(SRC, AUD_SHIFT)[:N]; voice[:len(v)] = v
f = int(0.01 * SR2); voice[:f] *= np.linspace(0, 1, f)[:, None]
rng = np.random.default_rng(11)
sfx = np.zeros((N, 2), np.float32)
def add(sig, t, g, pan=0.0):
    s0 = int(t * SR2)
    if s0 < 0: sig = sig[-s0:]; s0 = 0
    e = min(N, s0 + len(sig)); sig = sig[: e - s0] * g
    sfx[s0:e, 0] += sig * (1 - max(0, pan)); sfx[s0:e, 1] += sig * (1 + min(0, pan))
def lp(x, cut):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        a = 1 - math.exp(-2 * math.pi * cut[i] / SR2); acc += a * (x[i] - acc); y[i] = acc
    return y
def norm(x): return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)
def whoosh(dur=0.5, f0=300, f1=6000, curve=1.6):
    n = int(dur * SR2); tt = np.linspace(0, 1, n)
    x = lp(rng.standard_normal(n), f0 * (f1 / f0) ** np.sin(tt * math.pi / 2)); x -= lp(x, np.full(n, 150.0))
    return norm(x * np.sin(np.pi * tt) ** curve)
def soft_impact(dur=1.2):
    n = int(dur * SR2); tt = np.arange(n) / SR2
    body = np.sin(2 * np.pi * np.cumsum(42 + 60 * np.exp(-tt * 14)) / SR2) * np.exp(-tt * 3.2)
    air = lp(rng.standard_normal(n), np.full(n, 1800.0)) * np.exp(-tt * 9) * 0.6
    return norm(np.tanh(1.4 * (body + air)))
def shimmer(dur=1.6, lo=2600, hi=7200, k=18):
    n = int(dur * SR2); tt = np.arange(n) / SR2; x = np.zeros(n)
    for _ in range(k):
        st = rng.uniform(0, dur * 0.55); fq = rng.uniform(lo, hi); m = tt >= st
        x[m] += np.sin(2 * np.pi * fq * (tt[m] - st)) * np.exp(-(tt[m] - st) * rng.uniform(5, 9)) * rng.uniform(.3, 1)
    return norm(x * np.minimum(1, tt / 0.03))
def bubble(f0=520, f1=980, dur=0.11):
    n = int(dur * SR2); tt = np.arange(n) / SR2
    fq = f0 + (f1 - f0) * (1 - np.exp(-tt * 40))
    return norm(np.sin(2 * np.pi * np.cumsum(fq) / SR2) * np.exp(-tt * 38) * np.minimum(1, tt / 0.004))
def ding(fq=1568.0, dur=1.4):
    tt = np.arange(int(dur * SR2)) / SR2
    x = sum(g * np.sin(2 * np.pi * fq * r * tt) * np.exp(-tt * d) for r, g, d in [(1, 1, 3.2), (2.76, .35, 6), (5.4, .15, 10)])
    return norm(x * np.minimum(1, tt / 0.003))
def chime():
    tt = np.arange(int(1.8 * SR2)) / SR2; x = np.zeros_like(tt)
    for fq, g, dl in [(1046.5, 1, 0), (1318.5, .8, .08), (1568, .7, .16), (2093, .45, .24)]:
        m = tt >= dl; x[m] += g * np.sin(2 * np.pi * fq * (tt[m] - dl)) * np.exp(-(tt[m] - dl) * 2.8)
    return norm(x)
D = disp
add(soft_impact(), 0.0, 0.30); add(shimmer(1.8), 0.05, 0.10, 0.3)
add(bubble(480, 900), D(0.15), 0.11); add(bubble(560, 1050), D(1.41), 0.11)
add(bubble(450, 850), 0.85, 0.08); add(bubble(520, 980), 1.05, 0.08)
add(bubble(500, 950), D(14.45), 0.10); add(bubble(600, 1100), D(16.15), 0.10)
add(ding(1568), D(19.05), 0.055); add(shimmer(1.2), D(19.05), 0.045, -0.3)
add(bubble(520, 980), D(29.05), 0.10)
add(shimmer(1.4), D(35.4), 0.05, 0.3)
add(shimmer(1.4), D(65.3), 0.045, -0.3)
add(bubble(560, 1050), D(86.60), 0.10)
add(shimmer(1.2), D(104.6), 0.045)
add(bubble(520, 980), D(115.10), 0.10)
add(whoosh(0.7, 200, 2600, 1.2), D(117.55), 0.065, -0.5)
add(bubble(460, 860), D(118.00), 0.10)
add(shimmer(1.4), D(119.45), 0.055)
add(bubble(520, 980), D(131.60), 0.10)
add(whoosh(0.5, 250, 4500), D(135.30) - 0.25, 0.07); add(chime(), D(135.35), 0.07)

mus = load(MUSIC)
off = max(0, len(mus) / SR2 - N / SR2 - 0.6)
mus = mus[int(off * SR2): int(off * SR2) + N]
if len(mus) < N: mus = np.vstack([mus, np.zeros((N - len(mus), 2), np.float32)])
tt = np.arange(N) / SR2
lvl = np.full(N, 0.27, np.float32)
lvl = np.where(tt < 2.2, 0.50, lvl); r = (tt >= 2.2) & (tt < 3.0); lvl[r] = 0.50 + (0.27 - 0.50) * (tt[r] - 2.2) / 0.8
fo = tt > N / SR2 - 0.5; lvl[fo] *= np.clip((N / SR2 - tt[fo]) / 0.5, 0, 1)
fi = int(0.05 * SR2); lvl[:fi] *= np.linspace(0, 1, fi)
mus *= lvl[:, None]
for name, arr in [("voice", voice), ("sfx", sfx), ("music", mus)]:
    arr.astype(np.float32).tofile(os.path.join(HERE, f"v9_{name}.f32"))
def inp(n): return ["-f", "f32le", "-ar", str(SR2), "-ac", "2", "-i", os.path.join(HERE, f"v9_{n}.f32")]
fc = ("[1:a]highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,asplit=2[v][key];"
      "[3:a][key]sidechaincompress=threshold=0.06:ratio=3:attack=30:release=400[m];"
      "[v][2:a][m]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.0:LRA=10[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(HERE, "v9_video.mp4")] + inp("voice") + inp("sfx") + inp("music") +
               ["-filter_complex", fc, "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-ar", "48000", "-movflags", "+faststart", "-shortest", OUT], check=True)
print("done", OUT)
