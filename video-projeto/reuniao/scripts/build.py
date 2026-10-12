"""Reunião (vídeo WhatsApp de 09/10) no estilo do filme da equipa.
- Recorte 9:16 que esconde as legendas antigas do CapCut, cor igual ao filme da equipa.
- Apresentações novas (cards.py): fala pára durante o cartão, nome digitado com som de teclado.
- Efeitos do CapCut retirados (rebobinar, flashes, desfoques, desenhos animados); entrada em câmara lenta limpa.
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

# Cada bloco: (áudio, peças de imagem). O áudio corre contínuo a partir de a0 durante a soma das peças.
# áudio: ("o", a0) original | ("card", nome, a0|None, máx) | ("end", a0)
# peças: ("v", t, dur, zoom) vídeo limpo | ("slow", t, dur, factor) câmara lenta (60 fps) | ("s", frame, dur) imagem parada com zoom lento
#        ("c", nome, dur) cartão | ("e", t, dur) cartão final do logótipo
# Sem efeitos do CapCut: rebobinar, flashes, recorte P&B, desfoques e desenhos animados trocados por imagem real.
SLOW = 1.86
PLAN = [
    (("o", 0.0), [("slow", 0.6, 0.85, SLOW), ("slow", 1.6, 0.35, SLOW),
                  ("slow", 2.9, 1.5, SLOW), ("slow", 5.6, 0.85, SLOW), ("v", 6.6, 0.3, 1.0)]),
    (("card", "eric", 6.9, 99), [("c", "eric", 2.85)]),
    (("o", 10.5), [("s", 11.4, 0.8), ("v", 11.3, 3.18, 1.0)]),
    (("o", 14.68), [("v", 14.68, 2.46, 1.06)]),
    (("o", 17.34), [("v", 17.34, 0.84, 1.0)]),
    (("o", 18.62), [("v", 18.62, 1.62, 1.06)]),
    (("o", 20.48), [("v", 20.48, 1.94, 1.0)]),
    (("o", 22.62), [("v", 22.62, 0.16, 1.06), ("s", 22.7, 0.62), ("v", 23.4, 1.05, 1.0)]),
    (("card", "joel", None, 0), [("c", "joel", 2.3)]),
    (("o", 25.0), [("s", 24.8, 2.55), ("v", 27.55, 1.7, 1.0), ("v", 29.4, 0.55, 1.0), ("s", 29.7, 1.75)]),
    (("card", "alberto", 31.85, 0.35), [("c", "alberto", 2.3)]),
    (("o", 33.3), [("s", 34.3, 0.95), ("v", 34.25, 4.87, 1.0)]),
    (("o", 39.42), [("v", 39.42, 1.56, 1.06)]),
    (("o", 41.22), [("v", 41.22, 1.98, 1.0), ("s", 43.0, 2.0)]),
    (("end", 62.57), [("e", 62.57, 2.2)]),
]
LOOK = ("crop=366:650:49:0,scale=1080:1920:flags=lanczos,unsharp=5:5:0.6,eq=gamma=0.97:contrast=1.04,"
        "curves=all='0/0.03 0.25/0.22 0.5/0.5 0.78/0.81 1/0.95',"
        "colorbalance=rs=-0.01:bs=0.015:rh=0.02:gh=0.005:bh=-0.02,vignette=angle=PI/7")


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


def piece(pc, out):
    k = pc[0]
    if k == "v":
        _, t, d, z = pc; n = round(d * FPS)
        run("-ss", str(t), "-i", f"{W}/src1080.mp4", "-frames:v", str(n), "-vf", zoom(z), *ENC, out)
    elif k == "slow":
        _, t, d, f = pc; n = round(d * f * FPS)
        run("-ss", str(t), "-t", str(d + 0.1), "-i", f"{W}/in.mp4", "-an", "-frames:v", str(n),
            "-vf", f"setpts={f}*(PTS-STARTPTS),fps={FPS},{LOOK},setsar=1", *ENC, out)
    elif k == "s":
        _, t, d = pc; n = round(d * FPS)
        run("-ss", str(t), "-i", f"{W}/src1080.mp4", "-frames:v", "1", out + ".png")
        run("-loop", "1", "-i", out + ".png", "-frames:v", str(n),
            "-vf", f"scale=2160:3840,zoompan=z='1.0+0.04*on/{n}':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*0.4':d={n}:s=1080x1920:fps={FPS},setsar=1",
            *ENC, out)
    elif k == "c":
        _, name, d = pc; n = round(d * FPS)
        run("-i", f"{W}/intro/{name}.mp4", "-frames:v", str(n), "-vf", "setsar=1", *ENC, out)
    else:
        _, t, d = pc; n = round(d * FPS)
        run("-ss", str(t), "-i", END, "-frames:v", str(n), "-vf", "scale=1080:1920,setsar=1", *ENC, out)
    return n


vids, auds, smap, cards = [], [], [], []
T = 0.0
for i, (au, pieces) in enumerate(PLAN):
    n = 0
    for j, pc in enumerate(pieces):
        out = f"{W}/seg/{i:02d}_{j}.mp4"
        n += piece(pc, out); vids.append(out)
    d = n / FPS; L = int(round(d * SR))
    if au[0] == "o":
        a0 = au[1]; aud = ORIG[int(a0 * SR): int(a0 * SR) + L]
        smap.append((a0, a0 + d, T))
    elif au[0] == "card":
        _, name, a0, mx = au
        aud = np.zeros((L, 2))
        if a0 is not None:
            x = ORIG[int(a0 * SR): int(a0 * SR) + int(min(mx, d) * SR)]
            aud[: len(x)] = x
        cards.append((name, T))
    else:
        aud = load(END, au[1], d)
        aud = aud / (np.abs(aud).max() + 1e-9) * 0.35          # nivelado mais abaixo
    aud = np.pad(aud, ((0, max(0, L - len(aud))), (0, 0)))[:L].copy(); f = int(0.012 * SR)
    aud[:f] *= np.linspace(0, 1, f)[:, None]; aud[-f:] *= np.linspace(1, 0, f)[:, None]
    auds.append(aud)
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
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", f"{REPO}/render/kukulu_reuniao_v2.mp4")
print("total", round(TOTAL, 2), "s ·", len(ev), "legendas")
