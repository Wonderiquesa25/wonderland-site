# Fundos limpos com LaMa (remove textos / pessoa) + camadas de texto separadas por letra
# (para o efeito "teclado"). Saida: OUT/<i>_plate.png, OUT/<i>_<linha>.png (RGBA) e OUT/letters.json
import os, json, cv2, numpy as np, onnxruntime as ort
IMG = os.environ.get('IMG', 'images'); OUT = os.environ.get('OUT', 'layers2')
LAMA = os.environ.get('LAMA', 'lama_fp32.onnx'); PERSON = os.environ.get('PERSON', 'person_hq.png')
os.makedirs(OUT, exist_ok=True)
sess = ort.InferenceSession(LAMA, providers=['CPUExecutionProvider'])

def lama_win(img, mask, x0, y0):
    crop = img[y0:y0 + 512, x0:x0 + 512]; m = mask[y0:y0 + 512, x0:x0 + 512]
    if m.max() == 0: return img
    ph, pw = 512 - crop.shape[0], 512 - crop.shape[1]
    ci = np.pad(crop, ((0, ph), (0, pw), (0, 0)), mode='reflect'); cm = np.pad(m, ((0, ph), (0, pw)))
    o = sess.run(None, {'image': (ci.transpose(2, 0, 1)[None] / 255).astype(np.float32),
                        'mask': (cm[None, None] > 0).astype(np.float32)})[0][0].transpose(1, 2, 0)
    if o.max() <= 1.5: o = o * 255
    o = o[:crop.shape[0], :crop.shape[1]]
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 2) / 255
    # funde as bordas da janela (evita degraus entre janelas sobrepostas)
    hh, ww = a.shape; r = 48
    ry = np.ones(hh, np.float32); rx = np.ones(ww, np.float32)
    if y0 > 0: ry[:r] = np.linspace(0, 1, r)
    if y0 + 512 < img.shape[0]: ry[-r:] = np.linspace(1, 0, r)
    if x0 > 0: rx[:r] = np.linspace(0, 1, r)
    if x0 + 512 < img.shape[1]: rx[-r:] = np.linspace(1, 0, r)
    a = (a * ry[:, None] * rx[None, :])[..., None]
    out = img.copy(); out[y0:y0 + 512, x0:x0 + 512] = (crop * (1 - a) + o * a).clip(0, 255).astype(np.uint8)
    return out

def lama(img, mask):
    h, w = img.shape[:2]
    ys, xs = np.nonzero(mask)
    yw = list(range(max(0, ys.min() - 60), max(1, ys.max() - 300), 300)) or [0]
    yw = sorted(set(min(y, max(0, h - 512)) for y in yw + [max(0, min(ys.max() + 60, h) - 512)]))
    xw = sorted(set([0, max(0, w - 512)] + list(range(0, max(1, w - 512), 384))))
    for y0 in yw:
        for x0 in xw:
            img = lama_win(img, mask, x0, y0)
    return img

def proj(diffmask, x0, x1):
    col = diffmask[:, x0:x1].sum(0).astype(int)
    nz = np.nonzero(col > 0)[0]
    return {'x0': int(x0 + nz.min()), 'x1': int(x0 + nz.max() + 1), 'x': int(x0), 'col': col.tolist(),
            'y0': int(np.nonzero(diffmask[:, x0:x1].sum(1))[0].min()), 'y1': int(np.nonzero(diffmask[:, x0:x1].sum(1))[0].max() + 1)}

def letters(diffmask, x0, x1):
    """fronteiras das letras pela projeccao vertical dos pixels de texto"""
    col = diffmask[:, x0:x1].sum(0) > 0
    xs = []; inside = False
    for i, c in enumerate(col):
        if c and not inside: xs.append([x0 + i, None]); inside = True
        if not c and inside: xs[-1][1] = x0 + i; inside = False
    if inside: xs[-1][1] = x1
    # junta fragmentos muito estreitos ao vizinho
    out = []
    for a, b in xs:
        if out and (a - out[-1][1] < 3 or b - a < 4): out[-1][1] = b
        else: out.append([a, b])
    return out

