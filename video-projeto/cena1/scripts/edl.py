"""Dialogue-aware edit decision list: trim dead air at both ends of each part, shorten long pauses to ~0.3 s.
Pauses come from the speech envelope; words from Whisper. Cut points padded so no syllable is touched."""
import json, numpy as np, subprocess, sys
C = sys.argv[1]
FPS = 30
PARTS = ["nova1", "nova2", "nova3", "nova4"]
KEEP_GAP, MIN_CUT = 0.30, 0.22
EDGES = {"nova1": (1.95, 15.25), "nova2": (1.38, 26.70), "nova3": (1.66, 41.95), "nova4": (1.78, 16.85)}


def pauses(n):
    a = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", f"{C}/src/{n}.mp4", "-vn", "-ac", "1", "-ar", "16000", "-af",
                                      "highpass=f=120,lowpass=f=7000", "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
    fr = a[:len(a) // 160 * 160].reshape(-1, 160); db = 10 * np.log10((fr ** 2).mean(1) + 1e-12)
    db = np.convolve(db, np.ones(5) / 5, "same")
    p10, p95 = np.percentile(db, [10, 95]); sp = db > p10 + 0.35 * (p95 - p10)
    runs, st = [], None
    for i, v in enumerate(list(sp) + [True]):
        if not v and st is None: st = i
        if v and st is not None:
            runs.append((st * 0.01, i * 0.01)); st = None
    return runs, len(sp) * 0.01


edl = []
for n in PARTS:
    w = json.load(open(f"{C}/tr/{n}.json"))
    runs, dur = pauses(n)
    # speech start: earliest of Whisper's first word and the first loud frame after the lead silence
    start, end = EDGES[n]                       # measured on the 50 ms envelope (onset - pad, decay + pad; phone taps excluded)
    if n == PARTS[-1]: end += 0.35
    keep, cur = [], start
    for a, b in runs:
        if a <= start + 0.05 or b >= end - 0.05: continue
        if (b - a) - KEEP_GAP < MIN_CUT: continue
        ca, cb = a + KEEP_GAP / 2, b - KEEP_GAP / 2
        keep.append((cur, ca)); cur = cb
    keep.append((cur, end))
    for a, b in keep:
        fa, fb = round(a * FPS), round(b * FPS)
        edl.append(dict(part=n, f0=fa, f1=fb))
tot = sum(e["f1"] - e["f0"] for e in edl)
json.dump(edl, open(f"{C}/edl.json", "w"), indent=1)
for e in edl: print(e["part"], f'{e["f0"]/FPS:6.2f} -> {e["f1"]/FPS:6.2f}')
print("segments", len(edl), "new duration", round(tot / FPS, 2), "s (was 105.8)")
