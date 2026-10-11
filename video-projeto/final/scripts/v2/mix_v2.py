"""Mix v2 (no music): voice on top, SFX clearly audible in the gaps and ducked under speech, CCTV transition design,
keyboard keystrokes on the typed name cards. Writes mix_v2.wav + timeline.json"""
import sys, json, subprocess, numpy as np
S = sys.argv[1]; O = f"{S}/v2"; L = f"{S}/sfxlib/package/sounds"; SR = 48000
a2 = json.load(open(f"{O}/a2.json")); tr = json.load(open(f"{O}/T_cctv.json")); keys = json.load(open(f"{O}/intro/keys.json"))
T0 = a2["speech_end"] - 0.35; BS = tr["b_start"]; B_DUR = 61.0333; B_TEMPO = 1.06
TOTAL = T0 + tr["dur"] + (B_DUR - (tr["dur"] - BS)); N = int(TOTAL * SR) + SR
rng = np.random.default_rng(5)
def load(p, ch=2):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    return x.reshape(-1, ch).astype(np.float64)
def fx(x, af):
    return np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af", af, "-ar", str(SR), "-f", "f64le", "-"],
                                        input=np.ascontiguousarray(x).tobytes(), capture_output=True).stdout, np.float64).reshape(-1, 2).copy()
def place(bus, x, t, g=1.0):
    i = int(t * SR); x = x[: max(0, len(bus) - i)]; bus[i:i + len(x)] += x * g
def fade(x, a=0.01, b=0.01):
    x = x.copy(); na, nb = int(a * SR), int(b * SR)
    if na: x[:na] *= np.linspace(0, 1, na)[:, None]
    if nb: x[-nb:] *= np.linspace(1, 0, nb)[:, None]
    return x
def ui(name, peak=0.5):
    x = load(f"{L}/{name}.mp3"); return x / (np.abs(x).max() + 1e-9) * peak
def noise(d, band, env):
    n = rng.standard_normal((int(d * SR), 2)); n = fx(n, band)[: int(d * SR)]
    return n * env(np.arange(len(n)) / SR / d)[:, None]
voice = np.zeros((N, 2)); sfx = np.zeros((N, 2)); trans = np.zeros((N, 2))

# ---- part 1 ----
v1 = load(f"{O}/voice_a2.wav", 1).repeat(2, 1); place(voice, fade(v1, 0, 0.05), 0)
s1 = load(f"{O}/sfx_a2.wav")[: int((T0 + 0.3) * SR)]; place(sfx, fade(s1, 0, 0.3), 0)
# ---- scene 2 (Lourenço voice already matched to part 1) ----
s2 = fx(load(f"{O}/s2_v2_pre.wav"), f"rubberband=tempo={B_TEMPO}:transients=crisp:pitchq=quality")
TB = T0 + BS                                                    # scene-2 time 0 on the final timeline
place(voice, fade(s2, 0.03, 0.3), TB)
# level check: Lourenço speech level must equal part 1
def srms(x):
    h = int(0.05 * SR); e = np.sqrt(np.array([np.mean(x[i:i + h] ** 2) for i in range(0, len(x) - h, h)])); return np.sqrt(np.mean(e[e > np.percentile(e, 50)] ** 2))
lou = s2[int(12.6 / B_TEMPO * SR): int(41.48 / B_TEMPO * SR)]; g_lou = srms(v1[: int(T0 * SR)]) / srms(lou)
voice[int(TB * SR):] *= g_lou; print("scene-2 voice gain to match part 1:", round(20 * np.log10(g_lou), 1), "dB")

# ---- keyboard keystrokes on the typed name cards (intro start frames in scene-2 original timeline) ----
KEY = load(f"{L}/mechanical/typing.mp3"); KEY /= np.abs(KEY).max(); SPACE = ui("mechanical/press", 1.0)
for nm, f0 in [("hilaria", 308), ("lourenco", 668), ("joel", 1254), ("lima", 1808)]:
    for part, g in (("name", 0.42), ("role", 0.26)):
        for kt, ch in keys[nm][part]:
            t = TB + (f0 / 30 + kt) / B_TEMPO - 0.012
            k = SPACE * 0.6 if ch == " " else KEY
            rate = rng.uniform(0.93, 1.08); idx = np.arange(0, len(k) - 1, rate)       # tiny pitch/timbre variation per key
            kk = np.stack([np.interp(idx, np.arange(len(k)), k[:, c]) for c in range(2)], 1)
            place(sfx, kk, t, g * rng.uniform(0.8, 1.1))
    # the card "lands": soft select blip when the role finishes
    place(sfx, ui("scifi/select", 0.25), TB + (f0 / 30 + keys[nm]["role"][-1][0] + 0.05) / B_TEMPO)

