"""Voice v2 — SAME voice treatment in both parts.
Part 1: WPE-dereverbed dialogue (dialogue5) -> match EQ to Lourenço in scene 2 -> common chain (+ tempo 1.06 as before).
Scene 2: Lourenço region (12.6-41.48 s) -> WPE -> common chain (no tempo) -> fine LTAS match to the new part-1 voice ->
same speech loudness -> crossfaded back. Common chain = denoise, subtle deepening (pitch 0.955, formants preserved),
close-mic presence EQ (warmth, less boxiness, presence), de-ess, gate, compression."""
import sys, subprocess, numpy as np
S = sys.argv[1]; SR = 48000; F = f"{S}/final"; V = f"{S}/v11"; C = f"{S}/c1"; O = f"{S}/v2"
DR = f"{S}/tscripts/dereverb.py"
def load(p, ss=None, t=None, ch=1):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss else []) + (["-t", str(t)] if t else []) + ["-i", p, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32).astype(np.float64)
    return x.reshape(-1, ch) if ch > 1 else x
def af(x, chain):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", chain, "-ar", str(SR), "-f", "f64le", "-"],
                                        input=x.tobytes(), capture_output=True).stdout, np.float64).copy()
def save(x, p, ch=1):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", str(ch), "-i", "-", "-c:a", "pcm_s24le", p], input=x.tobytes(), check=True)
N = 4096; f = np.fft.rfftfreq(N, 1 / SR)
def ltas(x):
    fr = x[:len(x) // N * N].reshape(-1, N); e = np.sqrt((fr ** 2).mean(1)); fr = fr[e > np.percentile(e, 55)]
    return np.sqrt((np.abs(np.fft.rfft(fr * np.hanning(N), axis=1)) ** 2).mean(0))
def match_fir(src, ref, amount, lo=-6, hi=10):
    r = 20 * np.log10((ltas(ref) / ltas(ref).sum()) / (ltas(src) / ltas(src).sum()) + 1e-12)
    sm = np.array([r[(f > fc / 1.26) & (f < fc * 1.26)].mean() if fc > 20 else 0 for fc in f])
    g = np.clip(amount * sm, lo, hi); g[f < 80] = 0; g[f > 9000] = np.minimum(g[f > 9000], 0)
    ir = np.fft.irfft(10 ** (g / 20), N); return np.roll(ir, N // 2) * np.hanning(N)
def speech_rms(x):
    h = int(0.05 * SR); e = np.sqrt(np.array([np.mean(x[i:i + h] ** 2) for i in range(0, len(x) - h, h)]))
    return np.sqrt(np.mean(e[e > np.percentile(e, 50)] ** 2))
COMMON = ("rubberband={tempo}pitch=0.955:formant=preserved:transients=smooth:detector=soft:window=standard:pitchq=quality,"
          "equalizer=f=140:t=q:w=0.9:g=2.5,equalizer=f=400:t=q:w=1.1:g=-2.5,equalizer=f=2800:t=q:w=0.9:g=2.5,equalizer=f=5000:t=q:w=1:g=1.2,"
          "deesser=i=0.35,agate=threshold=0.02:ratio=3:attack=4:release=160:range=0.15:knee=4,"
          "acompressor=threshold=-22dB:ratio=3:attack=5:release=100:makeup=2,alimiter=limit=0.9")

# ---------------- part 1 ----------------
x = load(f"{C}/work/dialogue6.wav"); ref = load(f"{V}/dial14.wav", 12.6, 28.8)
y = np.convolve(x, match_fir(x, ref, 0.7), mode="same"); y = y / (np.abs(y).max() + 1e-9) * 0.7
c0, c1 = int(35.775 * SR), int(35.93 * SR); xf = int(0.01 * SR); fd = np.linspace(0, 1, xf)       # same edit as before (timeline kept)
y = np.concatenate([y[:c0 - xf], y[c0 - xf:c0] * (1 - fd) + y[c1 - xf:c1] * fd, y[c1:]])
p1 = af(y, "afftdn=nr=18:nf=-42:tn=1:ad=0.6,aexciter=amount=0.8:drive=4:blend=0:freq=3200,afftdn=nr=8:nf=-45:tn=1,"
           + COMMON.format(tempo="tempo=1.06:") + ",loudnorm=I=-16:TP=-2:LRA=8")
save(p1, f"{O}/voice_p1b.wav"); print("part1 voice", round(len(p1) / SR, 3), "s (old 84.539)")

# ---------------- scene 2: Lourenço ----------------
s2 = load(f"{F}/s2_nomusic.wav", ch=2); A, B = int(12.6 * SR), int(41.48 * SR); pad = 2400
reg = s2[A - pad:B + pad].mean(1)
save(reg, f"{O}/s2_lou_raw.wav"); subprocess.run(["python3", DR, f"{O}/s2_lou_raw.wav", f"{O}/s2_lou_wpe.wav", "10"], check=True)
subprocess.run(["python3", DR.replace("dereverb.py", "dereverb_ss.py"), f"{O}/s2_lou_wpe.wav", f"{O}/s2_lou_ss.wav", "0.6", "1.5"], check=True)
w = load(f"{O}/s2_lou_ss.wav")
w = af(w, "afftdn=nr=10:nf=-45:tn=1," + COMMON.format(tempo=""))[: len(reg)]
w = np.pad(w, (0, len(reg) - len(w)))
p1_raw_speed = load(f"{O}/voice_p1b.wav")
w = np.convolve(w, match_fir(w, p1_raw_speed, 1.0, -12, 8), mode="same")                       # land on the SAME tone as part 1
w *= speech_rms(p1_raw_speed) / speech_rms(w)                                                  # same speech level as part 1
# fit into the scene-2 bus at the level the original Lourenço had there
w *= speech_rms(reg) / speech_rms(w)
k = pad; fi = np.linspace(0, 1, k)
new = w.copy(); new[:k] = reg[:k] * (1 - fi) + w[:k] * fi; new[-k:] = w[-k:] * (1 - fi) + reg[-k:] * fi
out = s2.copy(); out[A - pad:B + pad] = new[:, None]
save(out.reshape(-1), f"{O}/s2_v2_pre.wav", 2)
z1, z2 = ltas(p1_raw_speed), ltas(load(f"{O}/s2_v2_pre.wav", 12.6, 28.8))
rr = 20 * np.log10((z1 / z1.sum()) / (z2 / z2.sum()) + 1e-12)
for lo, hi in [(120, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000)]:
    m = (f >= lo) & (f < hi); print(f"part1-vs-scene2 Lourenço {lo}-{hi} Hz: {rr[m].mean():+.1f} dB")
