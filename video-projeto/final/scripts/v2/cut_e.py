"""v4: remove the uncaptioned 'É' between 'do jeito certo.' and 'Muitos dizem' (A2 32.033-32.433, 12 frames),
muting the residue on both sides; everything after shifts 0.4 s earlier (CCTV render reused unchanged)."""
import json, subprocess, numpy as np
SR = 48000; A, B = 961 / 30, 973 / 30; D = B - A
def load(p, ch):
    return np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",p,"-ac",str(ch),"-ar",str(SR),"-f","f64le","-"],capture_output=True).stdout,np.float64).reshape(-1, ch).copy()
def save(x, p):
    subprocess.run(["ffmpeg","-y","-v","error","-f","f64le","-ar",str(SR),"-ac",str(x.shape[1]),"-i","-","-c:a","pcm_s24le",p], input=x.tobytes(), check=True)
for src, dst, mute in (("voice_a2.wav", "voice_a4.wav", True), ("sfx_a2.wav", "sfx_a4.wav", False)):
    x = load(src, 1 if "voice" in src else 2)
    if mute:                                                   # silence the 'É' residue left around the cut, with short fades
        for a, b in ((31.985, A), (B, 32.49)):
            ia, ib = int(a * SR), int(b * SR); x[ia:ib] = 0
        f = int(0.01 * SR); ia = int(31.985 * SR); x[ia - f:ia] *= np.linspace(1, 0, f)[:, None]
        ib = int(32.49 * SR); x[ib:ib + f] *= np.linspace(0, 1, f)[:, None]
    ia, ib = int(A * SR), int(B * SR); save(np.concatenate([x[:ia], x[ib:]]), dst)
subprocess.run(["ffmpeg","-y","-v","error","-i","A2.mp4","-vf",f"select='not(between(n,961,972))',setpts=N/30/TB","-c:v","libx264","-crf","14","-preset","medium","-pix_fmt","yuv420p","A4.mp4"], check=True)
a2 = json.load(open("a2.json")); a2.update(speech_end=a2["speech_end"] - D, a_cap=a2["a_cap"] - D, dur=a2["dur"] - D, cut_e=[A, B])
json.dump(a2, open("a4.json", "w"), indent=1); print("cut", round(D, 3), "s; new speech_end", round(a2["speech_end"], 3))
