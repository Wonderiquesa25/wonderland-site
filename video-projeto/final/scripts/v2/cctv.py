"""Transition v2 — CCTV control room: part 1 becomes CAM 01 feed -> camera pulls back to the Kukulu monitoring wall
(2x2 feeds) -> orange selector jumps to CAM 02 -> camera pushes into CAM 02 = scene 2. 2.1 s, 30 fps, 1080x1920.
usage: cctv.py A.mp4 tA0 A_cap B.mp4 photo3 photo4 fonts_dir out.mp4"""
import sys, json, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
A, tA0, A_cap, B, P3, P4, FD, OUT = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8]
W, H, FPS, DUR = 1080, 1920, 30, 2.1
N = int(round(DUR * FPS)); B_START = 1.55                 # B plays inside CAM 02 from t = 1.20
OR = (248, 168, 0)
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
fm = lambda s: ImageFont.truetype(MONO, max(6, int(s)))
fb = lambda s: ImageFont.truetype(f"{FD}/Montserrat-ExtraBold.ttf", max(6, int(s)))
fo = lambda s: ImageFont.truetype(f"{FD}/Oswald-Bold.ttf", max(6, int(s)))

def grab(path, ss, n):
    p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{ss:.3f}", "-i", path, "-frames:v", str(n), "-vf", f"scale={W}:{H}",
                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, H, W, 3)
nA = int((A_cap - tA0) * FPS) + 1
Af = grab(A, tA0, nA); Bf = grab(B, 0.0, int((DUR - B_START) * FPS) + 2)
ph = [np.asarray(Image.open(p).convert("RGB").resize((W, H))) for p in (P3, P4)]
rng = np.random.default_rng(11)

