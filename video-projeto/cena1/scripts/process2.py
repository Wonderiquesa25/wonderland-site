"""Cena 1 v2: stabilised -> RVM matte (true black bg) -> face-targeted light + skin retouch -> clean voice (dual mono)."""
import subprocess, sys, os, numpy as np, cv2
sys.path.insert(0, sys.argv[1])
from look2 import Matte, Face, grade
from multiprocessing import Pool
W, H = 1080, 1920
S = sys.argv[1]; SW, SH = 576, 1024
AUDIO = ("pan=mono|c0=0.5*c0+0.5*c1,highpass=f=85,afftdn=nf=-30:tn=1,equalizer=f=280:t=q:w=1.2:g=-2.5,"
         "equalizer=f=3200:t=q:w=1.0:g=2.5,equalizer=f=9000:t=q:w=1:g=1,deesser=i=0.3,"
         "acompressor=threshold=-22dB:ratio=3:attack=8:release=120:makeup=2,alimiter=limit=0.89,loudnorm=I=-16:TP=-1.5:LRA=9,"
         "pan=stereo|c0=c0|c1=c0")


def run(c): subprocess.run(c, check=True)


def work(a): return grade(a[0], a[1], a[2], 1.0)


if __name__ != '__main__': sys.argv = sys.argv[:2]
for name in sys.argv[2:]:
    src = f"{S}/src/{name}.mp4"; stb = f"{S}/work/{name}_stab.mp4"; trf = f"{S}/work/{name}.trf"
    if not os.path.exists(stb):
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", f"vidstabdetect=shakiness=6:accuracy=12:result={trf}", "-f", "null", "-"])
        run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vf", f"vidstabtransform=input={trf}:smoothing=25:zoom=3:interpol=bicubic",
             "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-an", stb])
    wav = f"{S}/work/{name}_v2.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", src, "-vn", "-af", AUDIO, "-ar", "48000", wav])
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", stb, "-vf", "hqdn3d=1.5:1.2:4:4", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                           stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{SW}x{SH}", "-r", "30", "-i", "-",
                            "-i", wav, "-map", "0:v", "-map", "1:a", "-vf", f"scale={W}:{H}:flags=lanczos,unsharp=5:5:0.45:5:5:0,noise=alls=2:allf=t", "-c:v", "libx264", "-crf", "17",
                            "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
                            "-movflags", "+faststart", f"{S}/out/{name}_v2.mp4"], stdin=subprocess.PIPE)
    mt, fc = Matte(), Face(SW, SH); FS = SW * SH * 3

    def frames():
        first = True
        while True:
            buf = dec.stdout.read(FS)
            if len(buf) < FS: return
            fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
            if first:                                   # warm up the recurrent matte so frame 0 is already clean
                for _ in range(8): mt(fr)
                first = False
            fg, pha = mt(fr)
            yield fg, pha, fc(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))

    k = 0
    with Pool(3) as pool:
        for out in pool.imap(work, frames(), chunksize=4):
            enc.stdin.write(out.tobytes()); k += 1
            if k % 300 == 0: print(name, k, flush=True)
    enc.stdin.close(); enc.wait(); dec.wait(); print(name, "done", k, flush=True)
