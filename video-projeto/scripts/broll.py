"""Overlay the Canva B-roll stills on the pre-intro picture (Ken Burns + film grade),
replacing some own-footage inserts; dialogue keeps running underneath."""
import subprocess, sys

S = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad"
D = f"{S}/v11"
IMG = f"{D}/canva"
LOOK = "curves=all='0/0.03 0.25/0.22 0.5/0.5 0.78/0.81 1/0.95',colorbalance=rs=-0.01:bs=0.015:rh=0.02:gh=0.005:bh=-0.02,eq=saturation=0.95,vignette=angle=PI/7,noise=alls=4:allf=t"

# (image, start, end, zoom from, zoom to, focus x, focus y)   pre-intro seconds
SLOTS = [
    ("planeamento", 14.0, 15.6, 1.00, 1.10, 0.5, 0.45),   # "como equipa, planearmos"
    ("residencia", 22.95, 24.0, 1.10, 1.00, 0.5, 0.5),    # "nas suas residências, casas"
    ("loja", 24.0, 25.85, 1.00, 1.10, 0.5, 0.5),          # "e estabelecimentos"
    ("vigilancia", 28.55, 29.95, 1.00, 1.12, 0.45, 0.4),  # "proteger os clientes"
    ("consulta", 34.1, 35.3, 1.08, 1.00, 0.5, 0.4),       # "a sua problemática"
    ("monitorizacao", 36.95, 37.6, 1.00, 1.08, 0.5, 0.5), # "a solução"
]


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2500:]); sys.exit(1)


clips = []
for name, a, b, z0, z1, fx, fy in SLOTS:
    n = round((b - a) * 30)
    z = f"{z0}+({z1}-{z0})*on/{n}"
    out = f"{D}/br_{name}.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", f"{IMG}/{name}.png", "-vf",
         f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
         f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{fx}*iw-iw/zoom/2))':y='max(0,min(ih-ih/zoom,{fy}*ih-ih/zoom/2))'"
         f":d=1:s=1080x1920:fps=30,{LOOK},format=yuv420p",
         "-frames:v", str(n), "-c:v", "libx264", "-crf", "14", out])
    clips.append((out, a, b))

inputs = ["-i", f"{D}/picture11.mp4"]
fc, last = [], "0:v"
for i, (out, a, b) in enumerate(clips, start=1):
    inputs += ["-itsoffset", str(a), "-i", out]
    fc.append(f"[{last}][{i}:v]overlay=enable='between(t,{a},{b - 0.001})':eof_action=pass[o{i}]")
    last = f"o{i}"
run(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", ";".join(fc) + f";[{last}]format=yuv420p[v]",
     "-map", "[v]", "-c:v", "libx264", "-crf", "14", "-preset", "medium", f"{D}/picture12.mp4"])
print("picture12 ok")
