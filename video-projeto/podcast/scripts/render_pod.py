# Video "podcast" 9:16: a imagem de papel fala o audio (maxilar pela voz), pisca, mexe a cabeca;
# camara 3D (mapa de profundidade) com planos aberto/medio/fechado; legendas grandes teclas a teclas.
import os, sys, json, subprocess, cv2, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from puppet import Puppet, K
IMG = os.environ.get('IMG', '7.jpg'); DEPTH = os.environ.get('DEPTH', 'depth.npy'); VOZ = os.environ.get('VOZ', 'a50.wav')
WORDS = os.environ.get('WORDS', 'words.json'); FONT = os.environ.get('FONT', 'Montserrat-ExtraBold.ttf')
LOGO = os.environ.get('LOGO', 'kukulu-logo@2x.png'); OUT = os.environ.get('OUT', 'pod_mudo.mp4')
W, H, FPS = 1080, 1920, 30
SHIFT = 1.66          # corta o silencio inicial do audio
VEND = 50.0 - SHIFT   # fim da fala usada
DUR = VEND + 3.2      # + cartao final
BY0, BH = 330, 1200   # faixa da cena no ecra
ORANGE = (248, 168, 0); WHITE = (255, 255, 255)

def clamp(x, a=0.0, b=1.0): return min(max(x, a), b)
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 0.5 - 0.5 * np.cos(np.pi * x)

# ---------- voz -> maxilar ----------
a, sr = sf.read(VOZ, dtype='float32')
if a.ndim > 1: a = a.mean(1)
a = a[int(SHIFT * sr):int(50.0 * sr)]
hop = sr // 100
fr = np.sqrt(np.maximum(np.convolve(a ** 2, np.ones(hop) / hop, 'same')[::hop], 0) + 1e-10)
db = 20 * np.log10(fr)
ref = np.percentile(db[db > -60], 95)
op = np.clip((db - (ref - 26)) / 24, 0, 1) ** 0.9
sm = np.zeros_like(op)
for i in range(1, len(op)):
    k = 0.55 if op[i] > sm[i - 1] else 0.35
    sm[i] = sm[i - 1] + k * (op[i] - sm[i - 1])
energy = np.convolve(op, np.ones(40) / 40, 'same')
def jaw_at(t):
    i = int(t * 100)
    return 15.0 * sm[i] if 0 <= i < len(sm) else 0.0
def en_at(t):
    i = int(t * 100); return energy[i] if 0 <= i < len(energy) else 0.0

rng = np.random.default_rng(11)
BLINKS = []; tb = 1.2
while tb < DUR: BLINKS.append(tb); tb += 2.4 + 2.6 * rng.random()
def blink_at(t):
    for b in BLINKS:
        if b <= t < b + 0.17: return 1 - abs((t - b) / 0.085 - 1)
    return 0.0

# ---------- planos de camara (tempo do audio original) ----------
# (inicio, centro x, centro y, largura inicial, largura final)  coords originais
SHOTS = [(1.66, 640, 455, 800, 730), (5.9, 600, 380, 600, 550), (10.1, 632, 300, 420, 370),
         (13.0, 595, 395, 640, 540), (20.2, 640, 455, 800, 720), (24.5, 632, 305, 430, 350),
         (28.7, 600, 380, 610, 545), (34.2, 650, 455, 800, 730), (42.3, 630, 310, 450, 330)]
SH = [(s - SHIFT, cx, cy, w0, w1) for s, cx, cy, w0, w1 in SHOTS]

src = cv2.imread(IMG); IH, IW = src.shape[:2]
pup = Puppet(src)
dep = cv2.resize(np.load(DEPTH), (IW * K, IH * K), interpolation=cv2.INTER_LINEAR)
gu, gv = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(BH, dtype=np.float32))

def shot_at(t):
    j = max(i for i, s in enumerate(SH) if s[0] <= max(t, 0)) if t >= 0 else 0
    s = SH[j]; e = SH[j + 1][0] if j + 1 < len(SH) else VEND
    u = eio((t - s[0]) / (e - s[0]))
    return s[1], s[2], s[3] + (s[4] - s[3]) * u, j

