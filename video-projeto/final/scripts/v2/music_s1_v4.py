"""Original cinematic score for scene 1 only (synthesised, no samples). D minor, 90 BPM.
Arc follows the narration: suspense (night worry) -> tension (clock) -> pulsing ostinato (technical part)
-> build -> drama/pride (perimeter 100% shielded) -> filtered fade inside the CCTV transition."""
import sys, numpy as np, subprocess
from scipy.signal import butter, sosfilt, fftconvolve
SR = 48000; BPM = 90; BEAT = 60 / BPM; BAR = 4 * BEAT
END = float(sys.argv[1]); FADE_END = float(sys.argv[2]); OUT = sys.argv[3]
N = int((FADE_END + 2) * SR); L = np.zeros(N); R = np.zeros(N); rng = np.random.default_rng(11)
B, C, D, E = 17.9, 31.9, 57.0, 67.2                       # section starts (scene-1 timeline, seconds)
def t(d): return np.arange(int(d * SR)) / SR
def bp(x, lo=None, hi=None, o=2):
    if lo and hi: s = butter(o, [lo, hi], "band", fs=SR, output="sos")
    elif lo: s = butter(o, lo, "high", fs=SR, output="sos")
    else: s = butter(o, hi, "low", fs=SR, output="sos")
    return sosfilt(s, x)
def env(n, a, r, sus=1.0):
    e = np.ones(n) * sus; na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    e[:na] = np.linspace(0, 1, na) * (sus if na < n else 1); e[n - nr:] *= np.linspace(1, 0, nr); return e
def add(x, at, gl=1.0, gr=None):
    i = int(at * SR); x = x[: max(0, N - i)]; gr = gl if gr is None else gr
    L[i:i + len(x)] += x * gl; R[i:i + len(x)] += x * gr
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def saw(f, d, det=(-0.12, 0, 0.12), ph=None):
    tt = t(d); y = 0
    for k in det: y = y + 2 * ((tt * f * 2 ** (k / 12) + rng.random()) % 1) - 1
    return y / len(det)
def sine(f, d): return np.sin(2 * np.pi * f * t(d))

# chords (MIDI) for the ostinato/drama: Dm, Bb, Gm, A  | drama: Dm, Bb, F, C
PROG1 = [[50, 53, 57], [46, 50, 53], [43, 46, 50], [45, 49, 52]]
PROG2 = [[50, 53, 57, 62], [46, 50, 53, 58], [41, 45, 48, 53], [48, 52, 55, 60]]

# --- A: suspense (0 - E) low drone D1/A1 with slow filter breathing
d = E + 0.5
drone = sine(hz(26), d) * 0.6 + sine(hz(33), d) * 0.35 + bp(saw(hz(38), d), hi=260) * 0.5
lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t(d))
add(drone * lfo * env(len(drone), 3.0, 1.5) * 0.18, 0)
# eerie high pad: detuned sines A5/D6 with slow tremolo, from 0 to C
d = C + 1
pad = (sine(hz(81), d) + sine(hz(81) * 1.004, d) + 0.6 * sine(hz(86), d) + 0.5 * sine(hz(86) * 0.996, d))
pad *= (0.5 + 0.5 * np.sin(2 * np.pi * 0.18 * t(d)))
add(bp(pad, hi=5000) * env(len(pad), 4, 3) * 0.018, 0, 0.8, 1.2)
# heartbeat sub thumps every 2 beats in A, every beat in B
def thump(g):
    tt = t(0.45); f = 45 + 60 * np.exp(-tt * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 9) * g
k = 2.0
while k < C:
    add(thump(0.30), k); add(thump(0.20), k + 0.28)
    k += 2 * BEAT if k < B else BEAT * 2
# --- B: clock tick (8ths) from B, continues under C
def tick(g):
    n = bp(rng.standard_normal(int(0.03 * SR)), 2500, 7000) * np.exp(-t(0.03) * 160); return n * g
k = B; i = 0
while k < E:
    add(tick(0.10 if i % 2 == 0 else 0.06), k, 0.7 if i % 2 else 1.0, 1.0 if i % 2 else 0.7); k += BEAT / 2; i += 1
