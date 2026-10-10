"""Dialogue for the tightened edit: restore each part (declip, denoise, EQ, de-ess, compress), cut by the EDL with
short equal-power crossfades (no clicks, no chopped consonants), then one loudness target for the whole scene."""
import json, subprocess, numpy as np, sys
C = sys.argv[1]; SR = 48000; FPS = 30
CHAIN = ("adeclip,highpass=f=80,afftdn=nf=-30:tn=1,anlmdn=s=4:p=0.002:r=0.006,equalizer=f=250:t=q:w=1.2:g=-2.5,"
         "equalizer=f=3000:t=q:w=1.0:g=2.5,equalizer=f=8500:t=q:w=1:g=1.2,deesser=i=0.3,"
         "acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=2")
edl = json.load(open(f"{C}/edl.json")); parts = {}
for n in sorted({e["part"] for e in edl}):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{C}/src/{n}.mp4", "-vn", "-af", f"pan=mono|c0=0.5*c0+0.5*c1,{CHAIN}",
                          "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    parts[n] = np.frombuffer(raw, np.float32).copy()
XF = int(0.012 * SR)                                   # 12 ms crossfade at every cut
out = np.zeros(0, np.float32); marks = []
for e in edl:
    a = parts[e["part"]][int(e["f0"] / FPS * SR) - XF // 2: int(e["f1"] / FPS * SR) + XF // 2].copy()
    if a.size == 0: continue
    if out.size == 0:
        out = a
    else:
        t = np.linspace(0, np.pi / 2, XF)
        out[-XF:] = out[-XF:] * np.cos(t) + a[:XF] * np.sin(t)
        out = np.concatenate([out, a[XF:]])
    marks.append(round(len(out) / SR, 3))
# match the video length exactly
n_vid = sum(e["f1"] - e["f0"] for e in edl); out = np.pad(out, (0, max(0, int(n_vid / FPS * SR) - len(out))))[: int(n_vid / FPS * SR)]
fade = int(0.08 * SR); out[:fade] *= np.linspace(0, 1, fade)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af",
                "loudnorm=I=-16:TP=-2:LRA=8", "-ar", str(SR), f"{C}/work/dialogue3.wav"], input=out.tobytes(), check=True)
print("dialogue ok", round(len(out) / SR, 2), "s; segment ends:", marks)
