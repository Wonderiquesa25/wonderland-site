# Video narrado v2: CEO recortado (BiRefNet + pymatting) a entrar em 3D, textos "teclados"
# letra a letra com cursor, fundos limpos (LaMa), transicoes zoom-blur. Tempos = voz sem pausas (+OFF).
import os, sys, json, subprocess, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
L = os.environ.get('LAYERS', 'layers2'); OUT = os.environ.get('OUT', 'mudo2.mp4')
FONT = os.environ.get('FONT', 'video-projeto/fonts/Montserrat-ExtraBold.ttf')
LOGO = os.environ.get('LOGO', 'brand/kukulu-logo@2x.png'); PERSON = os.environ.get('PERSON', 'person_hq.png')
W, H, FPS = 1080, 1920, 30
OFF = 0.4; DUR = 29.0
ORANGE = np.float32([248, 168, 0]); WHITE = np.float32([255, 255, 255])
META = json.load(open(f'{L}/letters.json'))
FW = ImageFont.truetype(FONT, 100)

def clamp(x): return min(max(x, 0.0), 1.0)
def ease(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_io(x): x = clamp(x); return 0.5 - 0.5 * np.cos(np.pi * x)
def back(x, c=1.70158):
    x = clamp(x); return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def ramp(t, a, b): return clamp((t - a) / (b - a))
def rd(p): return cv2.cvtColor(cv2.imread(p, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA if p.lower().endswith('png') else cv2.COLOR_BGR2RGBA)

class Layer:
    def __init__(self, rgba, s=1.0, ox=0, oy=0, crop=True):
        if s != 1.0:
            rgba = cv2.resize(rgba, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA)
        a = rgba[..., 3]
        if crop:
            ys, xs = np.nonzero(a > 2); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        else:
            y0, x0, y1, x1 = 0, 0, a.shape[0], a.shape[1]
        self.rgb = rgba[y0:y1, x0:x1, :3].astype(np.float32)
        self.a = rgba[y0:y1, x0:x1, 3].astype(np.float32) / 255
        self.x, self.y = x0 + ox, y0 + oy

def blend(cv, rgb, a, x, y, op=1.0):
    h, w = a.shape; x, y = int(round(x)), int(round(y))
    cx0, cy0, cx1, cy1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if cx1 <= cx0 or cy1 <= cy0 or op <= 0.003: return
    sa = a[cy0 - y:cy1 - y, cx0 - x:cx1 - x, None] * op
    cv[cy0:cy1, cx0:cx1] = cv[cy0:cy1, cx0:cx1] * (1 - sa) + rgb[cy0 - y:cy1 - y, cx0 - x:cx1 - x] * sa

def draw(cv, ly, op=1.0, sc=1.0, dx=0, dy=0, upto=None):
    """upto = coordenada x (canvas, antes de dx) ate onde a camada esta revelada"""
    rgb, a = ly.rgb, ly.a; h, w = a.shape
    if upto is not None:
        cut = upto - ly.x
        if cut <= 0: return
        if cut < w:
            xs = np.arange(w, dtype=np.float32)
            a = a * np.clip((cut - xs) / 2.5 + 0.5, 0, 1)[None, :]
    x, y = ly.x + dx, ly.y + dy
    if abs(sc - 1.0) > 1e-3:
        pad = int(abs(sc - 1) * max(w, h) / 2) + 2
        M = np.float32([[sc, 0, (1 - sc) * w / 2 + pad], [0, sc, (1 - sc) * h / 2 + pad]])
        size = (w + 2 * pad, h + 2 * pad)
        rgb = cv2.warpAffine(rgb, M, size); a = cv2.warpAffine(np.ascontiguousarray(a), M, size)
        x -= pad; y -= pad
    blend(cv, rgb, a, x, y, op)

# ---------------- texto "teclado" ----------------
class Typed:
    """camada de texto ja existente na imagem, revelada letra a letra com cursor"""
    def __init__(self, ly, meta, text, t0, t1, color, s, ox, oy, keys):
        self.ly, self.text, self.t0, self.t1, self.color = ly, text, t0, t1, color
        col = np.array(meta['col'], np.float32)
        xs = meta['x'] + np.arange(len(col))
        thr = max(2, 0.04 * col.max()); nz = np.nonzero(col >= thr)[0]
        x0, x1 = xs[nz.min()], xs[nz.max()] + 1
        self.y0, self.y1 = meta['y0'] * s + oy, meta['y1'] * s + oy
        tot = FW.getlength(text)
        cw = (x1 - x0) / max(len(text), 1)
        bounds = [x0]
        for n in range(1, len(text) + 1):
            if n == len(text): bounds.append(x1 + 1); break
            gx = x0 + (x1 - x0) * FW.getlength(text[:n]) / tot
            lo, hi = int(max(gx - 0.4 * cw, x0)), int(min(gx + 0.4 * cw, x1))
            seg = col[lo - meta['x']:hi - meta['x'] + 1]
            if len(seg):
                cand = np.nonzero(seg <= seg.min() + 0.5)[0] + lo
                gx = cand[np.argmin(np.abs(cand - gx))]
            bounds.append(max(gx, bounds[-1]))
        self.bounds = [b * s + ox for b in bounds]
        # tempos de cada tecla (ritmo humano: leve variacao, espacos mais rapidos)
        rng = np.random.default_rng(abs(hash(text)) % 2**32)
        wts = np.array([0.55 if c == ' ' else 1.0 + 0.35 * rng.random() for c in text])
        self.times = t0 + (t1 - t0) * np.concatenate([[0], np.cumsum(wts) / wts.sum()])[:-1]
        for tt, c in zip(self.times, text):
            if c != ' ': keys.append(tt)

    def n_at(self, t): return int(np.searchsorted(self.times, t, side='right'))

    def render(self, cv, t, dx=0, dy=0, op=1.0):
        if t < self.t0: return
        n = self.n_at(t)
        if n > 0: draw(cv, self.ly, op=op, dx=dx, dy=dy, upto=self.bounds[n])
        # cursor: fixo enquanto escreve, pisca um pouco no fim e desaparece
        on = (self.t0 <= t <= self.t1 + 0.05) or (t > self.t1 and t - self.t1 < 0.7 and int((t - self.t1) * 5) % 2 == 0)
        if on and n < len(self.bounds):
            hgt = self.y1 - self.y0; cwid = max(5, int(hgt * 0.09))
            x = int(self.bounds[n] + dx + 4); y0 = int(self.y0 + dy - hgt * 0.04); y1 = int(self.y1 + dy + hgt * 0.04)
            x0c, x1c = max(x, 0), min(x + cwid, W)
            if x1c > x0c:
                cv[max(y0, 0):min(y1, H), x0c:x1c] = cv[max(y0, 0):min(y1, H), x0c:x1c] * (1 - 0.95 * op) + self.color * 0.95 * op

KEYS = []  # instantes de cada tecla (para o som)

# ---------------- poster / CEO ----------------
S6 = W / 768; OY6 = (H - 1376 * S6) / 2
plate6 = cv2.resize(rd(f'{L}/6_plate.png')[..., :3], None, fx=S6, fy=S6, interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
P = {k: Layer(rd(f'{L}/6_{k}.png'), S6, 0, OY6) for k in ['prazer', 'ceo', 'de', 'seg', 'ele', 'logo', 'handle']}
o = OFF
T6 = {'prazer': ('Prazer, eu sou o', o + 0.0, o + 1.1, WHITE), 'ceo': ('CEO', o + 1.18, o + 1.4, WHITE),
      'de': ('DE', o + 1.44, o + 1.56, ORANGE), 'seg': ('SEGURANÇA', o + 1.58, o + 1.92, WHITE),
      'ele': ('ELETRÓNICA', o + 1.92, o + 2.6, ORANGE), 'handle': ('@kukulukua_mukambu', o + 4.75, o + 5.0, WHITE)}
ANTON = os.environ.get('ANTON', 'video-projeto/fonts/Anton-Regular.ttf')
FONTB = FONT.replace('ExtraBold', 'Bold')
def font_typed(txt, fpath, box, color, a, b):
    """texto novo (fonte real) encaixado na caixa do poster, escrito letra a letra"""
    f = ImageFont.truetype(fpath, 400); bb = f.getbbox(txt)
    im = Image.new('L', (bb[2] - bb[0], bb[3] - bb[1]), 0)
    ImageDraw.Draw(im).text((-bb[0], -bb[1]), txt, font=f, fill=255)
    x0, y0, x1, y1 = [v * S6 for v in box]; y0 += OY6; y1 += OY6
    tw, th = int(round(x1 - x0)), int(round(y1 - y0)); sx = tw / im.width
    al = np.array(im.resize((tw, th), Image.LANCZOS), np.float32)
    pad = 30
    alp = np.pad(al, pad); sh = cv2.GaussianBlur(alp, (0, 0), 10) * 0.55
    sh = np.roll(sh, (8, 6), (0, 1)); out_a = alp + sh * (1 - alp / 255)
    rgb = np.ones(alp.shape + (3,), np.float32) * color * (alp / 255)[..., None] / np.maximum(out_a / 255, 1e-3)[..., None]
    ly = Layer(np.dstack([rgb.clip(0, 255), out_a.clip(0, 255)]).astype(np.uint8), 1, x0 - pad, y0 - pad, crop=False)
    core = (al > 100).astype(np.uint8)
    meta = {'col': core.sum(0).tolist(), 'x': 0, 'y0': 0, 'y1': th}
    ty = Typed(ly, meta, txt, a, b, color, 1, x0, y0, KEYS)
    # fronteiras exactas das letras (a fonte e conhecida)
    ty.bounds = [x0 + (f.getlength(txt[:n]) - bb[0]) * sx if n < len(txt) else x1 + 2 for n in range(len(txt) + 1)]
    ty.bounds[0] = x0
    return ty
BOX6 = {'prazer': (34, 99, 394, 150), 'ceo': (29, 152, 740, 384), 'de': (33, 398, 149, 557),
        'seg': (174, 396, 738, 562), 'ele': (31, 558, 739, 766)}
FNT6 = {'prazer': FONTB, 'ceo': FONT, 'de': ANTON, 'seg': ANTON, 'ele': ANTON}
TY6 = {k: font_typed(txt, FNT6[k], BOX6[k], c, a, b) for k, (txt, a, b, c) in T6.items() if k != 'handle'}

# pessoa em alta qualidade, com cores corrigidas nas bordas
pr = rd(PERSON)
pr = cv2.resize(pr, None, fx=S6, fy=S6, interpolation=cv2.INTER_LANCZOS4)
ys, xs = np.nonzero(pr[..., 3] > 2)
PY0, PY1, PX0, PX1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
PM = 80
prc = cv2.copyMakeBorder(pr[PY0:PY1, PX0:PX1], PM, PM, PM, PM, cv2.BORDER_CONSTANT, value=0).astype(np.float32)
P_RGB_PRE = prc[..., :3] * (prc[..., 3:] / 255)  # pre-multiplicado
P_A = prc[..., 3] / 255
P_X, P_Y = PX0 - PM, PY0 + OY6 - PM
ph, pw = P_A.shape
def person_frame(theta_deg, scale, tx, ty):
    """projeccao em perspectiva (rotacao no eixo Y) do recorte"""
    th = np.radians(theta_deg); f = 1900.0
    cx, cy = pw / 2, ph * 0.55
    pts = []
    for (x, y) in [(0, 0), (pw, 0), (pw, ph), (0, ph)]:
        X, Y = (x - cx), (y - cy)
        Xr, Zr = X * np.cos(th), X * np.sin(th)
        k = f / (f + Zr)
        pts.append([cx + Xr * k * scale + tx, cy + Y * k * scale + ty])
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (pw, 0), (pw, ph), (0, ph)]), np.float32(pts))
    rgb = cv2.warpPerspective(P_RGB_PRE, M, (pw, ph), flags=cv2.INTER_LINEAR)
    a = cv2.warpPerspective(P_A, M, (pw, ph), flags=cv2.INTER_LINEAR)
    return rgb, a

