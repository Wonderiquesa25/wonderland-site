# Segundo corte de pausas por energia: trechos < THR dB com mais de MIN s ficam com KEEP s.
import sys, numpy as np, soundfile as sf
IN, OUT = sys.argv[1:3]; THR, MIN, KEEP = -34.0, 0.2, 0.13
a, sr = sf.read(IN, dtype='float32'); h = sr // 100
db = np.array([20 * np.log10(np.sqrt((a[i:i + h] ** 2).mean()) + 1e-9) for i in range(0, len(a) - h, h)])
low = db < THR
cuts = []; i = 0
while i < len(low):
    if low[i]:
        j = i
        while j < len(low) and low[j]: j += 1
        if (j - i) / 100 > MIN and i > 0 and j < len(low):
            cuts.append(((i / 100) + KEEP / 2, (j / 100) - KEEP / 2))
        i = j
    else: i += 1
out = []; cur = 0; xf = int(0.01 * sr)
for c0, c1 in cuts: out.append(a[int(cur * sr):int(c0 * sr)]); cur = c1
out.append(a[int(cur * sr):])
res = out[0]
for seg in out[1:]:
    r = np.linspace(0, 1, xf, dtype=np.float32)
    res[-xf:] = res[-xf:] * (1 - r) + seg[:xf] * r; res = np.concatenate([res, seg[xf:]])
sf.write(OUT, res, sr); print(len(cuts), 'cortes', round(len(a) / sr, 2), '->', round(len(res) / sr, 2))
