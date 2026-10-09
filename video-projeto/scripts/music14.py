"""Original high-energy electronic track (electro/future-house), 128 BPM, A major (A–E–F#m–D).
Bar grid anchored so a downbeat lands on the Joel cut (41.48 s) -> the drop; the grid also lands on the
Lima intro (~60.2 s) and the brand card (~62.6 s). Synthesised from scratch (no samples)."""
import numpy as np, subprocess

SR = 44100
BPM = 128
BEAT = 60 / BPM
BAR = 4 * BEAT
DROP = 41.48
TOTAL = 64.8133
OFFSET = DROP - int(DROP / BAR) * BAR           # first downbeat
D = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad/v11"
rng = np.random.default_rng(5)
N = int(TOTAL * SR) + SR
L = np.zeros(N); R = np.zeros(N); PUMP = np.ones(N)


def tt(d): return np.arange(int(d * SR)) / SR


def add(x, t, gl=1.0, gr=None, pump=True):
    i = int(t * SR)
    if i < 0 or i >= N: return
    x = x[: N - i]; gr = gl if gr is None else gr
    p = PUMP[i:i + len(x)] if pump else 1
    L[i:i + len(x)] += x * gl * p; R[i:i + len(x)] += x * gr * p


def filt(x, lo=0, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    if lo: X[f < lo] = 0
    if hi: X *= 1 / (1 + (f / hi) ** 4)
    return np.fft.irfft(X, len(x))


def hz(n): return 440 * 2 ** ((n - 69) / 12)


def saw(f, t, ph=0.0):
    return 2 * ((f * t + ph) % 1) - 1


def kick():
    t = tt(0.35); f = 45 + 160 * np.exp(-t * 38)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    x[:200] += np.linspace(0.6, 0, 200) * rng.standard_normal(200) * 0.3
    return np.tanh(1.6 * x) * 0.95


def clap():
    t = tt(0.25); n = filt(rng.standard_normal(len(t)), 1000, 6000)
    e = sum(np.exp(-np.maximum(t - d, 0) * 40) * (t >= d) for d in (0, 0.011, 0.022))
    return n * e * 0.22


def hat(open_=False):
    t = tt(0.22 if open_ else 0.05)
    return filt(rng.standard_normal(len(t)), 8000) * np.exp(-t * (16 if open_ else 90)) * (0.07 if open_ else 0.05)


def bass(note, dur):
    t = tt(dur); f = hz(note)
    x = saw(f, t) + 0.5 * saw(f * 1.005, t) + 0.6 * np.sin(2 * np.pi * f / 2 * t)
    x = filt(x, 0, 900) * np.minimum(1, t / 0.005) * np.exp(-t * 4)
    return np.tanh(1.8 * x) * 0.28


def supersaw(notes, dur, bright=1.0):
    t = tt(dur); x = np.zeros(len(t))
    for n in notes:
        for d in (-0.18, -0.11, -0.05, 0, 0.05, 0.11, 0.18):
            x += saw(hz(n) * (1 + d / 100 * 6), t, rng.random())
    x = filt(x, 120, 2500 + 4500 * bright)
    env = np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.05)
    return x * env * 0.012


def pluck(note, dur=0.18):
    t = tt(dur); x = saw(hz(note), t) + 0.4 * saw(hz(note) * 2.003, t)
    return filt(x, 300, 5000) * np.exp(-t * 22) * 0.07


def riser(dur):
    t = tt(dur); n = filt(rng.standard_normal(len(t)), 2000)
    sw = np.sin(2 * np.pi * np.cumsum(300 + 1700 * (t / dur) ** 2) / SR)
    return (0.5 * n + 0.3 * sw) * (t / dur) ** 2.5 * 0.35


def impact():
    t = tt(2.5); x = np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-t * 6)) / SR) * np.exp(-t * 2.2)
    x += filt(rng.standard_normal(len(t)), 200, 4000) * np.exp(-t * 3) * 0.25
    return x * 0.8


prog = [[57, 61, 64], [52, 56, 59], [54, 57, 61], [50, 54, 57]]     # A, E, F#m, D
roots = [33, 28, 30, 26]
nb = int((TOTAL - OFFSET) / BAR) + 2

# sidechain pump curve from the kick grid (only once the kick plays)
for b in range(nb):
    t0 = OFFSET + b * BAR
    if t0 < 10.3: continue
    for k in range(4):
        i = int((t0 + k * BEAT) * SR); n = int(0.22 * SR)
        if 0 <= i < N:
            seg = 1 - 0.6 * np.exp(-np.arange(min(n, N - i)) / SR * 14)
            PUMP[i:i + len(seg)] = np.minimum(PUMP[i:i + len(seg)], seg)

for b in range(-1, nb):
    t0 = OFFSET + b * BAR
    if t0 + BAR < 0: continue
    c = b % 4
    intro = t0 < 10.3
    build = 37.73 <= t0 < DROP
    drop = t0 >= DROP - 0.01
    # drums
    for k in range(4):
        tb = t0 + k * BEAT
        if not intro and not (build and t0 + BAR > DROP - BAR / 2 and k >= 2):
            add(kick(), tb, 1.0, pump=False)
        if not intro and k in (1, 3): add(clap(), tb, 0.8, 1.0)
        add(hat(True), tb + BEAT / 2, 0.8, 1.0)
        for s in range(4):
            if not intro or s % 2 == 0: add(hat(), tb + s * BEAT / 4, 1.0 if s % 2 else 0.7)
    # bass: offbeat 8ths
    if not intro:
        for k in range(4):
            add(bass(roots[c] + 12, BEAT / 2 * 0.9), t0 + k * BEAT + BEAT / 2, 1.0)
    # chords
    bright = 0.15 if intro else (1.0 if drop else 0.45)
    if intro:
        add(supersaw([n - 12 for n in prog[c]], BAR, bright) * 0.8, t0, 0.9, 1.0)
    else:
        for k in range(4):                       # pumping stabs
            add(supersaw(prog[c], BEAT * 0.95, bright) * (1.6 if drop else 1.0), t0 + k * BEAT, 0.9, 1.0)
    # arp plucks (16ths) in the drop and lightly in the groove
    if drop or (not intro and not build):
        arp = prog[c] + [prog[c][0] + 12]
        for s in range(16):
            g = 1.0 if drop else 0.45
            add(pluck(arp[s % 4] + 12) * g, t0 + s * BEAT / 4, 0.7 if s % 2 else 1.0, 1.0 if s % 2 else 0.7)
    # build: snare roll
    if build:
        for s in range(16):
            dens = 1 if t0 + BAR <= DROP - BAR else 2
            for r in range(dens):
                add(clap() * (0.35 + 0.65 * s / 16), t0 + s * BEAT / 4 + r * BEAT / 8, 0.7, 0.8)

add(riser(DROP - 37.73), 37.73, 1.0, pump=False)
add(impact(), DROP, 1.0, pump=False)
add(impact() * 0.7, 10.3, 1.0, pump=False)       # Hilária intro opens the groove
add(impact() * 0.6, 62.61, 1.0, pump=False)      # brand card

st = np.stack([L, R], 1)[: int(TOTAL * SR)]
st /= np.max(np.abs(st)) + 1e-9
st *= 0.85
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", f"afade=t=in:d=1.0,afade=t=out:st={TOTAL - 1.6}:d=1.6,loudnorm=I=-16:TP=-1.5,aresample=48000",
                f"{D}/music14.wav"], input=st.astype(np.float64).tobytes(), check=True)
print("music14 ok, offset", round(OFFSET, 3))
