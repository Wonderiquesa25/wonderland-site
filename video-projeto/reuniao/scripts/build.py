"""Reunião (vídeo WhatsApp de 09/10) no estilo do filme da equipa.
- Recorte 9:16 que esconde as legendas antigas do CapCut, cor igual ao filme da equipa.
- Apresentações novas (cards.py): fala pára durante o cartão, nome digitado com som de teclado.
- Pausas encurtadas, punch-in alternado nos cortes, legendas animadas palavra a palavra.
- Termina com o cartão do logótipo do filme da equipa.
Uso: python3 build.py <scratch>/wa   (precisa de in.mp4, src1080.mp4, orig.wav, w2.json, intro/)"""
import sys, json, subprocess, os
import numpy as np

W = sys.argv[1]
S = os.path.dirname(W)
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
END = f"{REPO}/render/cena2_final_1080p.mp4"
SFX = f"{S}/sfxlib/package/sounds"
SR, FPS = 48000, 30
os.makedirs(f"{W}/seg", exist_ok=True)

# (tipo, ...)  src: a, b, zoom | card: nome, dur, áudio | still: frame, a, b | end
PLAN = [
    ("src", 0.0, 6.9, 1.0),
    ("card", "eric", 2.85, (6.9, 9.75)),
    ("src2", 10.2, 9.75, 0.3),        # rebobinar sem o cartão antigo (imagem 10.2, som 9.75)
    ("src", 10.5, 14.48, 1.0),
    ("src", 14.68, 17.14, 1.08),
    ("src", 17.34, 18.18, 1.0),
    ("src", 18.62, 20.24, 1.08),
    ("src", 20.48, 22.42, 1.0),
    ("src", 22.62, 24.5, 1.08),
    ("card", "joel", 2.3, None),
    ("still", 24.8, 25.0, 27.25),
    ("src", 27.25, 31.55, 1.0),
    ("card", "alberto", 2.3, (31.85, 32.2)),
    ("still", 34.3, 33.3, 34.0),
    ("src", 34.0, 39.12, 1.0),
    ("src", 39.42, 40.98, 1.08),
    ("src", 41.22, 45.2, 1.0),
    ("end", 62.57, 64.77),
]


def run(*a):
    subprocess.run(["ffmpeg", "-y", "-v", "error", *a], check=True)


def load(p, ss=None, t=None):
    a = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss is not None else []) + (["-t", str(t)] if t else []) + \
        ["-i", p, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(a, capture_output=True).stdout, np.float32).reshape(-1, 2).astype(np.float64)


