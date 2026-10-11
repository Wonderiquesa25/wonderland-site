"""Original pop/comic graphic layer: hand-drawn (wobbly, progressively drawn) annotations, check marks, scribble
underlines, speed lines, impact frames, glitch, brush-stroke wipe. Brand colours: orange #F8A800, white, black."""
import math, numpy as np, cv2
W, H = 1080, 1920
OR = (248, 168, 0); WH = (255, 255, 255); BK = (0, 0, 0)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)


def wobble(pts, seed, amp=5):
    r = np.random.default_rng(seed)
    pts = np.asarray(pts, np.float32)
    return pts + r.normal(0, amp, pts.shape).astype(np.float32) * np.linspace(0.4, 1, len(pts))[:, None]


def ellipse_pts(c, rx, ry, turns=1.12, n=90, rot=-0.3):
    a = np.linspace(rot, rot + 2 * math.pi * turns, n)
    rxx = rx * (1 + 0.06 * np.sin(a * 3)); ryy = ry * (1 + 0.05 * np.cos(a * 2))
    return np.stack([c[0] + rxx * np.cos(a), c[1] + ryy * np.sin(a)], 1)


def arrow_pts(p0, p1, bend=0.18, n=40):
    p0, p1 = np.array(p0, np.float32), np.array(p1, np.float32)
    d = p1 - p0; nrm = np.array([-d[1], d[0]]) * bend
    t = np.linspace(0, 1, n)[:, None]
    return p0 + d * t + nrm * (4 * t * (1 - t))


def squiggle_pts(x0, x1, y, n=60, amp=10, waves=3.5):
    x = np.linspace(x0, x1, n); return np.stack([x, y + amp * np.sin(np.linspace(0, waves * 2 * math.pi, n))], 1)


def draw_stroke(lay, pts, p, col, w, shadow=True):
    """progressively draw a polyline (p = 0..1 of its length), marker-like, with a black under-stroke for contrast."""
    if p <= 0: return
    k = max(2, int(len(pts) * min(1, p)))
    seg = np.int32(pts[:k])
    if shadow: cv2.polylines(lay, [seg + 3], False, BK, w + 6, cv2.LINE_AA)
    cv2.polylines(lay, [seg], False, col, w, cv2.LINE_AA)


def arrow_head(lay, pts, col, w):
    p1, p0 = pts[-1], pts[-6]
    d = (p1 - p0); d /= (np.linalg.norm(d) + 1e-6)
    for s in (1, -1):
        r = np.array([[math.cos(2.6 * s), -math.sin(2.6 * s)], [math.sin(2.6 * s), math.cos(2.6 * s)]])
        q = p1 + (r @ d) * 48
        cv2.line(lay, tuple(np.int32(p1 + 3)), tuple(np.int32(q + 3)), BK, w + 6, cv2.LINE_AA)
        cv2.line(lay, tuple(np.int32(p1)), tuple(np.int32(q)), col, w, cv2.LINE_AA)


def check_pts(c, s=1.0):
    x, y = c; return np.array([[x - 60 * s, y], [x - 20 * s, y + 45 * s], [x + 70 * s, y - 60 * s]], np.float32)


def densify(pts, n=40):
    pts = np.asarray(pts, np.float32); out = []
    for a, b in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, n // (len(pts) - 1), endpoint=False): out.append(a + (b - a) * t)
    out.append(pts[-1]); return np.array(out)


