"""v14 picture on the FINAL timeline (1080x1920, no subtitles yet):
intros -> remove "casas" (28.60-29.333 s) -> new residence/shop slide at the cut -> hook zoom pulses ->
animated brand card -> character light & depth pass (subject lift, background separation)."""
import subprocess, sys, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

S = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad"
D = f"{S}/v11"
W, H, FPS = 1080, 1920, 30
C1F, C2F = 858, 880                     # frames removed ("casas")
CUT = (C2F - C1F) / FPS


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print(" ".join(c)[:300]); print(r.stderr[-2000:]); sys.exit(1)


def enc(out, crf="14"):
    return ["-c:v", "libx264", "-crf", crf, "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "30", out]


# 1+2) intros + cut
run(["ffmpeg", "-y", "-v", "error", "-i", f"{D}/picture14pre.mp4", "-i", f"{D}/intro/hilaria.mp4", "-i", f"{D}/intro/lourenco.mp4",
     "-i", f"{D}/intro/joel.mp4", "-i", f"{D}/intro/lima.mp4", "-filter_complex",
     "[0:v]trim=start_frame=0:end_frame=309,setpts=PTS-STARTPTS[a];[0:v]trim=start_frame=309:end_frame=600,setpts=PTS-STARTPTS[b];"
     "[0:v]trim=start_frame=600:end_frame=1139,setpts=PTS-STARTPTS[c];[0:v]trim=start_frame=1139:end_frame=1624,setpts=PTS-STARTPTS[d];"
     "[1:v]setpts=PTS-STARTPTS[i1];[2:v]setpts=PTS-STARTPTS[i2];[3:v]setpts=PTS-STARTPTS[i3];[4:v]setpts=PTS-STARTPTS[i4];"
     "[a][i1][b][i2][c][i3][d][i4]concat=n=8:v=1:a=0,fps=30,settb=1/30,split=2[x][y];"
     f"[x]trim=start_frame=0:end_frame={C1F},setpts=PTS-STARTPTS[p];[y]trim=start_frame={C2F},setpts=PTS-STARTPTS[q];"
     "[p][q]concat=n=2:v=1:a=0,format=yuv420p[v]", "-map", "[v]"] + enc(f"{D}/f14_cut.mp4"))
nframes = int(subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v", "-show_entries",
                              "stream=nb_read_packets", "-of", "csv=p=0", f"{D}/f14_cut.mp4"], capture_output=True, text=True).stdout)
print("cut ok", nframes, "frames")

# 3) residence -> shop slide re-timed around the cut
LOOK = "curves=all='0/0.03 0.25/0.22 0.5/0.5 0.78/0.81 1/0.95',colorbalance=rs=-0.01:bs=0.015:rh=0.02:gh=0.005:bh=-0.02,eq=saturation=0.95,vignette=angle=PI/7,noise=alls=4:allf=t"


def still(name, n, z0, z1, punch_in):
    base = f"{z0}+({z1}-{z0})*on/{n}"
    z = f"({base})*(1+0.30*pow(max(0,1-on/6),2))" if punch_in else base
    vf = (f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,zoompan=z='{z}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
          f":d=1:s={W}x{H}:fps=30,{LOOK}" + (",gblur=sigma=12:enable='lt(n,2)',gblur=sigma=5:enable='between(n,2,3)'" if punch_in else ""))
    out = f"{D}/s14_{name}.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", f"{D}/canva/{name}.png", "-vf", vf, "-frames:v", str(n)] + enc(out))
    return out


r = still("residencia", 38, 1.10, 1.0, True)        # 27.55 -> 28.80
l = still("loja", 34, 1.0, 1.06, False)             # 28.60 -> 29.733
run(["ffmpeg", "-y", "-v", "error", "-i", r, "-i", l, "-filter_complex", "[0][1]xfade=transition=slideleft:duration=0.2:offset=1.0667"]
    + enc(f"{D}/s14_pair.mp4"))
layers = [(f"{D}/s14_pair.mp4", 27.55)]

# 4) hook zoom pulses (final, post-cut times)
for k, tp in enumerate([9.22, 32.607, 38.267, 41.0, 46.287]):
    out = f"{D}/pulse{k}.mp4"
    z = "1+0.075*(1-pow(1-min(n/4,1),3))*exp(-max(n-4,0)/7)"
    run(["ffmpeg", "-y", "-v", "error", "-ss", str(tp), "-i", f"{D}/f14_cut.mp4", "-frames:v", "18", "-vf",
         f"scale=w='trunc(1080*({z})/2)*2':h=-2:eval=frame:flags=lanczos,crop=1080:1920"] + enc(out))
    layers.append((out, tp))

