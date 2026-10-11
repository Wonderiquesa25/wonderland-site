"""Original uplifting-epic score for scene 1 (synthesised, no samples): dramatic AND joyful.
D major, 100 BPM, I-V-vi-IV (D-A-Bm-G). Piano arpeggios from the start, pulsing strings from 17.6 s, toms build from 57 s,
big bright chorus (strings + brass + heroic melody + timpani) at 67.2 s ("perímetro 100% blindado... orgulho enorme"),
filtered fade inside the CCTV transition."""
import sys, numpy as np, subprocess
from scipy.signal import butter, sosfilt, fftconvolve
SR = 48000; BPM = 100; BEAT = 60 / BPM; BAR = 4 * BEAT
END = float(sys.argv[1]); FADE_END = float(sys.argv[2]); OUT = sys.argv[3]
N = int((FADE_END + 2) * SR); L = np.zeros(N); R = np.zeros(N); rng = np.random.default_rng(7)
B, C, D, E = 17.6, 31.8, 57.0, 67.2
def t(d): return np.arange(int(d * SR)) / SR
def flt(x, lo=None, hi=None, o=2):
    s = butter(o, [lo, hi], "band", fs=SR, output="sos") if lo and hi else butter(o, lo or hi, "high" if lo else "low", fs=SR, output="sos")
    return sosfilt(s, x)
def env(n, a, r):
    e = np.ones(n); na, nr = min(n, int(a * SR)), min(n, int(r * SR)); e[:na] = np.linspace(0, 1, na); e[n - nr:] *= np.linspace(1, 0, nr); return e
def add(x, at, gl=1.0, gr=None):
    i = int(at * SR)
    if i >= N: return
    x = x[: N - i]; gr = gl if gr is None else gr; L[i:i + len(x)] += x * gl; R[i:i + len(x)] += x * gr
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def saw(f, d, det=(-0.1, 0, 0.1)):
    tt = t(d); return sum(2 * ((tt * f * 2 ** (k / 12) + rng.random()) % 1) - 1 for k in det) / len(det)
def sine(f, d): return np.sin(2 * np.pi * f * t(d))
def piano(m, d, g):
    f = hz(m); tt = t(d); x = sum(np.sin(2 * np.pi * f * h * tt) * np.exp(-tt * (2.2 + 1.3 * h)) / h ** 1.2 for h in range(1, 6))
    return x * env(len(tt), 0.004, 0.08) * g
PROG = [[50, 54, 57], [45, 49, 52], [47, 50, 54], [43, 47, 50]]   # D A Bm G
def chord_at(k): return PROG[int(k // BAR) % 4]
# 1) piano arpeggios all the way (soft at start, brighter later)
k = 0.0
while k < END:
    ch = chord_at(k); bright = 0.6 + 0.4 * min(1, k / E)
    pat = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24, ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[2] + 12]
    for s, m in enumerate(pat):
        st = k + s * BEAT / 2
        if st < END: add(piano(m, 1.4, 0.05 * bright), st, 1.1 - 0.2 * (s % 2), 0.9 + 0.2 * (s % 2))
    add(piano(ch[0] - 12, 2.6, 0.07), k)                                   # bass note
    k += BAR
# 2) warm string pad from the start (soft), swelling later
k = 0.0
while k < END:
    ch = chord_at(k); g = 0.035 if k < B else (0.05 if k < E else 0.10)
    pd = sum(saw(hz(n), BAR + 0.3) for n in ch) / 3
    add(flt(pd, hi=1600 if k < E else 3800) * env(int((BAR + 0.3) * SR), 0.5, 0.5) * g, k, 0.9, 1.1)
    k += BAR
# 3) pulsing 8th-note strings from B (the 'drive')
k = B - (B % BAR) + BAR if B % BAR else B
while k < END:
    ch = chord_at(k); build = np.clip((k - B) / (E - B), 0, 1)
    for s in range(8):
        st = k + s * BEAT / 2
        if st >= END: break
        x = flt(saw(hz(ch[s % 2 * 2] - 12 if s % 4 else ch[0] - 12), BEAT / 2 * 0.9), hi=900 + 2200 * build) * env(int(BEAT / 2 * 0.9 * SR), 0.004, 0.05)
        add(x * (0.06 + 0.05 * build) * (1.25 if s % 2 == 0 else 1), st)
    k += BAR
# 4) percussion: soft kick+clap groove from C, toms build from D
def kick(g):
    tt = t(0.35); return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-tt * 35)) / SR) * np.exp(-tt * 10) * g
