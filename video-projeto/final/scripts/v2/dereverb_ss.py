"""Late-reverberation spectral suppression (Lebart / Habets model): late reverb PSD = decayed PSD from DELTA ago;
Wiener-like gain with floor and temporal smoothing. usage: dereverb_ss.py in.wav out.wav [T60] [beta]"""
import sys, subprocess, numpy as np
src, out = sys.argv[1], sys.argv[2]; T60 = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5; BETA = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
SR = 48000; NF, HOP = 1024, 256; DELTA = 0.05; GMIN = 0.28
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f64le", "-"], capture_output=True).stdout, np.float64)
win = np.hanning(NF + 1)[:-1]; nfr = (len(x) - NF) // HOP + 1
X = np.stack([np.fft.rfft(x[i * HOP:i * HOP + NF] * win) for i in range(nfr)])
P = np.abs(X) ** 2
a = np.exp(-0.5 * 6.9 * HOP / SR / (T60 / 2) * 2)          # PSD recursive smoothing
Ps = np.zeros_like(P); acc = P[0]
for i in range(nfr): acc = 0.6 * acc + 0.4 * P[i]; Ps[i] = acc
d = int(DELTA * SR / HOP); decay = np.exp(-2 * 6.9 * DELTA / T60)
Pl = np.zeros_like(P); Pl[d:] = decay * Ps[:-d]
G = np.maximum(1 - BETA * Pl / (Ps + 1e-12), GMIN)
for i in range(1, nfr): G[i] = np.maximum(G[i], 0.5 * G[i - 1])  # no abrupt gain drops (less musical noise)
Y = X * G
y = np.zeros(len(x)); wsum = np.zeros(len(x))
for i in range(nfr):
    y[i * HOP:i * HOP + NF] += np.fft.irfft(Y[i], NF) * win; wsum[i * HOP:i * HOP + NF] += win ** 2
y /= np.maximum(wsum, 1e-3)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s24le", out], input=y.tobytes(), check=True)