# annotation events: (t_start, t_end, kind, params)
ANN = [
    (7.21, 8.05, "circle", dict(c=(380, 880), rx=330, ry=175, col=OR)),
    (8.83, 10.10, "under", dict(x0=70, x1=1010, y=930, col=OR)),
    (8.95, 10.10, "arrow", dict(p0=(930, 560), p1=(800, 880), col=WH)),
    (47.40, 50.25, "arrow", dict(p0=(760, 230), p1=(360, 460), col=OR)),
    (47.70, 50.25, "circle", dict(c=(330, 520), rx=170, ry=130, col=WH)),
    (80.79, 84.85, "circle", dict(c=(400, 400), rx=190, ry=170, col=OR)),
    (81.20, 84.85, "arrow", dict(p0=(860, 900), p1=(520, 1120), col=WH)),
]
GRID_CHECKS = [(78.95 + 0.14 * j, ((W // 4) + (j % 2) * (W // 2), (H // 4) + (j // 2) * (H // 2))) for j in range(4)]
UNDERLINES = [(2.82, 4.10, 230), (10.70, 12.35, 175), (17.6, 18.70, 240), (22.6, 24.05, 170), (32.05, 33.40, 165), (44.6, 46.10, 190),
              (52.7, 54.00, 145), (62.2, 63.60, 225), (71.25, 72.30, 230), (78.6, 80.20, 185), (83.6, 85.60, 180), (88.75, 89.70, 200)]
TWO_LINE = {22.6, 32.05, 78.6, 83.6}
IMPACT = [17.45, 71.09, 73.63]
GLITCH = [(17.50, 0.10), (59.09, 0.22), (73.70, 0.12)]
SPEED = [2.67, 10.55, 17.45, 22.43, 31.90, 44.45, 52.55, 62.05, 71.09, 73.63, 78.45, 83.43, 88.61]
STARS = [(74.45, 1), (75.55, 2), (76.62, 3), (77.60, 4)]


def star_pts(c, r):
    a = np.linspace(-math.pi / 2, 1.5 * math.pi, 11)
    rr = np.where(np.arange(11) % 2 == 0, r, r * 0.45)
    return np.stack([c[0] + rr * np.cos(a), c[1] + rr * np.sin(a)], 1)


def overlay(t):
    """returns (rgb layer, alpha) drawn over the frame."""
    lay = np.zeros((H, W, 3), np.uint8); hit = False
    for a, b, kind, p in ANN:
        if a <= t < b:
            hit = True; pr = min(1, (t - a) / 0.38); seed = int(a * 100)
            if kind == "circle": draw_stroke(lay, wobble(ellipse_pts(p["c"], p["rx"], p["ry"]), seed, 3), pr, p["col"], 11)
            if kind == "under": draw_stroke(lay, wobble(squiggle_pts(p["x0"], p["x1"], p["y"], amp=9), seed, 2), pr, p["col"], 12)
            if kind == "arrow":
                pts = wobble(arrow_pts(p["p0"], p["p1"]), seed, 2); draw_stroke(lay, pts, pr, p["col"], 11)
                if pr >= 1: arrow_head(lay, pts, p["col"], 11)
    for st, c in GRID_CHECKS:
        if st <= t < 79.90:
            hit = True; draw_stroke(lay, densify(check_pts(c, 1.4), 30), min(1, (t - st) / 0.22), OR, 22)
    for st, j in STARS:
        if st <= t < st + 0.55:
            hit = True; f = (t - st) / 0.55; r = 40 + 30 * math.sin(math.pi * f)
            for cx, cy in [(110, 160), (W - 120, H - 520)][: 1 + j % 2]:
                pts = star_pts((cx, cy), r); cv2.fillPoly(lay, [np.int32(pts + 4)], BK, cv2.LINE_AA); cv2.fillPoly(lay, [np.int32(pts)], OR, cv2.LINE_AA)
    for a, b, size in UNDERLINES:
        if a <= t < b:
            hit = True; pr = min(1, (t - a) / 0.25)
            y = 760 + (size * 1.05 if a in TWO_LINE else size * 0.62) + 10
            draw_stroke(lay, wobble(squiggle_pts(250, 830, y, amp=7, waves=2.5), int(a * 10), 2), pr, OR, 13)
    alpha = (lay.max(axis=2) > 0).astype(np.float32) if hit else None
    if hit: alpha = cv2.GaussianBlur(alpha, (0, 0), 0.8)
    return lay.astype(np.float32), alpha


def speed_lines(img, t):
    for s in SPEED:
        dt = t - s
        if 0 <= dt < 0.32:
            r = np.random.default_rng(int(s * 100) + int(dt * 30))
            lay = np.zeros((H, W), np.float32)
            for _ in range(46):
                a = r.random() * 2 * math.pi; r0 = 520 + r.random() * 200; r1 = r0 + 300 + r.random() * 500
                p0 = (int(W / 2 + math.cos(a) * r0), int(780 + math.sin(a) * r0 * 1.2)); p1 = (int(W / 2 + math.cos(a) * r1), int(780 + math.sin(a) * r1 * 1.2))
                cv2.line(lay, p0, p1, 1.0, int(2 + 5 * r.random()), cv2.LINE_AA)
            f = math.sin(math.pi * dt / 0.32) * 0.75
            img = img * (1 - lay[..., None] * f) + lay[..., None] * f * 255
    return img


HALF = np.zeros((H, W), np.float32)
for _y in range(0, H, 16):
    for _x in range(8 if (_y // 16) % 2 else 0, W, 16): cv2.circle(HALF, (_x, _y), 4, 1.0, -1, cv2.LINE_AA)


def impact(img, t):
    for s in IMPACT:
        if 0 <= t - s < 2 / 30 + 1e-3:
            g = img.mean(axis=2, keepdims=True)
            hard = np.where(g > 110, 255.0, 0.0)
            return hard * np.array([1.0, 0.66, 0.0]) * 0.9 + (1 - hard / 255) * HALF[..., None] * np.array([248, 168, 0]) * 0.8
    return img


def glitch(img, t):
    for s, d in GLITCH:
        if s <= t < s + d:
            r = np.random.default_rng(int(t * 30)); out = img.copy()
            sh = int(10 + 18 * r.random())
            out[..., 0] = np.roll(img[..., 0], sh, axis=1); out[..., 2] = np.roll(img[..., 2], -sh, axis=1)
            for _ in range(5):
                y = int(r.random() * H); h = int(20 + 80 * r.random()); dx = int((r.random() - 0.5) * 120)
                out[y:y + h] = np.roll(out[y:y + h], dx, axis=1)
            return out
    return img


def brush_wipe(a, b, p):
    """thick orange marker stroke sweeps diagonally; A under the leading half, B revealed behind it."""
    pos = -0.25 + 1.5 * p
    u = (xx / W * 0.6 + yy / H * 0.4)
    band = np.abs(u - pos) < 0.13
    edge = np.clip((pos - u) * 40, 0, 1)[..., None]
    out = a * (1 - edge) + b * edge
    m = band.astype(np.float32); m = cv2.GaussianBlur(m, (0, 0), 2)[..., None]
    rough = 0.9 + 0.1 * np.sin(yy / 7 + xx / 13)[..., None]
    return out * (1 - m) + np.array(OR, np.float32) * rough * m
