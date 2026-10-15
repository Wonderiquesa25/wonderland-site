# Podcast v2 (16:9): voz sem pausas ate ao fim da frase, boca suave, legendas grandes escritas
# na parede a direita (atras do microfone, oclusao por profundidade), cenas origami com camara 3D.
import os, sys, json, subprocess, cv2, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from puppet import Puppet, K
IMG = os.environ.get('IMG', '7.jpg'); DEPTH = os.environ.get('DEPTH', 'depth.npy'); VOZ = os.environ.get('VOZ', 'ac48.wav')
WORDS = os.environ.get('WORDS', 'wc.json'); FONT = os.environ.get('FONT', 'Montserrat-ExtraBold.ttf')
LOGO = os.environ.get('LOGO', 'kukulu-logo@2x.png'); ORI = os.environ.get('ORI', 'origami'); OUT = os.environ.get('OUT', 'pod2_mudo.mp4')
W, H, FPS = 1920, 1080, 30
ORANGE = (248, 168, 0); WHITE = (255, 255, 255)
def clamp(x, a=0.0, b=1.0): return min(max(x, a), b)
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 0.5 - 0.5 * np.cos(np.pi * x)

# ---------- voz ----------
a, sr = sf.read(VOZ, dtype='float32')
if a.ndim > 1: a = a.mean(1)
VEND = len(a) / sr + 0.05
DUR = VEND + 3.2
hop = sr // 100
fr = np.sqrt(np.maximum(np.convolve(a ** 2, np.ones(hop) / hop, 'same')[::hop], 0) + 1e-10)
db = 20 * np.log10(fr); ref = np.percentile(db[db > -60], 95)
op = np.clip((db - (ref - 24)) / 22, 0, 1)
op = np.convolve(op, np.ones(5) / 5, 'same')  # suaviza
sm = np.zeros_like(op)
for i in range(1, len(op)):
    k = 0.30 if op[i] > sm[i - 1] else 0.16
    sm[i] = sm[i - 1] + k * (op[i] - sm[i - 1])
energy = np.convolve(op, np.ones(50) / 50, 'same')
def jaw_at(t): i = int(t * 100); return 8.5 * sm[i] if 0 <= i < len(sm) else 0.0
def en_at(t): i = int(t * 100); return energy[i] if 0 <= i < len(energy) else 0.0
rng = np.random.default_rng(11); BLINKS = []; tb = 1.0
while tb < DUR: BLINKS.append(tb); tb += 2.6 + 2.4 * rng.random()
def blink_at(t):
    for b in BLINKS:
        if b <= t < b + 0.17: return 1 - abs((t - b) / 0.085 - 1)
    return 0.0

# ---------- palavras e blocos de legenda ----------
WD = json.load(open(WORDS))
FIX = {'meio': 'meia', 'sair.': 'ir.', 'Sente': 'Ciente', 'fato': 'facto', 'elétrica?': 'eléctrica?', 'elétrica': 'eléctrica'}
words = []
for s, e, w in WD:
    w = FIX.get(w, w)
    if w.startswith('-') and words: ps, pe, pw = words[-1]; words[-1] = (ps, e, pw + w)
    else: words.append((s, e, w))
EMPH = {'imagina', 'meia', 'noite', 'barulhos', 'esposa', 'filhos', 'estranhas', 'perigo', 'família', 'vivos',
        'cerca', 'eléctrica', 'segurança', 'amas', 'ama', 'certeza', 'absoluta', 'prevenirias', 'mata', 'tempo',
        'residência', 'casa', 'bárbaro', 'importante'}
def is_emph(w): return w.lower().strip('.,?!') in EMPH
FS = 150; fnt = ImageFont.truetype(FONT, FS); MAXW = 860
def lines_of(ws):
    L = [[]]; lw = 0
    for w in ws:
        ww = fnt.getlength(w.upper())
        if L[-1] and lw + fnt.getlength(' ') + ww > MAXW: L.append([]); lw = 0
        lw += (fnt.getlength(' ') if L[-1] else 0) + ww; L[-1].append(w)
    return L
