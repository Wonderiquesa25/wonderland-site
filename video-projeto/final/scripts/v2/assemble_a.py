"""Part 1 v2: cut the leftover 'O que?' + real pauses (>=0.27 s, kept at 0.12 s), frame-accurate on video, voice and SFX,
then tempo 1.06 -> 1.09 overall. Writes A2.mp4 (no audio), voice_a2.wav, sfx_a2.wav, a2.json (speech end)."""
import sys, json, subprocess, numpy as np
S = sys.argv[1]; F = f"{S}/final"; O = f"{S}/v2"; SR = 48000; FPS = 30; K = 1.09 / 1.06
def load(p, ch):
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                                     capture_output=True).stdout, np.float32).astype(np.float64)
    return x.reshape(-1, ch)
v = load(f"{O}/voice_p1b.wav", 1); fx = load(f"{F}/sfx_p1.wav", 2)
dur_v = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{F}/A_fast.mp4"], capture_output=True, text=True).stdout)
# pauses on the new voice
h = int(0.01 * SR); db = 20 * np.log10(np.sqrt(np.array([np.mean(v[i:i + h, 0] ** 2) for i in range(0, len(v) - h, h)])) + 1e-9)
q = db < -30; cuts = [(33.335, 33.66), (33.76, 33.84)]                         # the 'O que?' leftovers ('O' + 'que' click)
i = 0
while i < len(q):
    if q[i]:
        j = i
        while j < len(q) and q[j]: j += 1
        a, b = i * 0.01, j * 0.01
        if b - a >= 0.27 and 1.0 < a < 82.5 and not (33.0 < a < 34.2):
            m = (a + b) / 2; cuts.append((m - (b - a - 0.12) / 2, m + (b - a - 0.12) / 2))
        i = j
    else: i += 1
cuts = sorted((round(a * FPS) / FPS, round(b * FPS) / FPS) for a, b in cuts)
cuts = [(a, b) for a, b in cuts if b > a]
print("cuts:", cuts, "removed", round(sum(b - a for a, b in cuts), 3), "s")
def cut_audio(x):
    xf = int(0.012 * SR); t = np.linspace(0, np.pi / 2, xf)[:, None]; out = []; last = 0
    for a, b in cuts:
        ia, ib = int(a * SR), int(b * SR)
        out.append(x[last:ia - xf // 2]); out.append(x[ia - xf // 2: ia - xf // 2 + xf] * np.cos(t) + x[ib - xf // 2: ib - xf // 2 + xf] * np.sin(t))
        last = ib - xf // 2 + xf
    out.append(x[last:]); return np.concatenate(out)
def save_af(x, ch, chain, p):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", str(ch), "-i", "-", "-af", chain, "-c:a", "pcm_s24le", p],
                   input=np.ascontiguousarray(x).tobytes(), check=True)
save_af(cut_audio(v), 1, f"rubberband=tempo={K:.6f}:formant=preserved:transients=smooth:detector=soft:pitchq=quality", f"{O}/voice_a2.wav")
save_af(cut_audio(fx), 2, f"atempo={K:.6f}", f"{O}/sfx_a2.wav")
sel = "+".join(f"between(t,{a:.4f},{b - 0.0005:.4f})" for a, b in cuts)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", f"{F}/A_fast.mp4", "-an", "-vf",
                f"select='not({sel})',setpts=N/{FPS}/TB,setpts=PTS/{K:.6f},fps={FPS}", "-c:v", "libx264", "-crf", "14", "-preset", "medium",
                "-pix_fmt", "yuv420p", f"{O}/A2.mp4"], check=True)
def mapt(t):                                         # P time -> A2 time
    return (t - sum(min(b, t) - a for a, b in cuts if a < t)) / K
vv = load(f"{O}/voice_a2.wav", 1)[:, 0]; db2 = 20 * np.log10(np.sqrt(np.array([np.mean(vv[i:i + h] ** 2) for i in range(0, len(vv) - h, h)])) + 1e-9)
speech_end = (np.where(db2 > -30)[0][-1] + 1) * 0.01
json.dump(dict(cuts=cuts, K=K, speech_end=speech_end, a_cap=mapt(84.22), dur=mapt(dur_v)), open(f"{O}/a2.json", "w"), indent=1)
print("A2 dur", round(mapt(dur_v), 3), "speech end", round(speech_end, 3), "A cap", round(mapt(84.22), 3))
