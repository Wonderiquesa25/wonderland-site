"""Pop version pass 1: only the shots that change (new project photos + showcase); other shots reuse alice/shots_nat."""
import sys, os, subprocess, math, numpy as np, cv2
B = sys.argv[1]; A = f"{B}/../alice"; sys.path.insert(0, A)
import wonder as WD
from shots import SHOTS, HANDLE
W, H, FPS = 1080, 1920, 30
OUT = f"{B}/shots"; os.makedirs(OUT, exist_ok=True)
P = {i: cv2.cvtColor(cv2.imread(f"{B}/photos/P{i}.png"), cv2.COLOR_BGR2RGB) for i in range(1, 12)}
# shot index -> photo, push centre (x,y in 0..1), zoom from, zoom to
PHOTO_SHOTS = {2: (6, (0.40, 0.42), 1.00, 1.14), 3: (4, (0.50, 0.45), 1.12, 1.00), 16: (5, (0.35, 0.30), 1.00, 1.16),
               25: (11, (0.45, 0.35), 1.00, 1.15)}


def kb(img, cx, cy, z):
    M = np.float32([[z, 0, W / 2 - cx * W * z], [0, z, H / 2 - cy * H * z]])
    M[0, 2] = min(0, max(W - W * z, M[0, 2])); M[1, 2] = min(0, max(H - H * z, M[1, 2]))
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)


def enc(path):
    return subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                             "-c:v", "libx264", "-crf", "11", "-preset", "fast", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)


def panel(img, w, h, z):
    """photo fitted (cover) into w x h panel with a light push."""
    s = max(w / W, h / H) * z
    r = cv2.resize(img, (int(W * s), int(H * s)), interpolation=cv2.INTER_AREA)
    y0 = (r.shape[0] - h) // 2; x0 = (r.shape[1] - w) // 2
    return r[y0:y0 + h, x0:x0 + w]


def ease_back(p):                      # overshoot pop
    c = 1.70158; p = p - 1; return 1 + (c + 1) * p ** 3 + c * p ** 2


def showcase(k):
    """74.45-79.90: four finished projects pop in as comic panels, then a 2x2 grid on '100% blindado' (78.45)."""
    oa, ob = SHOTS[k][0], SHOTS[k][1]
    n = round((ob - oa + 2 * HANDLE) * FPS)
    seq = [(74.45, 1), (75.55, 9), (76.62, 7), (77.60, 3)]
    grid_t = 78.45; grid = [1, 2, 4, 6]
    halftone = np.zeros((H, W), np.float32)
    for y in range(0, H, 22):
        for x in range(0 + (11 if (y // 22) % 2 else 0), W, 22):
            cv2.circle(halftone, (x, y), 5, 1.0, -1, cv2.LINE_AA)
    bg = np.full((H, W, 3), (14, 14, 14), np.float32) + halftone[..., None] * np.array([248, 168, 0]) * 0.22
    e = enc(f"{OUT}/shot_{k:02d}.mp4")
    for i in range(n):
        t = oa - HANDLE + i / FPS
        if t < grid_t:
            cur = [s for s in seq if s[0] <= t] or [seq[0]]
            ts, pid = cur[-1]; p = min(1, (t - ts) / 0.28) if t >= ts else 1
            z = 1.0 + 0.06 * (t - ts) if t >= ts else 1.0
            img = WD.grade_natural(kb(P[pid], 0.5, 0.45, 1.0 + 0.05 * max(0, t - ts)))
            if t >= seq[0][0]:
                # comic-panel entrance: frame slams in from slight tilt with white border
                s = 0.78 + 0.22 * ease_back(p); ang = (1 - p) * (-6 if pid % 2 else 6)
                M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, s)
                fr = cv2.copyMakeBorder(img[18:-18, 18:-18], 18, 18, 18, 18, cv2.BORDER_CONSTANT, value=(255, 255, 255))
                img = cv2.warpAffine(fr.astype(np.float32), M, (W, H), borderMode=cv2.BORDER_CONSTANT, borderValue=0)
                mask = cv2.warpAffine(np.ones((H, W), np.float32), M, (W, H))[..., None]
                img = img * mask + bg * (1 - mask)
        else:
            img = bg.copy(); g = 14; pw, ph = (W - 3 * g) // 2, (H - 3 * g) // 2
            for j, pid in enumerate(grid):
                st = grid_t + j * 0.09; p = np.clip((t - st) / 0.25, 0, 1)
                if p <= 0: continue
                pan = WD.grade_natural(panel(P[pid], pw, ph, 1.0 + 0.04 * (t - st)))
                pan = cv2.copyMakeBorder(pan[8:-8, 8:-8], 8, 8, 8, 8, cv2.BORDER_CONSTANT, value=(255, 255, 255))
                s = 0.6 + 0.4 * ease_back(p)
                ph2, pw2 = int(ph * s), int(pw * s)
                pan = cv2.resize(pan, (pw2, ph2))
                cx = g + (j % 2) * (pw + g) + pw // 2; cy = g + (j // 2) * (ph + g) + ph // 2
                y0, x0 = cy - ph2 // 2, cx - pw2 // 2
                img[max(0, y0):y0 + ph2, max(0, x0):x0 + pw2] = pan[max(0, -y0):, max(0, -x0):][:H - max(0, y0), :W - max(0, x0)]
        e.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    e.stdin.close(); e.wait(); print("showcase ok", flush=True)


def photo_shot(k):
    pid, (cx, cy), z0, z1 = PHOTO_SHOTS[k]
    oa, ob = SHOTS[k][0], SHOTS[k][1]
    n = round((ob - oa + 2 * HANDLE) * FPS)
    base = P[pid]
    e = enc(f"{OUT}/shot_{k:02d}.mp4")
    for i in range(n):
        p = i / (n - 1); z = z0 + (z1 - z0) * (p * p * (3 - 2 * p))
        e.stdin.write(np.clip(WD.grade_natural(kb(base, cx, cy, z)), 0, 255).astype(np.uint8).tobytes())
    e.stdin.close(); e.wait(); print("photo shot", k, "ok", flush=True)


if __name__ == "__main__":
    from multiprocessing import Pool
    jobs = list(PHOTO_SHOTS) + [24]
    with Pool(4) as pool:
        pool.map(lambda_ := (lambda k: showcase(k) if k == 24 else photo_shot(k)), jobs) if False else None
    for k in jobs:
        showcase(k) if k == 24 else photo_shot(k)
