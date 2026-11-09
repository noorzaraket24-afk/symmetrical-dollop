#!/usr/bin/env python3
"""Final audio mix: her voice (3 unbroken pieces) + designed SFX + music bed ducked under the voice."""
import subprocess, sys, math, os
import numpy as np

SRC, VIDEO, MUSIC, OUT = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__))
SR, FPS, TOTAL = 48000, 30, 60.0
SPINE = [(34.89, 37.34), (3.45, 31.80), (114.36, 141.30)]
TL = []; t = 0.0
for a, b in SPINE:
    nf = int(round((b - a) * FPS)); TL.append(dict(a=a, b=b, t0=t, nf=nf)); t += nf / FPS
SPEECH_END = t
def out_t(src):
    for p in TL:
        if p["a"] - 1e-6 <= src <= p["b"] + 1e-6: return p["t0"] + src - p["a"]
    raise ValueError(src)
# video cut points (B-roll in/out + spine joins + end card)
CUTS = [TL[1]["t0"], out_t(11.52), out_t(14.35), out_t(16.10), out_t(17.30), TL[2]["t0"], out_t(122.14), out_t(126.55), SPEECH_END]

N = int(TOTAL * SR)
def load(path, ss=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}"] + (["-t", f"{dur:.3f}"] if dur else []) + \
          ["-i", path, "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2).copy()

# ---------------- voice
voice = np.zeros((N, 2), np.float32)
for p in TL:
    x = load(SRC, p["a"], p["b"] - p["a"])[: int(p["nf"] / FPS * SR)]
    f = int(0.015 * SR); x[:f] *= np.linspace(0, 1, f)[:, None]; x[-f:] *= np.linspace(1, 0, f)[:, None]
    s0 = int(p["t0"] * SR); voice[s0:s0 + len(x)] += x

# ---------------- sound design (all synthesized, soft & premium)
rng = np.random.default_rng(11)
sfx = np.zeros((N, 2), np.float32)
def add(sig, t, g, pan=0.0):
    s0 = int(t * SR)
    if s0 < 0: sig = sig[-s0:]; s0 = 0
    e = min(N, s0 + len(sig)); sig = sig[: e - s0] * g
    sfx[s0:e, 0] += sig * (1 - max(0, pan)); sfx[s0:e, 1] += sig * (1 + min(0, pan))
def lp(x, cut):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        a = 1 - math.exp(-2 * math.pi * cut[i] / SR); acc += a * (x[i] - acc); y[i] = acc
    return y
def norm(x): return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)
def whoosh(dur=0.5, f0=300, f1=6000, curve=1.6):
    n = int(dur * SR); tt = np.linspace(0, 1, n)
    x = lp(rng.standard_normal(n), f0 * (f1 / f0) ** np.sin(tt * math.pi / 2))
    x -= lp(x, np.full(n, 150.0)); return norm(x * np.sin(np.pi * tt) ** curve)
def soft_impact(dur=1.2):
    n = int(dur * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(42 + 60 * np.exp(-tt * 14)) / SR) * np.exp(-tt * 3.2)
    air = lp(rng.standard_normal(n), np.full(n, 1800.0)) * np.exp(-tt * 9) * 0.6
    return norm(np.tanh(1.4 * (body + air)))
def shimmer(dur=1.6, lo=2600, hi=7200, k=18):
    n = int(dur * SR); tt = np.arange(n) / SR; x = np.zeros(n)
    for _ in range(k):
        st = rng.uniform(0, dur * 0.55); f = rng.uniform(lo, hi); m = tt >= st
        x[m] += np.sin(2 * np.pi * f * (tt[m] - st)) * np.exp(-(tt[m] - st) * rng.uniform(5, 9)) * rng.uniform(.3, 1)
    return norm(x * np.minimum(1, tt / 0.03))
def bubble(f0=520, f1=980, dur=0.11):
    n = int(dur * SR); tt = np.arange(n) / SR
    f = f0 + (f1 - f0) * (1 - np.exp(-tt * 40))
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 38) * np.minimum(1, tt / 0.004))
def ding(f=1568.0, dur=1.4):
    tt = np.arange(int(dur * SR)) / SR
    x = sum(g * np.sin(2 * np.pi * f * r * tt) * np.exp(-tt * d) for r, g, d in [(1, 1, 3.2), (2.76, .35, 6), (5.4, .15, 10)])
    return norm(x * np.minimum(1, tt / 0.003))
