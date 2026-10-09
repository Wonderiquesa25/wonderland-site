"""v13 picture (pre-intro timeline):
1) replace every leftover placeholder (re-used own footage) with the real continuous shot
2) B-roll stills with motivated transitions (zoom-punch entries, slide pushes, whip-in)
3) impact shake on the Joel cut
4) behind-the-subject typed text (Lourenço "A MELHOR SOLUÇÃO", Lima "MEDIMOS / MONTAMOS / AJUSTAMOS")"""
import subprocess, sys, os, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

S = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad"
D = f"{S}/v11"
J = f"{S}/scene1/joined.mp4"
IMG = f"{D}/canva"
W, H, FPS = 1080, 1920, 30
LOOK = "curves=all='0/0.03 0.25/0.22 0.5/0.5 0.78/0.81 1/0.95',colorbalance=rs=-0.01:bs=0.015:rh=0.02:gh=0.005:bh=-0.02,eq=saturation=0.95,vignette=angle=PI/7,noise=alls=4:allf=t"
ORANGE = (248, 168, 0)


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print(" ".join(c)[:400]); print(r.stderr[-2500:]); sys.exit(1)


def enc(out):
    return ["-c:v", "libx264", "-crf", "14", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "30", out]


def punch(s, cx, cy):
    w, h = round(W / s / 2) * 2, round(H / s / 2) * 2
    x = min(max(round(cx * W - w / 2), 0), W - w); y = min(max(round(cy * H - h / 2), 0), H - h)
    return f"crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos"


# 4) behind-the-subject typed text
from rembg import remove, new_session
sess = new_session("u2net_human_seg")
F_BIG = ImageFont.truetype(f"{S}/fonts/Oswald-Bold.ttf", 270)


def typed_layer(rows, t):
    """rows: list of (text, colour, y, t_start, t_end_typing); returns RGBA layer at time t."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for text, col, y, ts, te, fade_end in rows:
        if t < ts: continue
        k = int(len(text) * min(1, (t - ts) / max(te - ts, 1e-3)))
        alpha = 255 if t < fade_end - 0.2 else int(255 * max(0, (fade_end - t) / 0.2))
        if k <= 0 or alpha <= 0: continue
        s = text[:k]
        full_w = d.textbbox((0, 0), text, font=F_BIG)[2]
        x = (W - full_w) // 2
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((x + 8, y + 10), s, font=F_BIG, fill=(0, 0, 0, int(alpha * 0.45)))
        lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        d.text((x, y), s, font=F_BIG, fill=col + (alpha,))
        if k < len(text) and int(t * 6) % 2 == 0:      # blinking typing cursor
            cx = x + d.textbbox((0, 0), s, font=F_BIG)[2] + 10
            d.rectangle([cx, y + 60, cx + 14, y + 300], fill=ORANGE + (alpha,))
    return lay


EFFECTS = [
    ("lou", 16.40, 18.60, [("A MELHOR", (255, 255, 255), 40, 16.45, 16.95, 18.6),
                           ("SOLUÇÃO", ORANGE, 290, 17.10, 17.55, 18.6)]),
    ("lima", 50.40, 54.10, [("MEDIMOS", (255, 255, 255), 170, 50.50, 50.95, 54.1),
                            ("MONTAMOS", (255, 255, 255), 440, 51.93, 52.45, 54.1),
                            ("AJUSTAMOS", ORANGE, 710, 53.29, 53.80, 54.1)]),
]

def nfr(a, b): return round((b - a) * FPS)
key, a, b, rows = EFFECTS[0]
fdir = f"{D}/bt_lou2"; shutil.rmtree(fdir, ignore_errors=True); os.makedirs(fdir)
run(["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-i", f"{D}/picture13a.mp4", "-frames:v", str(nfr(a, b)), f"{fdir}/%04d.png"])
for j, fn in enumerate(sorted(os.listdir(fdir))):
    t = a + j / FPS
    fr = Image.open(f"{fdir}/{fn}").convert("RGB")
    m = remove(fr, session=sess, only_mask=True).filter(ImageFilter.GaussianBlur(1.5))
    out = fr.convert("RGBA"); out.alpha_composite(typed_layer(rows, t))
    subj = fr.convert("RGBA"); subj.putalpha(m); out.alpha_composite(subj)
    out.convert("RGB").save(f"{fdir}/{fn}")
run(["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", f"{fdir}/%04d.png"] + enc(f"{D}/bt_lou2.mp4"))
run(["ffmpeg", "-y", "-v", "error", "-i", f"{D}/picture13.mp4", "-itsoffset", str(a), "-i", f"{D}/bt_lou2.mp4", "-filter_complex",
     f"[0:v][1:v]overlay=enable='between(t,{a},{b - 0.001})':eof_action=pass,format=yuv420p[v]", "-map", "[v]"] + enc(f"{D}/picture14pre.mp4"))
print("ok")
