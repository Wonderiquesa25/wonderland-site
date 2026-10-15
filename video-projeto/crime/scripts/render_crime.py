# Video "investigacao criminal" (16:9): narrador origami + cenas origami de crime em cortes rapidos,
# recortes de jornal que caem com impacto, luzes de sirene, grade frio -> quente na chamada para accao.
import os, sys, json, subprocess, cv2, numpy as np, soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../podcast/scripts'))
from puppet import Puppet, K
P = os.environ.get('POD', '../pod/')
VOZ = os.environ.get('VOZ', 'voz.wav'); WORDS = os.environ.get('WORDS', 'voz_w.json'); ORI = os.environ.get('ORI', 'ori')
FONT = P + 'Montserrat-ExtraBold.ttf'; SERIF = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
SERIF_I = '/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf'
OUT = os.environ.get('OUT', 'crime_mudo.mp4')
W, H, FPS = 1920, 1080, 30
ORANGE = (248, 168, 0); WHITE = (255, 255, 255)
def clamp(x, a=0.0, b=1.0): return min(max(x, a), b)
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return 0.5 - 0.5 * np.cos(np.pi * x)
def back(x, s=1.7): x = clamp(x); x -= 1; return x * x * ((s + 1) * x + s) + 1

# ---------- voz ----------
a, sr = sf.read(VOZ, dtype='float32')
if a.ndim > 1: a = a.mean(1)
VEND = len(a) / sr + 0.1
DUR = VEND + 3.4
hop = sr // 100
fr = np.sqrt(np.maximum(np.convolve(a ** 2, np.ones(hop) / hop, 'same')[::hop], 0) + 1e-10)
db = 20 * np.log10(fr); ref = np.percentile(db[db > -60], 95)
op = np.convolve(np.clip((db - (ref - 24)) / 22, 0, 1), np.ones(5) / 5, 'same')
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

# ---------- palavras (correccoes de nomes e grafia) ----------
FIX = {'Clamba': 'Kilamba', 'Quiache,': 'Kiaxi,', 'Quianda,': 'Kianda,', 'diretor': 'director', 'elétrica': 'eléctrica',
       'câmeras': 'câmaras'}
words = []
for i, d in enumerate(json.load(open(WORDS))):
    s, e, w = d['s'], d['e'], d['w'].strip()
    if i == 26 and w == 'Segundo,': w = 'Segundo'           # "Segundo uma outra noticia" (preposicao)
    w = FIX.get(w, w)
    if words and w.lower().strip('.,?!') == words[-1][2].lower().strip('.,?!') and s - words[-1][1] < 0.15: continue  # eco duplicado
    if w.startswith('-') and words: ps, pe, pw = words[-1]; words[-1] = (ps, e, pw + w)
    else: words.append((s, e, w))
EMPH = {'madrugada', '22', 'abril', '2025', 'família', 'assaltantes', 'armados', 'kilamba', 'kiaxi', 'luanda', 'kianda',
        '10', 'indivíduos', 'invadido', 'inavic', 'morto', 'tiro', 'esposa', 'filhos', 'baleados', 'protegidos',
        'tragédia', 'portão', 'porta', 'investigação', 'justiça', 'dor', 'perdeu', 'trágica', 'prevenção', 'perigo',
        'câmaras', 'videovigilância', 'cerca', 'eléctrica', 'alarme', 'atacar', 'primeiro', 'defesa', 'ataque',
        'antecipado', 'duas', 'vezes', 'melhor'}
def is_emph(w): return w.lower().strip('.,?!') in EMPH
FS = 150; fnt = ImageFont.truetype(FONT, FS); MAXW = 800
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
def T(i): return words[i][0]  # tempo da palavra i (indices apos fusao de hifens)
def find(word, after=0.0):
    for s, e, w in words:
        if s >= after and w.lower().strip('.,?!') == word: return s
    raise KeyError(word)

