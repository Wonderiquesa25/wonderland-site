"""Procedural foley (original, royalty-free) placed on the v11 pre-intro timeline,
then stretched to the final timeline (silent gaps for the four intros)."""
import numpy as np, subprocess

SR = 48000
D = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad/v11"
rng = np.random.default_rng(7)
INTRO, CARD = 2.3, 2.2
INTROS = [10.3, 20.0, 37.95, 54.1333]
PRE = 54.1333


def t(n): return np.arange(n) / SR


def bp(x, lo, hi):
    """FFT band-pass (zero-phase, fine for short one-shots)."""
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def env(n, a, d):
    e = np.ones(n); ka = max(int(a * SR), 1); kd = max(int(d * SR), 1)
    e[:ka] = np.linspace(0, 1, ka); e[-kd:] *= np.linspace(1, 0, kd)
    return e


def res(x, f0, q=30):
    """bank of damped resonances excited by x (convolution with decaying sines)."""
    n = int(0.12 * SR); tt = t(n)
    k = np.sin(2 * np.pi * f0 * tt) * np.exp(-tt * f0 / q)
    return np.convolve(x, k)[: len(x)]


def norm(x, peak):
    m = np.max(np.abs(x)) + 1e-9
    return x / m * peak


def click(peak=0.5, lo=1500, hi=7000, dur=0.025):
    n = int(dur * SR); x = rng.standard_normal(n) * np.exp(-t(n) * 260)
    return norm(bp(x, lo, hi), peak)


def thump(peak=0.6, f=95, dur=0.18):
    n = int(dur * SR); tt = t(n)
    x = np.sin(2 * np.pi * f * tt * (1 - 0.3 * tt)) * np.exp(-tt * 28)
    x += 0.25 * bp(rng.standard_normal(n), 300, 2500) * np.exp(-tt * 90)
    return norm(x, peak)


def rustle(dur, peak=0.3, lo=900, hi=6000, grain=35):
    n = int(dur * SR); x = bp(rng.standard_normal(n), lo, hi)
    g = np.repeat(rng.random(int(dur * grain) + 2) ** 2, int(SR / grain) + 1)[:n]
    g = np.convolve(g, np.ones(400) / 400, "same")
    return norm(x * g * env(n, 0.05, 0.08), peak)


def creak(dur, peak=0.35, rate=(35, 70), f=(420, 950)):
    n = int(dur * SR); x = np.zeros(n); pos = 0.0
    while pos < n - 1:
        r = np.interp(pos / n, [0, 0.5, 1], [rate[0], rate[1], rate[0] * 0.8]) * (1 + 0.25 * rng.standard_normal())
        x[int(pos)] = 1 + 0.4 * rng.standard_normal(); pos += SR / max(r, 10)
    y = res(x, f[0], 18) + 0.6 * res(x, f[1], 25) + 0.3 * res(x, 2100, 40)
    return norm(y * env(n, 0.04, 0.12), peak)


def door_handle():
    a = click(0.55, 1200, 6000, 0.03)
    ring = np.sin(2 * np.pi * 2650 * t(4000)) * np.exp(-t(4000) * 45) * 0.15
    a = np.pad(a, (0, 4000)); a[:4000] += ring
    b = click(0.45, 800, 4000, 0.04)
    out = np.zeros(int(0.2 * SR)); out[:len(a)] += a; out[int(0.09 * SR):int(0.09 * SR) + len(b)] += b
    return out


def footstep(peak=0.35):
    h = click(0.8, 1800, 8000, 0.018); th = thump(0.5, 120, 0.12)
    out = np.zeros(len(th) + 600); out[:len(th)] += th; out[200:200 + len(h)] += h * 0.6
    return norm(out, peak)


def typing(dur, peak=0.18, rate=9):
    n = int(dur * SR); out = np.zeros(n); p = 0.05
    while p < dur - 0.05:
        c = click(1.0, 1500, 5000, 0.02) * (0.6 + 0.4 * rng.random())
        i = int(p * SR); out[i:i + len(c)] += c[: n - i]
        p += rng.exponential(1 / rate) + 0.03
    return norm(out, peak)


def ratchet(dur, peak=0.4, r0=55, r1=140):
    n = int(dur * SR); out = np.zeros(n); p = 0.0
    while p < dur - 0.01:
        c = click(1.0, 2500, 9000, 0.008); i = int(p * SR); out[i:i + len(c)] += c[: n - i]
        p += 1 / np.interp(p / dur, [0, 1], [r0, r1])
    out += 0.25 * bp(rng.standard_normal(n), 3000, 9000) * env(n, 0.05, 0.1)   # metal zip hiss
    return norm(out * env(n, 0.01, 0.05), peak)


def snap():
    z = ratchet(0.18, 0.5, 180, 260); k = click(0.7, 1000, 6000, 0.04)
    out = np.zeros(len(z) + len(k)); out[:len(z)] += z; out[len(z) - 200:len(z) - 200 + len(k)] += k
    return out


# ---------------- cue sheet (pre-intro seconds) ----------------
cues = [
    (0.02, door_handle(), 1.0),                         # Lourenço opens the door
    (0.14, creak(0.6, 0.28, (25, 45), (310, 720)), 1.0),
    (1.08, rustle(0.55, 0.32), 1.0),                    # Hilária swings feet off the desk
    (1.34, thump(0.55, 85, 0.2), 1.0), (1.46, thump(0.4, 100, 0.18), 1.0),
    (1.70, creak(0.75, 0.3, (40, 80), (520, 1200)), 1.0),   # settles in the chair
    (1.95, rustle(0.5, 0.2, 400, 3000, 20), 1.0),
    (3.00, typing(3.3), 1.0),                           # typing
    (32.85, rustle(0.6, 0.25), 1.0),                    # Lourenço sits at the table
    (33.25, creak(0.7, 0.32, (30, 60), (380, 860)), 1.0),
]
for s in [45.55, 46.0, 46.45, 46.92, 47.38, 47.8, 48.15]:   # Lima walks in
    cues.append((s, footstep(0.3 + 0.05 * rng.random()), 1.0))
cues += [
    (48.35, rustle(1.25, 0.34, 300, 4000, 25), 1.0),    # rummages in the bag
    (49.30, click(0.5, 1500, 6000, 0.03), 1.0),         # grabs the tape case
    (50.58, ratchet(0.75, 0.42, 60, 150), 1.0),         # pulls the tape out
    (51.58, snap(), 1.0),                               # tape snaps back
]

pre = np.zeros(int(PRE * SR) + SR)
for s, x, g in cues:
    i = int(s * SR); pre[i:i + len(x)] += g * x[: len(pre) - i]

# stretch to the final timeline
parts, prev = [], 0.0
for T in INTROS:
    parts.append(pre[int(prev * SR):int(T * SR)]); parts.append(np.zeros(int(INTRO * SR))); prev = T
parts.append(np.zeros(int(CARD * SR)))
fin = np.concatenate(parts)
st = np.stack([fin, fin], 1).astype(np.float32)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                "-af", "aecho=0.8:0.4:35|60:0.18|0.10,volume=0.5", f"{D}/foley.wav"],
               input=st.tobytes(), check=True)
print("foley ok", len(fin) / SR)
