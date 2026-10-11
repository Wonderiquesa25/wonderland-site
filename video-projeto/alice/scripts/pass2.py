"""Pass 2: timeline compositor - portal open/close, magical transitions, particles, petals, rays, electric arcs, finish.
Run in chunks: python3 pass2.py A t0 t1 out.mp4"""
import sys, subprocess, numpy as np, cv2, math
A = sys.argv[1]; sys.path.insert(0, A)
from shots import SHOTS, HANDLE, TOTAL
W, H, FPS = 1080, 1920, 30
cv2.setNumThreads(2)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
PORTAL = cv2.cvtColor(cv2.imread(f"{A}/plates/portal.png"), cv2.COLOR_BGR2RGB).astype(np.float32)
MC, MA, MB = (537.0, 763.0), 220.0, 422.0                        # mirror centre and semi-axes in the portal plate
ELL = np.clip(1.0 - (np.sqrt(((xx - MC[0]) / MA) ** 2 + ((yy - MC[1]) / MB) ** 2) - 1.0) / 0.012, 0, 1)
ELL = cv2.GaussianBlur(ELL, (0, 0), 2)
RING = np.exp(-((np.sqrt(((xx - MC[0]) / MA) ** 2 + ((yy - MC[1]) / MB) ** 2) - 1.0) / 0.035) ** 2)

# transitions at shot boundaries: (type, duration)
TRANS = {1: ("sparkle", .45), 2: ("ripple", .5), 3: ("petals", .55), 4: ("zoom", .35), 5: ("sparkle", .5), 6: ("ripple", .5),
         7: ("dissolve", .4), 8: ("cut", 0), 9: ("zoom", .35), 10: ("petals", .55), 11: ("sparkle", .45), 12: ("ripple", .45),
         13: ("zoom", .4), 14: ("cut", 0), 15: ("cut", 0), 16: ("glowline", .5), 17: ("cut", 0), 18: ("sparkle", .45),
         19: ("cut", 0), 20: ("flash", .3), 21: ("dissolve", .45), 22: ("zoom", .35), 23: ("cut", 0), 24: ("flash", .5),
         25: ("petals", .6), 26: ("dissolve", .45)}
GIANTS = [2.67, 10.55, 17.45, 22.43, 31.90, 44.45, 52.55, 62.05, 71.09, 73.63, 78.45, 83.43, 88.61]   # sparkle bursts
ARCS = [(44.45, 46.0, 0.6), (59.09, 60.5, 0.8), (73.63, 74.45, 1.0)]


class Reader:
    def __init__(self, k):
        self.k = k; self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{A}/shots/shot_{k:02d}.mp4", "-f", "rawvideo",
                                               "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.i = -1; self.f = None; self.hist = []

    def get(self, t):
        oa = SHOTS[self.k][0]
        want = int(round((t - oa + HANDLE) * FPS))
        while self.i < want:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            self.f = np.frombuffer(b, np.uint8).reshape(H, W, 3).astype(np.float32); self.i += 1
            self.hist = (self.hist + [self.f])[-8:]
        return self.f

    def close(self):
        self.p.stdout.close(); self.p.kill(); self.p.wait()


def shot_at(t):
    for k, s in enumerate(SHOTS):
        if s[0] <= t < s[1]: return k
    return len(SHOTS) - 1


def ease(p): return p * p * (3 - 2 * p)


def rng_pts(seed, n):
    r = np.random.default_rng(seed); return r.random((n, 6))


DUST = rng_pts(7, 110)


def dust_layer(t, strength):
    lay = np.zeros((H, W, 3), np.float32)
    for x0, y0, sp, sz, ph, hue in DUST:
        x = (x0 * W + 40 * math.sin(t * 0.6 + ph * 6)) % W
        y = (y0 * H - t * (25 + 50 * sp)) % H
        tw = 0.5 + 0.5 * math.sin(t * (2 + 3 * sp) + ph * 9)
        col = (255, 215, 130) if hue > 0.3 else (200, 150, 255)
        cv2.circle(lay, (int(x), int(y)), int(1 + 3 * sz), [c * tw for c in col], -1, cv2.LINE_AA)
    return cv2.GaussianBlur(lay, (0, 0), 2.2) * 1.6 * strength


def burst_layer(t):
    lay = np.zeros((H, W, 3), np.float32)
    for g in GIANTS:
        dt = t - g
        if 0 <= dt < 0.9:
            r = np.random.default_rng(int(g * 100))
            for ang, sp, sz, hue in r.random((70, 4)):
                a = ang * 2 * math.pi; d = (120 + 520 * sp) * (1 - (1 - dt / 0.9) ** 3)
                x = W / 2 + math.cos(a) * d; y = 780 + math.sin(a) * d * 0.7
                f = (1 - dt / 0.9) ** 1.5
                col = (255, 220, 140) if hue > 0.35 else (190, 120, 255)
                cv2.circle(lay, (int(x), int(y)), int(2 + 4 * sz), [c * f for c in col], -1, cv2.LINE_AA)
    return cv2.GaussianBlur(lay, (0, 0), 2.5) * 1.8


