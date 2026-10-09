"""Cena 1 parts: stabilise -> per-frame person mask (temporally smoothed) -> low-key studio grade -> cleaned voice."""
import subprocess, sys, numpy as np, cv2
from PIL import Image
sys.path.insert(0, sys.argv[1])
from look import grade, W, H
from rembg import remove, new_session
S = sys.argv[1]; sess = new_session("u2net_human_seg")
SW, SH = 576, 1024
AUDIO = ("highpass=f=85,afftdn=nf=-28:tn=1,equalizer=f=280:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.0:g=2.5,"
         "equalizer=f=9000:t=q:w=1:g=1,deesser=i=0.35,acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=2,"
         "alimiter=limit=0.89,loudnorm=I=-16:TP=-1.5:LRA=9")


def run(c): subprocess.run(c, check=True)


for name in sys.argv[2:]:
    src = f"{S}/src/{name}.mp4"; stb = f"{S}/work/{name}_stab.mp4"; trf = f"{S}/work/{name}.trf"
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", f"vidstabdetect=shakiness=6:accuracy=12:result={trf}", "-f", "null", "-"])
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", f"vidstabtransform=input={trf}:smoothing=25:zoom=3:interpol=bicubic",
         "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-an", stb])
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vn", "-af", AUDIO, "-ar", "48000", f"{S}/work/{name}.wav"])
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", stb, "-vf", "hqdn3d=1.5:1.2:4:4", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "30", "-i", "-",
                            "-i", f"{S}/work/{name}.wav", "-vf", "noise=alls=3:allf=t", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{S}/out/{name}_estudio.mp4"],
                           stdin=subprocess.PIPE)
    prev = None; k = 0; FS = SW * SH * 3; ker = np.ones((5, 5), np.uint8); ring_k = np.ones((13, 13), np.uint8)
    TOP = np.clip((0.50 - np.arange(SH, dtype=np.float32) / SH) / 0.08, 0, 1)[:, None]
    while True:
        buf = dec.stdout.read(FS)
        if len(buf) < FS: break
        fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
        m = np.asarray(remove(Image.fromarray(fr), session=sess, only_mask=True), np.float32) / 255
        m = cv2.erode(m, ker)                                   # pull the edge in: no bright-wall halo
        # wall clean-up around the head: in a thin ring on the mask edge, drop pixels that are bright, grey wall
        ring = cv2.dilate(m, ring_k) - cv2.erode(m, ring_k)
        hsv = cv2.cvtColor(fr, cv2.COLOR_RGB2HSV).astype(np.float32)
        wall = np.clip((hsv[..., 2] - 175) / 40, 0, 1) * np.clip((40 - hsv[..., 1]) / 25, 0, 1) * TOP
        m = m * (1 - np.clip(ring, 0, 1) * wall)
        if prev is None: prev = m
        else:                                                   # temporal smoothing only when the mask is steady
            moving = float(np.abs(m - prev).mean()) > 0.012
            prev = m if moving else 0.75 * m + 0.25 * prev
        big = cv2.resize(fr, (W, H), interpolation=cv2.INTER_LANCZOS4)
        mm = cv2.GaussianBlur(cv2.resize(prev, (W, H)), (0, 0), 2.5)
        enc.stdin.write(grade(big, mm).tobytes()); k += 1
        if k % 150 == 0: print(name, k, flush=True)
    enc.stdin.close(); enc.wait(); dec.wait(); print(name, "done", k, flush=True)