# ---- CCTV transition sound design (times relative to T0) ----
t = lambda x: T0 + x
place(trans, ui("scifi/recording", 0.35), t(0.02))                                         # REC beep as CAM 01 comes up
hum = np.sin(2 * np.pi * 50 * np.arange(int(1.9 * SR)) / SR) * 0.5 + np.sin(2 * np.pi * 100 * np.arange(int(1.9 * SR)) / SR) * 0.3
hum = np.stack([hum, hum], 1) * 0.035 + noise(1.9, "highpass=f=200,lowpass=f=3000", lambda u: 0.02 + 0 * u)
place(trans, fade(hum, 0.25, 0.3), t(0.15))                                                # control-room hum / fans
place(trans, noise(0.13, "highpass=f=1500,lowpass=f=9000", lambda u: (np.random.default_rng(1).random(len(u)) > 0.4) * (1 - u) * 0.5), t(0.27))   # glitch crackle
place(trans, ui("cinematic/swipe", 0.55), t(0.36))                                         # pull-back whoosh
place(trans, noise(0.65, "bandpass=f=900:width_type=o:w=2", lambda u: np.sin(np.pi * u) ** 2 * 0.16), t(0.35))
place(trans, ui("scifi/focus", 0.35), t(0.80))                                             # selector appears on CAM 01
place(trans, ui("mechanical/press", 0.5), t(1.09)); place(trans, ui("scifi/select", 0.45), t(1.10))   # click -> CAM 02
place(trans, noise(BS - 1.10 + 0.1, "highpass=f=800,lowpass=f=8000", lambda u: 0.07 * (0.6 + 0.4 * u) * (1 - np.clip((u - 0.85) / 0.15, 0, 1))), t(1.10))  # CAM 02 static
place(trans, ui("scifi/connect", 0.45), t(BS - 0.02))                                      # feed connects
place(trans, noise(0.75, "highpass=f=300,lowpass=f=6000", lambda u: u ** 2.5 * 0.22), t(1.20))  # push-in riser
tt = np.arange(int(1.4 * SR)) / SR
boom = np.sin(2 * np.pi * np.cumsum(34 + 90 * np.exp(-tt * 14)) / SR) * np.exp(-tt * 3.0) * 0.55
place(trans, np.stack([boom, boom], 1), t(tr["land"])); place(trans, ui("cinematic/drop", 0.5), t(tr["land"] - 0.02))   # landing impact
# ---- end: soft impact on the final card ----
END = TOTAL - 1.0
tt = np.arange(int(1.6 * SR)) / SR; eb = np.sin(2 * np.pi * np.cumsum(30 + 70 * np.exp(-tt * 12)) / SR) * np.exp(-tt * 2.6) * 0.3
place(sfx, np.stack([eb, eb], 1), END - 1.2)

# ---- ducking: SFX loud in the gaps, clearly under the voice when he speaks ----
h = int(0.03 * SR); env = np.sqrt(np.convolve((voice ** 2).mean(1), np.ones(h) / h, "same"))
spk = np.clip((20 * np.log10(env + 1e-9) + 42) / 12, 0, 1); k1 = int(0.2 * SR); spk = np.convolve(spk, np.ones(k1) / k1, "same")
g_sfx = 1.15 - 0.70 * spk                                                                   # ~+1 dB in gaps, ~-7 dB under speech
mix = voice + sfx * g_sfx[:, None] + trans * 1.1
mix = mix[: int(TOTAL * SR)]
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
                "acompressor=threshold=-18dB:ratio=2:attack=8:release=150,loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", str(SR), f"{O}/mix_v2.wav"],
               input=mix.tobytes(), check=True)
json.dump(dict(T0=T0, TB=TB, total=TOTAL, b_from=tr["dur"] - BS), open(f"{O}/timeline.json", "w"), indent=1)
print("mix ok", round(TOTAL, 3), "T0", round(T0, 3), "scene 2 starts", round(TB, 3))
