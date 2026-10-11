"""Restrained sound design (synthesised, original): whooshes on transitions, soft impacts on key words, marker
scribbles on hand-drawn annotations, pops on the project panels, a short glitch blip. Mixed well under the voice."""
import sys, numpy as np, subprocess
B = sys.argv[1]; SR = 48000; TOT = 89.766
sys.path.insert(0, f"{B}/../alice"); sys.path.insert(0, B)
from shots import SHOTS
import comic as CM
rng = np.random.default_rng(9); out = np.zeros((int(TOT * SR) + SR, 2))


def tt(d): return np.arange(int(d * SR)) / SR
def lp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X /= np.sqrt(1 + (f / fc) ** 4); return np.fft.irfft(X, len(x))
def hp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X *= (f / fc) ** 2 / np.sqrt(1 + (f / fc) ** 4); return np.fft.irfft(X, len(x))
def add(x, t, g=1.0, pan=0.0):
    i = int(t * SR)
    if i < 0 or i >= len(out): return
    x = x[: len(out) - i]; out[i:i + len(x), 0] += x * g * (1 - pan); out[i:i + len(x), 1] += x * g * (1 + pan)


def whoosh(d=0.45):
    t = tt(d); n = rng.standard_normal(len(t))
    env = np.sin(np.pi * t / d) ** 2
    sweep = np.array([lp(n[i:i + 2400], 600 + 5000 * (i / len(t))) for i in range(0, len(t), 2400)], dtype=object)
    x = np.concatenate([np.asarray(s, np.float64) for s in sweep])[: len(t)]
    return hp(x, 200) * env * 0.5


def impact():
    t = tt(0.6); f = 55 + 90 * np.exp(-t * 25)
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) + lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 18) * 0.4) * 0.8


def marker(d=0.35):
    t = tt(d); n = hp(rng.standard_normal(len(t)), 2500)
    grain = (np.sin(2 * np.pi * 38 * t) > 0.2).astype(float) * 0.6 + 0.4
    return lp(n, 7000) * grain * np.minimum(1, t / 0.02) * np.minimum(1, (d - t) / 0.05) * 0.22


def pop():
    t = tt(0.12); return np.sin(2 * np.pi * (500 + 900 * np.exp(-t * 60)) * t) * np.exp(-t * 40) * 0.35


def blip(d=0.2):
    t = tt(d); return np.sign(np.sin(2 * np.pi * 1300 * t)) * (rng.random(len(t)) > 0.5) * np.exp(-t * 12) * 0.12


TR = {1: .45, 2: .5, 3: .55, 4: .35, 5: .5, 6: .5, 7: .4, 9: .35, 10: .55, 11: .45, 12: .45, 13: .4, 16: .5, 18: .45, 20: .3,
      21: .45, 22: .35, 24: .5, 25: .6, 26: .45}
for k, d in TR.items():
    add(whoosh(max(0.35, d)), SHOTS[k][0] - max(0.35, d) / 2, 0.55, pan=(-0.3 if k % 2 else 0.3))
for s in CM.SPEED: add(impact(), s, 0.55)
for a, b, kind, p in CM.ANN: add(marker(0.38), a, 0.8, pan=0.2)
for st, c in CM.GRID_CHECKS: add(marker(0.22), st, 0.8, pan=-0.2)
for st, j in CM.STARS: add(pop(), st, 0.7)
for s, d in CM.GLITCH: add(blip(d), s, 0.6)
st = out[: int(TOT * SR)].astype(np.float32)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", "alimiter=limit=0.7",
                f"{B}/sfx.wav"], input=st.tobytes(), check=True)
print("sfx ok")