def chime():
    tt = np.arange(int(1.8 * SR)) / SR; x = np.zeros_like(tt)
    for f, g, dl in [(1046.5, 1, 0), (1318.5, .8, .08), (1568, .7, .16), (2093, .45, .24)]:
        m = tt >= dl; x[m] += g * np.sin(2 * np.pi * f * (tt[m] - dl)) * np.exp(-(tt[m] - dl) * 2.8)
    return norm(x)

hook_l2 = 35.95 - 34.89
add(soft_impact(), 0.0, 0.32)                 # hook opens with a soft low hit
add(shimmer(1.8), 0.05, 0.10, 0.3)            # + sparkle on the texture shot
add(bubble(480, 900), 35.05 - 34.89, 0.12)    # line 1
add(bubble(560, 1050), hook_l2, 0.12)         # line 2
for i, c in enumerate(CUTS):                  # airy whoosh on every picture change (very low)
    add(whoosh(0.5, 280, 5200), c - 0.27, 0.075 if i else 0.10, (-0.4, 0.4)[i % 2])
add(bubble(500, 950), out_t(14.45), 0.11)     # step 1 card
add(bubble(600, 1100), out_t(16.15), 0.11)    # step 2 card
add(ding(1568), out_t(19.05), 0.06)           # brand plate
add(shimmer(1.2), out_t(19.05), 0.05, -0.3)
add(bubble(520, 980), out_t(29.05), 0.11)     # coconut badge
add(bubble(520, 980), out_t(115.10), 0.10)    # "سكراب + زبدة" label
add(whoosh(0.7, 200, 2600, 1.2), out_t(117.55), 0.07, -0.5)  # spotlight sweeps to the other hand
add(bubble(460, 860), out_t(118.00), 0.10)    # "بدون" label
add(shimmer(1.4), out_t(119.45), 0.06)        # "واضح قديش في فرق" both hands lit
add(bubble(520, 980), out_t(131.60), 0.10)    # routine pill
add(whoosh(0.6, 250, 4500), SPEECH_END - 0.3, 0.10)   # end card in
add(chime(), SPEECH_END + 0.25, 0.09)
add(bubble(600, 1150), SPEECH_END + 0.30, 0.10)       # button

# ---------------- music: offset so its natural ending lands on the end card
mus_len = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", MUSIC],
                               capture_output=True, text=True).stdout)
offset = max(0.0, mus_len - TOTAL - 0.4)
music = load(MUSIC, offset, TOTAL)[:N]
if len(music) < N: music = np.vstack([music, np.zeros((N - len(music), 2), np.float32)])
# base level automation: present in hook & end card, low under her voice
tt = np.arange(N) / SR
lvl = np.full(N, 0.27, np.float32)
hook_end = TL[1]["t0"]
lvl = np.where(tt < hook_end - 0.3, 0.55, lvl)
ramp = (tt >= hook_end - 0.3) & (tt < hook_end + 0.4)
lvl[ramp] = 0.55 + (0.27 - 0.55) * (tt[ramp] - (hook_end - 0.3)) / 0.7
endr = tt >= SPEECH_END - 0.4
lvl[endr] = 0.27 + (0.5 - 0.27) * np.clip((tt[endr] - (SPEECH_END - 0.4)) / 0.6, 0, 1)
fade = tt > TOTAL - 0.9
lvl[fade] *= np.clip((TOTAL - tt[fade]) / 0.9, 0, 1)
music *= lvl[:, None]
# fade-in to avoid a click
fi = int(0.05 * SR); music[:fi] *= np.linspace(0, 1, fi)[:, None]

for name, arr in [("voice", voice), ("sfx", sfx), ("music", music)]:
    arr.astype(np.float32).tofile(os.path.join(HERE, f"v8_{name}.f32"))

def inp(n): return ["-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", os.path.join(HERE, f"v8_{n}.f32")]
fc = ("[1:a]highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,asplit=2[v][key];"
      "[3:a][key]sidechaincompress=threshold=0.06:ratio=3:attack=30:release=400[m];"
      "[v][2:a][m]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.0:LRA=10[out]")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", VIDEO] + inp("voice") + inp("sfx") + inp("music") +
               ["-filter_complex", fc, "-map", "0:v", "-map", "[out]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-ar", "48000", "-movflags", "+faststart", "-t", f"{TOTAL}", OUT], check=True)
print("done", OUT, "music offset", round(offset, 2))