# --- C/D: pulsing string-like ostinato in 16ths on the chord roots/thirds
k = C; bar = 0
while k < E:
    ch = PROG1[bar % 4]; build = np.clip((k - C) / (E - C), 0, 1)
    for s in range(16):
        st = k + s * BEAT / 4
        if st >= E: break
        note = ch[[0, 0, 1, 0, 2, 0, 1, 0, 0, 0, 1, 0, 2, 1, 0, 2][s]] - 12
        x = bp(saw(hz(note), BEAT / 4 * 0.95), hi=700 + 2200 * build) * env(int(BEAT / 4 * 0.95 * SR), 0.005, 0.06)
        add(x * (0.10 + 0.06 * build) * (1.2 if s % 4 == 0 else 1), st, 0.9, 1.1)
    # sustained low string pad under ostinato
    pd = sum(saw(hz(n - 12), BAR) for n in ch) / 3
    add(bp(pd, hi=900 + 1500 * build) * env(int(BAR * SR), 0.6, 0.6) * (0.06 + 0.04 * build), k)
    # taiko-ish low hit on bar starts
    tt = t(0.9); th = np.sin(2 * np.pi * np.cumsum(55 + 50 * np.exp(-tt * 18)) / SR) * np.exp(-tt * 5)
    th = th + bp(rng.standard_normal(len(tt)), 80, 600) * np.exp(-tt * 14) * 0.4
    add(th * (0.28 + 0.25 * build), k); 
    if k >= D: add(th * 0.22, k + 2 * BEAT); add(th * 0.16, k + 3.5 * BEAT)
    k += BAR; bar += 1
# --- D: riser into E
d = E - D; rz = bp(rng.standard_normal(int(d * SR)), 400, 9000) * (t(d) / d) ** 3 * 0.10
sw = sine(1, d) * 0; ff = 200 + 1800 * (t(d) / d) ** 2; sw = np.sin(2 * np.pi * np.cumsum(ff) / SR) * (t(d) / d) ** 2 * 0.03
add(rz + sw, D)
# --- E: drama / pride — big chords, brass-like swells, low strings, timpani rolls
k = E; bar = 0
while k < END:
    ch = PROG2[bar % 4]; dd = min(BAR, END - k + 1.5)
    strings = sum(saw(hz(n), dd, det=(-0.15, -0.05, 0.05, 0.15)) for n in ch) / len(ch)
    add(bp(strings, hi=3500) * env(int(dd * SR), 0.35, 0.8) * 0.11, k, 1.0, 0.9)
    brass = sum(saw(hz(n - 12), dd, det=(-0.06, 0.06)) for n in ch[:3]) / 3
    sweep = 400 + 1600 * np.sin(np.pi * np.clip(t(dd) / dd, 0, 1)) ** 1.5
    add(bp(brass, hi=1800) * env(int(dd * SR), 0.8, 0.9) * 0.10 * (0.6 + 0.4 * sweep / 2000), k, 0.9, 1.0)
    bass = sine(hz(ch[0] - 24), dd) + 0.3 * sine(hz(ch[0] - 12), dd)
    add(bass * env(int(dd * SR), 0.1, 0.6) * 0.20, k)
    melody = [[74, 72, 69], [70, 69, 65], [69, 67, 65], [67, 64, 67]][bar % 4]   # simple heroic line
    for j, mn in enumerate(melody):
        md = BEAT * (2 if j == 0 else 1)
        x = (sine(hz(mn), md) + 0.4 * sine(hz(mn) * 2, md) + 0.15 * sine(hz(mn) * 3, md)) * env(int(md * SR), 0.12, 0.3)
        x *= 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t(md))
        add(x * 0.035, k + [0, 2, 3][j] * BEAT, 1.1, 0.8)
    tt = t(1.4); tim = np.sin(2 * np.pi * np.cumsum(48 + 40 * np.exp(-tt * 10)) / SR) * np.exp(-tt * 3.0)
    add(tim * (0.42 if bar == 0 else 0.26), k)
    for s in range(8): add(tim[: int(0.3 * SR)] * 0.04 * (s / 8), k + 3 * BEAT + s * BEAT / 8)   # roll into next bar
    k += BAR; bar += 1
# impact on E (drama entrance)
tt = t(2.5); imp = np.sin(2 * np.pi * np.cumsum(30 + 80 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 1.8)
add(imp * 0.5 + bp(rng.standard_normal(len(tt)), 200, 6000) * np.exp(-tt * 6) * 0.12, E - 0.02)

mix = np.stack([L, R], 1)
# hall reverb: exponentially decaying noise IR
ir_t = t(2.6); ir = rng.standard_normal((len(ir_t), 2)) * np.exp(-ir_t * 2.6)[:, None]; ir[:, 0] = bp(ir[:, 0], hi=6000); ir[:, 1] = bp(ir[:, 1], hi=6000)
wet = np.stack([fftconvolve(mix[:, c], ir[:, c])[:N] for c in range(2)], 1); wet *= np.abs(mix).max() / (np.abs(wet).max() + 1e-9)
mix = mix * 0.8 + wet * 0.35
# master fade: low-pass sweep + fade between END and FADE_END (inside the CCTV transition)
g = np.ones(N); i0, i1 = int(END * SR), int(FADE_END * SR); g[i0:i1] = np.linspace(1, 0, i1 - i0) ** 1.5; g[i1:] = 0
mix *= g[:, None]; mix /= np.abs(mix).max() + 1e-9; mix *= 0.89
subprocess.run(["ffmpeg","-y","-v","error","-f","f64le","-ar",str(SR),"-ac","2","-i","-","-ar",str(SR),OUT], input=mix.tobytes(), check=True)
print("music ok", round(FADE_END, 2))