def caption_rgba(t, size_w, size_h, x0, y0, fs_scale=1.0):
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

# ---------- narrador origami (cena do podcast) ----------
src = cv2.imread(P + '7.jpg'); IH, IW = src.shape[:2]
pup = Puppet(src)
dep = cv2.resize(np.load(P + 'depth.npy'), (IW * K, IH * K), interpolation=cv2.INTER_LINEAR).astype(np.float32)
fg = np.clip((dep - 0.30) / 0.07, 0, 1)[..., None]
gu, gv = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
CAP_X0, CAP_Y = 735 * K, 352 * K
def podcast(t, cx, cy, ww):
    jaw = jaw_at(t); en = en_at(t)
    ang = 0.9 * np.sin(2 * np.pi * t / 4.1) + 0.9 * en * np.sin(2 * np.pi * t / 1.5)
    hdy = 1.6 * en * np.sin(2 * np.pi * t / 1.0)
    img = pup.frame(jaw, blink_at(t), ang, 0, hdy)
    cap = caption_rgba(t, IW * K, IH * K, CAP_X0, CAP_Y)
    if cap is not None:
        al = cap[..., 3:] / 255 * (1 - fg)
        sh = np.roll(cv2.GaussianBlur(cap[..., 3], (0, 0), 9)[..., None] / 255 * 0.65, (10, 12), (0, 1)) * (1 - fg)
        img = img * (1 - sh); img = img * (1 - al) + cap[..., :3][..., ::-1] * al
    wh = ww * H / W
    cy = clamp(cy, wh / 2, IH - wh / 2); cx = clamp(cx, ww / 2, IW - ww / 2)
    amp = 16 if ww > 900 else 10
    camx = amp * np.sin(2 * np.pi * t / 7.0) * K; camy = 0.35 * amp * np.sin(2 * np.pi * t / 5.3) * K
    s = ww * K / W; x0 = (cx - ww / 2) * K; y0 = (cy - wh / 2) * K
    mx = (x0 + gu * s).astype(np.float32); my = (y0 + gv * s).astype(np.float32)
    d = cv2.remap(dep, mx, my, cv2.INTER_LINEAR)
    mx = (mx + camx * (d - 0.5) * 1.6).astype(np.float32); my = (my + camy * (d - 0.5) * 1.6).astype(np.float32)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    if s < 1.05: bl = cv2.GaussianBlur(out, (0, 0), 1.3); out = out * 1.4 - bl * 0.4
    return out

# ---------- cenas origami com camara 3D (keyframes de zoom/pan + paralaxe por profundidade) ----------
ORIG = {i: (cv2.imread(f'{ORI}/c{i}.jpg').astype(np.float32), np.load(f'{ORI}/d{i}.npy').astype(np.float32)) for i in range(1, 15)}
def origami(i, t, t0, t1, mo):
    img, d0 = ORIG[i]
    z0, z1, px0, py0, px1, py1 = mo
    u = eio((t - t0) / max(t1 - t0, 0.1))
    z = z0 + (z1 - z0) * u; px = px0 + (px1 - px0) * u; py = py0 + (py1 - py0) * u
    s = 1 / z
    mx = (W / 2 + px + (gu - W / 2) * s).astype(np.float32); my = (H / 2 + py + (gv - H / 2) * s).astype(np.float32)
    d = cv2.remap(d0, mx, my, cv2.INTER_LINEAR)
    orb = 30 * np.sin(np.pi * u - np.pi / 2)
    mx = (mx + orb * (d - 0.5) * 1.6).astype(np.float32); my = (my - 0.3 * orb * (d - 0.5)).astype(np.float32)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    cap = caption_rgba(t, W, H, 1010, 300, 0.92)
    if cap is not None:
        al = cap[..., 3:] / 255
        sh = np.roll(cv2.GaussianBlur(cap[..., 3], (0, 0), 12)[..., None] / 255 * 0.85, (8, 8), (0, 1))
        out = out * (1 - sh); out = out * (1 - al) + cap[..., :3][..., ::-1] * al
    return out