def draw_person(cv, t, dx):
    # entrada: vem do fundo/direita, rodado 75 graus, e "aterra" no lugar
    e = ramp(t, 0.0, 0.85)
    k = back(e, 1.3)
    theta = -75 * (1 - k)
    scale = 0.45 + 0.55 * k
    tx = 420 * (1 - ease(e)); ty = 260 * (1 - ease(e))
    # vida: balanco 3D suave e respiracao
    if t > 0.6:
        w8 = clamp((t - 0.6) / 0.6)
        theta += w8 * 6.5 * np.sin(2 * np.pi * (t - 0.6) / 3.4)
        ty += w8 * 9 * np.sin(2 * np.pi * (t - 0.6) / 2.3)
        scale *= 1 + w8 * 0.012 * np.sin(2 * np.pi * (t - 0.6) / 2.3 + 1)
    # empurrao no "CEO"
    scale *= 1 + 0.035 * np.exp(-((t - (OFF + 1.2)) / 0.12) ** 2)
    if e <= 0: return
    if e < 1:  # motion blur na entrada
        acc_rgb = 0; acc_a = 0
        for j in range(4):
            tj = t - j * 0.012
            ej = ramp(tj, 0.0, 0.85); kj = back(ej, 1.3)
            r, a = person_frame(-75 * (1 - kj), 0.45 + 0.55 * kj, 420 * (1 - ease(ej)), 260 * (1 - ease(ej)))
            acc_rgb = acc_rgb + r; acc_a = acc_a + a
        rgb, a = acc_rgb / 4, acc_a / 4
    else:
        rgb, a = person_frame(theta, scale, tx, ty)
    op = ease(ramp(t, 0.0, 0.18))
    # sombra projectada na parede (profundidade)
    sh = cv2.GaussianBlur(a, (0, 0), 22) * 0.6 * op
    shx, shy = int(P_X + dx + 38), int(P_Y + 22)
    blend(cv, np.zeros((ph, pw, 3), np.float32), sh, shx, shy)
    # composicao com alfa pre-multiplicado
    x, y = int(round(P_X + dx)), int(round(P_Y))
    cx0, cy0, cx1, cy1 = max(x, 0), max(y, 0), min(x + pw, W), min(y + ph, H)
    aa = a[cy0 - y:cy1 - y, cx0 - x:cx1 - x, None] * op
    cv[cy0:cy1, cx0:cx1] = cv[cy0:cy1, cx0:cx1] * (1 - aa) + rgb[cy0 - y:cy1 - y, cx0 - x:cx1 - x] * op