def clap(g):
    n = flt(rng.standard_normal(int(0.18 * SR)), 900, 6000); return n * np.exp(-t(0.18) * 22) * g
def tom(f, g):
    tt = t(0.6); return np.sin(2 * np.pi * np.cumsum(f + f * 0.6 * np.exp(-tt * 20)) / SR) * np.exp(-tt * 6) * g
k = C
while k < END:
    for b in range(4):
        st = k + b * BEAT
        if st >= END: break
        if b in (0, 2): add(kick(0.30 if k < E else 0.42), st)
        if b in (1, 3): add(clap(0.07 if k < E else 0.10), st, 0.8, 1.2)
        if D <= st < E: add(tom(90 + 25 * (b % 2), 0.18 + 0.15 * (st - D) / (E - D)), st + BEAT / 2, 1.2, 0.8)
    k += BAR
# riser + snare roll into E
d = E - D; rz = flt(rng.standard_normal(int(d * SR)), 500, 9000) * (t(d) / d) ** 3 * 0.09; add(rz, D)
for i in range(16): add(clap(0.03 + 0.05 * i / 16), E - BAR / 2 + i * BAR / 32)
# 5) chorus at E: brass + bright strings + heroic melody + timpani
MEL = [(74, 2), (76, 1), (78, 1), (76, 2), (73, 2), (71, 2), (73, 1), (74, 1), (71, 2), (69, 2), (71, 1), (74, 1), (78, 2), (76, 4)]
k = E
while k < END:
    ch = chord_at(k); dd = min(BAR, END - k + 1.5)
    br = sum(saw(hz(n), dd, det=(-0.05, 0.05)) for n in ch) / 3
    add(flt(br, hi=2200) * env(int(dd * SR), 0.25, 0.6) * 0.09, k, 0.95, 1.05)
    hi_str = sum(saw(hz(n + 12), dd, det=(-0.12, 0, 0.12)) for n in ch) / 3
    add(flt(hi_str, hi=5000) * env(int(dd * SR), 0.3, 0.6) * 0.05, k, 1.1, 0.9)
    add((sine(hz(ch[0] - 24), dd) + 0.3 * sine(hz(ch[0] - 12), dd)) * env(int(dd * SR), 0.05, 0.5) * 0.22, k)
    tt = t(1.3); tim = np.sin(2 * np.pi * np.cumsum(55 + 35 * np.exp(-tt * 9)) / SR) * np.exp(-tt * 3.2)
    add(tim * (0.45 if k == E else 0.25), k)
    k += BAR
st = E
for m, beats in MEL:
    if st >= END: break
    d_ = beats * BEAT; tt = t(d_)
    x = (np.sin(2 * np.pi * hz(m) * tt) + 0.45 * np.sin(4 * np.pi * hz(m) * tt) + 0.2 * np.sin(6 * np.pi * hz(m) * tt)) * (1 + 0.005 * np.sin(2 * np.pi * 5.5 * tt))
    add(x * env(len(tt), 0.06, 0.25) * 0.05, st, 1.05, 0.95); st += d_
# cymbal swell + impact at E
tt = t(2.5); add(flt(rng.standard_normal(len(tt)), 3000, 14000) * np.exp(-tt * 1.6) * 0.08, E)
add(np.sin(2 * np.pi * np.cumsum(32 + 70 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 2) * 0.45, E - 0.01)
mix = np.stack([L, R], 1)
irt = t(2.2); ir = rng.standard_normal((len(irt), 2)) * np.exp(-irt * 3)[:, None]
ir[:, 0] = flt(ir[:, 0], hi=7000); ir[:, 1] = flt(ir[:, 1], hi=7000)
wet = np.stack([fftconvolve(mix[:, c], ir[:, c])[:N] for c in range(2)], 1); wet *= np.abs(mix).max() / (np.abs(wet).max() + 1e-9)
mix = mix * 0.82 + wet * 0.3
g = np.ones(N); i0, i1 = int(END * SR), int(FADE_END * SR); g[i0:i1] = np.linspace(1, 0, i1 - i0) ** 1.5; g[i1:] = 0
mix *= g[:, None]; mix /= np.abs(mix).max() + 1e-9; mix *= 0.89
subprocess.run(["ffmpeg","-y","-v","error","-f","f64le","-ar",str(SR),"-ac","2","-i","-","-ar",str(SR),OUT], input=mix.tobytes(), check=True)