def petal_sprites(t, p, n=34, seed=3):
    """petal swarm crossing the frame left->right as p goes 0->1; returns (rgb, alpha)."""
    lay = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W), np.float32)
    r = np.random.default_rng(seed)
    for x0, y0, sz, rot, hue, sp in r.random((n, 6)):
        x = (-0.4 + 1.8 * p * (0.8 + 0.4 * sp)) * W + x0 * 300 - 150
        y = y0 * H + 120 * math.sin(p * 6 + rot * 6)
        ax, ay = int(30 + 50 * sz), int(14 + 22 * sz)
        ang = rot * 360 + p * 400 * (sp - 0.5)
        col = (240, 120, 190) if hue > 0.5 else (185, 120, 245)
        cv2.ellipse(lay, (int(x), int(y)), (ax, ay), ang, 0, 360, col, -1, cv2.LINE_AA)
        cv2.ellipse(al, (int(x), int(y)), (ax, ay), ang, 0, 360, 0.92, -1, cv2.LINE_AA)
    return cv2.GaussianBlur(lay, (0, 0), 1.5), cv2.GaussianBlur(al, (0, 0), 1.5)


def ripple(img, amp, t):
    r = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2)
    d = amp * np.sin(r / 38 - t * 14)
    return cv2.remap(img, xx + d * (xx - W / 2) / (r + 1), yy + d * (yy - H / 2) / (r + 1), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def zoomed(img, z):
    M = np.float32([[z, 0, W / 2 * (1 - z)], [0, z, H / 2 * (1 - z)]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def radial_blur(img, z, n=4):
    acc = img.copy()
    for i in range(1, n): acc += zoomed(img, 1 + z * i / n)
    return acc / n


def transition(kind, a, b, p, t):
    e = ease(p)
    if kind == "cut": return a if p < 0.5 else b
    if kind == "dissolve":
        out = a * (1 - e) + b * e; glow = math.sin(math.pi * p) * 0.25
        return out + cv2.GaussianBlur(out, (0, 0), 18) * glow
    if kind == "sparkle":
        out = a * (1 - e) + b * e
        return out * (1 + 0.35 * math.sin(math.pi * p)) + cv2.GaussianBlur(out, (0, 0), 25) * 0.4 * math.sin(math.pi * p)
    if kind == "ripple":
        amp = 22 * math.sin(math.pi * p)
        return ripple(a, amp, t) * (1 - e) + ripple(b, amp, t) * e
    if kind == "zoom":
        if p < 0.5: return radial_blur(zoomed(a, 1 + 0.5 * e), 0.18 * math.sin(math.pi * p))
        return radial_blur(zoomed(b, 0.75 + 0.25 * e), 0.18 * math.sin(math.pi * p))
    if kind == "petals":
        pr, pa = petal_sprites(t, p)
        edge = (-0.3 + 1.6 * p) * W
        m = np.clip((edge - xx) / 160, 0, 1)[..., None]
        out = a * (1 - m) + b * m
        return out * (1 - pa[..., None]) + pr * pa[..., None]
    if kind == "glowline":
        edge = p * (W + 200) - 100
        m = np.clip((edge - xx) / 6, 0, 1)[..., None]
        line = np.exp(-((xx - edge) / 14) ** 2)[..., None] * np.array([255, 215, 140]) * 1.2
        return a * (1 - m) + b * m + line
    if kind == "flash":
        f = math.exp(-((p - 0.5) / 0.18) ** 2)
        out = a if p < 0.5 else b
        return out * (1 - f) + np.array([255, 245, 255], np.float32) * f * 0.95
    return b


def arcs_layer(t):
    lay = np.zeros((H, W, 3), np.float32)
    for a, b, s in ARCS:
        if a <= t < b:
            fr = int(t * 30); r = np.random.default_rng(fr)
            env = s * (1 - (t - a) / (b - a)) ** 0.5
            for _ in range(3):
                x, y = r.random() * W, 150 + r.random() * 500
                pts = [(x, y)]
                for _ in range(14):
                    x += r.normal(60, 25) * (1 if r.random() > .5 else -1) * .6; y += r.normal(35, 25)
                    pts.append((x, y))
                cv2.polylines(lay, [np.int32(pts)], False, (210, 150, 255), 3, cv2.LINE_AA)
            lay = cv2.GaussianBlur(lay, (0, 0), 3) * 2.2 + lay
            lay *= env * (0.6 + 0.4 * r.random())
    return lay


FOG = cv2.resize(np.random.default_rng(5).random((24, 14)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)


def fog_layer(t, s):
    sh = int(t * 18) % W
    f = np.roll(FOG, sh, axis=1) * np.clip((yy - H * 0.55) / (H * 0.45), 0, 1)
    return (f[..., None] * np.array([150, 130, 200])) * s


VIG = (1 - 0.42 * np.clip(np.sqrt(((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H * 0.45) / (H * 0.75)) ** 2) - 0.25, 0, 1))[..., None]
RAYS = np.zeros((H, W), np.float32)
for i in range(7):
    ang = -0.35 + i * 0.12
    cv2.line(RAYS, (int(W * 0.7), -50), (int(W * 0.7 + math.sin(ang) * 2600), int(math.cos(ang) * 2600)), 1.0, 40 + 25 * (i % 3))
RAYS = cv2.GaussianBlur(RAYS, (0, 0), 30)


def portal(content, t, opening):
    """opening: p 0->1 pushes into the mirror; closing uses p 1->0."""
    p = ease(np.clip(t, 0, 1))
    Z = 1 + 2.6 * p
    cx = MC[0] + (W / 2 - MC[0]) * p; cy = MC[1] + (H / 2 - MC[1]) * p
    M = np.float32([[Z, 0, cx - MC[0] * Z], [0, Z, cy - MC[1] * Z]])
    plate = cv2.warpAffine(PORTAL, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    ell = cv2.warpAffine(ELL, M, (W, H))[..., None]
    ring = cv2.warpAffine(RING, M, (W, H))[..., None]
    s = (2 * MB * Z) / H                                                     # content fills the mirror opening
    Mc = np.float32([[s, 0, cx - W / 2 * s], [0, s, cy - H / 2 * s]])
    inner = cv2.warpAffine(content, Mc, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    shimmer = 0.5 + 0.5 * math.sin(t * 9)
    out = plate * (1 - ell) + inner * ell + ring * np.array([255, 215, 150]) * (0.55 + 0.25 * shimmer)
    return out


def frame(t, readers):
    k = shot_at(t)
    def get(kk):
        if kk not in readers: readers[kk] = Reader(kk)
        return readers[kk].get(t)
    img = get(k)
    # transitions
    for b in (k, k + 1):
        if 1 <= b < len(SHOTS) and b in TRANS:
            kind, d = TRANS[b]; B = SHOTS[b][0]
            if d and B - d / 2 <= t < B + d / 2:
                img = transition(kind, get(b - 1), get(b), (t - (B - d / 2)) / d, t)
    # time-warp echo on "segundas chances"
    if k == 8 and len(readers[8].hist) > 4:
        h = readers[8].hist
        img = img * 0.55 + h[-3] * 0.25 + h[-5] * 0.2
    # portal open / close
    if t < 2.3: img = portal(img, t / 2.3, True)
    if t > TOTAL - 2.5: img = portal(img, (TOTAL - 0.25 - t) / 2.2, False)
    # atmosphere
    night = 1.0 if t < 12.55 or 68.7 <= t < 74.45 else 0.0
    if night: img = img + fog_layer(t, 0.22)
    if 74.45 <= t < 84.9: img = img + RAYS[..., None] * np.array([255, 205, 140]) * 0.32 * (0.85 + 0.15 * math.sin(t * 2))
    img = img + dust_layer(t, 0.9 if (t < 12.55 or t >= 74.45) else 0.55) + burst_layer(t) + arcs_layer(t)
    # bloom + vignette
    hi = np.clip(img - 200, 0, None)
    img = img + cv2.GaussianBlur(hi, (0, 0), 20) * 0.6
    img = img * VIG
    if t > TOTAL - 0.25: img *= max(0.0, (TOTAL - t) / 0.25)
    if t < 0.15: img *= t / 0.15
    return np.clip(img, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    t0, t1, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                            "-vf", "noise=alls=3:allf=t", "-c:v", "libx264", "-crf", "13", "-preset", "medium", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE)
    readers = {}
    n0, n1 = round(t0 * FPS), round(t1 * FPS)
    for n in range(n0, n1):
        t = n / FPS
        enc.stdin.write(frame(t, readers).tobytes())
        for kk in [kk for kk in readers if SHOTS[kk][1] + 0.6 < t]:
            readers.pop(kk).close()
        if n % 90 == 0: print(out.split("/")[-1], round(t, 1), flush=True)
    enc.stdin.close(); enc.wait()
    for r in readers.values(): r.close()
    print("done", out, flush=True)