# ---- wall layout (wall space == screen space when the camera shows the whole wall) ----
GX0, GY0, GW = 40, 190, 1000; GH = GW * 16 / 9                       # grid area
CW, CH = GW / 2, GH / 2
cells = [(GX0 + (i % 2) * CW, GY0 + (i // 2) * CH) for i in range(4)]   # top-left of each cell
LBL = ["CAM 01 · RECEPÇÃO", "CAM 02 · ESCRITÓRIO", "CAM 03 · PERÍMETRO", "CAM 04 · PORTÃO"]
S_FULL = W / CW                                                         # zoom that makes one cell fill the screen
cen = lambda i: (cells[i][0] + CW / 2, cells[i][1] + CH / 2)

def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def ease_c(x): x = min(max(x, 0), 1); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2

def camera(t):
    """(scale, centre) of the virtual camera over the wall"""
    wall = (1.0, (W / 2, H / 2))
    c1, c2 = (S_FULL, cen(0)), (S_FULL, cen(1))
    def lerp(a, b, k):
        s = np.exp(np.log(a[0]) + (np.log(b[0]) - np.log(a[0])) * k)
        # keep the motion natural: interpolate the point that stays under the screen centre in screen-space
        w = (1 / s - 1 / a[0]) / (1 / b[0] - 1 / a[0]) if b[0] != a[0] else k
        return s, (a[1][0] + (b[1][0] - a[1][0]) * w, a[1][1] + (b[1][1] - a[1][1]) * w)
    if t < 0.35: return c1
    if t < 1.00: return lerp(c1, wall, ease_c((t - 0.35) / 0.65))
    if t < 1.20: return wall
    if t < 1.95: return lerp(wall, c2, ease_c((t - 1.20) / 0.75))
    return c2

def to_screen(x, y, s, c): return ((x - c[0]) * s + W / 2, (y - c[1]) * s + H / 2)

def cctv_look(img, k, t, seed):
    """security-camera look, strength k (0..1)"""
    if k <= 0: return img.astype(np.float32)
    f = img.astype(np.float32)
    g = f.mean(2, keepdims=True)
    look = (f * 0.55 + g * 0.45) * np.array([0.93, 1.03, 1.0]) * 0.92 + 6
    look += np.random.default_rng(seed + int(t * 30)).normal(0, 7, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    return f * (1 - k) + look * k

def glitch(img, amt, t):
    out = img.copy(); r = np.random.default_rng(int(t * 1000))
    for _ in range(int(10 * amt)):
        y0 = r.integers(0, H - 80); h = r.integers(8, 80); dx = int(r.normal(0, 60 * amt))
        out[y0:y0 + h] = np.roll(out[y0:y0 + h], dx, axis=1)
    out[..., 0] = np.roll(out[..., 0], int(10 * amt), axis=1); out[..., 2] = np.roll(out[..., 2], -int(10 * amt), axis=1)
    return out

def static(shape, t):
    r = np.random.default_rng(int(t * 997)); n = r.uniform(0, 255, (shape[0] // 3 + 1, shape[1] // 3 + 1, 1))
    n = n.repeat(3, 0).repeat(3, 1)[: shape[0], : shape[1]]
    return np.repeat(n, 3, 2) * np.linspace(0.7, 1.0, shape[0])[:, None, None]

def feed(i, t):
    """content of cell i at time t (full 1080x1920, float), plus OSD strength"""
    if i == 0:
        fr = Af[min(int(t * FPS), len(Af) - 1)]
        k = ease(t / 0.35)
        return cctv_look(fr, k, t, 1), k
    if i == 1:
        if t < B_START:
            return static((H, W), t) * 0.85, 1.0
        fr = Bf[min(int((t - B_START) * FPS), len(Bf) - 1)]
        k = 1 - ease((t - 1.80) / 0.30)
        img = cctv_look(fr, k, t, 2)
        if t < B_START + 0.12: img = img * 0.5 + static((H, W), t) * 0.5
        return img, k
    p = ph[i - 2]; z = 1.04 + 0.03 * t                                          # slow drift on the still feeds
    m = cv2.resize(p, None, fx=z, fy=z); y0 = (m.shape[0] - H) // 2; x0 = (m.shape[1] - W) // 2 + int(10 * t * (1 if i == 2 else -1))
    return cctv_look(m[y0:y0 + H, x0:x0 + W], 1.0, t, i), 1.0

def osd(d, i, x0, y0, x1, y1, k, t):
    """on-screen display drawn in screen space inside the cell rect"""
    if k <= 0.02: return
    sc = (x1 - x0) / W; a = int(255 * k)
    d.rectangle([x0 + 28 * sc, y0 + 30 * sc, x0 + 28 * sc + fm(40 * sc).getlength(LBL[i]) + 30 * sc, y0 + 92 * sc], fill=(0, 0, 0, int(150 * k)))
    d.text((x0 + 43 * sc, y0 + 38 * sc), LBL[i], font=fm(40 * sc), fill=(255, 255, 255, a))
    if int(t * 2.5) % 2 == 0:
        d.ellipse([x1 - 210 * sc, y0 + 42 * sc, x1 - 178 * sc, y0 + 74 * sc], fill=(235, 30, 30, a))
    d.text((x1 - 165 * sc, y0 + 36 * sc), "REC", font=fm(40 * sc), fill=(255, 255, 255, a))
    sec = 7 + int(t)
    d.text((x0 + 36 * sc, y1 - 90 * sc), f"11/10/2026  18:42:{sec:02d}", font=fm(38 * sc), fill=(255, 255, 255, a))
    for cx, cy, dx, dy in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:     # camera corner marks
        L, o = 60 * sc, 18 * sc
        d.line([(cx + dx * o, cy + dy * o), (cx + dx * (o + L), cy + dy * o)], fill=(255, 255, 255, int(200 * k)), width=max(1, int(4 * sc)))
        d.line([(cx + dx * o, cy + dy * o), (cx + dx * o, cy + dy * (o + L))], fill=(255, 255, 255, int(200 * k)), width=max(1, int(4 * sc)))

enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
bgp = (14 + 10 * (1 - yy / H))[..., None] * np.array([0.8, 0.9, 1.1]); prev = None
def render(t):
    s, c = camera(t)
    frame = bgp.copy()
    # faint panel grid in wall space (parallax cue)
    for gx in range(-400, 1500, 90):
        X = int(to_screen(gx, 0, s, c)[0])
        if 0 <= X < W: frame[:, X] += 6
    for i in range(4):
        x0, y0 = to_screen(cells[i][0] + 3, cells[i][1] + 3, s, c); x1, y1 = to_screen(cells[i][0] + CW - 3, cells[i][1] + CH - 3, s, c)
        if x1 < 0 or y1 < 0 or x0 > W or y0 > H: continue
        img, k = feed(i, t)
        X0, Y0, X1, Y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        tw, th = X1 - X0, Y1 - Y0
        if tw < 4 or th < 4: continue
        sm = cv2.resize(img, (tw, th), interpolation=cv2.INTER_AREA if tw < W else cv2.INTER_LINEAR)
        lines = (np.arange(th) % 3 == 0).astype(np.float32)[:, None, None] * 0.13 * k     # scanlines in screen space
        sm = sm * (1 - lines)
        vx = np.linspace(-1, 1, tw)[None, :]; vy = np.linspace(-1, 1, th)[:, None]
        sm *= (1 - 0.35 * k * (vx ** 2 + vy ** 2) / 2)[..., None]
        sx0, sy0 = max(0, X0), max(0, Y0); sx1, sy1 = min(W, X1), min(H, Y1)
        frame[sy0:sy1, sx0:sx1] = sm[sy0 - Y0: sy1 - Y0, sx0 - X0: sx1 - X0]
    if 0.26 <= t <= 0.40: frame = glitch(frame, 1 - abs(t - 0.33) / 0.07, t)
    im = Image.fromarray(frame.clip(0, 255).astype(np.uint8)).convert("RGBA"); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for i in range(4):
        x0, y0 = to_screen(cells[i][0] + 3, cells[i][1] + 3, s, c); x1, y1 = to_screen(cells[i][0] + CW - 3, cells[i][1] + CH - 3, s, c)
        _, k = feed(i, t) if i in (0, 1) else (None, 1.0)
        osd(d, i, x0, y0, x1, y1, k, t)
        if i == 1 and t < B_START:
            d.text(((x0 + x1) / 2 - fm(46 * (x1 - x0) / W).getlength("A LIGAR...") / 2, (y0 + y1) / 2), "A LIGAR...", font=fm(46 * (x1 - x0) / W), fill=(255, 255, 255, 230))
    # header / footer of the monitoring wall (wall space)
    hx, hy = to_screen(GX0, 60, s, c)
    d.text((hx, hy), "CENTRAL DE MONITORIZAÇÃO", font=fo(64 * s), fill=(255, 255, 255, 235))
    hx2, hy2 = to_screen(GX0, 140, s, c); d.text((hx2, hy2), "KUKULU KUA MUKAMBU · SEGURANÇA ELECTRÓNICA 24H", font=fm(26 * s), fill=OR + (255,))
    lx, ly = to_screen(GX0 + GW - 190, 72, s, c)
    if int(t * 2.5) % 2 == 0: d.ellipse([lx, ly + 8 * s, lx + 28 * s, ly + 36 * s], fill=(235, 30, 30, 255))
    d.text((lx + 40 * s, ly), "AO VIVO", font=fm(36 * s), fill=(255, 255, 255, 235))
    fx_, fy_ = to_screen(GX0, GY0 + GH + 30, s, c)
    d.text((fx_, fy_), "4 CÂMARAS ONLINE   ·   SISTEMA ARMADO   ·   SINAL OK", font=fm(26 * s), fill=(160, 200, 160, 230))
    # orange selector: on CAM 01 from 0.80, jumps to CAM 02 at 1.10, fades with the push-in
    if 0.80 <= t < 2.05:
        i = 0 if t < 1.10 else 1
        a = ease((t - 0.80) / 0.1) * (1 - ease((t - 1.80) / 0.2))
        x0, y0 = to_screen(cells[i][0] - 4, cells[i][1] - 4, s, c); x1, y1 = to_screen(cells[i][0] + CW + 4, cells[i][1] + CH + 4, s, c)
        pop = 1 + 0.05 * (1 - ease((t - (0.80 if i == 0 else 1.10)) / 0.12)); mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        x0, x1 = mx + (x0 - mx) * pop, mx + (x1 - mx) * pop; y0, y1 = my + (y0 - my) * pop, my + (y1 - my) * pop
        d.rectangle([x0, y0, x1, y1], outline=OR + (int(255 * a),), width=max(2, int(8 * s)))
    im.alpha_composite(ov)
    return np.asarray(im.convert("RGB")).astype(np.float32)

for f in range(N):
    t = f / FPS
    moving = 0.40 < t < 1.00 or 1.22 < t < 1.93
    if moving:                                    # true motion blur: average sub-frames across the shutter
        out = np.mean([render(t + d / FPS) for d in np.linspace(-0.4, 0.4, 8)], axis=0)
    else:
        out = render(t)
    enc.stdin.write(out.clip(0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait()
json.dump(dict(dur=DUR, b_start=B_START, b_end_time=DUR - B_START, glitch=0.28, pull=[0.35, 1.0], select0=0.80, select=1.10,
               push=[1.20, 1.95], land=1.95), open(OUT.replace(".mp4", ".json"), "w"))
print("cctv ok", N, "frames; B continues from", round(DUR - B_START, 3))
