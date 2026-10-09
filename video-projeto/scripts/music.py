"""Original upbeat afro-house / amapiano-style bed, 120 BPM, A major (A – F#m – D – E).
Synthesised from scratch (no samples) -> fully owned, safe for any platform."""
import numpy as np, subprocess

SR = 48000
BPM = 120
BEAT = 60 / BPM
BAR = 4 * BEAT
OFFSET = 0.2            # first downbeat at 0.2 s so a downbeat lands on the Joel cut (42.2 s)
TOTAL = 65.5333
D = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad/v11"
rng = np.random.default_rng(11)
N = int(TOTAL * SR) + SR
L = np.zeros(N); R = np.zeros(N)


def tt(d): return np.arange(int(d * SR)) / SR


def add(x, t, gl=1.0, gr=None):
    i = int(t * SR)
    if i >= N or i < 0: return
    x = x[: N - i]; gr = gl if gr is None else gr
    L[i:i + len(x)] += x * gl; R[i:i + len(x)] += x * gr


def hp(x, f):
    X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR); X[fr < f] = 0; return np.fft.irfft(X, len(x))


def kick():
    t = tt(0.32); f = 48 + 110 * np.exp(-t * 32)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 0.9


def clap():
    t = tt(0.22); n = hp(rng.standard_normal(len(t)), 900)
    e = np.exp(-t * 28) + 0.6 * np.exp(-np.maximum(t - 0.012, 0) * 30) * (t > 0.012)
    return n * e * 0.28


def shaker(acc):
    t = tt(0.07); return hp(rng.standard_normal(len(t)), 6000) * np.exp(-t * 70) * (0.10 if acc else 0.05)


def openhat():
    t = tt(0.18); return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * 18) * 0.06


def logdrum(freq, dur=0.35):
    t = tt(dur); f = freq * (1 + 0.35 * np.exp(-t * 25))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    return np.tanh(2.2 * x) * 0.38


def keys(freqs, dur):
    t = tt(dur); x = np.zeros(len(t))
    for f in freqs:
        for h, a in [(1, 1), (2, 0.35), (3, 0.12), (4, 0.06)]:
            x += a * np.sin(2 * np.pi * f * h * t + 0.3 * np.sin(2 * np.pi * 5 * t))
    env = (1 - np.exp(-t * 60)) * np.exp(-t * 3.2)
    return x * env * 0.045


def pad(freqs, dur):
    t = tt(dur); x = np.zeros(len(t))
    for f in freqs:
        for det in (-0.6, 0.6):
            x += np.sin(2 * np.pi * (f + det) * t)
    env = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.4)
    return x * env * 0.018


def hz(n): return 440 * 2 ** ((n - 69) / 12)


chords = [[57, 61, 64, 69], [54, 57, 61, 66], [50, 54, 57, 62], [52, 56, 59, 64]]   # A, F#m, D, E
roots = [33, 30, 26, 28]
bass_pat = [0, 0.75, 1.5, 2.5, 3.25]            # syncopated log-drum hits (beats)

nbars = int((TOTAL - OFFSET) / BAR) + 1
for b in range(nbars):
    t0 = OFFSET + b * BAR
    ch = b % 4
    intro = b < 2                     # first 4 s: keys + shakers only (Hilária / door)
    for k in range(4):                # kick on every beat after the intro
        if not intro: add(kick(), t0 + k * BEAT, 0.9)
    if not intro:
        for k in (1, 3): add(clap(), t0 + k * BEAT, 0.8, 1.0)
        for k in range(4): add(openhat(), t0 + k * BEAT + BEAT / 2, 0.7, 1.0)
        for p in bass_pat: add(logdrum(hz(roots[ch]) * (1.5 if p == 2.5 else 1)), t0 + p * BEAT)
    for s in range(16):               # 16th shakers with swing
        add(shaker(s % 4 == 2), t0 + s * BEAT / 4 + (0.02 if s % 2 else 0), 1.0, 0.8)
    for k in (0.5, 1.5, 2.75, 3.5):   # off-beat piano stabs
        add(keys([hz(n) for n in chords[ch]], 0.45), t0 + k * BEAT, 1.0, 0.9)
    add(pad([hz(n) for n in chords[ch][:3]], BAR), t0, 0.9, 1.0)

st = np.stack([L, R], 1)[: int(TOTAL * SR)]
st /= np.max(np.abs(st)) + 1e-9
st *= 0.8
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", f"afade=t=in:d=1.5,afade=t=out:st={TOTAL - 2.2}:d=2.2,loudnorm=I=-18:TP=-2",
                "-ar", str(SR), f"{D}/music.wav"], input=st.astype(np.float64).tobytes(), check=True)
print("music ok")