# 5) animated brand card (replaces the last 66 frames)
card_start = (nframes - 66) / FPS
logo = Image.open("/home/user/wonderland-site/brand/kukulu-logo@2x.png").convert("RGBA")
lw = 860; logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
cdir = f"{D}/card14"; os.makedirs(cdir, exist_ok=True)
yy, xx = np.mgrid[0:H, 0:W]
glow = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - H / 2) / 520) ** 2))
for i in range(66):
    t = i / FPS
    bg = np.zeros((H, W, 3), np.float32)
    g = glow * (0.10 + 0.05 * np.sin(t * 3))
    bg[..., 0] = 248 * g; bg[..., 1] = 168 * g
    img = Image.fromarray(bg.clip(0, 255).astype(np.uint8)).convert("RGBA")
    k = min(t / 0.35, 1)
    s = 0.78 + 0.22 * (1 - (1 - k) ** 3) + 0.05 * np.sin(np.pi * k) if k < 1 else 1.0
    L = logo.resize((int(logo.width * s), int(logo.height * s)), Image.LANCZOS)
    a = min(t / 0.15, 1) * (1 if t < 1.8 else max(0, (2.2 - t) / 0.4))
    L.putalpha(L.getchannel("A").point(lambda v: int(v * a)))
    if 0.45 < t < 1.25:                                     # light sweep through the logo
        sweep = Image.new("L", L.size, 0); d = ImageDraw.Draw(sweep)
        cx = int((t - 0.45) / 0.8 * (L.width + 400)) - 200
        d.polygon([(cx, 0), (cx + 90, 0), (cx - 60, L.height), (cx - 150, L.height)], fill=170)
        sweep = sweep.filter(ImageFilter.GaussianBlur(18))
        m = Image.fromarray((np.asarray(sweep, np.float32) * np.asarray(L.getchannel("A"), np.float32) / 255).astype(np.uint8))
        white = Image.new("RGBA", L.size, (255, 255, 255, 0)); white.putalpha(m); L.alpha_composite(white)
    img.alpha_composite(L, ((W - L.width) // 2, (H - L.height) // 2))
    img.convert("RGB").save(f"{cdir}/{i:04d}.png")
run(["ffmpeg", "-y", "-v", "error", "-framerate", "30", "-i", f"{cdir}/%04d.png", "-vf", "noise=alls=3:allf=t"] + enc(f"{D}/card14.mp4"))
layers.append((f"{D}/card14.mp4", card_start))

inputs = ["-i", f"{D}/f14_cut.mp4"]; fc = []; last = "0:v"
for k, (clip, st) in enumerate(layers, start=1):
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", clip],
                               capture_output=True, text=True).stdout)
    inputs += ["-itsoffset", f"{st}", "-i", clip]
    fc.append(f"[{last}][{k}:v]overlay=enable='between(t,{st},{st + dur - 0.001})':eof_action=pass[o{k}]"); last = f"o{k}"
run(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(fc) + f";[{last}]format=yuv420p[v]", "-map", "[v]"]
    + enc(f"{D}/f14_fx.mp4"))
print("fx ok, card at", round(card_start, 3))

# 6) character light & depth pass (skip intros and the brand card)
from rembg import remove, new_session
sess = new_session("u2net_human_seg")
SKIP = [(10.3, 12.6), (22.3, 24.6), (41.83, 44.13), (60.31, 99)]
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{D}/f14_fx.mp4", "-vf", "hqdn3d=1.2:1.0:3:3", "-f", "rawvideo",
                        "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
encp = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-"]
                        + enc(f"{D}/f14_lit.mp4"), stdin=subprocess.PIPE)
FS = W * H * 3
lut_s = np.clip(255 * (np.arange(256) / 255) ** 0.90 * 1.03, 0, 255).astype(np.uint8)   # gentle lift on people
prev_m, prev_i, i = None, -99, 0


def mask_of(fr):
    small = Image.fromarray(fr).resize((540, 960), Image.BILINEAR)
    m = np.asarray(remove(small, session=sess, only_mask=True), np.float32) / 255
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(m, (0, 0), 6)


while True:
    buf = dec.stdout.read(FS)
    if len(buf) < FS: break
    fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3)
    t = i / FPS
    if any(a <= t < b for a, b in SKIP):
        encp.stdin.write(buf); i += 1; continue
    if prev_m is None or i - prev_i >= 3:
        prev_m, prev_i = mask_of(fr), i
    m = prev_m[..., None]
    f = fr.astype(np.float32)
    subj = cv2.LUT(fr, lut_s).astype(np.float32)
    subj[..., 0] *= 1.015; subj[..., 2] *= 0.985                                  # warm, natural skin
    bg = cv2.GaussianBlur(f, (0, 0), 2.2) * 0.9
    grey = bg.mean(axis=2, keepdims=True); bg = grey + (bg - grey) * 0.9
    out = subj * m + bg * (1 - m)
    detail = f - cv2.GaussianBlur(f, (0, 0), 3)                                   # clarity on people only
    out += detail * 0.35 * m
    encp.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes()); i += 1
encp.stdin.close(); encp.wait(); dec.wait()
print("lit ok", i, "frames")
