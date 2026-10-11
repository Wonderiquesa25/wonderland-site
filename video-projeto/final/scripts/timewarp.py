"""Time-travel transition (2.0 s): speed-ramp -> fast rewind pulled back into a tunnel of past frames with light trails,
radial streaks and chromatic separation -> flash -> next scene emerges from the tunnel centre and settles."""
import sys, subprocess, math, numpy as np, cv2
F = sys.argv[1]; W, H, FPS = 1080, 1920, 30
T0, DUR, A_END = 84.05, 2.0, 84.53
cv2.setNumThreads(4)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
R = np.sqrt((xx - W / 2) ** 2 + (yy - H / 2) ** 2)


def read(path, t0, t1):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


A = read(f"{F}/A_fast.mp4", 75.5, A_END); A0 = 75.5
B = read(f"{F}/B_fast.mp4", 0.0, 0.85)
def a_at(t): return A[int(np.clip(round((t - A0) * FPS), 0, len(A) - 1))].astype(np.float32)
def b_at(t): return B[int(np.clip(round(t * FPS), 0, len(B) - 1))].astype(np.float32)


def scaled(img, s, bg=0.0):
    M = np.float32([[s, 0, W / 2 * (1 - s)], [0, s, H / 2 * (1 - s)]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(bg, bg, bg))


def mask_scaled(s, feather=18):
    m = np.zeros((H, W), np.float32)
    w2, h2 = W * s / 2, H * s / 2
    cv2.rectangle(m, (int(W / 2 - w2), int(H / 2 - h2)), (int(W / 2 + w2), int(H / 2 + h2)), 1.0, -1)
    return cv2.GaussianBlur(m, (0, 0), feather)[..., None]


def radial(img, amt, n=6):
    if amt < 0.004: return img
    acc = img.copy()
    for i in range(1, n): acc += scaled(img, 1 + amt * i / n)
    return acc / n


def chroma(img, px):
    if px < 1: return img
    out = img.copy(); px = int(px)
    out[..., 0] = scaled(img[..., 0:1].repeat(3, 2), 1 + px / 1000)[..., 0]
    out[..., 2] = scaled(img[..., 2:3].repeat(3, 2), 1 - px / 1000)[..., 2]
    return out


rng = np.random.default_rng(11)
TRAILS = rng.random((85, 4))      # angle, speed, length, hue


def trails(tau, strength, inward=True):
    lay = np.zeros((H, W, 3), np.float32)
    for ang, sp, ln, hue in TRAILS:
        a = ang * 2 * math.pi
        ph = (sp * 3.0 + tau * (2.2 + 2.5 * sp)) % 1.0
        r1 = (1 - ph) * 1300 if inward else ph * 1300
        r0 = r1 + (60 + 260 * ln) * (1 if inward else -1)
        p0 = (int(W / 2 + math.cos(a) * r0), int(H / 2 + math.sin(a) * r0 * 1.15))
        p1 = (int(W / 2 + math.cos(a) * r1), int(H / 2 + math.sin(a) * r1 * 1.15))
        col = (255, 175, 30) if hue > 0.45 else (235, 240, 255)
        cv2.line(lay, p0, p1, col, 2 + int(3 * sp), cv2.LINE_AA)
    return (cv2.GaussianBlur(lay, (0, 0), 3) * 1.5 + lay) * strength


def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)


enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                        "-c:v", "libx264", "-crf", "12", "-preset", "medium", "-pix_fmt", "yuv420p", f"{F}/T_warp.mp4"], stdin=subprocess.PIPE)
n = int(DUR * FPS)
for i in range(n):
    tau = i / FPS
    if tau < 0.35:                                                     # 1) acceleration
        p = tau / 0.35
        img = a_at(min(T0 + tau * (1 + 1.4 * p), 84.22))
        img = radial(scaled(img, 1 + 0.06 * p * p), 0.10 * p * p)
        img = chroma(img, 6 * p)
        img = img * (1 - 0.15 * p) + trails(tau, 0.35 * p * p)
    elif tau < 1.25:                                                   # 2) rewind tunnel (pull back through time)
        p = (tau - 0.35) / 0.90; e = ease(p)
        at = 84.22 - 8.0 * e                                     # time runs backwards ~9x
        s = 1.0 - 0.62 * e                                             # pull back
        img = np.zeros((H, W, 3), np.float32)
        for k in range(6, 0, -1):                                      # tunnel walls: older frames, bigger, dimmer
            sk = s * (1 + 0.32 * k); fr = a_at(at + 0.18 * k)
            layer = scaled(fr, sk); mk = mask_scaled(sk, 30) * (1 - mask_scaled(s * (1 + 0.32 * (k - 1)), 30))
            img = img * (1 - mk * 0.85) + layer * mk * (0.55 - 0.06 * k)
        core = scaled(a_at(at), s); mc = mask_scaled(s, 6)
        img = img * (1 - mc) + core * mc
        img = radial(img, 0.16 + 0.10 * math.sin(math.pi * p))
        img = chroma(img, 10 + 10 * math.sin(math.pi * p))
        img = img * (1 - 0.35 * np.clip((R - 500) / 900, 0, 1))[..., None]
        img = img + trails(tau, 0.6)
        img = img + np.exp(-(R / 260) ** 2)[..., None] * np.array([255, 190, 80]) * (0.25 + 0.9 * p ** 3)   # light at the core
    else:                                                              # 3) emergence of the next scene
        p = (tau - 1.25) / 0.75; e = 1 - (1 - min(p, 1)) ** 3
        bt = (tau - 1.25)
        s = 0.18 + 0.82 * e
        bimg = scaled(b_at(bt), s, bg=0)
        bimg = radial(bimg, 0.20 * (1 - e))
        mk = mask_scaled(s, 10)
        flash = math.exp(-(p / 0.16) ** 2)
        tun = scaled(a_at(A_END - 8.3), 0.38 * (1 + 2.2 * e)) * (1 - e) * 0.5
        img = tun * (1 - mk) + bimg * mk
        img = chroma(img, 14 * (1 - e))
        img = img + trails(tau, 0.8 * (1 - e) ** 2, inward=False)
        img = img * (1 - flash) + np.array([255, 245, 230], np.float32) * flash * 0.95 + bimg * flash * 0.05
    hi = np.clip(img - 210, 0, None); img = img + cv2.GaussianBlur(hi, (0, 0), 14) * 0.5
    enc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print("warp ok", n)
