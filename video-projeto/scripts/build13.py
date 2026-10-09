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


layers = []   # (clip, start) full-frame overlays on the pre-intro timeline

# 1) placeholders -> continuous shot of Lourenço (same framing as the shot it interrupts)
for a, b, mot in [(15.8, 17.0, punch(1.15, 0.5, 0.3)), (22.4, 23.6, None), (28.4, 29.6, None), (34.3, 35.5, None)]:
    out = f"{D}/fix_{a}.mp4"; n = round((b - a) * FPS)
    vf = f"trim=start={a}:end={b + 0.1},setpts=PTS-STARTPTS,fps=30" + (f",{mot}" if mot else "") + f",trim=end_frame={n}"
    run(["ffmpeg", "-y", "-v", "error", "-i", J, "-an", "-vf", vf] + enc(out))
    layers.append((out, a))


# 2) B-roll
def still(name, n, z0, z1, fx, fy, entry="punch"):
    base = f"{z0}+({z1}-{z0})*on/{n}"
    z = f"({base})*(1+0.22*pow(max(0,1-on/6),2))" if entry == "punch" else base
    vf = (f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
          f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{fx}*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,{fy}*ih-ih/zoom/2))'"
          f":d=1:s={W}x{H}:fps=30,{LOOK}")
    if entry == "punch":
        vf += ",gblur=sigma=10:enable='lt(n,2)',gblur=sigma=4:enable='between(n,2,3)'"
    if entry == "whip":
        vf += (",avgblur=sizeX=70:sizeY=1:enable='lt(n,3)',avgblur=sizeX=28:sizeY=1:enable='between(n,3,5)'"
               ",avgblur=sizeX=8:sizeY=1:enable='between(n,6,7)'")
    out = f"{D}/st_{name}_{entry}.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", f"{IMG}/{name}.png", "-vf", vf, "-frames:v", str(n)] + enc(out))
    return out


def pair(a_clip, b_clip, dur_a, trans, out, d=0.2):
    run(["ffmpeg", "-y", "-v", "error", "-i", a_clip, "-i", b_clip, "-filter_complex",
         f"[0][1]xfade=transition={trans}:duration={d}:offset={dur_a - d}"] + enc(out))
    return out


def nfr(a, b): return round((b - a) * FPS)


layers.append((still("planeamento", nfr(14.0, 15.6), 1.0, 1.10, 0.5, 0.45), 14.0))
r = still("residencia", nfr(22.95, 24.2), 1.10, 1.0, 0.5, 0.5)
l = still("loja", nfr(24.0, 25.85), 1.0, 1.10, 0.5, 0.5, entry="none")
layers.append((pair(r, l, 1.25, "slideleft", f"{D}/pair_res_loja.mp4"), 22.95))
e = still("equipa", nfr(26.85, 28.75), 1.0, 1.08, 0.5, 0.45)
v = still("vigilancia", nfr(28.55, 29.95), 1.0, 1.12, 0.45, 0.4, entry="none")
layers.append((pair(e, v, 1.9, "zoomin", f"{D}/pair_eq_vig.mp4"), 26.85))
layers.append((still("consulta", nfr(34.1, 35.3), 1.08, 1.0, 0.5, 0.4), 34.1))
layers.append((still("monitorizacao", nfr(36.95, 37.6), 1.0, 1.08, 0.5, 0.5), 36.95))
i = still("instalacao", nfr(40.767, 42.567), 1.0, 1.08, 0.55, 0.35, entry="whip")
t = still("telemovel", nfr(42.367, 43.967), 1.08, 1.0, 0.35, 0.55, entry="none")
layers.append((pair(i, t, 1.8, "smoothup", f"{D}/pair_inst_tel.mp4"), 40.767))

# 3) impact shake on the Joel cut (first 10 frames of his shot)
shake = f"{D}/shake.mp4"
run(["ffmpeg", "-y", "-v", "error", "-ss", "37.6", "-i", f"{D}/picture11.mp4", "-frames:v", "10", "-vf",
     "scale=1140:2026,crop=1080:1920:x='30+26*sin(n*2.7)*exp(-n/3.5)':y='53+20*cos(n*3.1)*exp(-n/3.5)'"] + enc(shake))
layers.append((shake, 37.6))

# composite layers 1-3
inputs = ["-i", f"{D}/picture11.mp4"]; fc = []; last = "0:v"
for k, (clip, st) in enumerate(layers, start=1):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip],
                               capture_output=True, text=True).stdout)
    inputs += ["-itsoffset", f"{st}", "-i", clip]
    fc.append(f"[{last}][{k}:v]overlay=enable='between(t,{st},{st + dur - 0.001})':eof_action=pass[o{k}]"); last = f"o{k}"
run(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(fc) + f";[{last}]format=yuv420p[v]", "-map", "[v]"]
    + enc(f"{D}/picture13a.mp4"))
print("layers ok")

# 4) behind-the-subject typed text
from rembg import remove, new_session
sess = new_session("u2net_human_seg")
F_BIG = ImageFont.truetype(f"{S}/fonts/Oswald-Bold.ttf", 250)


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
    ("lou", 16.40, 18.60, [("A MELHOR", (255, 255, 255), 250, 16.45, 16.95, 18.6),
                           ("SOLUÇÃO", ORANGE, 520, 17.10, 17.55, 18.6)]),
    ("lima", 50.40, 54.10, [("MEDIMOS", (255, 255, 255), 170, 50.50, 50.95, 54.1),
                            ("MONTAMOS", (255, 255, 255), 440, 51.93, 52.45, 54.1),
                            ("AJUSTAMOS", ORANGE, 710, 53.29, 53.80, 54.1)]),
]
segs = []
for key, a, b, rows in EFFECTS:
    fdir = f"{D}/bt_{key}"; shutil.rmtree(fdir, ignore_errors=True); os.makedirs(fdir)
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(a), "-i", f"{D}/picture13a.mp4", "-frames:v", str(nfr(a, b)), f"{fdir}/%04d.png"])
    files = sorted(os.listdir(fdir))
    for j, fn in enumerate(files):
        t = a + j / FPS
        fr = Image.open(f"{fdir}/{fn}").convert("RGB")
        m = remove(fr, session=sess, only_mask=True).filter(ImageFilter.GaussianBlur(1.5))
        out = fr.convert("RGBA"); out.alpha_composite(typed_layer(rows, t))
        subj = fr.convert("RGBA"); subj.putalpha(m)
        out.alpha_composite(subj)
        out.convert("RGB").save(f"{fdir}/{fn}")
    clip = f"{D}/bt_{key}.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", f"{fdir}/%04d.png"] + enc(clip))
    segs.append((clip, a)); print(key, len(files), "frames")

inputs = ["-i", f"{D}/picture13a.mp4"]; fc = []; last = "0:v"
for k, (clip, st) in enumerate(segs, start=1):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip],
                               capture_output=True, text=True).stdout)
    inputs += ["-itsoffset", f"{st}", "-i", clip]
    fc.append(f"[{last}][{k}:v]overlay=enable='between(t,{st},{st + dur - 0.001})':eof_action=pass[o{k}]"); last = f"o{k}"
run(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(fc) + f";[{last}]format=yuv420p[v]", "-map", "[v]"]
    + enc(f"{D}/picture13.mp4"))
print("picture13 ok")
