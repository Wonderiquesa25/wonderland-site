"""Cover v2: the Canva photo as hero (big), energetic slanted headline, orange banner, electric arcs + sparks."""
import sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC, FD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
rng = np.random.default_rng(7)
OR = (248, 168, 0); WH = (255, 255, 255)
MB = lambda s: ImageFont.truetype(f"{FD}/Montserrat-ExtraBold.ttf", s)
OS = lambda s: ImageFont.truetype(f"{FD}/Oswald-Bold.ttf", s)
src = np.asarray(Image.open(SRC).convert("RGB")).astype(np.float32)

def bolt(p0, p1, rough, depth=6):
    pts = [np.array(p0, float), np.array(p1, float)]
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            m = (a + b) / 2; n = np.array([-(b - a)[1], (b - a)[0]]); n /= np.linalg.norm(n) + 1e-9
            new += [m + n * rng.normal(0, rough * np.linalg.norm(b - a)), b]
        pts = new
    return np.array(pts, np.int32)

def energy(W, H, arcs, sparks):
    """additive light layer: glowing arcs (white core, orange halo) + spark burst"""
    core = np.zeros((H, W), np.float32)
    for p0, p1, w in arcs:
        for k in range(2):
            pts = bolt(p0, p1, 0.18)
            cv2.polylines(core, [pts], False, 1.0, w, cv2.LINE_AA)
            br = pts[rng.integers(len(pts) // 4, 3 * len(pts) // 4)]       # side branch
            cv2.polylines(core, [bolt(br, br + rng.normal(0, 60, 2) * (w / 2 + 1), 0.25, 4)], False, 0.8, max(1, w - 1), cv2.LINE_AA)
    for (cx, cy, n, L) in sparks:
        for _ in range(n):
            a = rng.uniform(0, 2 * np.pi); l = rng.uniform(0.2, 1) * L
            cv2.line(core, (cx, cy), (int(cx + np.cos(a) * l), int(cy + np.sin(a) * l)), rng.uniform(0.5, 1), 2, cv2.LINE_AA)
        cv2.circle(core, (cx, cy), 10, 1.0, -1, cv2.LINE_AA)
    halo = cv2.GaussianBlur(core, (0, 0), 14) * 2.2 + cv2.GaussianBlur(core, (0, 0), 50) * 2.5
    col = core[..., None] * np.array([255, 245, 220]) + halo[..., None] * np.array(OR)
    return col

def place_photo(W, H, h, x, y):
    s = cv2.resize(src, (int(src.shape[1] * h / src.shape[0]), h), interpolation=cv2.INTER_LANCZOS4)
    out = np.zeros((H, W, 3), np.float32); m = np.zeros((H, W), np.float32)
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + s.shape[1]), min(H, y + s.shape[0])
    out[y0:y1, x0:x1] = s[y0 - y:y1 - y, x0 - x:x1 - x]
    sw = s.shape[1]; ex = np.clip(np.minimum(np.arange(W) - x, x + sw - np.arange(W)) / (0.10 * sw), 0, 1)
    m[y0:y1, :] = 1; m *= ex[None, :]
    return out, m, s.shape[1]

def grade(img):
    img = img.clip(0, 255) / 255; img = np.clip(img * 1.12 + 0.02, 0, 1); img = img * img * (3 - 2 * img) * 0.25 + img * 0.75      # s-curve punch
    return (img * 255).clip(0, 255)

def headline(d, x, y, sz, lines):
    for t, c in lines:
        if c == "box":
            f = MB(sz); w = d.textlength(t, font=f); bh = int(sz * 1.08)
            d.polygon([(x - 20, y + 4), (x + w + 50, y + 4), (x + w + 20, y + bh + 14), (x - 50, y + bh + 14)], fill=OR)
            d.text((x, y - int(sz * 0.02)), t, font=f, fill=(0, 0, 0))
            y += bh + 40
        else:
            d.text((x, y), t, font=MB(sz), fill=c, stroke_width=max(4, sz // 30), stroke_fill=(0, 0, 0)); y += int(sz * 1.08)
    return y

def text_layer(W, H, draw_fn, angle):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); draw_fn(ImageDraw.Draw(L))
    L = L.rotate(angle, resample=Image.BICUBIC, center=(W // 2, H // 2))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); a = L.split()[3].filter(ImageFilter.GaussianBlur(18))
    sh.putalpha(a.point(lambda v: int(v * 0.85)))
    return sh, L

def compose(base, shadow, txt, off=(10, 14)):
    im = Image.fromarray(base.astype(np.uint8)).convert("RGBA")
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(shadow.split()[3])
    im.alpha_composite(blk, off); im.alpha_composite(txt); return im.convert("RGB")

# ================= 16:9 =================
W, H = 2560, 1440
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
bg = np.zeros((H, W, 3), np.float32) + 4
bg += np.exp(-(((x - 1900) / 900) ** 2 + ((y - 560) / 700) ** 2))[..., None] * np.array(OR) * 0.38
ph, m, pw = place_photo(W, H, 1900, 1240, -110)          # photo BIG: man fills right side
img = bg * (1 - m[..., None]) + np.maximum(ph, bg) * m[..., None]
# scale factor 1900/3055 on source coords -> arcs along the fence wires near the drill
k = 1900 / 3055; X = lambda u: int(1240 + u * k); Y = lambda v: int(-110 + v * k)
arcs = [((X(330), Y(560)), (X(1250), Y(860)), 4), ((X(330), Y(1190)), (X(1000), Y(1330)), 3), ((X(330), Y(860)), (X(820), Y(1000)), 3)]
img += energy(W, H, [], [(X(380), Y(1185), 46, 120)]) * 0.9
img = grade(img)
vg = 1 - 0.45 * np.clip(((x - 1500) / 1700) ** 2 + ((y - 720) / 1000) ** 2, 0, 1); img *= vg[..., None]
def draw16(d):
    d.polygon([(120, 120), (840, 120), (820, 205), (100, 205)], fill=WH)
    d.text((140, 124), "SEGURANÇA ELECTRÓNICA", font=OS(62), fill=(0, 0, 0))
    yy = headline(d, 130, 260, 178, [("A SUA CASA", WH), ("ESTÁ REALMENTE", WH), ("PROTEGIDA?", "box")])
    d.text((140, yy + 10), "CERCA ELÉCTRICA  •  INSTALAÇÃO PROFISSIONAL", font=OS(76), fill=OR, stroke_width=3, stroke_fill=(0, 0, 0))
sh, tx = text_layer(W, H, draw16, 3)
cv = compose(img, sh, tx)
cv.save(f"{OUT}/capa_youtube_16x9.png"); cv.save(f"{OUT}/capa_youtube_16x9.jpg", quality=93)
cv.resize((1280, 720), Image.LANCZOS).save(f"{OUT}/capa_youtube_1280x720.jpg", quality=92)

# ================= 9:16 =================
W, H = 1080, 1920
y, x = np.mgrid[0:H, 0:W].astype(np.float32)
bg = np.zeros((H, W, 3), np.float32) + 4 + np.exp(-(((x - 650) / 600) ** 2 + ((y - 700) / 650) ** 2))[..., None] * np.array(OR) * 0.4
ph, m, pw = place_photo(W, H, 1420, 20, 100)
img = bg * (1 - m[..., None]) + np.maximum(ph, bg) * m[..., None]
k = 1420 / 3055; X = lambda u: int(20 + u * k); Y = lambda v: int(100 + v * k)
arcs = [((X(330), Y(560)), (X(1300), Y(880)), 3), ((X(330), Y(1190)), (X(1000), Y(1330)), 3)]
img += energy(W, H, [], [(X(380), Y(1185), 36, 95)]) * 0.9
img = grade(img); img *= (1 - 0.88 * np.clip((y - 960) / 260, 0, 1))[..., None]
def draw9(d):
    d.polygon([(90, 70), (650, 70), (635, 142), (75, 142)], fill=WH); d.text((110, 72), "SEGURANÇA ELECTRÓNICA", font=OS(48), fill=(0, 0, 0))
    yy = headline(d, 90, 1190, 124, [("A SUA CASA", WH), ("ESTÁ", WH), ("REALMENTE", WH), ("PROTEGIDA?", "box")])
    d.text((95, yy + 2), "CERCA ELÉCTRICA • INSTALAÇÃO PROFISSIONAL", font=OS(44), fill=OR)
sh, tx = text_layer(W, H, draw9, 2)
compose(img, sh, tx, (7, 10)).save(f"{OUT}/capa_vertical_9x16.png")
print("ok")
