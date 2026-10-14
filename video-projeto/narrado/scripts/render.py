# Renderiza o video narrado: poster do CEO (elementos um a um) -> obras -> CTA.
# Tempos tirados da gravacao de voz (faster-whisper, palavra a palavra).
import os, sys, subprocess, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
L = os.environ.get('LAYERS', 'layers'); OUT = os.environ.get('OUT', 'video_mudo.mp4')
FONT = os.environ.get('FONT', 'video-projeto/fonts/Montserrat-ExtraBold.ttf')
LOGO = os.environ.get('LOGO', 'brand/kukulu-logo@2x.png')
W, H, FPS, DUR = 1080, 1920, 30, 40.0
ORANGE = (248, 168, 0)

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0), 1); c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def ramp(t, a, b): return min(max((t - a) / (b - a), 0), 1)

class Layer:
    def __init__(self, rgba, s=1.0, ox=0, oy=0):
        if s != 1.0:
            rgba = cv2.resize(rgba, None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4 if s > 1 else cv2.INTER_AREA)
        a = rgba[..., 3]
        ys, xs = np.nonzero(a > 2)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        self.rgb = rgba[y0:y1, x0:x1, :3].astype(np.float32)
        self.a = rgba[y0:y1, x0:x1, 3].astype(np.float32) / 255
        self.x, self.y = x0 + ox, y0 + oy

def draw(cv, ly, op=1.0, sc=1.0, dx=0, dy=0, wipe=None, feather=60):
    if op <= 0.003 or (wipe is not None and wipe <= 0): return
    rgb, a = ly.rgb, ly.a
    h, w = a.shape
    if wipe is not None and wipe < 1:
        xs = np.arange(w, dtype=np.float32)
        edge = wipe * (w + feather) - feather
        a = a * np.clip((edge + feather - xs) / feather, 0, 1)[None, :]
    x, y = ly.x + dx, ly.y + dy
    if sc != 1.0:
        M = np.float32([[sc, 0, (1 - sc) * w / 2], [0, sc, (1 - sc) * h / 2]])
        pad = int(abs(sc - 1) * max(w, h) / 2) + 2
        M[:, 2] += pad
        size = (w + 2 * pad, h + 2 * pad)
        rgb = cv2.warpAffine(rgb, M, size, flags=cv2.INTER_LINEAR)
        a = cv2.warpAffine(np.ascontiguousarray(a), M, size, flags=cv2.INTER_LINEAR)
        x -= pad; y -= pad; h, w = a.shape
    x, y = int(round(x)), int(round(y))
    cx0, cy0, cx1, cy1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if cx1 <= cx0 or cy1 <= cy0: return
    sa = a[cy0 - y:cy1 - y, cx0 - x:cx1 - x, None] * op
    cv[cy0:cy1, cx0:cx1] = cv[cy0:cy1, cx0:cx1] * (1 - sa) + rgb[cy0 - y:cy1 - y, cx0 - x:cx1 - x] * sa

