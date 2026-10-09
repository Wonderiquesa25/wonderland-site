"""v11 sound: clean each speaker, keep only speech (gate by word timings), level every
speaker to -16 LUFS, pause dialogue during the four character intros, add original SFX."""
import json, subprocess, re, sys
import numpy as np

S = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad"
D = f"{S}/v11"
SR = 48000
INTRO = 2.3
CARD = 2.2
PRE_END = 54.1333                                   # end of Lima shot (pre-intro timeline)
INTROS = [10.3, 20.0, 37.95, PRE_END]                # insert points (pre-intro timeline)


def ff(args):
    r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args, capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-2000:]); sys.exit(1)


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def save(a, path):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", path],
                   input=a.astype(np.float32).tobytes(), check=True)


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])


# ---------- word timings on the pre-intro timeline ----------
tl = json.load(open(f"{S}/tr/transcript_large.json"))
fw = json.load(open(f"{S}/tr/film_words.json"))
words = {}
words["hil"] = [(w["s"] - 0.5, w["e"] - 0.5) for s in tl["02_hilaria_pes_na_mesa"] for w in s["words"]]
lou = [(w["s"], w["e"]) for w in fw if 10.5 < w["s"] < 37.3]
last = [w for s in tl["01_eu_entrando"] for w in s["words"]][-1]          # "solução"
lou.append((last["s"] + 7.6, last["e"] + 7.6))
words["lou"] = lou
words["joel"] = [(w["s"] + 36.6, w["e"] + 36.6) for s in tl["03_joel_simao"] for w in s["words"]]
words["lima"] = [(max(w["s"], 1.3) + 42.867, w["e"] + 42.867) for s in tl["05_lima"] for w in s["words"]]
json.dump(words, open(f"{D}/speech_words.json", "w"))


def gate(a, t0, spans, pre=0.12, post=0.22, merge=0.4, ramp=0.04):
    n = len(a); m = np.zeros(n, np.float32)
    iv = sorted((max(s - pre, t0), e + post) for s, e in spans)
    merged = []
    for s, e in iv:
        if merged and s - merged[-1][1] < merge:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    for s, e in merged:
        i0, i1 = int((s - t0) * SR), int((e - t0) * SR)
        m[max(i0, 0):max(min(i1, n), 0)] = 1
    k = int(ramp * SR); ker = np.ones(k, np.float32) / k
    m = np.convolve(m, ker, mode="same")
    return a * m[:, None]


# ---------- per-speaker segments (source, start, end on pre-intro timeline, chain) ----------
J = f"{S}/scene1/joined.mp4"
SEG = [
    ("hil", J, 0.0, 0.0, 10.45, "highpass=f=100,afftdn=nr=18:nf=-40:tn=1,lowpass=f=9000,acompressor=threshold=-26dB:ratio=3:attack=10:release=150:makeup=2"),
    ("lou", J, 10.45, 10.45, 37.6, "highpass=f=90,afftdn=nr=12:nf=-42:tn=1,lowpass=f=10000,acompressor=threshold=-26dB:ratio=3:attack=10:release=150:makeup=2"),
    ("joel", f"{S}/scene3/c4_stab.mp4", 1.0, 37.6, 40.7667, "highpass=f=90,afftdn=nr=12:nf=-42:tn=1,lowpass=f=10000,acompressor=threshold=-28dB:ratio=4:attack=8:release=150:makeup=2"),
    ("lima", f"{S}/scene7/c5_stab.mp4", 1.1, 43.9667, PRE_END, "highpass=f=90,afftdn=nr=10:nf=-42:tn=1,lowpass=f=11000,acompressor=threshold=-24dB:ratio=2.5:attack=10:release=200:makeup=1"),
]
total_pre = PRE_END
bed = np.zeros((int(round(total_pre * SR)), 2), np.float32)
for key, src, src_t0, t0, t1, chain in SEG:
    dur = t1 - t0
    ff(["-ss", str(src_t0), "-t", str(dur), "-i", src, "-vn", "-af", chain, "-ac", "2", "-ar", str(SR), f"{D}/c_{key}.wav"])
    a = load(f"{D}/c_{key}.wav")
    a = gate(a, t0, words[key])
    save(a, f"{D}/g_{key}.wav")
    gain = -16.0 - lufs(f"{D}/g_{key}.wav")
    a *= 10 ** (gain / 20)
    i0 = int(round(t0 * SR)); bed[i0:i0 + len(a)] += a[: len(bed) - i0]
    print(key, "gain", round(gain, 1), "dB")


# ---------- insert silent pauses for the intros ----------
def fmap(t, at_intro=False):
    k = sum(1 for T in INTROS if (T < t or (T <= t and not at_intro)))
    return t + INTRO * k


pieces, prev = [], 0.0
for T in INTROS:
    pieces.append(bed[int(round(prev * SR)):int(round(T * SR))])
    pieces.append(np.zeros((int(round(INTRO * SR)), 2), np.float32))
    prev = T
pieces.append(np.zeros((int(round(CARD * SR)), 2), np.float32))
dia = np.concatenate(pieces)
save(dia, f"{D}/dialogue11.wav")
TOTAL = len(dia) / SR

# ---------- SFX (pre-intro times; intro cues land on the intro start) ----------
cues = [("whoosh_big", 0.55, 1), ("thump", 4.4, 1), ("thump", 13.3, 1), ("thump", 23.6, 1), ("thump", 29.6, 1),
        ("whoosh_sm", 15.65, 1), ("whoosh_sm", 22.25, 1), ("whoosh_sm", 28.25, 1), ("whoosh_sm", 34.15, 1),
        ("riser", 36.2, 1), ("boom", 37.6, 1), ("whip", 40.467, 1), ("boom_soft", 40.767, 1),
        ("whoosh_sm", 43.82, 1), ("tick", 50.867, 1)]
final = []
for n, t, v in cues:
    final.append((n, fmap(t), v))
for T in INTROS:                                          # intro accents
    final.append(("whoosh_sm", fmap(T, True) - 0.12, 1))
    final.append(("boom_soft", fmap(T, True), 0.7))
final.append(("boom_end", fmap(PRE_END) + INTRO * 0, 1))  # cut to brand card
json.dump({"intros_final": [fmap(T, True) for T in INTROS], "card": fmap(PRE_END), "total": TOTAL},
          open(f"{D}/timeline.json", "w"))

inputs = ["-i", f"{D}/dialogue11.wav"]; parts = []
for i, (n, t, v) in enumerate(final, start=1):
    inputs += ["-i", f"{S}/v9/{n}.wav"]
    ms = int(t * 1000)
    parts.append(f"[{i}]volume={v},adelay={ms}|{ms}[s{i}]")
mix = "".join(f"[s{i}]" for i in range(1, len(final) + 1))
fc = ";".join(parts) + f";{mix}amix={len(final)}:normalize=0[sfx];[0][sfx]amix=2:normalize=0,alimiter=limit=0.85:level=false"
ff(inputs + ["-filter_complex", fc, "-t", f"{TOTAL:.4f}", "-ar", str(SR), f"{D}/mix11.wav"])
print("total", round(TOTAL, 3), "intros at", [round(fmap(T, True), 2) for T in INTROS], "card", round(fmap(PRE_END), 2))