ORIG = load(f"{W}/orig.wav")
ENC = ["-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def zoom(z):
    return f"crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:(ih-ih/{z})*0.4,scale=1080:1920:flags=lanczos,setsar=1"


vids, auds, smap, cards = [], [], [], []
T = 0.0
for i, p in enumerate(PLAN):
    out = f"{W}/seg/{i:02d}.mp4"
    k = p[0]
    if k == "src":
        _, a, b, z = p
        n = round((b - a) * FPS); d = n / FPS
        run("-ss", str(a), "-i", f"{W}/src1080.mp4", "-frames:v", str(n), "-vf", zoom(z), *ENC, out)
        aud = ORIG[int(a * SR): int(a * SR) + int(d * SR)]
        smap.append((a, a + d, T))
    elif k == "src2":
        _, v0, a0, d = p
        n = round(d * FPS); d = n / FPS
        run("-ss", str(v0), "-i", f"{W}/src1080.mp4", "-frames:v", str(n), "-vf", zoom(1.0), *ENC, out)
        aud = ORIG[int(a0 * SR): int(a0 * SR) + int(d * SR)]
    elif k == "card":
        _, name, d, ar = p
        n = round(d * FPS); d = n / FPS
        run("-i", f"{W}/intro/{name}.mp4", "-frames:v", str(n), "-vf", "setsar=1", *ENC, out)
        aud = np.zeros((int(d * SR), 2))
        if ar:
            x = ORIG[int(ar[0] * SR): int(ar[1] * SR)]
            aud[: len(x)] = x[: len(aud)]
        cards.append((name, T))
    elif k == "still":
        _, ft, a, b = p
        n = round((b - a) * FPS); d = n / FPS
        run("-ss", str(ft), "-i", f"{W}/src1080.mp4", "-frames:v", "1", f"{W}/seg/still{i}.png")
        run("-loop", "1", "-i", f"{W}/seg/still{i}.png", "-frames:v", str(n),
            "-vf", f"scale=2160:3840,zoompan=z='1.0+0.05*on/{n}':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*0.4':d={n}:s=1080x1920:fps={FPS},setsar=1",
            *ENC, out)
        aud = ORIG[int(a * SR): int(a * SR) + int(d * SR)]
        smap.append((a, a + d, T))
    else:
        _, a, b = p
        n = round((b - a) * FPS); d = n / FPS
        run("-ss", str(a), "-i", END, "-frames:v", str(n), "-vf", "scale=1080:1920,setsar=1", *ENC, out)
        aud = load(END, a, d)
        aud = np.pad(aud, ((0, max(0, int(d * SR) - len(aud))), (0, 0)))[: int(d * SR)]
        aud = aud / (np.abs(aud).max() + 1e-9) * 0.35          # nivelado mais abaixo
    aud = aud.copy(); f = int(0.012 * SR)
    if len(aud) > 2 * f:
        aud[:f] *= np.linspace(0, 1, f)[:, None]; aud[-f:] *= np.linspace(1, 0, f)[:, None]
    vids.append(out); auds.append(aud)
    T += d
TOTAL = T

# ---- áudio: falas + música originais, teclado nos cartões, blip quando o cartão assenta ----
voice = np.concatenate(auds)
sfx = np.zeros_like(voice)
keys = json.load(open(f"{W}/intro/keys.json"))
rng = np.random.default_rng(5)
KEY = load(f"{SFX}/mechanical/typing.mp3"); KEY /= np.abs(KEY).max()
SPACE = load(f"{SFX}/mechanical/press.mp3"); SPACE /= np.abs(SPACE).max()
SEL = load(f"{SFX}/scifi/select.mp3"); SEL = SEL / np.abs(SEL).max() * 0.25


def place(bus, x, t, g=1.0):
    i = int(t * SR); x = x[: max(0, len(bus) - i)]; bus[i:i + len(x)] += x * g


for name, t0 in cards:
    for part, g in (("name", 0.42), ("role", 0.26)):
        for kt, ch in keys[name][part]:
            k = SPACE * 0.6 if ch == " " else KEY
            rate = rng.uniform(0.93, 1.08); idx = np.arange(0, len(k) - 1, rate)
            kk = np.stack([np.interp(idx, np.arange(len(k)), k[:, c]) for c in range(2)], 1)
            place(sfx, kk, t0 + kt - 0.012, g * rng.uniform(0.8, 1.1))
    place(sfx, SEL, t0 + keys[name]["role"][-1][0] + 0.05)

# falas mais à frente: leve compressão só na voz; depois mistura e normalização a -14 LUFS
mix = voice * 1.6 + sfx * 0.5
mix.astype(np.float32).tofile(f"{W}/mix.f32")
run("-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", f"{W}/mix.f32",
    "-af", "highpass=f=70,acompressor=threshold=-22dB:ratio=2.5:attack=8:release=120,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000",
    "-c:a", "pcm_s16le", f"{W}/mix.wav")


# ---- legendas (palavra a palavra, estilo do filme da equipa) ----
def fmap(t):
    for a, b, F in smap:
        if a - 1e-6 <= t <= b + 1e-6:
            return F + (t - a)
    nxt = [F for a, b, F in smap if a > t]
    return min(nxt) if nxt else TOTAL


words = json.load(open(f"{W}/w2.json"))
joel = []
for w, s, e in words["joel"]:
    if w.startswith("-"):
        joel[-1][0] += w; joel[-1][2] = e
    else:
        joel.append([w, s, e])
fix = {"Como": 10.82}                      # o 1.º "Como" vem colado ao efeito de rebobinar
for w in words["eric1"]:
    if w[0] in fix:
        w[1] = fix.pop(w[0])
PLAN_SUB = [
    ([[w, s, e] for w, s, e in words["eric1"]], [5, 3, 2, 4, 2, 3, 2], {8, 9, 20}),
    ([[w, s, e] for w, s, e in words["eric2"]], [3, 4, 3, 1, 3, 5, 2], {10}),
    (joel, [2, 2, 2, 3, 2, 2], {12}),
    ([[w, s, e] for w, s, e in words["alb"]], [3, 1, 3, 4, 4, 2, 3, 3, 1], {3, 15, 16, 17, 18, 19}),
]
words["eric2"][0][1] = 18.66                # "Então" começa depois da pausa cortada
MAIN, HOOK = "&H0000A8F8&", "&H00FFFFFF&"
card_starts = [t for _, t in cards] + [TOTAL - 2.2]


def ts(t):
    t = max(t, 0); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


ev = []
import random
random.seed(3)
for tokens, counts, hooks in PLAN_SUB:
    if tokens is PLAN_SUB[1][0]:
        tokens[0][1] = 18.66
    lines, i = [], 0
    for c in counts:
        lines.append(list(range(i, i + c))); i += c
    for li, idx in enumerate(lines):
        start = fmap(tokens[idx[0]][1]) - 0.06
        end = fmap(tokens[idx[-1]][2]) + 0.4
        if li + 1 < len(lines):
            end = min(end, fmap(tokens[lines[li + 1][0]][1]) - 0.06)
        for c in card_starts:
            if start < c:
                end = min(end, c - 0.03)
        has_hook = any(k in hooks for k in idx)
        style = ["blur", "pop", "flip", "grow"][(li + len(ev)) % 4]
        tilt = random.choice([-3, -2, 2, 3]) if has_hook else 0
        txt = "{\\an2\\move(540,1585,540,1555,0,350)\\fad(0,110)\\frz%d}" % tilt
        prev = None
        for k in idx:
            word, ws, _ = tokens[k]
            a = max(int((fmap(ws) - start) * 1000), 0)
            hk = k in hooks
            if prev is not None and hk != prev:
                txt += "\\N"
            prev = hk
            w = word.lower()
            if hk:
                txt += (f"{{\\c{HOOK}\\fs132\\bord10\\alpha&HFF&\\fscx30\\fscy30\\blur6"
                        f"\\t({a},{a + 1},\\alpha&H00&)\\t({a},{a + 130},\\fscx112\\fscy112\\blur0)"
                        f"\\t({a + 130},{a + 230},\\fscx95\\fscy95)\\t({a + 230},{a + 320},\\fscx100\\fscy100)}}{w} ")
            elif style == "blur":
                txt += (f"{{\\c{MAIN}\\fs108\\bord9\\alpha&HFF&\\fscx118\\fscy118\\blur10"
                        f"\\t({a},{a + 150},\\alpha&H00&\\fscx100\\fscy100\\blur0)}}{w} ")
            elif style == "pop":
                txt += (f"{{\\c{MAIN}\\fs108\\bord9\\alpha&HFF&\\fscx0\\fscy0"
                        f"\\t({a},{a + 1},\\alpha&H00&)\\t({a},{a + 120},\\fscx112\\fscy112)\\t({a + 120},{a + 200},\\fscx100\\fscy100)}}{w} ")
            elif style == "flip":
                txt += (f"{{\\c{MAIN}\\fs108\\bord9\\alpha&HFF&\\frx85"
                        f"\\t({a},{a + 60},\\alpha&H00&)\\t({a},{a + 180},\\frx0)}}{w} ")
            else:
                txt += (f"{{\\c{MAIN}\\fs108\\bord9\\alpha&HFF&\\fscy10"
                        f"\\t({a},{a + 60},\\alpha&H00&)\\t({a},{a + 170},\\fscy100)}}{w} ")
        ev.append(f"Dialogue: 0,{ts(start)},{ts(end)},Main,,0,0,0,,{txt.strip()}")

head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Montserrat ExtraBold,108,&H0000A8F8,&H0000A8F8,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,6,3,2,60,60,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(f"{W}/subs.ass", "w").write(head + "\n".join(ev) + "\n")

# ---- montagem final ----
with open(f"{W}/seg/list.txt", "w") as f:
    for v in vids:
        f.write(f"file '{v}'\n")
run("-f", "concat", "-safe", "0", "-i", f"{W}/seg/list.txt", "-c", "copy", f"{W}/pic.mp4")
run("-i", f"{W}/pic.mp4", "-i", f"{W}/mix.wav",
    "-vf", f"subtitles={W}/subs.ass:fontsdir={REPO}/fonts,noise=alls=3:allf=t,format=yuv420p",
    "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-b:v", "6M", "-maxrate", "8M", "-bufsize", "12M", "-preset", "slow",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", f"{REPO}/render/kukulu_reuniao_v1.mp4")
print("total", round(TOTAL, 2), "s ·", len(ev), "legendas")