# ---------- recortes de jornal ----------
fh = lambda s: ImageFont.truetype(SERIF, s); fi = lambda s: ImageFont.truetype(SERIF_I, s)
def wrap(d, text, f, maxw):
    L = [[]]
    for w in text.split():
        if L[-1] and d.textlength(' '.join(L[-1] + [w]), font=f) > maxw: L.append([])
        L[-1].append(w)
    return [' '.join(l) for l in L]
def make_clip(kicker, head, sub, src_line, photo, seed, wd=760):
    r = np.random.default_rng(seed); pad = 34; inner = wd - 2 * pad
    tmp = ImageDraw.Draw(Image.new('RGB', (10, 10)))
    hl = wrap(tmp, head.upper(), fh(70), inner)
    hph = int(inner * 0.42) if photo is not None else 0
    hh = 26 + 64 + 46 + len(hl) * 74 + 16 + (44 if sub else 0) + (hph + 22 if hph else 0) + 6 * 26 + (40 if src_line else 0) + 40
    im = Image.new('RGB', (wd, hh), (233, 224, 200)); d = ImageDraw.Draw(im)
    y = 26
    d.line([pad, y, wd - pad, y], fill=(40, 34, 28), width=3); y += 10
    d.text((wd // 2, y + 22), 'ÚLTIMA HORA  •  SEGURANÇA', font=fh(34), fill=(30, 26, 22), anchor='mm'); y += 50
    d.line([pad, y, wd - pad, y], fill=(40, 34, 28), width=1); y += 14
    d.text((pad, y), kicker.upper(), font=fi(30), fill=(165, 28, 22)); y += 46
    for l in hl: d.text((pad, y), l, font=fh(70), fill=(18, 16, 14)); y += 74
    y += 6
    if sub: d.text((pad, y), sub, font=fi(32), fill=(55, 48, 40)); y += 44
    if hph:
        ph = cv2.cvtColor(np.clip(photo, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        ph = cv2.resize(ph, (inner, int(inner * ph.shape[0] / ph.shape[1])))[:hph]
        ph = cv2.equalizeHist(ph).astype(np.float32)
        yy, xx = np.mgrid[0:ph.shape[0], 0:ph.shape[1]]
        dots = (np.sin(xx * 0.9) * np.sin(yy * 0.9) * 0.5 + 0.5) * 255           # retícula de impressao
        ph = np.where(ph > dots * 0.85 + 20, 236, 40).astype(np.uint8)
        ph = cv2.GaussianBlur(ph, (0, 0), 0.7)
        im.paste(Image.fromarray(cv2.cvtColor(ph, cv2.COLOR_GRAY2RGB)).convert('RGB').point(lambda v: int(v * 0.92 + 12)), (pad, y + 4))
        d.rectangle([pad, y + 4, pad + inner, y + 4 + hph], outline=(40, 34, 28), width=2); y += hph + 22
    colw = (inner - 24) // 2                                            # texto corrido ilegivel (so manchas)
    for c in range(2):
        for k in range(6):
            ln = colw if k < 5 else int(colw * (0.4 + 0.4 * r.random()))
            d.rectangle([pad + c * (colw + 24), y + k * 26, pad + c * (colw + 24) + ln, y + k * 26 + 11], fill=(120, 110, 96))
    y += 6 * 26 + 6
    if src_line: d.text((pad, y), src_line, font=fi(28), fill=(80, 70, 58)); y += 40
    arr = np.array(im).astype(np.float32)
    # envelhecimento: grao, manchas, bordas mais escuras
    arr += r.normal(0, 7, arr.shape[:2])[..., None]
    for _ in range(5):
        cy_, cx_ = r.integers(0, hh), r.integers(0, wd); rad = r.integers(40, 160)
        yy, xx = np.mgrid[0:hh, 0:wd]
        arr *= 1 - 0.10 * np.exp(-((xx - cx_) ** 2 + (yy - cy_) ** 2) / (2 * rad ** 2))[..., None]
    yy, xx = np.mgrid[0:hh, 0:wd]
    edge = np.minimum.reduce([xx, yy, wd - 1 - xx, hh - 1 - yy]).astype(np.float32)
    arr *= (0.80 + 0.20 * np.clip(edge / 40, 0, 1))[..., None]
    # bordas rasgadas (alpha)
    al = np.ones((hh, wd), np.float32)
    for side in range(4):
        n = wd if side < 2 else hh
        prof = np.cumsum(r.normal(0, 1.4, n)); prof = np.abs(prof - np.linspace(prof[0], prof[-1], n))
        prof = 3 + np.clip(prof, 0, 9) + 3 * r.random(n)
        for p in range(n):
            q = int(prof[p])
            if side == 0: al[:q, p] = 0
            elif side == 1: al[hh - q:, p] = 0
            elif side == 2: al[p, :q] = 0
            else: al[p, wd - q:] = 0
    al = cv2.GaussianBlur(al, (0, 0), 0.8)
    bgr = np.clip(arr, 0, 255)[..., ::-1]
    return np.dstack([bgr, al * 255]).astype(np.float32)

def stamp(text, seed):
    f = fh(64); tmp = ImageDraw.Draw(Image.new('RGB', (10, 10))); tw = int(tmp.textlength(text, font=f))
    im = Image.new('RGBA', (tw + 70, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([6, 6, tw + 64, 114], radius=10, outline=(200, 30, 26, 255), width=7)
    d.text((35, 60), text, font=f, fill=(200, 30, 26, 255), anchor='lm')
    a_ = np.array(im).astype(np.float32); r = np.random.default_rng(seed)
    a_[..., 3] *= np.clip(0.55 + 0.6 * r.random(a_.shape[:2]), 0, 1)              # tinta irregular
    return np.dstack([a_[..., 2::-1], a_[..., 3]])

def blit(cv, rgba, cx, cy, scale, rot, opac):
    h, w = rgba.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale); M[0, 2] += cx - w / 2; M[1, 2] += cy - h / 2
    warped = cv2.warpAffine(rgba, M, (W, H), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    al = warped[..., 3:] / 255 * opac
    sh = cv2.GaussianBlur(np.roll(al[..., 0], (18, 22), (0, 1)), (0, 0), 14)[..., None] * 0.75
    cv = cv * (1 - sh)
    return cv * (1 - al) + warped[..., :3] * al

# ---------- linha de tempo ----------
def mo(z0, z1, px0=0, py0=0, px1=0, py1=0): return (z0, z1, px0, py0, px1, py1)
WIDE, MED, CLOSE = (620, 395, 1200, 1100), (765, 300, 900, 830), (815, 262, 760, 700)
t_pense = find('pense'); t_lugar = find('lugar'); t_e = find('e', t_lugar); t_torna = find('torna-se')
t_se = find('se', t_torna); t_fechar = find('fechar'); t_inv = find('investigação'); t_aut = find('autoridades')
t_mas = find('mas', t_aut); t_nao = find('não'); t_prev = find('prevenção'); t_inst = find('instale')
t_cerca = find('cerca'); t_ponha = find('ponha'); t_desse = find('desse'); t_primeiro = find('primeiro')
t_ou = find('ou', t_primeiro); t_mas2 = find('mas', t_ou)
TL = [('o', 0.0, 6, mo(1.0, 1.18, 0, 0, 40, 10)),
      ('o', find('2025'), 1, mo(1.05, 1.22, -60, 0, 60, 10)),
      ('o', find('família'), 2, mo(1.0, 1.15, 40, 0, -40, 0)),
      ('o', find('assaltantes'), 1, mo(1.35, 1.55, 200, 60, 260, 80)),
      ('o', find('residência'), 3, mo(1.1, 1.0, 0, -20, 0, 20)),
      ('o', find('kilamba'), 6, mo(1.2, 1.35, -200, -60, -260, -80)),
      ('o', find('segundo'), 8, mo(1.0, 1.12, 0, 0, 30, 0)),
      ('o', find('10'), 3, mo(1.15, 1.3, 0, 40, -120, 20)),
      ('o', find('o', 16.5), 4, mo(1.0, 1.14, -40, 0, 40, 0)),
      ('o', find('de', find('david')), 4, mo(1.45, 1.6, 120, 160, 160, 180)),
      ('o', find('foi', find('anos')), 5, mo(1.0, 1.15, 0, 0, 40, -10)),
      ('o', find('esposa'), 5, mo(1.35, 1.5, -240, 0, -200, 10)),
      ('p', t_pense) + WIDE,
      ('o', find('família', t_pense), 2, mo(1.12, 1.0, 0, 0, 0, 0)),
      ('p', t_lugar) + MED,
      ('o', t_e, 6, mo(1.0, 1.2, -40, 0, 60, -20)),
      ('o', t_torna, 5, mo(1.2, 1.45, 0, 0, 30, 20)),
      ('p', t_se) + CLOSE,
      ('o', t_fechar - 0.5, 7, mo(1.0, 1.18, 60, 0, -20, 0)),
      ('o', t_inv, 8, mo(1.25, 1.0, 0, 0, 0, 0)),
      ('o', t_aut, 9, mo(1.0, 1.15, 0, 0, -60, 0)),
      ('o', t_mas, 10, mo(1.0, 1.18, 0, 30, 0, 0)),
      ('p', t_nao) + MED, ('p', t_prev) + WIDE,
      ('o', t_inst, 11, mo(1.0, 1.2, 0, 0, 120, -20)),
      ('o', t_cerca - 0.3, 12, mo(1.1, 1.3, -60, 0, 80, -10)),
      ('o', t_ponha, 13, mo(1.0, 1.18, 60, 0, 120, 0)),
      ('p', t_desse) + CLOSE,
      ('o', t_primeiro, 13, mo(1.3, 1.5, -300, 40, -340, 50)),
      ('p', t_ou) + MED,
      ('o', t_mas2, 14, mo(1.2, 1.0, 0, 0, 0, 0))]
TL.sort(key=lambda s: s[1])
CUTS = [s[1] for s in TL[1:]]
def seg_at(t):
    j = max(i for i, s in enumerate(TL) if s[1] <= t)
    return j, TL[j], (TL[j + 1][1] if j + 1 < len(TL) else VEND)
def shot(t):
    j, s, e = seg_at(t)
    if s[0] == 'p':
        u = eio((t - s[1]) / (e - s[1]))
        return podcast(t, s[2], s[3], s[4] + (s[5] - s[4]) * u)
    return origami(s[2], t, s[1], e, s[3])

# recortes: (entrada, saida, rgba, cx, cy, rot, escala)
NEWS_END = t_pense
CLIPS = [
    (0.30, find('família') - 0.05, make_clip('Madrugada de 22 de Abril de 2025', 'Família surpreendida por assaltantes armados',
     'Dentro da própria residência', None, ORIG[1][0], 1), 470, 560, -4, 0.95),
    (find('kilamba') - 0.15, find('segundo') - 0.05, stamp('KILAMBA KIAXI • LUANDA', 2), 520, 760, -8, 1.0),
    (find('segundo') + 0.15, find('10') + 1.4, make_clip('24 de Abril', 'Dez indivíduos terão invadido a casa', None,
     'Segundo notícia do Correio da Kianda', ORIG[3][0], 3), 480, 560, 3, 0.92),
    (find('o', 16.5) + 0.1, find('foi', find('anos')) - 0.05, make_clip('Vítima', 'Antigo director-geral do INAVIC morto a tiro',
     'Carlos Manuel David, 67 anos', None, ORIG[4][0], 4), 470, 560, -3, 0.92),
    (find('esposa') - 0.05, t_pense - 0.05, make_clip('Família baleada', 'Esposa e os dois filhos também foram baleados',
     None, None, ORIG[5][0], 5), 480, 580, 4, 0.92)]
# no quadro da investigacao: os recortes voam em sucessao rapida para o quadro de cortica
BOARD = [(t_inv + 0.15 + 0.16 * k, t_aut - 0.05, CLIPS[ci][2], x, y, r_, 0.36)
         for k, (ci, (x, y, r_)) in enumerate(zip([0, 2, 3, 4], [(260, 330, -8), (590, 280, 6), (340, 680, -3), (680, 640, 9)]))]
ALLCLIPS = CLIPS + BOARD
IMPACTS = [c[0] + 0.24 for c in ALLCLIPS]

def clip_layer(cv, t):
    shake = np.zeros(2); flash = 0.0
    for t0, t1, rgba, cx, cy, rot, sc in ALLCLIPS:
        if not (t0 <= t < t1 + 0.14): continue
        u = (t - t0) / 0.28
        if t > t1:                                                    # saida rapida
            v = (t - t1) / 0.14
            cv = blit(cv, rgba, cx - 900 * ease(v), cy, sc * (1 + 0.1 * v), rot - 10 * v, 1 - v); continue
        s = sc * (1.7 - 0.7 * back(u)); r = rot + 14 * (1 - ease(u)); op = clamp(u * 4)
        drift = (t - t0) * 0.012
        cv = blit(cv, rgba, cx, cy - 70 * (1 - ease(u)), s * (1 + drift), r + 0.8 * np.sin(t * 1.3), op)
        k = t - (t0 + 0.24)
        if 0 <= k < 0.4:
            amp = (18 if sc > 0.5 else 8) * np.exp(-k * 9)
            shake += amp * np.array([np.sin(k * 90), np.cos(k * 70)])
            flash = max(flash, (0.35 if sc > 0.5 else 0.12) * np.exp(-k * 30))
    return cv, shake, flash

logo = cv2.imread(P + 'kukulu-logo@2x.png', cv2.IMREAD_UNCHANGED).astype(np.float32)
def put(cv, rgba, x, y, op=1.0):
    h, w = rgba.shape[:2]; al = rgba[..., 3:] / 255 * op
    cv[y:y + h, x:x + w] = cv[y:y + h, x:x + w] * (1 - al) + rgba[..., :3] * al
fnt_e = ImageFont.truetype(FONT, 96); fnt_n = ImageFont.truetype(FONT, 72); fnt_s = ImageFont.truetype(FONT, 32)
def endcard(t):
    cv = np.zeros((H, W, 3), np.float32); cv[:] = (14, 12, 12); u = t - VEND
    k = ease(u / 0.4); lg = cv2.resize(logo, (int(760 * (0.85 + 0.15 * k)), int(760 * (0.85 + 0.15 * k) * logo.shape[0] / logo.shape[1])))
    put(cv, lg, 480 - lg.shape[1] // 2, 540 - lg.shape[0] // 2, k)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    l1, l2 = 'A PREVENÇÃO', 'COMEÇA ANTES.'
    n1 = int(clamp((u - 0.3) / 0.6) * len(l1)); n2 = int(clamp((u - 0.95) / 0.45) * len(l2))
    d.text((960, 300), l1[:n1], font=fnt_e, fill=WHITE); d.text((960, 410), l2[:n2], font=fnt_e, fill=ORANGE)
    if u > 1.5:
        kk = ease((u - 1.5) / 0.3); pw = int(820 * kk)
        d.rounded_rectangle([960, 600, 960 + pw, 730], radius=65, fill=(37, 211, 102, 255))
        num = '+244 921 112 654'; nn = int(clamp((u - 1.7) / 0.7) * len(num))
        d.text((1000, 622), num[:nn], font=fnt_n, fill=WHITE)
        d.text((975, 555), 'WHATSAPP / LIGUE', font=fnt_s, fill=(37, 211, 102))
        d.text((960, 770), 'Câmaras  •  Cerca eléctrica  •  Alarmes', font=fnt_s, fill=(200, 200, 200))
    arr = np.array(im).astype(np.float32); arr[..., :3] = arr[..., :3][..., ::-1]
    put(cv, arr, 0, 0)
    return cv

# ---------- acabamento: sirene, grade, vinheta, grao ----------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.18 - 0.62 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H / 2) / (H * 0.70)) ** 2), 0.3, 1)[..., None]
LEFT = np.exp(-(xx / 520) ** 2)[..., None]; RIGHT = np.exp(-((W - xx) / 520) ** 2)[..., None]
grain_rng = np.random.default_rng(7)
def finish(img, t):
    crime = t < t_nao
    w = clamp((t - (t_nao - 0.6)) / 1.2)                        # transicao frio -> quente na chamada para accao
    cool = np.float32([1.10, 0.97, 0.86]); warm = np.float32([0.94, 1.0, 1.06])
    img = img * (cool * (1 - w) + warm * w)
    if t < t_se + 0.3 and seg_at(t)[1][0] == 'o':               # luzes de sirene nas cenas de crime
        ph = (t * 2.2) % 1.0; pulse = (np.sin(t * 2 * np.pi * 2.2) * 0.5 + 0.5) ** 2
        red = np.float32([30, 30, 255]); blue = np.float32([255, 90, 30])
        img = img + (LEFT * (red if ph < 0.5 else blue) + RIGHT * (blue if ph < 0.5 else red)) * 0.22 * pulse
    o = np.clip(img / 255, 0, 1)
    o = o * o * (3 - 2 * o) * 0.5 + o * 0.5
    o = o * VIG
    o = o + grain_rng.normal(0, 0.018 if crime else 0.010, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1).astype(np.float32)
    return o * 255

def frame(t):
    if t >= VEND:
        return endcard(t)
    img = shot(t)
    j, s, e = seg_at(t)
    dt = t - s[1]
    if j > 0 and dt < 0.10:                                       # corte em chicote (whip) entre planos
        v = 1 - dt / 0.10
        sh_ = int(160 * v) * (1 if j % 2 else -1)
        img = cv2.blur(np.roll(img, sh_, 1), (int(1 + 60 * v), 1))
    img, shake, flash = clip_layer(img, t)
    if np.any(shake):
        M = np.float32([[1.03, 0, shake[0] - W * 0.015], [0, 1.03, shake[1] - H * 0.015]])
        img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    img = finish(img, t)
    if flash > 0: img = img * (1 - flash) + 255 * flash
    if t < 0.2: img *= ease(t / 0.2)
    if t > VEND - 0.25: img *= clamp((VEND - t) / 0.25)
    return img

if __name__ == '__main__':
    json.dump({'keys': sorted(KEYS), 'cuts': CUTS, 'impacts': IMPACTS, 'vend': VEND, 'dur': DUR,
               'endkeys': [VEND + 0.3 + 0.05 * i for i in range(11)] + [VEND + 0.95 + 0.04 * i for i in range(13)] + [VEND + 1.7 + 0.044 * i for i in range(16)]},
              open('crime_events.json', 'w'))
    if len(sys.argv) > 1:
        for ts in sys.argv[1:]:
            cv2.imwrite(f'cr_{ts}.jpg', np.clip(frame(float(ts)), 0, 255).astype(np.uint8))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for i in range(n):
        p.stdin.write(np.clip(frame(i / FPS), 0, 255).astype(np.uint8).tobytes())
        if i % 150 == 0: print(i, '/', n, flush=True)
    p.stdin.close(); p.wait(); print('FIM', flush=True)