NAME, ROLE = 'LOURENÇO SEBASTIÃO', 'CEO · KUKULU KUA MUKAMBU'
fn_name = ImageFont.truetype(FONT, 50); fn_role = ImageFont.truetype(FONT, 30)
NT = (OFF + 2.7, OFF + 4.1); RT = (OFF + 4.16, OFF + 4.95)
_rng = np.random.default_rng(7)
def _times(txt, a, b):
    w = np.array([0.55 if c == ' ' else 1 + 0.35 * _rng.random() for c in txt])
    return a + (b - a) * np.concatenate([[0], np.cumsum(w) / w.sum()])[:-1]
NTT, RTT = _times(NAME, *NT), _times(ROLE, *RT)
KEYS += [tt for tt, c in zip(NTT, NAME) if c != ' '] + [tt for tt, c in zip(RTT, ROLE) if c != ' ']

def name_card(cv, t):
    if t < NT[0] - 0.15: return
    n = int(np.searchsorted(NTT, t, side='right')); r = int(np.searchsorted(RTT, t, side='right'))
    grow = ease(ramp(t, NT[0] - 0.15, NT[0] + 0.1))
    x0 = 40
    im = Image.new('RGBA', (W, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    wname = d.textlength(NAME, font=fn_name) + 60
    d.rectangle([x0, 0, x0 + int(wname * grow), 78], fill=(255, 255, 255, 245))
    d.rectangle([x0, 0, x0 + 12, 78], fill=(248, 168, 0, 255))
    d.text((x0 + 34, 10), NAME[:n], font=fn_name, fill=(18, 18, 18))
    blink = t <= NT[1] + 0.05 or (t < RT[0] and int(t * 5) % 2 == 0)
    if blink and n <= len(NAME) and t < RT[0]:
        cx = x0 + 34 + d.textlength(NAME[:n], font=fn_name); d.rectangle([cx + 4, 12, cx + 10, 66], fill=(248, 168, 0))
    if t >= RT[0] - 0.12:
        wrole = d.textlength(ROLE, font=fn_role) + 46
        d.rectangle([x0, 84, x0 + int(wrole * ease(ramp(t, RT[0] - 0.12, RT[0] + 0.05))), 134], fill=(248, 168, 0, 255))
        d.text((x0 + 22, 91), ROLE[:r], font=fn_role, fill=(18, 18, 18))
        if t <= RT[1] + 0.05 or (t - RT[1] < 0.7 and int(t * 5) % 2 == 0):
            cx = x0 + 22 + d.textlength(ROLE[:r], font=fn_role); d.rectangle([cx + 3, 94, cx + 8, 126], fill=(18, 18, 18))
    ly = Layer(np.array(im), crop=False); ly.y = 1262
    draw(cv, ly)

HANDLE = Typed(P['handle'], META['6']['handle'], *T6['handle'][:3], WHITE, S6, 0, OY6, KEYS)

def poster(t, t0, t1):
    u = ease_io(ramp(t, 0, t1))
    cv = np.empty((H, W, 3), np.float32)
    # paralaxe: fundo devagar, textos a meio, pessoa a frente
    bx = -18 * u
    M = np.float32([[1.03, 0, -16 + bx], [0, 1.03, -29]])
    cv[:] = cv2.warpAffine(plate6, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    tdx = -34 * u
    for k in ['prazer', 'ceo', 'de', 'seg', 'ele']:
        ty = TY6[k]
        ty.render(cv, t, dx=tdx)
    draw_person(cv, t, dx=-62 * u)
    name_card(cv, t)
    if t >= OFF + 4.36:
        k = ramp(t, OFF + 4.36, OFF + 4.7)
        draw(cv, P['logo'], op=ramp(t, OFF + 4.36, OFF + 4.45), sc=0.4 + 0.6 * back(k, 2.2), dx=tdx)
    HANDLE.render(cv, t, dx=tdx)
    if t < 0.25: cv *= ease(t / 0.25)
    z = 1.0 + 0.05 * u
    sx = sy = 0
    tc = OFF + 1.2
    if tc <= t < tc + 0.22:
        a = (tc + 0.22 - t) / 0.22 * 12; sx = a * np.sin(t * 190); sy = a * np.cos(t * 150)
    Mz = np.float32([[z, 0, (1 - z) * 540 + sx], [0, z, (1 - z) * 700 + sy]])
    return cv2.warpAffine(cv, Mz, (W, H), borderMode=cv2.BORDER_REFLECT)

# ---------------- obras ----------------
TXT = {
  4: {'sub': 'Instalação concluída no Maie Maie', 'sub2': '(depois do Sequele).', 'l1': 'ESTAVA ABERTO.', 'l2': 'AGORA ESTÁ PROTEGIDO.'},
  5: {'sub': 'Instalação concluída no Zango, Viana.', 'l1': 'ESTAVA ABERTO.', 'l2': 'AGORA ESTÁ PROTEGIDO.'},
  3: {'l1': 'PROTEJA QUEM VOCÊ AMA.', 'l2': 'O SEU LAR TOTALMENTE SEGURO!', 'sub': 'Instalação de cerca elétrica concluída no Zango 0.'},
  2: {'l1': 'PROTEJA QUEM VOCÊ AMA.', 'l2': 'O SEU LAR TOTALMENTE SEGURO!', 'sub': 'Instalação de cerca elétrica concluída no Benfica.'},
}
TIM = {  # (inicio, fim) da escrita, sincronizado com a voz
  4: {'sub': (5.28, 6.74), 'sub2': (6.74, 7.02), 'l1': (6.74, 7.48), 'l2': (7.48, 8.9)},
  5: {'sub': (8.96, 10.36), 'l1': (11.5, 12.24), 'l2': (12.32, 13.0)},
  3: {'l1': (13.08, 15.12), 'l2': (15.22, 16.9), 'sub': (16.2, 16.9)},
  2: {'l1': (16.95, 17.5), 'l2': (17.25, 17.85), 'sub': (17.34, 20.0)},
}
PH = {}
for i in [4, 5, 3, 2]:
    pl = rd(f'{L}/{i}_plate.png'); h, w = pl.shape[:2]; s = W / w; oy = (H - h * s) / 2
    img = cv2.resize(pl[..., :3], None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    if h * s < H:  # imagem 2: preenche com fundo desfocado
        cover = cv2.resize(pl[..., :3], None, fx=H / h, fy=H / h).astype(np.float32)
        cx = (cover.shape[1] - W) // 2; base = cv2.GaussianBlur(cover[:, cx:cx + W], (0, 0), 30) * 0.45
        y0 = int(round(oy)); a = np.ones(img.shape[:2], np.float32)
        a[:30] = np.linspace(0, 1, 30)[:, None]; a[-30:] = np.linspace(1, 0, 30)[:, None]
        base[y0:y0 + img.shape[0]] = base[y0:y0 + img.shape[0]] * (1 - a[..., None]) + img * a[..., None]
    else:
        o_ = int(round(-oy)); base = img[o_:o_ + H]
    tys = {}
    for k, txt in TXT[i].items():
        ly = Layer(rd(f'{L}/{i}_{k}.png'), s, 0, oy)
        a, b = TIM[i][k]
        col = ORANGE if k == 'l1' else WHITE
        tys[k] = Typed(ly, META[str(i)][k], txt, OFF + a, OFF + b, col, s, 0, oy, KEYS)
    PH[i] = (base, tys)

PROT = {4: OFF + 8.2, 5: OFF + 12.32}
def photo(i, t, t0, t1):
    base, tys = PH[i]; cv = base.copy()
    for ty in tys.values(): ty.render(cv, t)
    u = (t - t0) / (t1 - t0 + 0.4)
    z = 1.0 + 0.075 * u
    if i in PROT: z += 0.03 * ease(ramp(t, PROT[i], PROT[i] + 0.18))
    M = np.float32([[z, 0, (1 - z) * 540 - 14 * u], [0, z, (1 - z) * 1150]])
    return cv2.warpAffine(cv, M, (W, H), borderMode=cv2.BORDER_REFLECT)

# ---------------- CTA ----------------
def text_rgba(txt, size, color, shadow=True):
    f = ImageFont.truetype(FONT, size); b = f.getbbox(txt)
    pad = 40
    im = Image.new('RGBA', (b[2] - b[0] + 2 * pad, b[3] - b[1] + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((pad - b[0], pad - b[1]), txt, font=f, fill=tuple(int(c) for c in color))
    arr = np.array(im)
    if shadow:
        a = arr[..., 3].astype(np.float32)
        sh = cv2.GaussianBlur(a, (0, 0), 12) * 0.7
        out_a = a + sh * (1 - a / 255)
        rgb = arr[..., :3].astype(np.float32) * (a / 255)[..., None] / np.maximum(out_a / 255, 1e-3)[..., None]
        arr = np.dstack([rgb.clip(0, 255), out_a.clip(0, 255)]).astype(np.uint8)
    return arr, pad

def typed_text(txt, size, color, cy, a, b):
    arr, pad = text_rgba(txt, size, color)
    x0 = (W - arr.shape[1]) // 2; y0 = cy - arr.shape[0] // 2
    ly = Layer(arr, 1, x0, y0, crop=False)
    core = (np.array(text_rgba(txt, size, color, shadow=False)[0])[..., 3] > 100).astype(np.uint8)
    meta = {'col': core.sum(0).tolist(), 'x': 0, 'y0': int(np.nonzero(core.sum(1))[0].min()), 'y1': int(np.nonzero(core.sum(1))[0].max() + 1)}
    return Typed(ly, meta, txt, a, b, color, 1, x0, y0, KEYS)

logo = rd(LOGO); lw = 860
logo = cv2.resize(logo, (lw, int(logo.shape[0] * lw / logo.shape[1])), interpolation=cv2.INTER_AREA)
LG = Layer(logo, 1, (W - lw) // 2, 430 - logo.shape[0] // 2)
CT = OFF + 20.0
Q1 = typed_text('QUER A SUA CASA', 84, WHITE, 820, OFF + 20.04, OFF + 20.84)
Q2 = typed_text('PROTEGIDA?', 132, ORANGE, 945, OFF + 20.84, OFF + 21.5)
FC = typed_text('FALE CONNOSCO', 58, WHITE, 1110, OFF + 21.68, OFF + 22.4)
HD = typed_text('@kukulukua_mukambu  ·  Zango 0, Luanda', 38, np.float32([225, 225, 225]), 1475, OFF + 25.5, OFF + 26.6)
NUM_G = [('921', OFF + 22.42, OFF + 22.86), (' 112', OFF + 22.86, OFF + 23.92), (' 654', OFF + 23.92, OFF + 25.2)]
NUM_T = []
for g, a, b in NUM_G:
    for j, c in enumerate(g):
        NUM_T.append((a + (b - a) * j / len(g), c))
        if c != ' ': KEYS.append(a + (b - a) * j / len(g))
fn_num = ImageFont.truetype(FONT, 92); fn_wa = ImageFont.truetype(FONT, 30)
ctabg = cv2.GaussianBlur(plate6[8:8 + H], (0, 0), 16) * 0.45
yy, xx = np.mgrid[0:H, 0:W]
ctabg = ctabg + np.exp(-(((xx - 540) / 700) ** 2 + ((yy - 900) / 800) ** 2))[..., None] * np.float32([70, 40, 0])

def pill(cv, t):
    k = back(ramp(t, OFF + 22.3, OFF + 22.6), 2.0)
    txt = '+244 ' + ''.join(c for tt, c in NUM_T if t >= tt)
    im = Image.new('RGBA', (W, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pw_ = 900; x0 = (W - pw_) // 2
    lt = 'WHATSAPP / LIGUE'; d.text(((W - d.textlength(lt, font=fn_wa)) / 2, 0), lt, font=fn_wa, fill=(37, 211, 102))
    d.rounded_rectangle([x0, 46, x0 + pw_, 206], radius=80, fill=(37, 211, 102, 255))
    full = '+244 921 112 654'; fw = d.textlength(full, font=fn_num); tx = (W - fw) / 2
    d.text((tx, 72), txt, font=fn_num, fill=(255, 255, 255))
    if t < OFF + 25.9 and (t < OFF + 25.2 or int(t * 5) % 2 == 0):
        cx = tx + d.textlength(txt, font=fn_num); d.rectangle([cx + 6, 82, cx + 13, 178], fill=(255, 255, 255))
    ly = Layer(np.array(im), crop=False); ly.y = 1180
    puls = 1.0 + (0.022 * np.sin((t - OFF - 25.3) * 6) if t > OFF + 25.3 else 0)
    draw(cv, ly, sc=max(k * puls, 0.01))

def cta(t, t0, t1):
    cv = ctabg.copy()
    k = ramp(t, CT - 0.05, CT + 0.35); draw(cv, LG, op=ease(k), sc=0.7 + 0.3 * back(k))
    for ty in (Q1, Q2, FC): ty.render(cv, t)
    if t >= OFF + 22.3: pill(cv, t)
    HD.render(cv, t)
    z = 1.0 + 0.03 * ramp(t, t0, DUR)
    M = np.float32([[z, 0, (1 - z) * 540], [0, z, (1 - z) * 960]])
    out = cv2.warpAffine(cv, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    if t > DUR - 0.5: out *= ease((DUR - t) / 0.5) * 0.85 + 0.15
    return out

# ---------------- montagem + transicoes zoom-blur ----------------
G = lambda k: OFF + 0.625 * k  # grelha da musica (96 BPM)
SCN = [(6, 0, G(8)), (4, G(8), G(14)), (5, G(14), G(21)), (3, G(21), G(27)), (2, G(27), CT), ('cta', CT, DUR)]
def scene(nm, t, t0, t1):
    if nm == 6: return poster(t, t0, t1)
    if nm == 'cta': return cta(t, t0, t1)
    return photo(nm, t, t0, t1)

def zoom_blur(img, amt, center=(540, 960), n=7):
    if amt < 0.004: return img
    acc = np.zeros_like(img)
    for j in range(n):
        z = 1 + amt * j / (n - 1)
        M = np.float32([[z, 0, (1 - z) * center[0]], [0, z, (1 - z) * center[1]]])
        acc += cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return acc / n

def chroma(img, px):
    if px < 0.5: return img
    out = img.copy()
    out[..., 0] = cv2.warpAffine(img[..., 0], np.float32([[1, 0, px], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    out[..., 2] = cv2.warpAffine(img[..., 2], np.float32([[1, 0, -px], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    return out

TRH = 0.2
def frame(t):
    for j, (nm, t0, t1) in enumerate(SCN):
        if t0 <= t < t1 or (j == len(SCN) - 1 and t >= t0): break
    if j + 1 < len(SCN) and t > t1 - TRH:  # saida: acelera para dentro
        p = ease_io((t - (t1 - TRH)) / TRH)
        img = scene(nm, t, t0, t1)
        z = 1 + 0.35 * p * p
        img = cv2.warpAffine(img, np.float32([[z, 0, (1 - z) * 540], [0, z, (1 - z) * 960]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        img = zoom_blur(img, 0.22 * p); img = chroma(img, 14 * p)
        return img + 90 * p * p
    if j > 0 and t < t0 + TRH:  # entrada: chega de perto e assenta
        p = 1 - ease((t - t0) / TRH)
        img = scene(nm, t, t0, t1)
        z = 1 + 0.25 * p
        img = cv2.warpAffine(img, np.float32([[z, 0, (1 - z) * 540], [0, z, (1 - z) * 960]]), (W, H), borderMode=cv2.BORDER_REFLECT)
        img = zoom_blur(img, 0.18 * p); img = chroma(img, 12 * p)
        return img + 90 * p * p
    return scene(nm, t, t0, t1)

if __name__ == '__main__':
    json.dump({'keys': sorted(KEYS), 'cuts': [s[1] for s in SCN[1:]], 'off': OFF, 'dur': DUR}, open('events.json', 'w'))
    if len(sys.argv) > 1:
        for ts in sys.argv[1:]:
            cv2.imwrite(f'test_{ts}.jpg', cv2.cvtColor(np.clip(frame(float(ts)), 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for f in range(n):
        p.stdin.write(np.clip(frame(f / FPS), 0, 255).astype(np.uint8).tobytes())
        if f % 120 == 0: print(f, '/', n, flush=True)
    p.stdin.close(); p.wait()
