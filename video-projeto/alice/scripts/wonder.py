"""Wonderland look: sky replacement (column-connected sky mask that keeps wires), emerald/violet/gold grade, atmosphere."""
import numpy as np, cv2

W, H = 1080, 1920
P = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad/alice/plates"
PLATES = {k: cv2.cvtColor(cv2.imread(f"{P}/{k}.png"), cv2.COLOR_BGR2RGB).astype(np.float32) for k in ("sky1", "sky2", "portal")}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def sky_mask(rgb, prev=None, ref_prev=None, tol=26, ymax=1.0):
    """Sky key: sample the sky colour at the top of the frame, key pixels close to it (clouds included), keep only the
    keyed area connected to the top edge, and key softly so wires / razor coils / leaves stay on top of the new sky."""
    sw, sh = W // 4, H // 4
    small = cv2.resize(rgb, (sw, sh), interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_RGB2LAB).astype(np.float32)
    top = lab[: int(sh * 0.08)].reshape(-1, 3)
    top = top[top[:, 0] > 125]
    if len(top) < 50:
        return np.zeros((H, W), np.float32), ref_prev
    ref = np.median(top, axis=0)
    if ref_prev is not None: ref = 0.8 * ref_prev + 0.2 * ref
    def keyed(lb):
        d = np.sqrt(((lb[..., 0] - ref[0]) * 0.45) ** 2 + (lb[..., 1] - ref[1]) ** 2 + (lb[..., 2] - ref[2]) ** 2)
        return np.clip((tol - d) / 12, 0, 1)
    k = keyed(lab)
    g = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY).astype(np.float32)
    hf = cv2.GaussianBlur(np.abs(cv2.Laplacian(g, cv2.CV_32F, ksize=3)), (0, 0), 1.0)
    busy = cv2.GaussianBlur((hf > 10).astype(np.float32), (0, 0), 3)         # corrugated sheets, brick: not sky
    k = k * np.clip((ymax * sh - np.arange(sh)[:, None]) / (0.05 * sh), 0, 1)
    b = cv2.morphologyEx((k > 0.5).astype(np.uint8), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 17)))
    n, labs, stats, _ = cv2.connectedComponentsWithStats(b)
    keep = [i for i in set(np.unique(labs[0:2, :])) - {0} if stats[i, cv2.CC_STAT_AREA] > sw * sh * 0.01]
    region = np.isin(labs, keep).astype(np.float32)
    region = cv2.GaussianBlur(cv2.dilate(region, np.ones((3, 3), np.uint8)), (0, 0), 1.2)
    region = cv2.resize(region, (W, H), interpolation=cv2.INTER_LINEAR)
    kf = keyed(cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32))
    m = region * cv2.GaussianBlur(kf, (0, 0), 0.8)
    if prev is not None:
        m = 0.6 * m + 0.4 * prev
    return m, ref


def place_sky(name, t, shift=(0.0, 0.0), zoom=1.32):
    pl = PLATES[name]
    z = zoom + 0.012 * t
    shift = (float(np.clip(shift[0], -150, 150)), float(np.clip(shift[1], -260, 260)))
    cx, cy = W / 2 + shift[0], H * 0.42 + shift[1]
    M = np.float32([[z, 0, W / 2 - cx * z], [0, z, H * 0.42 - cy * z]])
    return cv2.warpAffine(pl, M, (W, H), borderMode=cv2.BORDER_REFLECT)


def grade(rgb, mood="day"):
    f = rgb.astype(np.float32) / 255
    lum = f.mean(axis=2, keepdims=True)
    # split toning: shadows -> deep blue/violet, highlights -> warm gold
    sh = np.clip(1 - lum * 2.2, 0, 1); hi = np.clip(lum * 2 - 1, 0, 1)
    f += sh * np.array([0.04, -0.01, 0.10]) * (1.6 if mood in ("night", "cold") else 1.0)
    f += hi * np.array([0.06, 0.03, -0.04])
    # greens -> emerald, saturation up
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    green = np.clip((g - np.maximum(r, b)) * 4, 0, 1)
    f[..., 2] += green * 0.06; f[..., 0] -= green * 0.03
    l2 = f.mean(axis=2, keepdims=True); f = l2 + (f - l2) * 1.22
    # filmic contrast
    f = np.clip(f, 0, 1); f = f * f * (3 - 2 * f) * 0.55 + f * 0.45
    if mood == "night":
        f = f * np.array([0.78, 0.80, 0.98])
    elif mood == "cold":
        l3 = f.mean(axis=2, keepdims=True); f = (l3 + (f - l3) * 0.7) * np.array([0.92, 0.97, 1.06])
    elif mood == "gold":
        f = f * np.array([1.05, 1.01, 0.93])
    return np.clip(f * 255, 0, 255)


def compose(rgb, sky, m, mood="day"):
    g = grade(rgb, mood)
    m3 = m[..., None]
    out = g * (1 - m3) + sky * m3
    # light wrap: sky colour bleeding softly over the edges of buildings for integration
    wrap = cv2.GaussianBlur(sky * m3, (0, 0), 10) * (1 - m3) * 0.18
    out = out + wrap
    return out


def grade_natural(rgb):
    """Brand cinematic look (as in Cena 2): gentle S-curve, lifted blacks, slight warm highlights / cool shadows, vignette-ready."""
    f = rgb.astype(np.float32) / 255
    lum = f.mean(axis=2, keepdims=True)
    sh = np.clip(1 - lum * 2.2, 0, 1); hi = np.clip(lum * 2 - 1, 0, 1)
    f += sh * np.array([-0.012, 0.0, 0.018]) + hi * np.array([0.03, 0.012, -0.025])
    l2 = f.mean(axis=2, keepdims=True); f = l2 + (f - l2) * 1.08
    f = np.clip(f, 0, 1); f = 0.03 + 0.92 * (f * f * (3 - 2 * f) * 0.45 + f * 0.55)
    return np.clip(f * 255, 0, 255)
