"""Part-1 voice mastering: matching EQ toward the Scene-2 reference (partial, smoothed, capped), harmonic exciter,
cut of the stray 'o que', then speech-aware tempo 1.06 + subtle deepening (pitch -0.8 st, formants preserved) + warmth."""
import sys, subprocess, numpy as np
F, C, V = sys.argv[1], sys.argv[2], sys.argv[3]; SR = 48000
def load(p, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss else []) + (["-t", str(t)] if t else []) + ["-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).astype(np.float64)
def ltas(x, N=4096):
    fr = x[:len(x) // N * N].reshape(-1, N); e = np.sqrt((fr ** 2).mean(1)); fr = fr[e > np.percentile(e, 55)]
    return np.sqrt((np.abs(np.fft.rfft(fr * np.hanning(N), axis=1)) ** 2).mean(0))
x = load(f"{C}/work/dialogue3.wav"); ref = load(f"{V}/dial14.wav", 12.6, 28.8)
N = 4096; f = np.fft.rfftfreq(N, 1 / SR)
r = 20 * np.log10((ltas(ref) / ltas(ref).sum()) / (ltas(x) / ltas(x).sum()) + 1e-12)
# 1/3-octave smoothing, 70 % of the difference, capped (+12 dB / -6 dB), no change below 80 Hz / above 12 kHz
sm = np.array([r[(f > fc / 1.26) & (f < fc * 1.26)].mean() if fc > 20 else 0 for fc in f])
g = np.clip(0.7 * sm, -6, 12); g[f < 80] = 0; g[f > 12000] = np.minimum(g[f > 12000], g[np.searchsorted(f, 12000)])
H = 10 ** (g / 20)
# zero-phase FIR from the gain curve, applied by overlap-add
ir = np.fft.irfft(H, N); ir = np.roll(ir, N // 2) * np.hanning(N)
y = np.convolve(x, ir, mode="same")
y = y / (np.abs(y).max() + 1e-9) * 0.7
c0, c1 = int(35.775 * SR), int(35.93 * SR); xf = int(0.01 * SR); fd = np.linspace(0, 1, xf)
y = np.concatenate([y[:c0 - xf], y[c0 - xf:c0] * (1 - fd) + y[c1 - xf:c1] * fd, y[c1:]])
CH = ("afftdn=nr=20:nf=-42:tn=1:ad=0.6,aexciter=amount=0.8:drive=4:blend=0:freq=3200,afftdn=nr=10:nf=-45:tn=1,"
      "rubberband=tempo=1.06:pitch=0.955:formant=preserved:transients=smooth:detector=soft:window=standard:pitchq=quality,"
      "equalizer=f=140:t=q:w=0.9:g=2.5,equalizer=f=380:t=q:w=1.2:g=-1.5,equalizer=f=3000:t=q:w=1:g=1.5,"
      "deesser=i=0.35,agate=threshold=0.02:ratio=3:attack=4:release=160:range=0.18:knee=4,"
      "acompressor=threshold=-21dB:ratio=2.6:attack=6:release=110:makeup=2,alimiter=limit=0.9,loudnorm=I=-16:TP=-2:LRA=8")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", CH, "-ar", str(SR), f"{F}/voice_p1.wav"],
               input=y.tobytes(), check=True)
z = ltas(load(f"{F}/voice_p1.wav")); rr = 20 * np.log10((ltas(ref) / ltas(ref).sum()) / (z / z.sum()) + 1e-12)
for lo, hi in [(120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000)]:
    m = (f >= lo) & (f < hi); print(f"after: {lo}-{hi} Hz ref-vs-voice {rr[m].mean():+.1f} dB")
print("dur", round(len(load(f'{F}/voice_p1.wav')) / SR, 3))
