import subprocess, sys

S = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad"
D = f"{S}/v9"
SR = 48000


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        print(" ".join(cmd)); print(r.stderr[-3000:]); sys.exit(1)


def ff(args):
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args)


# ---- original sounds (synthesised, royalty free) ----
def whoosh(name, d, gain):
    ff(["-f", "lavfi", "-i", f"anoisesrc=color=pink:sample_rate={SR}:d={d}:a=1",
        "-f", "lavfi", "-i", f"aevalsrc='0.5*sin(2*PI*(120*t+300*t*t/{d}))':s={SR}:d={d}",
        "-filter_complex",
        f"[0][1]amix=2:normalize=0,highpass=f=250,lowpass=f=5000,"
        f"volume='{gain}*pow(sin(PI*t/{d}),3)':eval=frame,aformat=channel_layouts=stereo,"
        f"aecho=0.8:0.5:40:0.25",
        "-ar", str(SR), f"{D}/{name}.wav"])


def boom(name, d, gain):
    ff(["-f", "lavfi", "-i",
        f"aevalsrc='{gain}*(sin(2*PI*(62*t-14*t*t))*exp(-3.2*t)+0.35*sin(2*PI*124*t)*exp(-9*t))':s={SR}:d={d}",
        "-f", "lavfi", "-i", f"anoisesrc=color=brown:sample_rate={SR}:d=0.08:a=1",
        "-filter_complex", f"[1]volume={gain*0.6},afade=t=out:d=0.08[c];[0][c]amix=2:normalize=0,"
        "lowpass=f=900,aformat=channel_layouts=stereo,aecho=0.8:0.6:120:0.3",
        "-ar", str(SR), f"{D}/{name}.wav"])


def riser(name, d, gain):
    ff(["-f", "lavfi", "-i", f"anoisesrc=color=white:sample_rate={SR}:d={d}:a=1",
        "-f", "lavfi", "-i", f"aevalsrc='0.4*sin(2*PI*(180*t+700*t*t/(2*{d})))':s={SR}:d={d}",
        "-filter_complex",
        f"[0]highpass=f=1500,volume=0.35[n];[n][1]amix=2:normalize=0,"
        f"volume='{gain}*pow(t/{d},2.2)':eval=frame,aformat=channel_layouts=stereo",
        "-ar", str(SR), f"{D}/{name}.wav"])


def thump(name, gain):
    ff(["-f", "lavfi", "-i", f"aevalsrc='{gain}*sin(2*PI*85*t)*exp(-22*t)':s={SR}:d=0.35",
        "-af", "aformat=channel_layouts=stereo", "-ar", str(SR), f"{D}/{name}.wav"])


whoosh("whoosh_big", 0.5, 0.45)
whoosh("whoosh_sm", 0.3, 0.3)
whoosh("whip", 0.6, 0.55)
boom("boom", 1.8, 0.9)
boom("boom_soft", 1.2, 0.45)
boom("boom_end", 2.6, 1.0)
riser("riser", 1.4, 0.55)
thump("thump", 0.38)
thump("tick", 0.3)

# ---- dialogue bed: previously approved, already cleaned/normalised audio ----
ff(["-i", f"{S}/cena1_v2.mp4", "-vn", "-af", "atrim=0:37.0,afade=t=out:st=36.99:d=0.01", "-ar", str(SR), "-ac", "2", f"{D}/d1.wav"])
ff(["-i", f"{S}/scene3/a3.wav", "-af", "atrim=1.0:3.96667,asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st=2.95667:d=0.01", "-ac", "2", f"{D}/d2.wav"])
ff(["-i", f"{S}/scene4/a2full.wav", "-af", "atrim=1.764:4.964,asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=3.18:d=0.02", "-ac", "2", f"{D}/d3.wav"])
ff(["-i", f"{S}/scene7/a5.wav", "-af", "atrim=1.1:12.0,asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=10.78:d=0.12", "-ac", "2", f"{D}/d4.wav"])
ff(["-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=stereo", "-t", "2.2", f"{D}/d5.wav"])
ff(["-i", f"{D}/d1.wav", "-i", f"{D}/d2.wav", "-i", f"{D}/d3.wav", "-i", f"{D}/d4.wav", "-i", f"{D}/d5.wav",
    "-filter_complex", "[0][1][2][3][4]concat=n=5:v=0:a=1", f"{D}/dialogue.wav"])

# ---- SFX placement (seconds on the new timeline) ----
cues = [
    ("whoosh_big", 0.55),
    ("thump", 4.4), ("thump", 13.3), ("thump", 23.6), ("thump", 29.6),
    ("whoosh_sm", 15.65), ("whoosh_sm", 22.25), ("whoosh_sm", 28.25), ("whoosh_sm", 34.15),
    ("riser", 35.6), ("boom", 37.0),
    ("whip", 39.67), ("boom_soft", 39.967),
    ("whoosh_sm", 43.02),
    ("tick", 50.067),
    ("boom_end", 54.067),
]
inputs = ["-i", f"{D}/dialogue.wav"]
parts = []
for i, (n, t) in enumerate(cues, start=1):
    inputs += ["-i", f"{D}/{n}.wav"]
    ms = int(t * 1000)
    parts.append(f"[{i}]adelay={ms}|{ms}[s{i}]")
mix = "".join(f"[s{i}]" for i in range(1, len(cues) + 1))
fc = ";".join(parts) + f";{mix}amix={len(cues)}:normalize=0[sfx];[0][sfx]amix=2:normalize=0,alimiter=limit=0.85:level=false"
ff(inputs + ["-filter_complex", fc, "-t", "56.2667", "-ar", str(SR), f"{D}/mix.wav"])
print("audio done")
