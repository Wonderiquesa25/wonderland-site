"""Pro SFX: uisfx (MIT) cinematic + sci-fi UI sounds layered with synthesised sub impacts/whooshes, on the original timeline,
then the stray 'o que' is cut (35.775-35.93) from the voice+SFX mix so everything stays in sync."""
import sys, subprocess, numpy as np
B, L, VOICE = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, f"{B}/../alice"); sys.path.insert(0, B)
from shots import SHOTS
import hud as HUD
SR = 48000; TOT = 89.766; rng = np.random.default_rng(4)
bus = np.zeros((int(TOT * SR) + SR, 2))


def load(name):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{L}/{name}.mp3", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    return x / (np.abs(x).max() + 1e-9) * 0.4


def tt(d): return np.arange(int(d * SR)) / SR
def add(x, t, g=1.0, pan=0.0):
    if x.ndim == 1: x = np.stack([x, x], 1)
    i = int(t * SR)
    if i < 0 or i >= len(bus): return
    x = x[: len(bus) - i]; bus[i:i + len(x), 0] += x[:, 0] * g * (1 - pan); bus[i:i + len(x), 1] += x[:, 1] * g * (1 + pan)


def sub_boom():
    t = tt(0.9); f = 38 + 70 * np.exp(-t * 18)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5) * 0.55


def air_whoosh(d=0.5):
    t = tt(d); n = rng.standard_normal(len(t))
    X = np.fft.rfft(n); f = np.fft.rfftfreq(len(n), 1 / SR); X *= np.exp(-((np.log(f + 1) - np.log(1800)) ** 2) / 0.8); x = np.fft.irfft(X, len(n))
    return x / (np.abs(x).max() + 1e-9) * np.sin(np.pi * t / d) ** 2 * 0.22


S = {n: load(n) for n in ["cinematic/swipe", "cinematic/drop", "cinematic/open", "cinematic/achievement", "cinematic/start",
                          "cinematic/complete", "scifi/scanning", "scifi/lock", "scifi/typing", "scifi/complete", "scifi/error",
                          "scifi/warning", "scifi/connect"]}
TR = {1: .45, 2: .5, 3: .55, 4: .35, 5: .5, 6: .5, 7: .4, 9: .35, 10: .55, 11: .45, 12: .45, 13: .4, 16: .5, 18: .45, 20: .3,
      21: .45, 22: .35, 24: .5, 25: .6, 26: .45}
for k, d in TR.items():
    t0 = SHOTS[k][0]; pan = -0.35 if k % 2 else 0.35
    add(S["cinematic/swipe"], t0 - 0.30, 0.8, pan); add(air_whoosh(0.55), t0 - 0.30, 0.8, -pan)
for g in HUD.GIANTS:
    add(sub_boom(), g, 0.9); add(S["cinematic/drop"], g, 0.55)
for a, b, rect, label, side in HUD.TARGETS:
    sc = S["scifi/scanning"][: int(0.75 * SR)].copy(); sc[-2400:] *= np.linspace(1, 0, 2400)[:, None]
    add(sc, a, 0.5); add(S["scifi/lock"], a + 0.33, 0.8)
    for j in range(len(label) // 2): add(S["scifi/typing"], a + 0.33 + j * 0.035, 0.35, 0.2)
for a, label in HUD.SHOW_TAGS:
    add(S["cinematic/open"], a, 0.7)
    for j in range(4): add(S["scifi/typing"], a + 0.15 + j * 0.06, 0.3, -0.2)
for j in range(4): add(S["scifi/lock"], HUD.GRID_T + 0.35 + j * 0.12, 0.7, (-0.3, 0.3, -0.3, 0.3)[j])
add(S["scifi/complete"], HUD.GRID_T + 0.9, 0.8)
add(S["scifi/error"], 59.09, 0.7); add(S["scifi/warning"], 73.63, 0.6)
add(S["cinematic/start"], 0.0, 0.6); add(S["cinematic/complete"], 88.61, 0.6)
sfx = bus[: int(TOT * SR)]
v = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", VOICE, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout,
                  np.float32).reshape(-1, 2).astype(np.float64)
v = np.pad(v, ((0, max(0, len(sfx) - len(v))), (0, 0)))[: len(sfx)]
mix = v + sfx * 0.42
# cut the stray "o que" (35.775-35.93) with a 10 ms crossfade
c0, c1 = int(35.775 * SR), int(35.93 * SR); xf = int(0.01 * SR)
fade = np.linspace(0, 1, xf)[:, None]
joined = mix[c0 - xf:c0] * (1 - fade) + mix[c1 - xf:c1] * fade
mix = np.concatenate([mix[:c0 - xf], joined, mix[c1:]])
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                "afade=t=out:st=89.25:d=0.36,loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), f"{B}/mix_hud.wav"], input=mix.tobytes(), check=True)
print("mix ok", round(len(mix) / SR, 3))
