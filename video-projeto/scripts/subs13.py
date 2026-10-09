"""Kinetic subtitles inspired by the reference: yellow/orange main text with blur-in per word,
hook words in WHITE, bigger, with a bouncy grow/shrink pop and a slight playful tilt."""
import json, random

S = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad"
D = f"{S}/v11"
INTRO = 2.3
INTROS = [10.3, 20.0, 37.95, 54.1333]
MAIN, HOOK = "&H0000A8F8&", "&H00FFFFFF&"     # brand yellow-orange, white hooks
random.seed(3)


def fmap(t):
    return t + INTRO * sum(1 for T in INTROS if T < t)


tl = json.load(open(f"{S}/tr/transcript_large.json"))
fw = json.load(open(f"{S}/tr/film_words.json"))
hil = [[w["w"].strip(), w["s"] - 0.5, w["e"] - 0.5] for s in tl["02_hilaria_pes_na_mesa"] for w in s["words"]]
hil[6][0] = "ao"
lou = [[w["w"], w["s"], w["e"]] for w in fw[10:72]]
for i, t in {16: "de,", 18: "equipa,", 19: "planearmos", 20: "o", 21: "que", 37: "nas", 43: "No entanto,", 71: "a"}.items():
    lou[i - 10][0] = t
sol = [w for s in tl["01_eu_entrando"] for w in s["words"]][-1]
lou.append(["solução.", sol["s"] + 7.6, sol["e"] + 7.6])
joel = [[w["w"].strip(), w["s"] + 36.6, w["e"] + 36.6] for s in tl["03_joel_simao"] for w in s["words"]][1:]
lw = [[w["w"].strip(), w["s"] + 42.867, w["e"] + 42.867] for s in tl["05_lima"] for w in s["words"]]
lima = [["Kukulu,", 1.4 + 42.867, lw[0][2]], ["Kukulu…", lw[1][1], lw[1][2]]] + lw[8:]

# lines as token counts; hooks as token indices (within each speaker list)
plan = [
    (hil, [4, 5, 3], {9, 10, 11}),
    (lou, [3, 4, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 5, 2, 2, 5, 4, 3], {13, 14, 15, 39, 40, 41, 55, 62}),
    (joel, [4, 2], {4, 5}),
    (lima, [2, 2, 3], {0, 1, 3, 4, 5, 6}),
]


def ts(t):
    t = max(t, 0); return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


ev = []
for tokens, counts, hooks in plan:
    lines, i = [], 0
    for c in counts:
        lines.append(list(range(i, i + c))); i += c
    for li, idx in enumerate(lines):
        if (tokens is lou and li == 4) or (tokens is lima and li in (1, 2)):
            continue
        start = fmap(tokens[idx[0]][1]) - 0.06
        end = fmap(tokens[idx[-1]][2]) + 0.45
        if li + 1 < len(lines):
            end = min(end, fmap(tokens[lines[li + 1][0]][1]) - 0.06)
        for T in INTROS:
            Tf = T + INTRO * sum(1 for X in INTROS if X < T)
            if start < Tf:
                end = min(end, Tf - 0.02)
        has_hook = any(k in hooks for k in idx)
        style = ["blur", "pop", "flip", "grow"][(li + len(ev)) % 4]
        tilt = random.choice([-3, -2, 2, 3]) if has_hook else 0
        txt = "{\\an2\\move(540,1540,540,1515,0,350)\\fad(0,110)\\frz%d}" % tilt
        prev_hook = None
        for k in idx:
            word, ws, _ = tokens[k]
            a = max(int((fmap(ws) - start) * 1000), 0)
            hk = k in hooks
            if prev_hook is not None and hk != prev_hook:
                txt += "\\N"
            prev_hook = hk
            w = word if word.startswith("Kukulu") else word.lower()
            if hk:      # white hook, big, bouncy: 30% -> 128% -> 92% -> 100%
                txt += (f"{{\\c{HOOK}\\fs140\\bord8\\alpha&HFF&\\fscx30\\fscy30\\blur6"
                        f"\\t({a},{a + 1},\\alpha&H00&)\\t({a},{a + 130},\\fscx128\\fscy128\\blur0)"
                        f"\\t({a + 130},{a + 230},\\fscx92\\fscy92)\\t({a + 230},{a + 320},\\fscx100\\fscy100)}}{w} ")
            elif style == "blur":
                txt += (f"{{\\c{MAIN}\\fs100\\bord7\\alpha&HFF&\\fscx118\\fscy118\\blur10"
                        f"\\t({a},{a + 150},\\alpha&H00&\\fscx100\\fscy100\\blur0)}}{w} ")
            elif style == "pop":
                txt += (f"{{\\c{MAIN}\\fs100\\bord7\\alpha&HFF&\\fscx0\\fscy0"
                        f"\\t({a},{a + 1},\\alpha&H00&)\\t({a},{a + 120},\\fscx112\\fscy112)\\t({a + 120},{a + 200},\\fscx100\\fscy100)}}{w} ")
            elif style == "flip":
                txt += (f"{{\\c{MAIN}\\fs100\\bord7\\alpha&HFF&\\frx85"
                        f"\\t({a},{a + 60},\\alpha&H00&)\\t({a},{a + 180},\\frx0)}}{w} ")
            else:       # grow: rises from the baseline
                txt += (f"{{\\c{MAIN}\\fs100\\bord7\\alpha&HFF&\\fscy10"
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
Style: Main,Montserrat ExtraBold,100,&H0000A8F8,&H0000A8F8,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,6,3,2,60,60,400,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(f"{D}/subs13.ass", "w").write(head + "\n".join(ev) + "\n")
print(len(ev), "lines")