def scene(t):
    tt = t
    jaw = jaw_at(tt); en = en_at(tt)
    ang = 1.1 * np.sin(2 * np.pi * tt / 3.9) + 1.3 * en * np.sin(2 * np.pi * tt / 1.35)
    hdy = 2.5 * en * np.sin(2 * np.pi * tt / 0.9)
    img = pup.frame(jaw, blink_at(tt), ang, 0, hdy)
    cx, cy, ww, j = shot_at(tt)
    wh = ww * BH / W
    cy = clamp(cy, wh / 2, IH - wh / 2); cx = clamp(cx, ww / 2, IW - ww / 2)
    # camara 3D: orbita suave + profundidade (o que esta perto mexe mais)
    close = ww < 500
    amp = 10 if close else 22
    camx = amp * np.sin(2 * np.pi * tt / 6.5) * K; camy = 0.4 * amp * np.sin(2 * np.pi * tt / 4.7) * K
    sx = ww * K / W; x0 = (cx - ww / 2) * K; y0 = (cy - wh / 2) * K
    mx = (x0 + gu * sx).astype(np.float32); my = (y0 + gv * sx).astype(np.float32)
    d = cv2.remap(dep, mx, my, cv2.INTER_LINEAR)
    df = 0.55
    mx = (mx + camx * (d - df) * 1.6).astype(np.float32); my = (my + camy * (d - df) * 1.6).astype(np.float32)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if sx < 0.95:  # nitidez nos planos fechados
        bl = cv2.GaussianBlur(out, (0, 0), 1.4); out = out * 1.45 - bl * 0.45
    return out, j

# ---------- legendas ----------
WD = json.load(open(WORDS))
words = []
for s, e, w in WD:
    if s >= 50.0: continue
    if w.startswith('-') and words: ps, pe, pw = words[-1]; words[-1] = (ps, e - SHIFT, pw + w)
    else: words.append((s - SHIFT, e - SHIFT, w))
EMPH = {'imagina', 'meia-noite', 'barulhos', 'esposa', 'filhos', 'estranhas', 'perigo', 'família', 'vivos', 'vivos.',
        'cerca', 'eléctrica', 'elétrica', 'segurança', 'amas', 'ama', 'certeza', 'absoluta', 'importante', 'prevenirias',
        'mata', 'tempo', 'residência', 'casa', 'família'}
def is_emph(w): return w.lower().strip('.,?!') in {e.strip('.,?!') for e in EMPH}
FS = 100; fnt = ImageFont.truetype(FONT, FS)
MAXW = 980
chunks = []; cur = []
for i, (s, e, w) in enumerate(words):
    test = cur + [(s, e, w)]
    lines = []; line = ''
    for _, _, ww_ in test:
        cand = (line + ' ' + ww_).strip()
        if fnt.getlength(cand.upper()) > MAXW and line: lines.append(line); line = ww_
        else: line = cand
    lines.append(line)
    gap = s - cur[-1][1] if cur else 0
    if cur and (len(lines) > 2 or gap > 0.5 or cur[-1][2][-1] in '.?!'):
        chunks.append(cur); cur = [(s, e, w)]
    else:
        cur = test
if cur: chunks.append(cur)
CH = []
for k, c in enumerate(chunks):
    st = c[0][0] - 0.05; en_ = chunks[k + 1][0][0] - 0.05 if k + 1 < len(chunks) else VEND + 0.3
    en_ = min(en_, c[-1][1] + 0.9)
    CH.append((st, en_, c))
KEYS = []
for st, en_, c in CH:
    for s, e, w in c:
        dur = min(max(e - s, 0.12) * 0.75, 0.42)
        for i in range(len(w)): KEYS.append(s + dur * i / max(len(w), 1))