chunks = []; cur = []
for s, e, w in words:
    test = cur + [(s, e, w)]
    gap = s - cur[-1][1] if cur else 0
    if cur and (len(lines_of([x[2] for x in test])) > 2 or gap > 0.45 or cur[-1][2][-1] in '.?!,'):
        chunks.append(cur); cur = [(s, e, w)]
    else: cur = test
if cur: chunks.append(cur)
CH = []
for k, c in enumerate(chunks):
    st = c[0][0] - 0.04; en_ = chunks[k + 1][0][0] - 0.04 if k + 1 < len(chunks) else VEND
    CH.append((st, min(en_, c[-1][1] + 1.0), c))
KEYS = []
def wdur(s, e): return min(max(e - s, 0.12) * 0.7, 0.4)
for st, en_, c in CH:
    for s, e, w in c:
        for i in range(len(w)): KEYS.append(s + wdur(s, e) * i / len(w))

def caption_rgba(t, size_w, size_h, x0, y0, fs_scale=1.0):
    """imagem RGBA com o bloco de legenda actual (escrito letra a letra) numa caixa"""
    for st, en_, c in CH:
        if st <= t < en_: break
    else: return None
    toks = []
    for s, e, w in c:
        d = wdur(s, e)
        n = len(w) if t >= s + d else (max(0, int(len(w) * (t - s) / d) + 1) if t >= s else 0)
        toks.append((w.upper(), min(n, len(w)), is_emph(w)))
    L = lines_of([w for w, _, _ in toks]); fsz = FS
    widest = max(fnt.getlength(' '.join(l).upper()) for l in L)
    f = fnt
    if widest > MAXW: fsz = int(FS * MAXW / widest); f = ImageFont.truetype(FONT, fsz)
    if fs_scale != 1.0: fsz = int(fsz * fs_scale); f = ImageFont.truetype(FONT, fsz)
    im = Image.new('RGBA', (size_w, size_h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lh = int(fsz * 1.08); ti = 0; cursor = None
    ytop = y0 - (len(L) * lh) // 2
    for li, ln in enumerate(L):
        x = x0; y = ytop + li * lh
        for w in ln:
            W_, n, em = toks[ti]; ti += 1
            if n > 0:
                d.text((x, y), W_[:n], font=f, fill=ORANGE if em else WHITE)
                cursor = (x + f.getlength(W_[:n]), y)
            x += f.getlength(W_ + ' ')
    typing = any(0 < n < len(w) for w, n, _ in toks)
    if cursor and (typing or int(t * 4) % 2 == 0):
        cx, cy = cursor; d.rectangle([cx + 8, cy + fsz * 0.12, cx + 8 + fsz * 0.09, cy + fsz * 0.95], fill=ORANGE)
    return np.array(im).astype(np.float32)

# ---------- podcast (cena original) ----------
src = cv2.imread(IMG); IH, IW = src.shape[:2]
pup = Puppet(src)
dep = cv2.resize(np.load(DEPTH), (IW * K, IH * K), interpolation=cv2.INTER_LINEAR).astype(np.float32)
fg = np.clip((dep - 0.30) / 0.07, 0, 1)[..., None]  # microfone e pessoa a frente da parede
gu, gv = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
# legenda na parede: caixa a direita (coords x2)
CAP_X0, CAP_Y = 735 * K, 352 * K

def podcast(t, cx, cy, ww):
    jaw = jaw_at(t); en = en_at(t)
    ang = 0.9 * np.sin(2 * np.pi * t / 4.1) + 0.9 * en * np.sin(2 * np.pi * t / 1.5)
    hdy = 1.6 * en * np.sin(2 * np.pi * t / 1.0)
    img = pup.frame(jaw, blink_at(t), ang, 0, hdy)
    cap = caption_rgba(t, IW * K, IH * K, CAP_X0, CAP_Y)
    if cap is not None:
        al = cap[..., 3:] / 255 * (1 - fg)
        sh = cv2.GaussianBlur(cap[..., 3], (0, 0), 9)[..., None] / 255 * 0.65
        sh = np.roll(sh, (10, 12), (0, 1)) * (1 - fg)
        img = img * (1 - sh)
        img = img * (1 - al) + cap[..., :3][..., ::-1] * al
    wh = ww * H / W
    cy = clamp(cy, wh / 2, IH - wh / 2); cx = clamp(cx, ww / 2, IW - ww / 2)
    amp = 16 if ww > 900 else 10
    camx = amp * np.sin(2 * np.pi * t / 7.0) * K; camy = 0.35 * amp * np.sin(2 * np.pi * t / 5.3) * K
    s = ww * K / W; x0 = (cx - ww / 2) * K; y0 = (cy - wh / 2) * K
    mx = (x0 + gu * s).astype(np.float32); my = (y0 + gv * s).astype(np.float32)
    d = cv2.remap(dep, mx, my, cv2.INTER_LINEAR)
    mx = (mx + camx * (d - 0.5) * 1.6).astype(np.float32); my = (my + camy * (d - 0.5) * 1.6).astype(np.float32)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if s < 1.05:
        bl = cv2.GaussianBlur(out, (0, 0), 1.3); out = out * 1.4 - bl * 0.4
    return out

# ---------- origami ----------
ORIG = {i: (cv2.imread(f'{ORI}/o{i}.jpg').astype(np.float32), np.load(f'{ORI}/d{i}.npy').astype(np.float32)) for i in range(1, 11)}
def origami(i, t, t0, t1, motion):
    img, d0 = ORIG[i]
    u = eio((t - t0) / max(t1 - t0, 0.1))
    z0, z1, px, py = motion
    z = z0 + (z1 - z0) * u
    cxo = W / 2 + px * (u - 0.5); cyo = H / 2 + py * (u - 0.5)
    s = 1 / z
    mx = (cxo + (gu - W / 2) * s).astype(np.float32); my = (cyo + (gv - H / 2) * s).astype(np.float32)
    d = cv2.remap(d0, mx, my, cv2.INTER_LINEAR)
    orb = 26 * np.sin(np.pi * u - np.pi / 2)
    mx = (mx + orb * (d - 0.5) * 1.5).astype(np.float32)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    cap = caption_rgba(t, W, H, 1010, 300, 0.92)
    if cap is not None:
        al = cap[..., 3:] / 255
        sh = np.roll(cv2.GaussianBlur(cap[..., 3], (0, 0), 12)[..., None] / 255 * 0.8, (8, 8), (0, 1))
        out = out * (1 - sh); out = out * (1 - al) + cap[..., :3][..., ::-1] * al
    return out

# ---------- linha de tempo ----------
# ('p', inicio, cx, cy, largura0, largura1) | ('o', inicio, imagem, (zoom0, zoom1, pan x, pan y))
WIDE, MED, CLOSE = (620, 395, 1200, 1100), (700, 300, 900, 820), (760, 262, 760, 690)
TL = [('p', 0.0) + WIDE, ('o', 1.25, 1, (1.0, 1.12, 60, 0)), ('o', 3.74, 2, (1.08, 1.0, -80, 0)),
      ('o', 5.56, 3, (1.0, 1.1, 0, -40)), ('o', 7.88, 4, (1.12, 1.0, 100, 0)),
      ('p', 10.7) + MED, ('p', 13.34) + CLOSE, ('p', 16.54) + WIDE, ('p', 18.6) + MED,
      ('o', 21.44, 5, (1.0, 1.1, 0, 30)), ('p', 24.24) + CLOSE, ('o', 25.18, 6, (1.1, 1.0, 0, 0)),
      ('p', 28.06) + MED, ('o', 29.8, 7, (1.0, 1.12, -60, 0)), ('o', 32.26, 8, (1.12, 1.0, 80, 0)),
      ('p', 35.14) + WIDE, ('p', 37.0) + CLOSE, ('o', 38.84, 9, (1.0, 1.1, 0, -30)),
      ('o', 42.7, 10, (1.0, 1.12, 40, 0)), ('p', 45.4) + CLOSE]
def seg_at(t):
    j = max(i for i, s in enumerate(TL) if s[1] <= t)
    return j, TL[j], (TL[j + 1][1] if j + 1 < len(TL) else VEND)
def shot(t):
    j, s, e = seg_at(t)
    if s[0] == 'p':
        u = eio((t - s[1]) / (e - s[1]))
        return podcast(t, s[2], s[3], s[4] + (s[5] - s[4]) * u)
    return origami(s[2], t, s[1], e, s[3])

logo = cv2.imread(LOGO, cv2.IMREAD_UNCHANGED).astype(np.float32)
def put(cv, rgba, x, y, op=1.0):
    h, w = rgba.shape[:2]; al = rgba[..., 3:] / 255 * op
    cv[y:y + h, x:x + w] = cv[y:y + h, x:x + w] * (1 - al) + rgba[..., :3] * al
fnt_e = ImageFont.truetype(FONT, 96); fnt_n = ImageFont.truetype(FONT, 72); fnt_s = ImageFont.truetype(FONT, 32)
def endcard(t):
    cv = np.zeros((H, W, 3), np.float32); cv[:] = (14, 12, 12); u = t - VEND
    k = ease(u / 0.4); lg = cv2.resize(logo, (int(760 * (0.85 + 0.15 * k)), int(760 * (0.85 + 0.15 * k) * logo.shape[0] / logo.shape[1])))
    put(cv, lg, 480 - lg.shape[1] // 2, 540 - lg.shape[0] // 2, k)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    l1, l2 = 'PROTEJA QUEM', 'VOCÊ AMA.'
    n1 = int(clamp((u - 0.3) / 0.6) * len(l1)); n2 = int(clamp((u - 0.95) / 0.45) * len(l2))
    d.text((960, 300), l1[:n1], font=fnt_e, fill=WHITE); d.text((960, 410), l2[:n2], font=fnt_e, fill=ORANGE)
    if u > 1.5:
        kk = ease((u - 1.5) / 0.3); pw = int(820 * kk)
        d.rounded_rectangle([960, 600, 960 + pw, 730], radius=65, fill=(37, 211, 102, 255))
        num = '+244 921 112 654'; nn = int(clamp((u - 1.7) / 0.7) * len(num))
        d.text((1000, 622), num[:nn], font=fnt_n, fill=WHITE)
        d.text((975, 555), 'WHATSAPP / LIGUE', font=fnt_s, fill=(37, 211, 102))
    arr = np.array(im).astype(np.float32); arr[..., :3] = arr[..., :3][..., ::-1]
    put(cv, arr, 0, 0)
    return cv

XF = 0.18
def frame(t):
    if t >= VEND: return endcard(t)
    img = shot(t)
    j, s, e = seg_at(t)
    if j > 0 and t - s[1] < XF:  # dissolve curto entre planos
        img = img * ((t - s[1]) / XF) + shot(s[1] - 0.001) * (1 - (t - s[1]) / XF)
    if t < 0.25: img *= ease(t / 0.25)
    return img

if __name__ == '__main__':
    endkeys = [VEND + 0.3 + 0.05 * i for i in range(12)] + [VEND + 0.95 + 0.05 * i for i in range(9)] + [VEND + 1.7 + 0.044 * i for i in range(16)]
    json.dump({'keys': sorted(KEYS + endkeys), 'vend': VEND, 'dur': DUR}, open('pod2_events.json', 'w'))
    if len(sys.argv) > 1:
        for ts in sys.argv[1:]:
            cv2.imwrite(f'p2_{ts}.jpg', np.clip(frame(float(ts)), 0, 255).astype(np.uint8))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        p.stdin.write(np.clip(frame(i / FPS), 0, 255).astype(np.uint8).tobytes())
        if i % 150 == 0: print(i, '/', n, flush=True)
    p.stdin.close(); p.wait()
