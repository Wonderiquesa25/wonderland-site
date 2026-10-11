"""Professional cyber/HUD motion-graphics layer (clean vector, eased, brand orange #F8A800 / white / black).
All times are on the ORIGINAL (pre-cut) timeline; the compositor maps output time -> original time."""
import math, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
OR = (248, 168, 0); WH = (255, 255, 255)
FONT = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad/alice/fonts"
F_TAG = ImageFont.truetype(f"{FONT}/Oswald-Bold.ttf", 46)
F_SMALL = ImageFont.truetype(f"{FONT}/Montserrat-Bold.ttf", 26)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def ease_out(p): p = min(max(p, 0), 1); return 1 - (1 - p) ** 3
def ease_back(p):
    p = min(max(p, 0), 1); c = 1.6; q = p - 1; return 1 + (c + 1) * q ** 3 + c * q ** 2


# target locks: (t0, t1, (x0,y0,x1,y1), label, label side)
TARGETS = [(7.25, 8.06, (40, 760, 720, 1080), "CERCA ELÉCTRICA", "top"),
           (8.85, 10.12, (40, 830, 1040, 975), "CERCA ELÉCTRICA", "top"),
           (47.40, 50.25, (190, 370, 520, 670), "INSTALAÇÃO", "right"),
           (80.80, 84.85, (220, 240, 580, 610), "EQUIPA KUKULU", "right")]
SHOW_TAGS = [(74.45, "OBRA 01"), (75.55, "OBRA 02"), (76.62, "OBRA 03"), (77.60, "OBRA 04")]
GRID_T = 78.45
GIANTS = [2.67, 10.55, 17.45, 22.43, 31.90, 44.45, 52.55, 62.05, 71.09, 73.63, 78.45, 83.43, 88.61]
GIANT_END = [4.10, 12.35, 18.70, 24.05, 33.40, 46.10, 54.00, 63.60, 72.30, 74.70, 80.20, 85.60, 89.78]
GIANT_SIZE = [230, 175, 240, 170, 165, 190, 145, 225, 230, 135, 185, 180, 200]
TWO_LINE = {22.43, 31.90, 78.45, 83.43}
CYBER_IMPACT = [17.45, 71.09, 73.63]
GLITCH = [(59.09, 0.24), (73.70, 0.10)]


def _bracket(d, x0, y0, x1, y1, L, col, w):
    for (cx, cy, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(cx, cy), (cx + sx * L, cy)], fill=col, width=w); d.line([(cx, cy), (cx, cy + sy * L)], fill=col, width=w)


def _tag(d, x, y, text, p_type, accent=OR):
    n = int(len(text) * min(1, p_type)); s = text[:n]
    tw = d.textlength(text, font=F_TAG); bw, bh = int(tw + 46), 70
    d.rectangle([x, y, x + bw, y + bh], fill=(0, 0, 0, 175))
    d.rectangle([x, y, x + 8, y + bh], fill=accent + (255,))
    d.text((x + 24, y + 6), s, font=F_TAG, fill=WH + (255,))
    if n < len(text) and int(p_type * 40) % 2 == 0:
        cx = x + 24 + d.textlength(s, font=F_TAG) + 4; d.rectangle([cx, y + 16, cx + 14, y + bh - 14], fill=accent + (255,))
    return bw, bh


