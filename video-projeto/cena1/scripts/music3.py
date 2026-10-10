"""Original cinematic underscore for Cena 1 (synthesised, royalty-free). 80 BPM, D minor -> warm Bb/F lift at 'orgulho'.
Sections follow the edit: night worry (0-12.8) | reality of security (12.8-35.6) | the fence, technical (35.6-74.6) | pride (74.6-end)."""
import numpy as np, subprocess, sys
C = sys.argv[1]; SR = 48000; TOT = 89.78; BPM = 80; BEAT = 60 / BPM
N = int(TOT * SR) + SR; L = np.zeros(N); R = np.zeros(N); rng = np.random.default_rng(3)
S1, S2, S3 = 12.845, 35.612, 74.579


def tt(d): return np.arange(int(d * SR)) / SR
def hz(n): return 440 * 2 ** ((n - 69) / 12)
def add(x, t, gl=1.0, gr=None):
    i = int(t * SR)
    if i >= N: return
    x = x[:N - i]; gr = gl if gr is None else gr; L[i:i + len(x)] += x * gl; R[i:i + len(x)] += x * gr
def lp(x, fc):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X /= (1 + (f / fc) ** 4); return np.fft.irfft(X, len(x))


def pad(notes, dur, bright):
    t = tt(dur); x = np.zeros(len(t))
    for n in notes:
        for d in (-0.08, 0, 0.08):
            f = hz(n) * (1 + d / 100 * 3)
            x += np.sin(2 * np.pi * f * t + rng.random() * 6) + 0.25 * np.sin(2 * np.pi * 2 * f * t) * bright
    env = np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.2)
    return lp(x, 900 + 2500 * bright) * env * 0.035


def piano(n, dur=2.5, v=1.0):
    t = tt(dur); f = hz(n); x = sum(a * np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.6 + k * 0.8)) for k, a in [(1, 1), (2, .4), (3, .15), (4, .07)])
    return x * (1 - np.exp(-t * 300)) * 0.10 * v


def pulse():
    t = tt(0.45); f = 42 + 50 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 0.55


def tick():
    t = tt(0.04); n = rng.standard_normal(len(t)); n = n - lp(n, 6000)
    return n * np.exp(-t * 120) * 0.035


drone = tt(TOT); add((np.sin(2 * np.pi * hz(38) * drone) + 0.4 * np.sin(2 * np.pi * hz(50) * drone)) * 0.05
                    * np.minimum(1, drone / 3), 0)
prog_dark = [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]]        # Dm Bb F C
prog_lift = [[46, 50, 53, 58], [53, 57, 60, 65], [48, 52, 55, 60], [50, 53, 57, 62]]   # Bb F C Dm (open voicings)
BAR = 4 * BEAT; t0 = 0.0; b = 0
while t0 < TOT:
    sec = 0 if t0 < S1 else 1 if t0 < S2 else 2 if t0 < S3 else 3
    prog = prog_lift if sec == 3 else prog_dark
    ch = prog[b % 4]
    add(pad(ch, BAR + 1.2, [0.1, 0.3, 0.45, 0.9][sec]), t0, 0.9, 1.0)
    if sec == 0:                                   # sparse night piano
        for k, n in enumerate([ch[2] + 12, ch[1] + 12]): add(piano(n, v=0.7), t0 + k * 2 * BEAT, 1.0, 0.8)
    if sec >= 1:                                   # heartbeat pulse
        for k in (0, 2) if sec < 3 else (0, 1, 2, 3):
            add(pulse() * (0.8 if sec == 1 else 1.0), t0 + k * BEAT)
            add(pulse() * 0.45, t0 + k * BEAT + 0.28)
    if sec == 2:                                   # clock-like ticks: precision / technique
        for s in range(8): add(tick(), t0 + s * BEAT / 2, 0.7 if s % 2 else 1.0, 1.0 if s % 2 else 0.7)
    if sec == 3:                                   # warm arpeggio of pride
        for s in range(8): add(piano(ch[s % 4] + 12, 1.6, 0.55), t0 + s * BEAT / 2, 0.8 + 0.2 * (s % 2), 1.0 - 0.2 * (s % 2))
    t0 += BAR; b += 1
# soft swell into the cut to scene 2
t = tt(3.0); sw = lp(rng.standard_normal(len(t)), 3000) * (t / 3) ** 3 * 0.12; add(sw, TOT - 3.0)
st = np.stack([L, R], 1)[: int(TOT * SR)]; st /= np.abs(st).max() + 1e-9
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                f"afade=t=in:d=2,afade=t=out:st={TOT - 0.6}:d=0.6,loudnorm=I=-24:TP=-3", "-ar", str(SR), f"{C}/work/music3.wav"],
               input=st.astype(np.float64).tobytes(), check=True)
print("music ok")
