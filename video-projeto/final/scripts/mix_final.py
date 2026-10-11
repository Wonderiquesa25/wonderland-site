"""Final mix on the joined timeline: part-1 voice + part-1 SFX + time-travel sound design + Scene-2 audio + CC0 music bed
(filtered build, reverse 'rewind', drop on the downbeat at the reveal, deliberate ending) with ducking under all speech."""
import sys, subprocess, numpy as np
F, L, M = sys.argv[1], sys.argv[2], sys.argv[3]; SR = 48000
T_CUT, T_REVEAL, TOTAL = 84.05, 85.30, 147.533
DROP_TRACK, END_TRACK = 61.253, 122.69                      # downbeats in the music (93.75 BPM)
END_FINAL = T_REVEAL + (END_TRACK - DROP_TRACK)
N = int(TOTAL * SR) + SR
def load(p, ch=2):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    return x.reshape(-1, ch).astype(np.float64)
def place(bus, x, t, g=1.0):
    i = int(t * SR); x = x[: max(0, len(bus) - i)]; bus[i:i + len(x)] += x * g
def fx(x, af):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", af, "-f", "f64le", "-"],
                                        input=x.astype(np.float64).tobytes(), capture_output=True).stdout, np.float64).reshape(-1, 2).copy()
def fade(x, a=0.01, b=0.01):
    x = x.copy(); na, nb = int(a * SR), int(b * SR)
    if na: x[:na] *= np.linspace(0, 1, na)[:, None]
    if nb: x[-nb:] *= np.linspace(1, 0, nb)[:, None]
    return x
voice = np.zeros((N, 2)); sfx = np.zeros((N, 2)); mus = np.zeros((N, 2))
v1 = load(f"{F}/voice_p1.wav", 1).repeat(2, 1)[: int(T_CUT * SR)]; place(voice, fade(v1, 0, 0.03), 0)
s1 = load(f"{F}/sfx_p1.wav")[: int(T_CUT * SR)]; place(sfx, fade(s1, 0, 0.05), 0)
s2 = load(f"{F}/s2_audio.wav"); place(voice, fade(s2, 0.02, 0.3), T_REVEAL, 1.15)
# ---- time-travel sound design ----
tail = voice[int((T_CUT - 7.5) * SR): int(T_CUT * SR)][::-1]            # last 7.5 s of the story, reversed
rw = fx(tail, "rubberband=tempo=6.0:pitch=1.6,highpass=f=300,lowpass=f=6000,volume=0.55")
rw = fade(rw[: int(1.15 * SR)], 0.08, 0.25); place(sfx, rw, T_CUT + 0.12)
t = np.arange(int(2.4 * SR)) / SR; rng = np.random.default_rng(3)
noise = rng.standard_normal((len(t), 2))
swell = fx(noise, "highpass=f=2500,lowpass=f=12000") * ((t / t[-1]) ** 3)[:, None] * 0.35   # reverse-cymbal swell into the flash
place(sfx, swell, T_REVEAL - 2.4)
sub = np.sin(2 * np.pi * np.cumsum(32 + 80 * np.exp(-t * 14)) / SR) * np.exp(-t * 3.2) * 0.9
place(sfx, np.stack([sub, sub], 1), T_REVEAL)
for name, tt, g in [("cinematic/swipe", T_CUT - 0.05, 0.9), ("cinematic/drop", T_REVEAL, 0.9), ("scifi/connect", T_REVEAL + 0.05, 0.5),
                    ("cinematic/open", T_REVEAL + 0.35, 0.5)]:
    x = load(f"{L}/{name}.mp3"); x = x / (np.abs(x).max() + 1e-9) * 0.45; place(sfx, x, tt, g)
whoosh_in = fx(rng.standard_normal((int(0.9 * SR), 2)), "highpass=f=400,lowpass=f=4000")[::-1] * (np.linspace(0, 1, int(0.9 * SR)) ** 2)[:, None] * 0.3
place(sfx, whoosh_in, T_REVEAL - 0.9)                                     # suck-in into the reveal
# ---- music ----
trk = load(f"{M}/t_18_4.wav")
p1 = trk[: int((T_CUT - 0.0) * SR)]
p1 = fx(p1, f"lowpass=f=1600,volume=0.85")                                # softer, filtered bed under the narration
op = trk[int((T_CUT - 4.0) * SR): int(T_CUT * SR)]                         # last 4 s: filter opens (build)
seg = np.zeros_like(op); k = 8
for j in range(k):
    a, b = j * len(op) // k, (j + 1) * len(op) // k
    fc = int(1600 * (10 ** (j / (k - 1))))
    seg[a:b] = fx(op[a:b], f"lowpass=f={min(fc, 16000)}")[: b - a]
p1[int((T_CUT - 4.0) * SR):] = seg[: len(p1) - int((T_CUT - 4.0) * SR)]
place(mus, fade(p1, 1.5, 0.05), 0)
rev = trk[int((T_CUT - 2.6) * SR): int(T_CUT * SR)][::-1]
rev = fx(rev, "rubberband=tempo=2.1:pitch=0.85,lowpass=f=5000")[: int((T_REVEAL - T_CUT) * SR)]
place(mus, fade(rev, 0.02, 0.15), T_CUT, 0.9)
main = trk[int(DROP_TRACK * SR): int(END_TRACK * SR) + int(0.05 * SR)]
place(mus, fade(main, 0.005, 0.05), T_REVEAL)
tailr = fx(trk[int(END_TRACK * SR): int((END_TRACK + 0.35) * SR)], "aecho=0.8:0.7:120|240|420:0.45|0.32|0.2,lowpass=f=7000")
place(mus, fade(tailr, 0.01, 0.3), END_FINAL)                             # final hit with a ringing tail
x = load(f"{L}/cinematic/complete.mp3"); place(sfx, x / (np.abs(x).max() + 1e-9) * 0.4, END_FINAL, 0.8)
# ---- ducking: music follows the speech envelope ----
env = np.sqrt(np.convolve((voice ** 2).mean(1), np.ones(int(0.03 * SR)) / int(0.03 * SR), "same"))
spk = np.clip((20 * np.log10(env + 1e-9) + 40) / 12, 0, 1)
k1 = int(0.25 * SR); spk = np.convolve(spk, np.ones(k1) / k1, "same")
gain = 0.30 - 0.17 * spk                                                  # ~ -10 dB bed, -17 dB under speech
gain[: int(T_CUT * SR)] *= 0.9
gain[int((T_CUT - 0.2) * SR): int((T_REVEAL + 0.8) * SR)] = np.maximum(gain[int((T_CUT - 0.2) * SR): int((T_REVEAL + 0.8) * SR)], 0.42)
mix = voice + sfx * 0.9 + mus * gain[:, None]
mix = mix[: int(TOTAL * SR)]
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                "acompressor=threshold=-16dB:ratio=2:attack=10:release=150,loudnorm=I=-14:TP=-1.5:LRA=10", "-ar", str(SR), f"{F}/mix_final.wav"],
               input=mix.tobytes(), check=True)
print("final mix ok", round(len(mix) / SR, 3), "end hit at", round(END_FINAL, 2))