def layer(t):
    """RGBA overlay (PIL) for time t, or None."""
    im = None; d = None
    def canvas():
        nonlocal im, d
        if im is None: im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        return d
    for a, b, (x0, y0, x1, y1), label, side in TARGETS:
        if a <= t < b:
            d = canvas(); p = (t - a); out = max(0.0, min(1.0, (b - t) / 0.25))
            k = ease_back(p / 0.35); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            s = 1.6 - 0.6 * k
            bx0, by0, bx1, by1 = cx + (x0 - cx) * s, cy + (y0 - cy) * s, cx + (x1 - cx) * s, cy + (y1 - cy) * s
            al = int(255 * min(1, p / 0.12) * out)
            # soft dark tint outside the target (focus) for the first second
            _bracket(d, bx0, by0, bx1, by1, 46, OR + (al,), 7)
            d.line([(cx - 16, cy), (cx + 16, cy)], fill=WH + (int(al * 0.8),), width=3); d.line([(cx, cy - 16), (cx, cy + 16)], fill=WH + (int(al * 0.8),), width=3)
            if 0.18 < p < 0.75:                                       # scan line inside the target
                sy = by0 + (by1 - by0) * ease_out((p - 0.18) / 0.55)
                d.line([(bx0 + 10, sy), (bx1 - 10, sy)], fill=OR + (int(200 * out),), width=4)
            if p > 0.3:                                               # leader line + typed tag
                pt = (p - 0.3) / 0.45
                if side == "top": lx, ly = x0 + 10, max(40, y0 - 120)
                else: lx, ly = min(x1 + 40, W - 470), max(40, y0 - 40)
                ex, ey = (x1, y0) if side == "right" else (x0 + 40, y0)
                d.line([(ex, ey), (lx + 4, ly + 70)], fill=WH + (int(220 * out),), width=3)
                _tag(d, lx, ly, label, pt)
    for a, label in SHOW_TAGS:
        if a <= t < min(a + 1.05, GRID_T):
            d = canvas(); p = t - a
            _tag(d, 60, 120, label, (p - 0.15) / 0.3)
            d.text((64, 200), "KUKULU KUA MUKAMBU", font=F_SMALL, fill=OR + (230,))
    if GRID_T <= t < 80.0:                                            # grid: lock each panel + "CONCLUÍDO"
        d = canvas(); g = 14; pw, ph = (W - 3 * g) // 2, (H - 3 * g) // 2
        for j in range(4):
            st = GRID_T + 0.35 + j * 0.12; p = t - st
            if p < 0: continue
            x0 = g + (j % 2) * (pw + g); y0 = g + (j // 2) * (ph + g)
            _bracket(d, x0 + 18, y0 + 18, x0 + pw - 18, y0 + ph - 18, 50, OR + (255,), 7)
            _tag(d, x0 + 34, y0 + ph - 110, "✓ CONCLUÍDO" if False else "CONCLUÍDO", p / 0.3)
    for g0, g1, size in zip(GIANTS, GIANT_END, GIANT_SIZE):           # clean orange bar under giant words
        if g0 + 0.12 <= t < g1:
            d = canvas(); p = ease_out((t - g0 - 0.12) / 0.3); out = max(0.0, min(1.0, (g1 - t) / 0.2))
            y = 760 + (size * 1.08 if g0 in TWO_LINE else size * 0.64) + 6
            hw = 280 * p
            d.rounded_rectangle([540 - hw, y, 540 + hw, y + 12], radius=6, fill=OR + (int(255 * out),))
    return im


def shockwave(img, t):
    for g in GIANTS:
        dt = t - g
        if 0 <= dt < 0.45:
            r = 150 + 900 * ease_out(dt / 0.45); f = (1 - dt / 0.45) ** 1.5
            ring = np.exp(-((np.sqrt((xx - W / 2) ** 2 + ((yy - 780) * 0.85) ** 2) - r) / 10) ** 2)
            img = img + ring[..., None] * np.array(OR, np.float32) * 0.9 * f
        if 0 <= dt < 0.1:                                              # brief RGB split on the hit
            sh = int(12 * (1 - dt / 0.1)) + 2
            img = img.copy(); img[..., 0] = np.roll(img[..., 0], sh, axis=1); img[..., 2] = np.roll(img[..., 2], -sh, axis=1)
    return img


SCAN = (np.sin(yy * math.pi / 3.0) * 0.5 + 0.5)[..., None]


def cyber_impact(img, t):
    for s in CYBER_IMPACT:
        dt = t - s
        if 0 <= dt < 3 / 30:
            f = 1 - dt / (3 / 30)
            out = img.copy(); sh = int(26 * f) + 4
            out[..., 0] = np.roll(img[..., 0], sh, axis=1); out[..., 2] = np.roll(img[..., 2], -sh, axis=1)
            out = out * (1 + 0.35 * f) * (0.82 + 0.18 * SCAN)
            return out
    return img


def glitch(img, t):
    for s, d in GLITCH:
        if s <= t < s + d:
            r = np.random.default_rng(int(t * 30)); out = img.copy(); sh = int(8 + 16 * r.random())
            out[..., 0] = np.roll(img[..., 0], sh, axis=1); out[..., 2] = np.roll(img[..., 2], -sh, axis=1)
            for _ in range(6):
                y = int(r.random() * H); h = int(12 + 70 * r.random()); dx = int((r.random() - 0.5) * 140)
                out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
            return out * (0.85 + 0.15 * SCAN)
    return img


def slice_wipe(a, b, p, n=10):
    """frame cut into horizontal slices that slide out (alternating) while the next shot slides in, with a light edge."""
    e = p * p * (3 - 2 * p); out = np.empty_like(a); hs = H // n
    for i in range(n):
        y0, y1 = i * hs, (H if i == n - 1 else (i + 1) * hs)
        d = 1 if i % 2 else -1; delay = (i % 3) * 0.08
        q = min(1, max(0, (e - delay) / (1 - 0.16)))
        off = int(q * W) * d
        band = np.roll(a[y0:y1], off, axis=1); bb = np.roll(b[y0:y1], off - d * W, axis=1)
        m = (np.arange(W)[None, :] < off) if d > 0 else (np.arange(W)[None, :] >= W + off)
        out[y0:y1] = np.where(m[..., None], bb, band)
        edge = (W + off) if d < 0 else off
        if 0 < q < 1:
            ex = int(np.clip(edge, 0, W - 1)); out[y0:y1, max(0, ex - 3):ex + 3] = np.array(OR, np.float32)
    return out
