"""Low-key studio look for selfie talking-head: dark background, sculpted key light on the subject."""
import numpy as np, cv2

W, H = 1080, 1920
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# soft warm spotlight behind the head (studio backlight on a dark wall)
SPOT = np.exp(-(((xx - W * 0.52) / (W * 0.55)) ** 2 + ((yy - H * 0.30) / (H * 0.30)) ** 2))
# key light from upper-left, falling off to the right / bottom (Rembrandt-ish modelling)
FACE = np.exp(-(((xx - W * 0.45) / (W * 0.42)) ** 2 + ((yy - H * 0.24) / (H * 0.22)) ** 2))
KEY = np.clip((0.98 - 0.30 * (xx / W)) * (0.70 + 0.42 * FACE) - 0.18 * np.clip((yy - H * 0.55) / (H * 0.45), 0, 1), 0.40, 1.08)
RIMSIDE = np.clip((xx / W - 0.35) / 0.4, 0, 1) * 0.8 + np.clip(1 - yy / (H * 0.35), 0, 1) * 0.4
VIG = 1 - 0.55 * np.clip(np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H * 0.42) / (H * 0.70)) ** 2) - 0.35, 0, 1)

# tone curve for the subject: restore blacks, compress washed-out highlights (shirt), mild S
x = np.arange(256) / 255
c = np.interp(x, [0, 0.12, 0.30, 0.55, 0.80, 1.0], [0, 0.03, 0.17, 0.44, 0.74, 0.92])
SUBJ_LUT = np.clip(c * 255, 0, 255).astype(np.uint8)


def grade(fr, m):
    """fr: HxWx3 uint8 RGB at W x H, m: HxW float mask (1 = person)."""
    f = fr.astype(np.float32)
    subj = cv2.LUT(fr, SUBJ_LUT).astype(np.float32)
    # warmth on skin, slight cool in shadows
    subj[..., 0] *= 1.04; subj[..., 1] *= 1.0; subj[..., 2] *= 0.94
    lum = subj.mean(axis=2, keepdims=True)
    subj = lum + (subj - lum) * 1.08
    subj *= KEY[..., None]
    detail = f - cv2.GaussianBlur(f, (0, 0), 2.5)
    subj += detail * 0.45
    # background: crush to deep charcoal, keep a faint trace of the room, blurred
    bg = cv2.GaussianBlur(f, (0, 0), 6)
    bl = bg.mean(axis=2, keepdims=True) / 255
    bgc = np.empty_like(f)
    base = 10 + 28 * bl[..., 0]
    bgc[..., 0] = base * 1.00; bgc[..., 1] = base * 0.96; bgc[..., 2] = base * 1.06
    spot = SPOT[..., None] * np.array([46, 30, 8], np.float32)     # warm brand-orange glow behind head
    bgc = bgc + spot
    # rim light: bright edge where mask falls off (back light separating subject from dark bg)
    edge = np.clip(m - cv2.GaussianBlur(m, (0, 0), 7), 0, 1)
    edge = cv2.GaussianBlur(edge, (0, 0), 2) * 2.2 * RIMSIDE
    out = subj * m[..., None] + bgc * (1 - m[..., None])
    out += edge[..., None] * np.array([255, 200, 130], np.float32) * 0.28
    out *= VIG[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)
