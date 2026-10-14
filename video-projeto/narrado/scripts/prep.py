# Prepara camadas para o video narrado (Kukulu): fundo "fosco" + faixas de texto originais
# reveladas uma a uma; poster do CEO separado em fundo / textos / pessoa / logo.
import os, cv2, numpy as np
IMG = os.environ.get('IMG', 'images'); OUT = os.environ.get('OUT', 'layers')
os.makedirs(OUT, exist_ok=True)

# faixas de texto (y0,y1) em coords originais, por ordem de cima para baixo
BANDS = {
  4: {'l1': (168,226), 'l2': (226,281), 'sub': (281,356)},
  5: {'l1': (168,226), 'l2': (226,281), 'sub': (281,332)},
  3: {'l1': (118,212), 'l2': (212,298), 'sub': (298,352)},
  2: {'l1': (144,242), 'l2': (242,322), 'sub': (322,382)},
}

def band_alpha(h, w, y0, y1, f=7):
    a = np.zeros((h, w), np.float32); a[y0:y1] = 1
    return cv2.GaussianBlur(a, (0, 0), f)

for i, bands in BANDS.items():
    img = cv2.imread(f'{IMG}/{i}.jpg'); h, w = img.shape[:2]
    y0 = min(b[0] for b in bands.values()); y1 = max(b[1] for b in bands.values())
    m = np.zeros((h, w), np.uint8); m[y0-6:y1+6] = 255
    sm = cv2.resize(img, None, fx=.25, fy=.25); smm = cv2.resize(m, (sm.shape[1], sm.shape[0]))
    inp = cv2.inpaint(sm, smm, 9, cv2.INPAINT_TELEA)
    inp = cv2.GaussianBlur(cv2.resize(inp, (w, h), interpolation=cv2.INTER_CUBIC), (0, 0), 14)
    frost = (inp * 0.62).astype(np.float32)
    a = band_alpha(h, w, y0-4, y1+4, 10)[..., None]
    plate = (img * (1-a) + frost * a).astype(np.uint8)
    cv2.imwrite(f'{OUT}/{i}_plate.png', plate)
    for k, (b0, b1) in bands.items():
        al = np.zeros((h, w), np.float32); al[b0:b1] = 1
        if k == list(bands)[0]: al[b0-12:b0] = 1
        if k == list(bands)[-1]: al[b1:b1+12] = 1
        al = cv2.GaussianBlur(al, (0, 0), 3)
        cv2.imwrite(f'{OUT}/{i}_{k}.png', np.dstack([img, (al*255).astype(np.uint8)]))

# --- poster do CEO ---
img = cv2.imread(f'{IMG}/6.jpg'); h, w = img.shape[:2]
pm = cv2.imread(os.environ.get('PMASK', 'p6mask.png'), 0)
lum = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
bgest = cv2.medianBlur(img, 61)
diff = np.abs(img.astype(np.int16) - bgest.astype(np.int16)).max(2)
gimbal = np.zeros_like(pm); cv2.rectangle(gimbal, (122, 795), (300, 1010), 255, -1)
gimbal = gimbal & ((diff > 18).astype(np.uint8) * 255)
gimbal = cv2.morphologyEx(gimbal, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
person = np.maximum(pm, cv2.GaussianBlur(gimbal, (0, 0), 2))
cv2.imwrite(f'{OUT}/6_person.png', np.dstack([img, person]))
PB = {'prazer': (25,92,400,150), 'ceo': (25,148,748,382), 'de': (25,395,172,560),
      'seg': (172,395,745,560), 'ele': (25,560,745,765), 'logo': (565,1055,740,1268),
      'handle': (515,1278,740,1332)}
pers_hard = (pm > 60).astype(np.uint8) * 255
rm = np.maximum(cv2.dilate(pers_hard, np.ones((31, 31), np.uint8)), cv2.dilate(gimbal, np.ones((21, 21), np.uint8)))
for k, (x0, y0, x1, y1) in PB.items():
    m = np.zeros_like(pm)
    m[y0:y1, x0:x1] = (lum[y0:y1, x0:x1] > 85).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8))
    a = cv2.GaussianBlur(m, (0, 0), 1.0)
    a = np.where(pers_hard > 0, 0, a).astype(np.uint8)  # texto fica atras da pessoa
    cv2.imwrite(f'{OUT}/6_{k}.png', np.dstack([img, a]))
    rm[y0-6:y1+6, x0-6:x1+6] = 255
# fundo: gradiente escuro do proprio poster (pixels livres) + grao
free = rm == 0
yy, xx = np.mgrid[0:h, 0:w]
base = np.zeros_like(img, np.float32)
A = np.c_[np.ones(free.sum()), xx[free]/w, yy[free]/h, (xx[free]/w)**2, (yy[free]/h)**2, xx[free]*yy[free]/(w*h)]
X = np.c_[np.ones(h*w), xx.ravel()/w, yy.ravel()/h, (xx.ravel()/w)**2, (yy.ravel()/h)**2, xx.ravel()*yy.ravel()/(w*h)]
for c in range(3):
    coef, *_ = np.linalg.lstsq(A, img[..., c][free].astype(np.float32), rcond=None)
    base[..., c] = (X @ coef).reshape(h, w)
grain = np.random.default_rng(1).normal(0, 3.5, (h, w, 1)).astype(np.float32)
grain = cv2.GaussianBlur(grain, (0, 0), 1.2)[..., None] * 2
pl = np.clip(base + grain, 0, 255)
s = cv2.GaussianBlur(rm, (0, 0), 6).astype(np.float32)[..., None] / 255
plate = (img * (1 - s) + pl * s).astype(np.uint8)
cv2.imwrite(f'{OUT}/6_plate.png', plate)
print('ok')
