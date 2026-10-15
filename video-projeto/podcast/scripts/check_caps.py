# Verifica, plano a plano, se cada bloco de legenda (ja completo) cabe no ecra com margem.
import os, sys, numpy as np
sys.argv = [sys.argv[0]]
import importlib; R = importlib.import_module(os.environ.get("MOD", "render_pod2"))
M = 40; bad = []
for st, en_, c in R.CH:
    for t in np.arange(max(st, 0) + 0.02, en_, 0.1):
        tfull = min(en_ - 0.01, c[-1][1] + 0.5)
        j, sg, e = R.seg_at(t)
        if sg[0] == 'p':
            cap = R.caption_rgba(tfull, R.IW * R.K, R.IH * R.K, R.CAP_X0, R.CAP_Y)
            ys, xs = np.nonzero(cap[..., 3] > 10)
            u = R.eio((t - sg[1]) / (e - sg[1])); ww = sg[4] + (sg[5] - sg[4]) * u; wh = ww * R.H / R.W
            cy = R.clamp(sg[3], wh / 2, R.IH - wh / 2); cx = R.clamp(sg[2], ww / 2, R.IW - ww / 2)
            sc = ww * R.K / R.W; x0 = (cx - ww / 2) * R.K; y0 = (cy - wh / 2) * R.K
            bx0, bx1 = (xs.min() - x0) / sc, (xs.max() - x0) / sc; by0, by1 = (ys.min() - y0) / sc, (ys.max() - y0) / sc
        else:
            cap = R.caption_rgba(tfull, R.W, R.H, 1010, 300, 0.92)
            ys, xs = np.nonzero(cap[..., 3] > 10); bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
        if bx0 < M or bx1 > R.W - M or by0 < M or by1 > R.H - M:
            bad.append((round(t, 2), sg[0], ' '.join(w for _, _, w in c), int(bx0), int(bx1), int(by0), int(by1)))
seen = set()
for b in bad:
    if b[2] not in seen: seen.add(b[2]); print(b)
print('blocos com problema:', len(seen), 'de', len(R.CH))
