# Recorte de alta qualidade do CEO: BiRefNet-portrait (mascara) + pymatting (bordas finas)
# + estimativa da cor do primeiro plano (tira o halo escuro do fundo).
import os, sys, cv2, numpy as np, onnxruntime as ort
from pymatting import estimate_alpha_cf, estimate_foreground_ml
IMG, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
img = cv2.cvtColor(cv2.imread(IMG), cv2.COLOR_BGR2RGB); h, w = img.shape[:2]
sess = ort.InferenceSession(MODEL, providers=['CPUExecutionProvider'])
x = cv2.resize(img, (1024, 1024), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
x = (x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]
x = x.transpose(2, 0, 1)[None].astype(np.float32)
o = sess.run(None, {sess.get_inputs()[0].name: x})[0]
m = 1 / (1 + np.exp(-o[0, 0])) if o.min() < 0 else o[0, 0]
m = cv2.resize(m.astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC).clip(0, 1)
cv2.imwrite(OUT.replace('.png', '_raw.png'), (m * 255).astype(np.uint8))
# trimap: certeza dentro/fora, faixa desconhecida fina nas bordas
fg = cv2.erode((m > 0.9).astype(np.uint8), np.ones((7, 7), np.uint8))
bg = cv2.erode((m < 0.1).astype(np.uint8), np.ones((7, 7), np.uint8))
tri = np.full((h, w), 0.5); tri[fg > 0] = 1; tri[bg > 0] = 0
im = img.astype(np.float64) / 255
alpha = estimate_alpha_cf(im, tri)
alpha = np.clip(alpha, 0, 1)
fgc = estimate_foreground_ml(im, alpha)
rgba = np.dstack([(fgc * 255).clip(0, 255), alpha * 255]).astype(np.uint8)
cv2.imwrite(OUT, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
print('ok', alpha.mean())