def camera(img, z, cx, cy, sx=0, sy=0):
    M = np.float32([[z, 0, (1 - z) * cx + sx], [0, z, (1 - z) * cy + sy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def rd(p): return cv2.cvtColor(cv2.imread(p, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA if p.endswith('png') else cv2.COLOR_BGR2RGBA)

def text_img(txt, size, color, stroke=0, sc=(0, 0, 0)):
    f = ImageFont.truetype(FONT, size)
    b = f.getbbox(txt, stroke_width=stroke)
    im = Image.new('RGBA', (b[2] - b[0] + 20, b[3] - b[1] + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - b[0], 10 - b[1]), txt, font=f, fill=color, stroke_width=stroke, stroke_fill=sc)
    return np.array(im)

def shadowed(rgba, r=10, op=0.75):
    a = rgba[..., 3].astype(np.float32)
    pad = r * 3
    big = np.zeros((rgba.shape[0] + 2 * pad, rgba.shape[1] + 2 * pad, 4), np.float32)
    sh = cv2.GaussianBlur(np.pad(a, pad), (0, 0), r) * op
    big[..., 3] = sh
    fa = np.pad(a, pad) / 255
    big[..., :3] = np.pad(rgba[..., :3].astype(np.float32), ((pad, pad), (pad, pad), (0, 0))) * fa[..., None]
    out_a = fa * 255 + sh * (1 - fa)
    big[..., 3] = out_a
    return big.clip(0, 255).astype(np.uint8)

def centered(rgba, cy):
    ly = Layer(rgba); ly.x = (W - ly.a.shape[1]) // 2; ly.y = cy - ly.a.shape[0] // 2; return ly

# ---------- cena 1: poster ----------
S6 = W / 768; OY6 = (H - 1376 * S6) / 2
P = {k: Layer(rd(f'{L}/6_{k}.png'), S6, 0, OY6) for k in ['person', 'prazer', 'ceo', 'de', 'seg', 'ele', 'logo', 'handle']}
plate6 = cv2.resize(rd(f'{L}/6_plate.png')[..., :3], None, fx=S6, fy=S6, interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
o = int(round(-OY6)); plate6 = plate6[o:o + H]
PRAZER_X = (205 * S6 - P['prazer'].x) / P['prazer'].a.shape[1]  # fim de "Prazer,"

NAME, ROLE = 'LOURENÇO SEBASTIÃO', 'CEO · KUKULU KUA MUKAMBU'
fn_name = ImageFont.truetype(FONT, 50); fn_role = ImageFont.truetype(FONT, 30)
def name_card(cv, t):
    if t < 4.75: return
    n = int(len(NAME) * ramp(t, 4.88, 6.6)); r = int(len(ROLE) * ramp(t, 7.0, 8.2))
    grow = ease(ramp(t, 4.75, 5.0))
    x0, y0 = 40, 1250
    im = Image.new('RGBA', (W, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    wname = d.textlength(NAME, font=fn_name) + 56
    d.rectangle([x0, 0, x0 + int(wname * grow), 78], fill=(255, 255, 255, 245))
    d.rectangle([x0, 0, x0 + 12, 78], fill=ORANGE + (255,))
    d.text((x0 + 34, 12), NAME[:n], font=fn_name, fill=(18, 18, 18))
    if n and n < len(NAME) and int(t * 4) % 2 == 0:
        cx = x0 + 34 + d.textlength(NAME[:n], font=fn_name); d.rectangle([cx + 3, 14, cx + 8, 64], fill=ORANGE)
    if t >= 6.95:
        wrole = d.textlength(ROLE, font=fn_role) + 44
        d.rectangle([x0, 84, x0 + int(wrole * ease(ramp(t, 6.95, 7.15))), 134], fill=ORANGE + (255,))
        d.text((x0 + 22, 91), ROLE[:r], font=fn_role, fill=(18, 18, 18))
    ly = Layer(np.array(im)); ly.y += 0
    ly.y = y0 + (ly.y)
    draw(cv, ly)

def poster(t):
    cv = plate6.copy()
    if t >= 1.15:  # o CEO entra quando diz "Prazer"
        e = ease(ramp(t, 1.15, 1.65))
    else: e = 0
    # textos atras da pessoa
    p1 = 0.0
    if t >= 1.32: p1 = PRAZER_X * ease(ramp(t, 1.32, 2.0))
    if t >= 2.26: p1 = PRAZER_X + (1 - PRAZER_X) * ease(ramp(t, 2.26, 3.2))
    draw(cv, P['prazer'], wipe=p1, feather=40)
    if t >= 3.28:
        k = ramp(t, 3.28, 3.58); draw(cv, P['ceo'], op=ramp(t, 3.28, 3.36), sc=1.45 - 0.45 * back(k))
    if t >= 3.6:
        k = ease(ramp(t, 3.6, 3.85)); draw(cv, P['de'], op=k, dx=-120 * (1 - k))
    if t >= 3.72:
        k = ease(ramp(t, 3.72, 3.98)); draw(cv, P['seg'], op=k, dx=160 * (1 - k))
    if t >= 3.96:
        k = ramp(t, 3.96, 4.3); draw(cv, P['ele'], op=ramp(t, 3.96, 4.05), sc=1.25 - 0.25 * back(k))
    draw(cv, P['person'], op=e, dy=140 * (1 - e), sc=1.06 - 0.06 * e)
    name_card(cv, t)
    if t >= 7.7:
        k = ramp(t, 7.7, 8.05); draw(cv, P['logo'], op=ramp(t, 7.7, 7.8), sc=0.5 + 0.5 * back(k))
    if t >= 7.95:
        k = ease(ramp(t, 7.95, 8.25)); draw(cv, P['handle'], op=k, dy=30 * (1 - k))
    if t < 0.4: cv *= ease(t / 0.4)
    z = 1.0 + 0.055 * ease(t / 8.6)
    sx = sy = 0
    if 3.28 <= t < 3.5:  # tremor no "CEO"
        a = (3.5 - t) / 0.22 * 14; sx = a * np.sin(t * 190); sy = a * np.cos(t * 150)
    return camera(cv, z, 540, 560, sx, sy)

# ---------- cenas de obras ----------
BANDS = {4: ['l1', 'l2', 'sub'], 5: ['l1', 'l2', 'sub'], 3: ['l1', 'l2', 'sub'], 2: ['l1', 'l2', 'sub']}
PH = {}
for i in BANDS:
    pl = rd(f'{L}/{i}_plate.png'); h, w = pl.shape[:2]
    if w / h > 0.6:  # imagem 2 (896x1200): ajusta a largura e preenche com fundo desfocado
        s = W / w; oy = (H - h * s) / 2
        cover = cv2.resize(pl[..., :3], None, fx=H / h, fy=H / h)
        cx = (cover.shape[1] - W) // 2; bg = cover[:, cx:cx + W].astype(np.float32)
        bg = cv2.GaussianBlur(bg, (0, 0), 30) * 0.45
        img = cv2.resize(pl[..., :3], None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
        y0 = int(round(oy)); a = np.ones(img.shape[:2], np.float32)
        a[:24] = np.linspace(0, 1, 24)[:, None]; a[-24:] = np.linspace(1, 0, 24)[:, None]
        bg[y0:y0 + img.shape[0]] = bg[y0:y0 + img.shape[0]] * (1 - a[..., None]) + img * a[..., None]
        base, ox = bg, (s, 0, oy)
    else:
        s = W / w; oy = (H - h * s) / 2
        img = cv2.resize(pl[..., :3], None, fx=s, fy=s, interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
        o = int(round(-oy)); base = img[o:o + H]; ox = (s, 0, oy)
    PH[i] = (base, {k: Layer(rd(f'{L}/{i}_{k}.png'), *ox) for k in BANDS[i]})

# (layer, inicio, fim do wipe) — sincronizado com a voz
REVEAL = {
  4: [('sub', 9.95, 10.95), ('l1', 10.92, 11.6), ('l2', 12.24, 13.6)],
  5: [('sub', 15.1, 16.66), ('l1', 18.18, 19.3), ('l2', 19.48, 20.4)],
  3: [('l1', 20.78, 23.3), ('l2', 23.64, 25.9), ('sub', 25.0, 25.9)],
  2: [('l1', 26.28, 26.75), ('l2', 26.45, 26.95), ('sub', 26.76, 27.6)],
}
SCN = [(6, 0, 8.45), (4, 8.45, 14.52), (5, 14.52, 20.72), (3, 20.72, 26.24), (2, 26.24, 29.96), ('cta', 29.96, DUR)]
PROT = {4: 13.66, 5: 19.48}

def photo(i, t, t0, t1):
    base, ly = PH[i]; cv = base.copy()
    for k, a, b in REVEAL[i]:
        if t >= a: draw(cv, ly[k], wipe=ease(ramp(t, a, b)), feather=90)
    z = 1.0 + 0.07 * ((t - t0) / (t1 - t0 + 0.3))
    if i in PROT and t >= PROT[i]:  # punch-in no "protegida"
        z += 0.025 * ease(ramp(t, PROT[i], PROT[i] + 0.2))
    return camera(cv, z, 540, 1150)

# ---------- CTA ----------
logo = rd(LOGO); lw = 860; logo = cv2.resize(logo, (lw, int(logo.shape[0] * lw / logo.shape[1])), interpolation=cv2.INTER_AREA)
LG = centered(shadowed(logo, 16, 0.6), 430)
Q1 = centered(shadowed(text_img('QUER A SUA CASA', 84, (255, 255, 255))), 820)
Q2 = centered(shadowed(text_img('PROTEGIDA?', 132, ORANGE)), 945)
FC = centered(shadowed(text_img('FALE CONNOSCO', 58, (255, 255, 255))), 1115)
HD = centered(shadowed(text_img('@kukulukua_mukambu  ·  Zango 0, Luanda', 38, (225, 225, 225))), 1470)
fn_num = ImageFont.truetype(FONT, 92); fn_wa = ImageFont.truetype(FONT, 30)
ctabg = cv2.GaussianBlur(plate6, (0, 0), 18) * 0.5
yy, xx = np.mgrid[0:H, 0:W]
glow = np.exp(-(((xx - 540) / 700) ** 2 + ((yy - 900) / 800) ** 2))[..., None] * np.float32([60, 35, 0])
ctabg = (ctabg + glow).astype(np.float32)

def pill(t):
    k = back(ramp(t, 32.95, 33.3))
    im = Image.new('RGBA', (W, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    groups = [('+244 921', 33.08), (' 112', 34.02), (' 654', 35.62)]
    txt = ''.join(g for g, gt in groups if t >= gt)
    pw = 900; x0 = (W - pw) // 2
    d.rounded_rectangle([x0, 46, x0 + pw, 206], radius=80, fill=(37, 211, 102, 255))
    lt = 'WHATSAPP / LIGUE'; d.text(((W - d.textlength(lt, font=fn_wa)) / 2, 0), lt, font=fn_wa, fill=(37, 211, 102))
    tw = d.textlength(txt, font=fn_num)
    d.text(((W - tw) / 2, 72), txt, font=fn_num, fill=(255, 255, 255))
    ly = Layer(np.array(im)); ly.y += 1170
    puls = 1.0 + (0.025 * np.sin((t - 36) * 6) if t > 36.2 else 0)
    return ly, k * puls

def cta(t):
    cv = ctabg.copy()
    k = ramp(t, 29.96, 30.4); draw(cv, LG, op=ease(k), sc=0.7 + 0.3 * back(k))
    k = ease(ramp(t, 30.0, 30.35)); draw(cv, Q1, op=k, dy=50 * (1 - k))
    if t >= 31.0: k = ramp(t, 31.0, 31.3); draw(cv, Q2, op=ramp(t, 31.0, 31.08), sc=1.4 - 0.4 * back(k))
    if t >= 31.86: k = ease(ramp(t, 31.86, 32.2)); draw(cv, FC, op=k, dy=40 * (1 - k))
    if t >= 32.95:
        ly, s = pill(t); draw(cv, ly, sc=max(s, 0.01))
    if t >= 36.3: k = ease(ramp(t, 36.3, 36.8)); draw(cv, HD, op=k, dy=30 * (1 - k))
    return camera(cv, 1.0 + 0.03 * ramp(t, 29.96, DUR), 540, 960)

def scene(name, t, t0, t1):
    if name == 6: return poster(t)
    if name == 'cta': return cta(t)
    return photo(name, t, t0, t1)

TR = 0.32
def frame(t):
    for j, (nm, t0, t1) in enumerate(SCN):
        if t0 <= t < t1 or (j == len(SCN) - 1 and t >= t0):
            img = scene(nm, t, t0, t1)
            # transicao "push" vertical em volta do corte
            if j + 1 < len(SCN) and t > t1 - TR / 2:
                nm2, a2, b2 = SCN[j + 1]; e = (t - (t1 - TR / 2)) / TR
                e = 0.5 - 0.5 * np.cos(np.pi * min(max(e, 0), 1)); off = int(e * H)
                nxt = scene(nm2, a2, a2, b2)
                img = np.vstack([img[off:], nxt[:off]]) if off else img
            if j > 0 and t < t0 + TR / 2:
                pnm, p0, p1 = SCN[j - 1]
                e = (t - (t0 - TR / 2)) / TR; e = 0.5 - 0.5 * np.cos(np.pi * e); off = int(e * H)
                prv = scene(pnm, p1 - 0.001, p0, p1)
                img = np.vstack([prv[off:], img[:off]])
            return img

if __name__ == '__main__':
    if len(sys.argv) > 1:  # frames de teste
        for ts in sys.argv[1:]:
            cv2.imwrite(f'test_{ts}.jpg', cv2.cvtColor(np.clip(frame(float(ts)), 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        sys.exit()
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for f in range(n):
        p.stdin.write(np.clip(frame(f / FPS), 0, 255).astype(np.uint8).tobytes())
        if f % 150 == 0: print(f, '/', n, flush=True)
    p.stdin.close(); p.wait()
