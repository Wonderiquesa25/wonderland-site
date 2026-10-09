"""Animated ASS subtitles: word-by-word blur/scale pop, brand orange text, yellow highlights."""
import json

S = "/tmp/claude-0/-home-user-wonderland-site/50f38ae3-2900-5f56-9ef8-a960ab790e38/scratchpad"
D = f"{S}/v11"
INTRO = 2.3
INTROS = [10.3, 20.0, 37.95, 54.1333]
ORANGE, YELLOW = "&H0000A8F8&", "&H0000D6FF&"


def fmap(t):
    return t + INTRO * sum(1 for T in INTROS if T < t)


tl = json.load(open(f"{S}/tr/transcript_large.json"))
fw = json.load(open(f"{S}/tr/film_words.json"))

# (text, start, end) tokens on the pre-intro timeline
hil = [[w["w"].strip(), w["s"] - 0.5, w["e"] - 0.5] for s in tl["02_hilaria_pes_na_mesa"] for w in s["words"]]
hil[6][0] = "ao"                                   # "até ao nosso cliente" (PT)
lou = [[w["w"], w["s"], w["e"]] for w in fw[10:72]]
fix = {16: "de,", 18: "equipa,", 19: "planearmos", 20: "o", 21: "que", 37: "nas", 43: "No entanto,", 71: "a"}
for i, t in fix.items():
    lou[i - 10][0] = t
sol = [w for s in tl["01_eu_entrando"] for w in s["words"]][-1]
lou.append(["solução.", sol["s"] + 7.6, sol["e"] + 7.6])
joel = [[w["w"].strip(), w["s"] + 36.6, w["e"] + 36.6] for s in tl["03_joel_simao"] for w in s["words"]][1:]  # skip unclear first word
lima_w = [[w["w"].strip(), w["s"] + 42.867, w["e"] + 42.867] for s in tl["05_lima"] for w in s["words"]]
lima = [["Kukulu,", 1.4 + 42.867, lima_w[0][2]], ["Kukulu…", lima_w[1][1], lima_w[1][2]]] + lima_w[8:]

# line breaks (token counts) and highlighted tokens per speaker
plan = [
    (hil, [4, 5, 3], {"existe", "um", "processo."}),
    (lou, [3, 4, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 5, 2, 2, 5, 4, 3],
     {17: None}),
    (joel, [4, 2], {"ganham", "vida."}),
    (lima, [2, 2, 3], {"medimos,", "montamos", "e", "ajustamos."}),
]
# highlights for Lourenço by token index within his list
lou_hl = {13, 14, 15,            # a melhor solução
          39, 40, 41,            # proteger os clientes,
          62}                    # solução.


def ts(t):
    t = max(t, 0); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


events = []
for tokens, counts, hl in plan:
    i = 0
    lines = []
    for c in counts:
        lines.append(list(range(i, i + c))); i += c
    for li, idx in enumerate(lines):
        toks = [tokens[k] for k in idx]
        start = fmap(toks[0][1]) - 0.06
        nxt = fmap(tokens[lines[li + 1][0]][1]) - 0.06 if li + 1 < len(lines) else None
        end = fmap(toks[-1][2]) + 0.45
        if nxt is not None:
            end = min(end, nxt)
        for T in INTROS:                       # never run into an intro freeze
            Tf = T + INTRO * sum(1 for X in INTROS if X < T)
            if start < Tf:
                end = min(end, Tf - 0.02)
        txt = "{\\fad(0,120)}"
        for k in idx:
            word, ws, _ = tokens[k]
            a = max(int((fmap(ws) - start) * 1000), 0)
            is_hl = (k in lou_hl) if tokens is lou else (word in hl)
            col, size = (YELLOW, 100) if is_hl else (ORANGE, 86)
            txt += (f"{{\\c{col}\\fs{size}\\alpha&HFF&\\fscx120\\fscy120\\blur8"
                    f"\\t({a},{a + 140},\\alpha&H00&\\fscx100\\fscy100\\blur0)}}{word.lower() if not word.startswith('Kukulu') else word} ")
        events.append(f"Dialogue: 0,{ts(start)},{ts(end)},Main,,0,0,0,,{txt.strip()}")

head = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Montserrat ExtraBold,78,&H0000A8F8,&H0000A8F8,&H00000000,&H90000000,0,0,0,0,100,100,0,0,1,6,3,2,60,60,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
open(f"{D}/subs11.ass", "w").write(head + "\n".join(events) + "\n")
print(len(events), "lines")
for e in events[:3] + events[-4:]:
    print(e[:160])
