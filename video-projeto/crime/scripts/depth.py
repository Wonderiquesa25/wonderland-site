# Mapas de profundidade (Depth-Anything-v2-small ONNX) para as cenas origami: dN.npy normalizado 0 (longe) .. 1 (perto)
import sys, cv2, numpy as np, onnxruntime as ort
MODEL, *IMGS = sys.argv[1:]
s = ort.InferenceSession(MODEL, providers=['CPUExecutionProvider'])
for p in IMGS:
    im = cv2.imread(p); h, w = im.shape[:2]
    x = cv2.resize(cv2.cvtColor(im, cv2.COLOR_BGR2RGB), (686, 392)).astype(np.float32) / 255
    x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
    d = s.run(None, {'pixel_values': x})[0][0]
    d = cv2.resize(d, (w, h), interpolation=cv2.INTER_CUBIC)
    d = (d - np.percentile(d, 1)) / (np.percentile(d, 99) - np.percentile(d, 1) + 1e-6)
    d = cv2.GaussianBlur(np.clip(d, 0, 1), (0, 0), 3).astype(np.float32)
    np.save(p.replace('/c', '/d').rsplit('.', 1)[0] + '.npy', d); print(p, flush=True)