META = {}
BANDS = {
  4: {'l1': (168, 226), 'l2': (226, 281), 'sub': (281, 320), 'sub2': (320, 356)},
  5: {'l1': (168, 226), 'l2': (226, 281), 'sub': (281, 332)},
  3: {'l1': (118, 212), 'l2': (212, 298), 'sub': (298, 352)},
  2: {'l1': (144, 242), 'l2': (242, 322), 'sub': (322, 382)},
}
for i, bands in BANDS.items():
    img = cv2.imread(f'{IMG}/{i}.jpg'); h, w = img.shape[:2]
    m = np.zeros((h, w), np.uint8)
    for b0, b1 in bands.values(): m[b0:b1, 20:w - 20] = 255
    plate = lama(img, m)
    cv2.imwrite(f'{OUT}/{i}_plate.png', plate)
    d = (np.abs(img.astype(np.int16) - plate.astype(np.int16)).max(2) > 28).astype(np.uint8)
    d = cv2.morphologyEx(d, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    META[i] = {}
    for k, (b0, b1) in bands.items():
        al = np.zeros((h, w), np.float32); al[b0:b1, 20:w - 20] = 1
        al = cv2.GaussianBlur(al, (0, 0), 2)
        cv2.imwrite(f'{OUT}/{i}_{k}.png', np.dstack([img, (al * 255).astype(np.uint8)]))
        sub = np.zeros_like(d); sub[b0:b1] = d[b0:b1]
        META[i][k] = proj(sub, 20, w - 20)

# --- poster ---
img = cv2.imread(f'{IMG}/6.jpg'); h, w = img.shape[:2]
pa = cv2.imread(PERSON, cv2.IMREAD_UNCHANGED)[..., 3]
PB = {'prazer': (25, 92, 400, 150), 'ceo': (25, 148, 748, 382), 'de': (25, 395, 172, 560),
      'seg': (172, 395, 745, 560), 'ele': (25, 560, 745, 765), 'logo': (565, 1055, 740, 1268),
      'handle': (515, 1278, 740, 1332)}
m = cv2.dilate((pa > 8).astype(np.uint8) * 255, np.ones((17, 17), np.uint8))
for x0, y0, x1, y1 in PB.values(): m[y0 - 6:y1 + 12, x0 - 6:x1 + 6] = 255
s = 512 / w
sm_img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
sm_m = (cv2.resize(m, (sm_img.shape[1], sm_img.shape[0])) > 0).astype(np.uint8) * 255
sp = lama(sm_img, sm_m)
up = cv2.resize(sp, (w, h), interpolation=cv2.INTER_CUBIC)
a = (cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3) / 255)[..., None]
plate = (img * (1 - a) + up * a).astype(np.uint8)
cv2.imwrite(f'{OUT}/6_plate.png', plate)
d = np.abs(img.astype(np.int16) - plate.astype(np.int16)).max(2)
pers = pa > 30
META[6] = {}
for k, (x0, y0, x1, y1) in PB.items():
    al = np.zeros((h, w), np.uint8)
    al[y0:y1, x0:x1] = (d[y0:y1, x0:x1] > 30).astype(np.uint8) * 255
    al = cv2.morphologyEx(al, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    al = cv2.dilate(al, np.ones((3, 3), np.uint8))
    al = cv2.GaussianBlur(al, (0, 0), 0.8)
    al[pers] = 0
    cv2.imwrite(f'{OUT}/6_{k}.png', np.dstack([img, al]))
    META[6][k] = proj((al > 60).astype(np.uint8), x0, x1)
json.dump(META, open(f'{OUT}/letters.json', 'w'))
print({i: {k: (v['x0'], v['x1'], v['y0'], v['y1']) for k, v in d_.items()} for i, d_ in META.items()})
