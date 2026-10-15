# Estudio sem o boneco de papel (BiRefNet + LaMa) e camada da frente (microfone + mesa) por profundidade.
import sys, cv2, numpy as np, onnxruntime as ort
sys.path.insert(0, '/home/user/wonderland-site/video-projeto/narrado/scripts')
IMG, DEPTH, BIREF, LAMA = sys.argv[1:5]
img = cv2.imread(IMG); h, w = img.shape[:2]; dep = np.load(DEPTH)
s = ort.InferenceSession(BIREF, providers=['CPUExecutionProvider'])
x = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (1024, 1024)).astype(np.float32) / 255
x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
o = s.run(None, {s.get_inputs()[0].name: x})[0][0, 0]
m = cv2.resize(1 / (1 + np.exp(-o)), (w, h))
xx = np.arange(w)[None, :].repeat(h, 0)
yy = np.arange(h)[:, None].repeat(w, 1)
mug = (xx > 640) & (xx < 800) & (yy > 555) & (yy < 725)
fg = ((dep > 0.5) & (xx > 735) & ~mug).astype(np.float32)          # microfone, suporte, mesa
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
person = (((m > 0.3) | mug) & (fg < 0.5)).astype(np.uint8) * 255
person = cv2.dilate(person, np.ones((15, 15), np.uint8))
cv2.imwrite('person_mask.png', person)
# LaMa com janelas 512 numa versao reduzida
L = ort.InferenceSession(LAMA, providers=['CPUExecutionProvider'])
sc = 0.6; si = cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA); sm = cv2.resize(person, (si.shape[1], si.shape[0]))
out = si.copy(); H2, W2 = si.shape[:2]
for y0 in sorted({0, max(0, H2 - 512)}):
    for x0 in sorted({0, max(0, W2 - 512), max(0, (W2 - 512) // 2)}):
        crop = out[y0:y0 + 512, x0:x0 + 512]; mk = sm[y0:y0 + 512, x0:x0 + 512]
        if mk.max() == 0: continue
        ph, pw = 512 - crop.shape[0], 512 - crop.shape[1]
        ci = np.pad(crop, ((0, ph), (0, pw), (0, 0)), mode='reflect'); cm = np.pad(mk, ((0, ph), (0, pw)))
        r = L.run(None, {'image': (ci.transpose(2, 0, 1)[None] / 255).astype(np.float32), 'mask': (cm[None, None] > 0).astype(np.float32)})[0][0].transpose(1, 2, 0)
        if r.max() <= 1.5: r = r * 255
        r = r[:crop.shape[0], :crop.shape[1]]; a = (mk > 0)[..., None]
        out[y0:y0 + 512, x0:x0 + 512] = np.where(a, r, crop).clip(0, 255).astype(np.uint8)
up = cv2.resize(out, (w, h), interpolation=cv2.INTER_CUBIC)
a = (cv2.GaussianBlur(person.astype(np.float32), (0, 0), 3) / 255)[..., None]
plate = (img * (1 - a) + up * a).astype(np.uint8)
cv2.imwrite('studio_plate.png', plate)
# profundidade do estudio vazio: preenche a zona da pessoa
d8 = (dep * 255).astype(np.uint8); dp = cv2.inpaint(d8, person, 15, cv2.INPAINT_TELEA).astype(np.float32) / 255
np.save('studio_depth.npy', dp)
fga = cv2.GaussianBlur(fg, (0, 0), 1.2)
cv2.imwrite('studio_fg.png', np.dstack([img, (fga * 255).astype(np.uint8)]))
print('ok')
