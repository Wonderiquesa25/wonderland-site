# Narrador cinematografico a partir do video real (sem IA generativa): fundo preto de estudio,
# luz chave ambar de um lado, sombra do outro, luz de recorte quente, boca discretamente escondida
# (microfone fixo + sombra suave que acompanha a cabeca). Sem audio. Sai em 3840x2160.
import os, sys, json, subprocess, cv2, numpy as np
FR = os.environ.get('FR', 'mod/fr'); LM = os.environ.get('LM', 'mod/lm.json'); MICSRC = os.environ.get('MIC', 'studio_fg.png')
OUT = os.environ.get('OUT', 'narrador_4k.mp4'); DUR = float(os.environ.get('DUR', '48'))
W, H, FPS = 1920, 1080, 24
S = 1.5  # 1280x720 -> 1920x1080

# --- ordem dos fotogramas: vai e volta suave para cobrir a duracao da locucao ---
N = 192; A0 = 56
order = list(range(0, N))
while len(order) < int(DUR * FPS):
    order += list(range(N - 2, A0 - 1, -1)) + list(range(A0 + 1, N))
order = order[:int(DUR * FPS)]

# --- pontos da cara (boca/olhos) suavizados ---
L = json.load(open(LM))
def col(k): return np.array([np.nan if l is None else l[k] for l in L], np.float32)
mx = (col(10) + col(12)) / 2; my = (col(11) + col(13)) / 2; mw = np.abs(col(12) - col(10)); ex = (col(4) + col(6)) / 2
for a in (mx, my, mw, ex):
    idx = np.arange(len(a)); ok = ~np.isnan(a); a[:] = np.interp(idx, idx[ok], a[ok])
def smooth(a, s=3.0):
    k = np.exp(-0.5 * (np.arange(-9, 10) / s) ** 2); k /= k.sum()
    return np.convolve(np.pad(a, 9, mode='edge'), k, 'valid')
mx, my, mw, ex = [smooth(a) * S for a in (mx, my, mw, ex)]

# --- microfone (escuro, discreto) fixo na posicao media da boca ---
mic = cv2.imread(MICSRC, cv2.IMREAD_UNCHANGED)[415:880, 740:995].astype(np.float32)
MS_ = 2.75
mic = cv2.resize(mic, None, fx=MS_, fy=MS_, interpolation=cv2.INTER_CUBIC)
mic[..., :3] = mic[..., :3].mean(2, keepdims=True) * np.float32([0.30, 0.34, 0.40])  # escuro e quente
# brilho ambar subtil na aresta de cima do microfone (mesma luz chave)
ma = mic[..., 3] / 255
edge = np.clip(ma - cv2.warpAffine(ma, np.float32([[1, 0, 0], [0, 1, 6]]), (ma.shape[1], ma.shape[0])), 0, 1)
mic[..., :3] += cv2.GaussianBlur(edge, (0, 0), 2)[..., None] * np.float32([40, 120, 200]) * 0.6
MIC_HEAD = (55 * MS_, 55 * MS_)            # centro da grelha do microfone dentro do recorte, apos escala
MCX, MCY = float(np.median(mx)) + 25, float(np.median(my)) + 55
MIC_X, MIC_Y = int(MCX - MIC_HEAD[0]), int(MCY - MIC_HEAD[1])

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
vign = np.clip(1.15 - 0.55 * (((xx - W * 0.45) / (W * 0.62)) ** 2 + ((yy - H * 0.45) / (H * 0.75)) ** 2), 0.25, 1)[..., None]
haze = np.exp(-(((xx - W * 0.4) / 650) ** 2 + ((yy - H * 0.35) / 420) ** 2))[..., None] * np.float32([6, 11, 18])
rng = np.random.default_rng(3)

def frame(k):
    i = order[k]
    f = cv2.imread(f'{FR}/f{i:04d}.png', cv2.IMREAD_UNCHANGED)
    f = cv2.resize(f, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    rgb, a = f[..., :3], f[..., 3:] / 255
    # luz chave ambar do lado esquerdo do rosto, sombra controlada do lado direito
    cx = ex[i]
    side = np.clip(0.5 - (xx - cx) / 520, 0, 1)[..., None]           # 1 a esquerda do rosto, 0 a direita
    key = 0.42 + 0.78 * side ** 1.3
    warm = np.float32([0.80, 0.95, 1.10])                              # BGR: puxa para ambar
    p = rgb * key * warm
    # sombra cinematografica na parte de baixo do rosto (segue a cabeca)
    rx, ry = mw[i] * 1.05, mw[i] * 0.62
    sh = 1 - 0.78 * np.exp(-(((xx - mx[i]) / rx) ** 2 + ((yy - (my[i] + 0.15 * mw[i])) / ry) ** 2))
    p = p * sh[..., None]
    # luz de recorte quente na cabeca e ombros
    a0 = a[..., 0]
    rim = np.clip(a0 - cv2.erode(a0, np.ones((11, 11), np.uint8)), 0, 1)
    rim = cv2.GaussianBlur(rim, (0, 0), 3) * np.clip(1.25 - yy / H, 0, 1) * (0.55 + 0.45 * (xx > cx))
    p = p + rim[..., None] * np.float32([60, 150, 255]) * 0.55
    # fundo preto de estudio com leve neblina quente
    bg = np.zeros_like(p) + np.float32([7, 8, 10]) + haze
    out = bg * (1 - a) + p * a
    # microfone a frente da parte de baixo do rosto
    h_, w_ = mic.shape[:2]; x0, y0 = MIC_X, MIC_Y
    xa, ya = max(x0, 0), max(y0, 0); xb, yb = min(x0 + w_, W), min(y0 + h_, H)
    sub = mic[ya - y0:yb - y0, xa - x0:xb - x0]; al = sub[..., 3:] / 255
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al
    # gradacao: contraste em S, pretos densos, vinheta, grao fino
    o = np.clip(out / 255, 0, 1)
    o = o * o * (3 - 2 * o) * 0.55 + o * 0.45
    o = o * vign
    o = o + rng.normal(0, 0.012, (H, W, 1)).astype(np.float32)
    return np.clip(o * 255, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for t in sys.argv[1:]:
            cv2.imwrite(f'n4_{t}.jpg', frame(int(float(t) * FPS)))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-vf', 'scale=3840:2160:flags=lanczos,unsharp=5:5:0.6:5:5:0.0', '-an', '-c:v', 'libx264', '-preset', 'slow',
                          '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
    for k in range(len(order)):
        p.stdin.write(frame(k).tobytes())
        if k % 120 == 0: print(k, '/', len(order), flush=True)
    p.stdin.close(); p.wait()
