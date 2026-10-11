"""Pass 1: one graded, sky-replaced clip per shot (with 0.5 s handles) -> shots/shot_XX.mp4"""
import sys, os, subprocess, numpy as np, cv2
A = sys.argv[1]; sys.path.insert(0, A)
import wonder as WD
from shots import SHOTS, HANDLE
W, H, FPS = 1080, 1920, 30
os.makedirs(f"{A}/shots", exist_ok=True)
cv2.setNumThreads(1)


def ladder(kind):
    im = cv2.cvtColor(cv2.imread(f"{A}/src/ladder.jpg"), cv2.COLOR_BGR2RGB)   # 1500x2000
    h, w = im.shape[:2]; cw = int(h * 9 / 16)
    x0 = (w - cw) // 2 if kind == "ladder" else w - cw
    return cv2.resize(im[:, x0:x0 + cw], (W, H), interpolation=cv2.INTER_AREA)


def render(k):
    oa, ob, sa, sb, sky, mood, tol, ymax, _ = SHOTS[k]
    out = f"{A}/shots/shot_{k:02d}.mp4"
    if os.path.exists(out): return
    n_out = round((ob - oa + 2 * HANDLE) * FPS)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                            "-c:v", "libx264", "-crf", "11", "-preset", "fast", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    if isinstance(sa, str):                                      # still photo: slow push-in (and a tighter push for the wire shot)
        base = ladder(sa); m, ref = WD.sky_mask(base, tol=tol, ymax=ymax)
        for i in range(n_out):
            t = i / FPS
            z = (1.0 + 0.10 * t / (n_out / FPS)) if sa == "ladder" else (1.45 + 0.25 * t / (n_out / FPS))
            cx, cy = (W * 0.50, H * 0.45) if sa == "ladder" else (W * 0.62, H * 0.30)
            M = np.float32([[z, 0, W / 2 - cx * z], [0, z, H / 2 - cy * z]])
            fr = cv2.warpAffine(base, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
            mm = cv2.warpAffine(m, M, (W, H))
            o = WD.compose(fr, WD.place_sky(sky, t, (0, -t * 6)), mm, mood)
            enc.stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes())
    else:
        speed = (sb - sa) / (ob - oa)
        s0 = max(0.0, sa - HANDLE * speed); s1 = sb + HANDLE * speed + 0.2
        raw = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{s0:.3f}", "-t", f"{s1 - s0:.3f}", "-i", f"{A}/src/canva_material.mp4",
                                "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        frames = []
        while True:
            b = raw.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            frames.append(np.frombuffer(b, np.uint8).reshape(H, W, 3))
        raw.wait()
        # global camera motion (phase correlation) so the new sky moves with the camera
        shifts = [np.zeros(2)]
        prevg = None
        for f in frames:
            g = cv2.resize(cv2.cvtColor(f, cv2.COLOR_RGB2GRAY), (270, 480)).astype(np.float32)
            if prevg is not None:
                (dx, dy), _ = cv2.phaseCorrelate(prevg, g)
                shifts.append(shifts[-1] + np.clip([dx, dy], -15, 15) * 4)
            prevg = g
        shifts = shifts[1:] if len(shifts) > len(frames) else shifts
        m = None; ref = None
        t0 = sa - s0                                             # where out-time 0 (minus handle) maps in the decoded range
        for i in range(n_out):
            t = i / FPS
            st = (sa - HANDLE * speed - s0) + t * speed
            fi = st * FPS; i0 = int(np.clip(np.floor(fi), 0, len(frames) - 1)); i1 = min(i0 + 1, len(frames) - 1); a = fi - np.floor(fi)
            fr = frames[i0] if (speed > 0.95 or a < 0.15) else cv2.addWeighted(frames[i0], 1 - a, frames[i1], a, 0)
            m, ref = WD.sky_mask(fr, m, ref, tol=tol, ymax=ymax)
            sh = shifts[i0] * 0.6
            o = WD.compose(fr, WD.place_sky(sky, t, (-sh[0], -sh[1])), m, mood)
            enc.stdin.write(np.clip(o, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait(); print("shot", k, "ok", flush=True)


if __name__ == "__main__":
    from multiprocessing import Pool
    ks = [int(x) for x in sys.argv[2:]] or list(range(len(SHOTS)))
    with Pool(4) as p: p.map(render, ks, chunksize=1)
