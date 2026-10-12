"""Qualidade de imagem da reunião: limpeza de ruído/blocos, crop sem as legendas antigas, upscale 1080x1920,
luz nos rostos (sombras levantadas + contraste local suave) e restauro do rosto principal (CodeFormer, estável no tempo).
Uso: python3 enhance.py <scratch>/wa [max_frames]  -> <wa>/src1080.mp4"""
import sys, os, subprocess, numpy as np, cv2
W = sys.argv[1]; MAXF = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "cena1", "scripts"))
from facefix import StableRestorer, M
OW, OH, FPS = 1080, 1920, 30

PRE = ("fps=30,hqdn3d=2:1.5:5:5,crop=366:650:49:0,"
       "scale=1080:1920:flags=lanczos")
# luz: levanta meios-tons/sombras (rostos escuros contra parede clara), segura os brancos
POST = ("curves=all='0/0.02 0.12/0.16 0.3/0.38 0.55/0.61 0.8/0.83 1/0.96',"
        "eq=contrast=1.05:saturation=1.06,"
        "colorbalance=rs=-0.01:bs=0.015:rh=0.02:gh=0.005:bh=-0.02,vignette=angle=PI/8,"
        "unsharp=5:5:0.45:5:5:0,noise=alls=2:allf=t")

det = cv2.FaceDetectorYN.create(f"{M}/yunet.onnx", "", (540, 960), 0.6, 0.3, 50)
rs = StableRestorer("codeformer", threads=4); rs.reset()
clahe = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8))

dec = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", os.environ.get("SS", "0"), "-i", f"{W}/in.mp4", "-an", "-vf", PRE, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                        "-vf", POST + ",format=yuv420p", "-c:v", "libx264", "-crf", "13", "-preset", "medium", os.environ.get("OUT", f"{W}/src1080.mp4")],
                       stdin=subprocess.PIPE)
FS = OW * OH * 3; i = 0; prev_small = None; lm_s = None
while i < MAXF:
    buf = dec.stdout.read(FS)
    if len(buf) < FS: break
    fr = np.frombuffer(buf, np.uint8).reshape(OH, OW, 3)
    # contraste local suave na luminância (dá volume aos rostos sem estourar a parede)
    lab = cv2.cvtColor(fr, cv2.COLOR_RGB2LAB)
    L = lab[..., 0]; lab[..., 0] = cv2.addWeighted(L, 0.55, clahe.apply(L), 0.45, 0)
    fr = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    small = cv2.resize(fr, (540, 960), interpolation=cv2.INTER_AREA)
    g = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY).astype(np.float32)
    if prev_small is not None and np.abs(g - prev_small).mean() > 28:      # corte de plano
        rs.reset(); lm_s = None
    prev_small = g
    _, faces = det.detect(cv2.cvtColor(small, cv2.COLOR_RGB2BGR))
    if faces is not None and len(faces):
        f = faces[np.argmax(faces[:, 2] * faces[:, 3])]
        if f[2] * 2 >= 70:                                                 # rosto com tamanho útil
            lm = f[4:14].reshape(5, 2).astype(np.float32) * 2
            lm_s = lm if lm_s is None or np.abs(lm - lm_s).mean() > 25 else 0.6 * lm + 0.4 * lm_s
            fr = rs(fr, lm_s, weight=0.75, fidelity=0.6, infer=(i % 2 == 0))
            # luz extra só na cabeça (elipse suave), para o rosto não ficar escuro contra a parede
            x, y, w, h = (f[:4] * 2).astype(float)
            m = np.zeros((OH // 4, OW // 4), np.float32)
            cv2.ellipse(m, (int((x + w / 2) / 4), int((y + h * 0.55) / 4)), (int(w * 0.85 / 4), int(h * 1.05 / 4)), 0, 0, 360, 1, -1)
            m = cv2.resize(cv2.GaussianBlur(m, (0, 0), w / 16), (OW, OH))[..., None]
            dark = (1 - fr.mean(2, keepdims=True) / 255.0) ** 1.6          # só pele/sombras, a parede clara fica igual (sem halo)
            fr = np.clip(fr * (1 + 0.28 * m * dark) + 8 * m * dark, 0, 255).astype(np.uint8)
        else:
            rs.reset(); lm_s = None
    else:
        rs.reset(); lm_s = None
    enc.stdin.write(fr.tobytes()); i += 1
    if i % 150 == 0: print(i, flush=True)
enc.stdin.close(); enc.wait(); dec.kill(); print("done", i)
