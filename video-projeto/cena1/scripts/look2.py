"""v2 studio look: true black background (RVM matte), face-targeted key light + skin retouch, body falloff."""
import numpy as np, cv2, onnxruntime as ort

M = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad/models"
W, H = 576, 1024          # graded at source resolution, upscaled afterwards
RETOUCH = 0.45            # light: CodeFormer restores the face afterwards


class Matte:
    """Robust Video Matting: recurrent, so the cut-out is stable frame to frame (no flicker/halo)."""
    def __init__(self):
        o = ort.SessionOptions(); o.intra_op_num_threads = 2
        self.s = ort.InferenceSession(f"{M}/rvm_mobilenetv3_fp32.onnx", o, providers=["CPUExecutionProvider"])
        self.rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
        self.dr = np.array([0.45], np.float32)

    def __call__(self, rgb):
        src = (rgb.astype(np.float32) / 255).transpose(2, 0, 1)[None]
        fgr, pha, *self.rec = self.s.run(None, {"src": src, "r1i": self.rec[0], "r2i": self.rec[1], "r3i": self.rec[2],
                                                 "r4i": self.rec[3], "downsample_ratio": self.dr})
        return (fgr[0].transpose(1, 2, 0) * 255).clip(0, 255), pha[0, 0]


class Face:
    """YuNet face box, smoothed over time."""
    def __init__(self, w, h):
        self.d = cv2.FaceDetectorYN.create(f"{M}/yunet.onnx", "", (w, h), 0.6, 0.3, 5)
        self.box = None

    def __call__(self, bgr):
        _, f = self.d.detect(bgr)
        if f is not None and len(f):
            b = f[np.argmax(f[:, 2] * f[:, 3])][:4].astype(np.float32)
            self.box = b if self.box is None else 0.6 * self.box + 0.4 * b
        return self.box


yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
x = np.arange(256) / 255
TONE = np.clip(np.interp(x, [0, 0.10, 0.30, 0.55, 0.80, 1.0], [0, 0.02, 0.19, 0.47, 0.76, 0.93]) * 255, 0, 255).astype(np.uint8)


def ellipse(box, s, grow=1.0, dy=0.0):
    bx, by, bw, bh = box * s
    cx, cy = bx + bw / 2, by + bh / 2 + dy * bh
    return np.exp(-(((xx - cx) / (bw * 0.62 * grow)) ** 2 + ((yy - cy) / (bh * 0.70 * grow)) ** 2))


def grade(fgr, pha, box, s):
    """fgr HxWx3 float RGB (already W x H), pha HxW 0..1, box face box in source px, s = scale src->out."""
    f = fgr.astype(np.float32)
    # de-haze: the phone footage has a milky veil -> stretch the subject's own black/white points
    lum = f.mean(axis=2)
    sel = lum[pha > 0.6]
    lo, hi = (np.percentile(sel, [0.5, 99.5]) if sel.size > 500 else (20.0, 250.0))
    b = lo * 0.75
    v = f - b
    v = 6 * np.log1p(np.exp(np.clip(v / 6, -30, 30)))               # soft toe: shadows roll off, never clip to blocks
    f = v / max(hi - b, 1) * 245
    t = cv2.LUT(np.clip(f, 0, 255).astype(np.uint8), TONE).astype(np.float32)
    g = t.mean(axis=2, keepdims=True); t = g + (t - g) * 1.12          # a bit more colour overall
    t[..., 0] *= 1.04; t[..., 2] *= 0.93                               # warm
    t = np.clip(t, 0, 255)
    if box is not None:
        face = ellipse(box, s)                          # skin of the face
        halo = ellipse(box, s, grow=2.1, dy=0.25)       # wider pool of light around face / neck
        # skin retouch: frequency separation (smooth low freq, keep 35% fine texture) only on the face
        u8 = np.clip(t, 0, 255).astype(np.uint8)
        smooth = cv2.bilateralFilter(u8, 0, 22, 4).astype(np.float32)
        tex = t - cv2.GaussianBlur(t, (0, 0), 0.8)
        retouched = smooth + tex * 0.35
        k = (face * RETOUCH)[..., None]
        t = t * (1 - k) + retouched * k
        # key light on the face: lift shadows on skin, gentle glow; body falls off into darkness
        lift = 255 * ((np.clip(t, 0, 255) / 255) ** 0.82)
        g = lift.mean(axis=2, keepdims=True); lift = g + (lift - g) * 1.22   # richer skin tone
        lift[..., 0] *= 1.04; lift[..., 2] *= 0.94
        t = t * (1 - face[..., None] * 0.8) + lift * face[..., None] * 0.8
        light = 0.48 + 0.60 * np.maximum(halo, face)
    else:
        light = 0.85 * np.ones((H, W), np.float32)
    light *= np.clip(1.06 - 0.22 * (xx / W), 0.8, 1.06)            # key from camera-left
    light *= 1 - 0.35 * np.clip((yy - H * 0.55) / (H * 0.45), 0, 1)  # lower body falls into shadow
    t *= light[..., None]
    # micro-contrast for eyes / beard
    t += (t - cv2.GaussianBlur(t, (0, 0), 1.1)) * 0.35
    a = pha[..., None]
    out = t * a                                                   # pure black background
    # faint back-light so the head separates from black
    edge = np.clip(cv2.GaussianBlur(pha, (0, 0), 1.6) - cv2.GaussianBlur(pha, (0, 0), 5), 0, 1)
    out += (edge * np.clip(1 - yy / (H * 0.45), 0, 1))[..., None] * np.array([255, 190, 120], np.float32) * 0.35
    return np.clip(out, 0, 255).astype(np.uint8)
