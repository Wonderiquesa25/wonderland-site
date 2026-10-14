# Encurta as pausas da voz: cada silencio > 0.16 s fica com GAP s (crossfade curto nas juncoes).
import re, subprocess, sys, numpy as np, soundfile as sf
IN, OUT = sys.argv[1], sys.argv[2]; GAP = 0.16; LEAD = 0.25
log = subprocess.run(['ffmpeg', '-i', IN, '-af', 'highpass=f=80,afftdn=nf=-25,silencedetect=n=-38dB:d=0.16', '-f', 'null', '-'],
                     capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]
en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
a, sr = sf.read(IN, dtype='float32')
dur = len(a) / sr
if len(en) < len(st): en.append(dur)
keep = []  # segmentos de fala (com folga)
cur = 0.0
for s, e in zip(st, en):
    if s <= 0.01:  # silencio inicial
        cur = max(e - LEAD, 0); continue
    keep.append((cur, s + GAP / 2)); cur = e - GAP / 2
if cur < dur: keep.append((cur, min(dur, cur + 0.6)) if en and en[-1] >= dur - 0.01 else (cur, dur))
xf = int(0.012 * sr); out = np.zeros(0, np.float32)
for s, e in keep:
    seg = a[int(s * sr):int(e * sr)].copy()
    if len(out) >= xf and len(seg) >= xf:
        r = np.linspace(0, 1, xf, dtype=np.float32)
        out[-xf:] = out[-xf:] * (1 - r) + seg[:xf] * r; seg = seg[xf:]
    out = np.concatenate([out, seg])
sf.write(OUT, out, sr)
print(f'{dur:.2f}s -> {len(out)/sr:.2f}s')
