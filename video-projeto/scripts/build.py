import subprocess, os, sys

S = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad"
D = f"{S}/v9"
J = f"{S}/scene1/joined.mp4"
C2 = f"{S}/scene1/c2_stab.mp4"
C3 = f"{S}/scene2/c3_stab.mp4"
C4 = f"{S}/scene3/c4_stab.mp4"
C5 = f"{S}/scene7/c5_stab.mp4"
LOGO = "/home/user/wonderland-site/brand/kukulu-logo@2x.png"

LOOK = "curves=all='0/0.03 0.25/0.22 0.5/0.5 0.78/0.81 1/0.95',colorbalance=rs=-0.01:bs=0.015:rh=0.02:gh=0.005:bh=-0.02,eq=saturation=0.95,vignette=angle=PI/7,noise=alls=4:allf=t"
N1 = "eq=gamma=0.96:contrast=1.03,colorbalance=rm=0.025:gm=-0.01:bm=-0.01"
N2 = "eq=brightness=0.02:gamma=1.5:contrast=1.14:saturation=1.08,colorbalance=rm=0.035:gm=-0.045:bm=0.0:rs=0.015:gs=-0.02,curves=g='0/0 0.5/0.48 1/0.98'"
OUT = "scale=1080:1920:flags=lanczos,unsharp=5:5:0.55,setsar=1,fps=30,format=yuv420p"
W, H = 1080, 1920


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-3000:]); sys.exit(1)


def punch(s, cx, cy):
    w, h = round(W / s / 2) * 2, round(H / s / 2) * 2
    x = min(max(round(cx * W - w / 2), 0), W - w)
    y = min(max(round(cy * H - h / 2), 0), H - h)
    return f"crop={w}:{h}:{x}:{y},scale={W}:{H}:flags=lanczos"


def push(s0, s1, cx, cy, frames, ease=False):
    p = f"pow(on/{frames},2)" if ease else f"(on/{frames})"
    z = f"{s0}+({s1}-{s0})*{p}"
    return (f"scale={W*2}:{H*2}:flags=lanczos,"
            f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{cx}*iw-iw/zoom/2))':"
            f"y='max(0,min(ih-ih/zoom,{cy}*ih-ih/zoom/2))':d=1:s={W}x{H}:fps=30")


def settle(s0, frames_settle, cx, cy):
    z = f"if(lt(on,{frames_settle}),{s0}-({s0}-1)*sin(PI/2*on/{frames_settle}),1)"
    return (f"scale={W*2}:{H*2}:flags=lanczos,"
            f"zoompan=z='{z}':x='max(0,min(iw-iw/zoom,{cx}*iw-iw/zoom/2))':"
            f"y='max(0,min(ih-ih/zoom,{cy}*ih-ih/zoom/2))':d=1:s={W}x{H}:fps=30")


G1 = f"{N1},{LOOK},{OUT}"                                  # clip1 / Mr Joel / Mr Lima grade
G3 = f"crop=464:825:0:3,{N1},{LOOK},{OUT}"                  # Lima+Joel grade
G2 = f"{N2},{LOOK},crop=360:640:67:60,{OUT}"                # Hilaria close grade

# (source, start, end, prefilter (grade or None for already-graded J), motion)
P = [
    (J, 0.0, 0.8, None, None),
    (J, 0.8, 2.4, None, None),
    (J, 2.4, 4.4, None, None),
    (J, 4.4, 6.5, None, punch(1.15, 0.55, 0.55)),
    (J, 6.5, 10.8, None, push(1.0, 1.08, 0.5, 0.4, 129)),
    (J, 10.8, 13.3, None, None),
    (J, 13.3, 15.8, None, punch(1.15, 0.5, 0.3)),
    (C2, 9.0, 10.2, G2, None),                                       # insert: her reaction
    (J, 17.0, 20.0, None, push(1.0, 1.06, 0.5, 0.3, 90)),
    (J, 20.0, 22.4, None, None),
    (C3, 12.2, 13.4, G3, punch(1.3, 0.55, 0.32)),                     # insert: brand vest
    (J, 23.6, 26.0, None, punch(1.15, 0.5, 0.3)),
    (J, 26.0, 28.4, None, None),
    (C3, 4.0, 5.2, G3, push(1.0, 1.06, 0.6, 0.35, 36)),              # insert: whiteboard
    (J, 29.6, 31.9, None, punch(1.12, 0.42, 0.35)),
    (J, 31.9, 34.3, None, None),
    (C4, 7.0, 8.2, G1, punch(1.7, 0.5, 0.27)),                       # insert: Mr Joel teaser
    (J, 35.5, 37.0, None, push(1.0, 1.15, 0.45, 0.3, 45, ease=True)),
    (C4, 1.0, 2.5, G1, settle(1.10, 12, 0.5, 0.4)),                  # Mr Joel (impact settle)
    (C4, 2.5, 3.95, G1, punch(1.12, 0.5, 0.4)),
    (C3, 1.764, 4.964, G3, push(1.0, 1.08, 0.5, 0.4, 96)),           # Lima + Joel (whip-in)
    (C5, 1.1, 3.0, G1, None),                                        # Mr Lima
    (C5, 3.0, 5.5, G1, punch(1.12, 0.55, 0.45)),
    (C5, 5.5, 8.0, G1, None),
    (C5, 8.0, 9.0, G1, punch(1.6, 0.68, 0.4)),
    (C5, 9.0, 12.0, G1, push(1.0, 1.12, 0.5, 0.35, 90, ease=True)),
]

WHIP_IN = 20  # index of Lima+Joel piece

files = []
for i, (src, a, b, pre, mot) in enumerate(P):
    n = round((b - a) * 30)
    chain = [f"trim=start={a}:end={b+0.2}", "setpts=PTS-STARTPTS"]
    if pre:
        chain.append(pre)
    else:
        chain.append("fps=30")
    if mot:
        chain.append(mot)
    if i == WHIP_IN:
        chain.append("avgblur=sizeX=60:sizeY=1:enable='lt(n,3)'")
        chain.append("avgblur=sizeX=24:sizeY=1:enable='between(n,3,5)'")
        chain.append("avgblur=sizeX=8:sizeY=1:enable='between(n,6,7)'")
    chain += [f"trim=end_frame={n}", "setpts=PTS-STARTPTS", "format=yuv420p"]
    out = f"{D}/p{i:02d}.mp4"
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src, "-an",
         "-vf", ",".join(chain), "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-r", "30", out])
    files.append(out)
    print(i, a, b, n)

# brand end card: logo fades/settles in on black, holds, fades out (2.2s)
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
     "-f", "lavfi", "-i", "color=c=black:s=1080x1920:r=30:d=2.2", "-loop", "1", "-t", "2.2", "-i", LOGO,
     "-filter_complex",
     "[1:v]scale=820:-1,format=rgba,fade=t=in:st=0.15:d=0.5:alpha=1,fade=t=out:st=1.7:d=0.5:alpha=1[l];"
     "[0:v][l]overlay=x=(W-w)/2:y=(H-h)/2,noise=alls=3:allf=t,format=yuv420p",
     "-frames:v", "66", "-c:v", "libx264", "-crf", "14", "-r", "30", f"{D}/p99.mp4"])
files.append(f"{D}/p99.mp4")

with open(f"{D}/list.txt", "w") as f:
    for p in files:
        f.write(f"file '{p}'\n")
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
     "-i", f"{D}/list.txt", "-c", "copy", f"{D}/picture.mp4"])
print("picture done")
