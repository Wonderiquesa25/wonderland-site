# Verifica que nenhuma legenda sai do ecra (cenas origami e narrador) amostrando o fim de cada bloco.
import sys, os, numpy as np
sys.argv = sys.argv[:1]; sys.path.insert(0, os.path.dirname(__file__))
import render_crime as R
bad = 0
for st, en, c in R.CH:
    t = min(en - 0.02, c[-1][1] + 0.3)
    if t >= R.VEND: continue
    j, s, e = R.seg_at(t)
    if s[0] == 'o':
        cap = R.caption_rgba(t, R.W, R.H, 1010, 300, 0.92); ys, xs = np.nonzero(cap[..., 3] > 10)
        ok = xs.min() >= 40 and xs.max() <= R.W - 40 and ys.min() >= 30 and ys.max() <= R.H - 30
    else:
        u = R.eio((t - s[1]) / (e - s[1])); ww = s[4] + (s[5] - s[4]) * u; wh = ww * R.H / R.W
        cx = R.clamp(s[2], ww / 2, R.IW - ww / 2); cy = R.clamp(s[3], wh / 2, R.IH - wh / 2)
        cap = R.caption_rgba(t, R.IW * R.K, R.IH * R.K, R.CAP_X0, R.CAP_Y); ys, xs = np.nonzero(cap[..., 3] > 10)
        x0, y0 = (cx - ww / 2) * R.K, (cy - wh / 2) * R.K; sc = R.W / (ww * R.K)
        X0, X1, Y0, Y1 = (xs.min() - x0) * sc, (xs.max() - x0) * sc, (ys.min() - y0) * sc, (ys.max() - y0) * sc
        ok = X0 >= 30 and X1 <= R.W - 30 and Y0 >= 20 and Y1 <= R.H - 20
    if not ok: bad += 1; print('FORA', round(t, 2), s[0], ' '.join(w for _, _, w in c))
print('problemas:', bad, 'blocos:', len(R.CH))
