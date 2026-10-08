"""Character intro: freeze frame, cut-out sticker with white outline + dark echo,
sepia halftone background, brand lower third (name box + typed role bar)."""
import subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from rembg import remove, new_session

S = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad"
D = f"{S}/v9/intro"
PIC = f"{S}/v9/picture.mp4"
FONTS = f"{S}/fonts"
W, H, FPS = 1080, 1920, 30

ORANGE = (248, 168, 0)
YELLOW = (255, 214, 0)
INK = (17, 17, 17)

# name, role, freeze frame time (source), overlay start, overlay end
CHARS = [
    ("lourenco", "Lourenço Sebastião", "CEO", 12.0, 11.0, 13.3),
    ("hilaria", "Hilária Mukango", "Secretária", 9.3, 3.4, 5.7),
    ("joel", "Joel Simão", "Técnico de Segurança Electrónica", 38.7, 37.5, 39.75),
    ("lima", "Lima", "Técnico de Segurança Electrónica", 52.3, 51.9, 54.0667),
]

session = new_session("u2net_human_seg")
f_name = ImageFont.truetype(f"{FONTS}/Oswald-Bold.ttf", 86)
f_role = ImageFont.truetype(f"{FONTS}/Montserrat-Bold.ttf", 38)


def grab(t):
    out = f"{D}/frame_{t}.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", PIC, "-frames:v", "1", out], check=True)
    return Image.open(out).convert("RGB")


def largest_component(mask):
    from scipy import ndimage
    lab, n = ndimage.label(mask > 127)
    if n == 0:
        return mask
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = np.argmax(sizes) + 1
    m = (lab == keep)
    m = ndimage.binary_fill_holes(m)
    return (m * 255).astype(np.uint8)


def halftone_bg(img):
    g = np.asarray(img.convert("L")).astype(np.float32) / 255.0
    cell = 11
    yy, xx = np.mgrid[0:H, 0:W]
    cy = (yy // cell) * cell + cell / 2
    cx = (xx // cell) * cell + cell / 2
    # darkness sampled at cell centre
    gs = g[np.clip(cy.astype(int), 0, H - 1), np.clip(cx.astype(int), 0, W - 1)]
    r = (1.0 - gs) * cell * 0.62
    dot = (np.hypot(yy - cy, xx - cx) < r).astype(np.float32)
    base = 0.55 + 0.45 * g                      # keep image legible under the dots
    lum = base * (1 - 0.55 * dot)
    sep = np.stack([lum * 1.0, lum * 0.86, lum * 0.70], -1) * 0.92
    return Image.fromarray((np.clip(sep, 0, 1) * 255).astype(np.uint8))


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def build(key, name, role, tf, t0, t1):
    frame = grab(tf)
    cut = remove(frame, session=session, only_mask=True)
    m = largest_component(np.asarray(cut))
    mask = Image.fromarray(m).filter(ImageFilter.GaussianBlur(1.2))
    outline = Image.fromarray(m).filter(ImageFilter.MaxFilter(31)).filter(ImageFilter.GaussianBlur(1.5))
    bg = halftone_bg(frame)

    # static layers at scale 1
    subject = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    subject.paste(frame, (0, 0), mask)
    white = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    white.putalpha(outline)
    echo = Image.new("RGBA", (W, H), (26, 20, 16, 0))
    echo.putalpha(outline.point(lambda v: int(v * 0.88)))

    # lower third geometry
    nb = f_name.getbbox(name)
    rb = f_role.getbbox(role)
    pad = 34
    name_w = nb[2] - nb[0] + pad * 2 + 14
    role_w = max(rb[2] - rb[0] + pad * 2, int(name_w * 0.62))
    box_h, bar_h = 118, 62
    y0 = int(H * 0.735)

    n = round((t1 - t0) * FPS)
    os.makedirs(f"{D}/{key}", exist_ok=True)
    for i in range(n):
        t = i / FPS
        canvas = bg.copy().convert("RGBA")
        # subject pop (1.06 -> 1.0 in 0.2s) then slow drift to 1.025
        s = 1.0 + 0.06 * (1 - ease_out(t / 0.2)) + 0.025 * (t / (n / FPS))
        def scaled(layer, dx=0, dy=0):
            lw, lh = int(W * s), int(H * s)
            l = layer.resize((lw, lh), Image.BICUBIC)
            canvas.alpha_composite(l, (int((W - lw) / 2 + dx), int((H - lh) / 2 + dy)))
        scaled(echo, -78, -34)
        scaled(white)
        scaled(subject)

        # lower third (in: 0.05-0.4s, out: last 0.25s)
        out_k = ease_out((t - (n / FPS - 0.28)) / 0.25)
        shift = -int(out_k * (max(name_w, role_w) + 40))
        d = ImageDraw.Draw(canvas)
        wn = int(name_w * ease_out((t - 0.05) / 0.32))
        if wn > 0:
            layer = Image.new("RGBA", (name_w, box_h), (255, 255, 255, 255))
            ld = ImageDraw.Draw(layer)
            ld.rectangle([0, 0, 12, box_h], fill=YELLOW)
            ld.text((pad + 14 - nb[0], (box_h - (nb[3] - nb[1])) / 2 - nb[1]), name, font=f_name, fill=INK)
            canvas.alpha_composite(layer.crop((0, 0, wn, box_h)), (shift, y0))
        wr = int(role_w * ease_out((t - 0.25) / 0.3))
        if wr > 0:
            chars = int(len(role) * min(max((t - 0.35) / 0.55, 0), 1))
            layer = Image.new("RGBA", (role_w, bar_h), ORANGE + (255,))
            ld = ImageDraw.Draw(layer)
            ld.text((pad - rb[0], (bar_h - (rb[3] - rb[1])) / 2 - rb[1]), role[:chars], font=f_role, fill=INK)
            canvas.alpha_composite(layer.crop((0, 0, wr, bar_h)), (shift, y0 + box_h))
        canvas.convert("RGB").save(f"{D}/{key}/{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", f"{D}/{key}/%04d.png",
                    "-vf", "noise=alls=4:allf=t,format=yuv420p", "-c:v", "libx264", "-crf", "15", f"{D}/{key}.mp4"], check=True)
    print(key, n, "frames")


only = sys.argv[1:]
for c in CHARS:
    if not only or c[0] in only:
        build(*c)
