# Prepara o video do narrador real: recorte por fotograma (RVM) + abertura da boca (YuNet + escuro entre os labios).
import os, sys, json, cv2, numpy as np, onnxruntime as ort
VID, RVM, YUNET, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)
cap = cv2.VideoCapture(VID); frames = []
while True:
    ok, f = cap.read()
    if not ok: break
    frames.append(f)
s = ort.InferenceSession(RVM, providers=['CPUExecutionProvider'])
rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
det = cv2.FaceDetectorYN.create(YUNET, '', (frames[0].shape[1], frames[0].shape[0]), 0.6)
info = []
for i, f in enumerate(frames):
    src = (cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float32) / 255).transpose(2, 0, 1)[None]
    fgr, pha, *rec = s.run(None, {'src': src, 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3],
                                  'downsample_ratio': np.array([0.4], np.float32)})
    a = (pha[0, 0] * 255).clip(0, 255).astype(np.uint8)
    cv2.imwrite(f'{OUT}/f{i:04d}.png', np.dstack([f, a]))
    _, faces = det.detect(f)
    op = None; box = None
    if faces is not None:
        fc = max(faces, key=lambda r: r[2] * r[3])
        box = [float(v) for v in fc[:4]]
        rmx, rmy, lmx, lmy = fc[10], fc[11], fc[12], fc[13]  # cantos da boca
        cx, cy = (rmx + lmx) / 2, (rmy + lmy) / 2; w = max(abs(lmx - rmx), 10)
        x0, x1 = int(cx - 0.35 * w), int(cx + 0.35 * w); y0, y1 = int(cy - 0.25 * w), int(cy + 0.45 * w)
        g = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32)
        ref = np.percentile(g, 70)
        op = float((g < ref * 0.55).mean())
    info.append({'open': op, 'box': box})
json.dump({'n': len(frames), 'fps': cap.get(cv2.CAP_PROP_FPS) or 24, 'frames': info}, open(f'{OUT}/info.json', 'w'))
print(len(frames), 'frames')