def caption(cv, t):
    for st, en_, c in CH:
        if st <= t < en_: break
    else: return
    # monta linhas com as palavras (cada palavra escrita durante a fala dela)
    toks = []
    for s, e, w in c:
        dur = min(max(e - s, 0.12) * 0.75, 0.42)
        n = len(w) if t >= s + dur else max(0, int(len(w) * (t - s) / dur) + (1 if t >= s else 0))
        toks.append((w.upper(), min(n, len(w)), is_emph(w)))
    lines = [[]]; lw = 0
    for w, n, em in toks:
        ww_ = fnt.getlength(w + ' ')
        if lw + ww_ > MAXW + fnt.getlength(' ') and lines[-1]: lines.append([]); lw = 0
        lines[-1].append((w, n, em)); lw += ww_
    im = Image.new('RGBA', (W, 2 * (FS + 30) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cursor = None
    for li, ln in enumerate(lines):
        full = ' '.join(w for w, _, _ in ln); x = (W - fnt.getlength(full)) / 2; y = 20 + li * (FS + 26)
        for w, n, em in ln:
            if n > 0:
                d.text((x, y), w[:n], font=fnt, fill=ORANGE if em else WHITE, stroke_width=7, stroke_fill=(10, 10, 10))
                if n < len(w) or cursor is None or True: cursor = (x + fnt.getlength(w[:n]), y)
            x += fnt.getlength(w + ' ')
    typing = any(n < len(w) for w, n, _ in toks) and any(n > 0 for _, n, _ in toks)
    last_done = all(n == len(w) for w, n, _ in toks)
    if cursor and (typing or (not last_done) or int(t * 4) % 2 == 0):
        cx, cy = cursor; d.rectangle([cx + 6, cy + 6, cx + 16, cy + FS + 4], fill=ORANGE)
    arr = np.array(im).astype(np.float32)
    al = arr[..., 3:] / 255
    sh = cv2.GaussianBlur(arr[..., 3], (0, 0), 10)[..., None] / 255 * 0.6
    y0 = 1255
    reg = cv[y0:y0 + arr.shape[0]]
    reg[:] = reg * (1 - sh) ; reg[:] = reg * (1 - al) + arr[..., :3][..., ::-1] * al

# ---------- composicao ----------
logo = cv2.imread(LOGO, cv2.IMREAD_UNCHANGED); lw_ = 420
logo = cv2.resize(logo, (lw_, int(logo.shape[0] * lw_ / logo.shape[1])), interpolation=cv2.INTER_AREA).astype(np.float32)
fnt_s = ImageFont.truetype(FONT, 34)
def put_rgba(cv, rgba, x, y, op=1.0):
    h, w = rgba.shape[:2]; al = rgba[..., 3:] / 255 * op
    cv[y:y + h, x:x + w] = cv[y:y + h, x:x + w] * (1 - al) + rgba[..., :3] * al

ramp = np.ones((BH, 1, 1), np.float32); f = 70
ramp[:f, 0, 0] = np.linspace(0, 1, f); ramp[-f:, 0, 0] = np.linspace(1, 0, f)

def endcard(t):
    cv = np.zeros((H, W, 3), np.float32); cv[:] = (14, 12, 12)
    u = t - VEND
    k = ease(u / 0.4)
    lg = cv2.resize(logo, None, fx=1.9 * (0.8 + 0.2 * k), fy=1.9 * (0.8 + 0.2 * k))
    put_rgba(cv, lg, (W - lg.shape[1]) // 2, 520 - lg.shape[0] // 2, k)
    im = Image.new('RGBA', (W, 700), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    l1 = 'PROTEJA QUEM'; l2 = 'VOCÊ AMA.'
    n1 = int(clamp((u - 0.3) / 0.6) * len(l1)); n2 = int(clamp((u - 0.95) / 0.45) * len(l2))
    d.text(((W - fnt.getlength(l1)) / 2, 0), l1[:n1], font=fnt, fill=WHITE)
    d.text(((W - fnt.getlength(l2)) / 2, 110), l2[:n2], font=fnt, fill=ORANGE)
    if u > 1.5:
        kk = ease((u - 1.5) / 0.3); pw = int(880 * kk); x0 = (W - pw) // 2
        d.rounded_rectangle([x0, 290, x0 + pw, 430], radius=70, fill=(37, 211, 102, 255))
        num = '+244 921 112 654'; nn = int(clamp((u - 1.7) / 0.7) * len(num))
        fn2 = ImageFont.truetype(FONT, 76)
        d.text(((W - fn2.getlength(num)) / 2, 318), num[:nn], font=fn2, fill=WHITE)
        lt = 'WHATSAPP / LIGUE'; d.text(((W - fnt_s.getlength(lt)) / 2, 245), lt, font=fnt_s, fill=(37, 211, 102))
    arr = np.array(im).astype(np.float32); arr[..., :3] = arr[..., :3][..., ::-1]
    put_rgba(cv, arr, 0, 860)
    return cv

def frame(t):
    if t >= VEND: return endcard(t)
    band, j = scene(t)
    cv = np.empty((H, W, 3), np.float32)
    small = cv2.resize(band, (W // 8, BH // 8)); bg = cv2.GaussianBlur(cv2.resize(small, (W, H)), (0, 0), 25) * 0.35
    cv[:] = bg
    cv[BY0:BY0 + BH] = cv[BY0:BY0 + BH] * (1 - ramp) + band * ramp
    put_rgba(cv, logo, (W - logo.shape[1]) // 2, 150)
    caption(cv, t)
    # corte com flash curto entre planos
    for s in SH[1:]:
        if 0 <= t - s[0] < 0.1: cv = cv + 50 * (1 - (t - s[0]) / 0.1)
    if t < 0.3: cv *= ease(t / 0.3)
    return cv

if __name__ == '__main__':
    json.dump({'keys': sorted(KEYS), 'cuts': [s[0] for s in SH[1:]] + [VEND], 'shift': SHIFT, 'vend': VEND, 'dur': DUR}, open('pod_events.json', 'w'))
    if len(sys.argv) > 1:
        for ts in sys.argv[1:]:
            cv2.imwrite(f'ptest_{ts}.jpg', np.clip(frame(float(ts)), 0, 255).astype(np.uint8))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        p.stdin.write(np.clip(frame(i / FPS), 0, 255).astype(np.uint8).tobytes())
        if i % 150 == 0: print(i, '/', n, flush=True)
    p.stdin.close(); p.wait()
