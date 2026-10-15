# Verificador de legendas para render_pod3 (planos com janela ancorada a direita + cenas origami).
import sys, numpy as np
sys.argv = [sys.argv[0]]
import render_pod3 as R
M = 40; bad = {}
for st, en_, c in R.CH:
    tfull = min(en_ - 0.01, c[-1][1] + 0.5)
    for t in np.arange(max(st, 0) + 0.02, en_, 0.1):
        j, sg, e = R.seg_at(t)
        if sg[0] == 'p':
            xs = R.chunk_x(tfull); cap = R.caption_rgba(tfull, R.W, R.H, xs, R.CAP_Y, 0.85, maxw_px=R.W - 110 - xs)
            ys, xs = np.nonzero(cap[..., 3] > 10)
            u = R.eio((t - sg[1]) / (e - sg[1])); w = sg[3] + (sg[4] - sg[3]) * u; h = w * R.H / R.W
            x0 = R.W - w; y0 = R.clamp(sg[2] - h / 2, 0, R.H - h); k = R.W / w
            bx0, bx1, by0, by1 = (xs.min() - x0) * k, (xs.max() + 12 - x0) * k, (ys.min() - y0) * k, (ys.max() + 6 - y0) * k
        else:
            cap = R.caption_rgba(tfull, R.W, R.H, 1010, 300, 0.92)
            ys, xs = np.nonzero(cap[..., 3] > 10); bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
        if bx0 < M or bx1 > R.W - M or by0 < M or by1 > R.H - M:
            bad.setdefault(' '.join(w for _, _, w in c), (round(t, 2), sg[0], int(bx0), int(bx1), int(by0), int(by1)))
for k, v in bad.items(): print(v, k)
print('blocos com problema:', len(bad), 'de', len(R.CH))
