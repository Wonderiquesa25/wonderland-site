"""Animated captions (ASS): word-by-word pop on a lower rail (brand yellow-gold, Montserrat ExtraBold) with inline hook words
in Cinzel (ivory + violet glow), plus giant centre-screen hook words with scale/blur/tracking reveals. *word = inline hook."""
import sys
A = sys.argv[1]
PHRASES = [
 (0.00, 0.65, [("Me", 0.00), ("diz", 0.19), ("aí,", 0.43)]),
 (0.65, 2.66, [("quantas", 0.75), ("vezes", 1.57), ("de", 1.87)]),
 (3.31, 5.45, [("com", 3.31), ("a", 3.91), ("cabeça", 4.01), ("já", 4.45), ("na", 4.71), ("*almofada,", 4.87)]),
 (5.61, 6.81, [("ficou", 5.61), ("*preocupado", 6.11)]),
 (6.81, 8.03, [("se", 6.81), ("a", 6.93), ("sua", 7.03), ("*residência", 7.21)]),
 (8.03, 9.25, [("ou", 8.03), ("a", 8.53), ("sua", 8.63), ("*empresa", 8.83)]),
 (9.25, 10.54, [("estava", 9.25), ("realmente", 10.13)]),
 (11.59, 12.40, [("ou", 11.59), ("*não?", 12.05)]),
 (12.60, 14.23, [("A", 12.60), ("maioria", 12.95), ("das", 13.27), ("pessoas", 13.69)]),
 (14.23, 15.89, [("só", 14.23), ("pensa", 14.97), ("em", 15.39), ("*segurança", 15.51)]),
 (15.89, 17.44, [("depois", 15.89), ("do", 16.87)]),
 (17.97, 19.19, [("depois", 17.97), ("que", 18.17), ("o", 18.47), ("*pior", 18.57), ("acontece.", 18.77)]),
 (19.50, 21.37, [("Mas", 19.50), ("a", 19.89), ("*verdade", 20.60), ("é", 21.09), ("que", 21.27)]),
 (21.37, 22.42, [("a", 21.37), ("segurança", 21.43), ("não", 21.81), ("dá", 22.11)]),
 (24.00, 25.28, [("E", 24.00), ("segurança", 24.24), ("*de verdade,", 24.62)]),
 (25.56, 27.52, [("hoje", 25.56), ("em", 26.18), ("dia,", 26.30), ("já", 26.60), ("não", 26.80), ("é", 26.98), ("ter", 27.20)]),
 (27.52, 29.90, [("*muros", 27.52), ("altos", 27.94), ("ou", 28.74), ("*arames", 29.20)]),
 (29.90, 31.14, [("na", 29.90), ("sua", 30.10), ("residência.", 30.38)]),
 (31.20, 31.89, [("É", 31.20), ("ter", 31.44), ("a", 31.76)]),
 (33.14, 35.38, [("e", 33.14), ("instalada", 33.78), ("do", 34.60), ("*jeito certo.", 34.76)]),
 (36.05, 37.81, [("Muitos", 36.05), ("dizem", 36.83), ("que", 37.31), ("é", 37.47), ("só", 37.63)]),
 (37.81, 38.73, [("esticar", 37.81), ("*arame,", 38.17)]),
 (38.80, 39.80, [("mas", 38.80), ("*não,", 39.37)]),
 (39.91, 41.79, [("não", 39.91), ("trata-se", 40.65), ("só", 41.21), ("de", 41.45), ("ter", 41.63)]),
 (41.79, 42.87, [("*arames", 41.79), ("*esticados,", 42.21)]),
 (43.00, 44.44, [("é", 43.00), ("cálculo", 43.27), ("de", 44.09)]),
 (45.19, 46.03, [("adequado,", 45.19)]),
 (46.20, 48.71, [("é", 46.20), ("arames", 46.37), ("esticados", 47.89)]),
 (48.71, 50.27, [("da", 48.71), ("forma", 48.91), ("*adequada,", 49.27)]),
 (50.33, 52.53, [("*esticadores", 50.33), ("bem", 51.05), ("*calibrados,", 51.57)]),
 (53.19, 55.43, [("pois", 53.19), ("uma", 53.59), ("*cerca", 54.31), ("*eléctrica,", 54.63)]),
 (55.47, 56.61, [("se", 55.47), ("não", 55.67), ("tiver", 55.79), ("aterramento,", 56.05)]),
 (56.63, 58.21, [("podemos", 56.63), ("afirmar", 56.95), ("*categoricamente", 57.53)]),
 (58.21, 59.85, [("que", 58.21), ("o", 58.53), ("*choque", 59.09)]),
 (59.85, 62.04, [("daquela", 59.85), ("cerca", 60.59), ("eléctrica", 60.83), ("é", 61.41)]),
 (63.71, 65.61, [("Mas", 63.71), ("o", 64.29), ("mais", 64.87), ("*interessante", 65.11)]),
 (65.61, 66.43, [("não", 65.61), ("é", 65.89), ("isso,", 66.03)]),
 (66.57, 68.69, [("é", 66.57), ("ter", 66.99), ("a", 67.43), ("*certeza", 67.57), ("que", 68.07)]),
 (68.69, 71.08, [("quem", 68.69), ("tentar", 69.31), ("*ultrapassar", 69.89), ("aquele", 70.87)]),
 (72.10, 73.62, [("certamente", 72.10), ("será", 72.85)]),
 (74.60, 76.62, [("Ver", 74.60), ("o", 74.86), ("*resultado", 75.06), ("*final", 75.68)]),
 (76.62, 78.44, [("de", 76.62), ("um", 77.60), ("perímetro", 77.83)]),
 (79.91, 81.83, [("e", 79.91), ("a", 80.39), ("nossa", 80.57), ("*equipa", 80.79), ("em", 81.35), ("ação", 81.49)]),
 (81.83, 83.42, [("dá", 81.83), ("um", 82.55)]),
 (85.71, 87.01, [("Mas,", 85.71), ("bom,", 86.47)]),
 (87.15, 88.60, [("não", 87.15), ("é", 87.61), ("assim", 87.83), ("que", 88.09), ("as", 88.31), ("coisas", 88.39)]),
]
#        text                  start  end    colour   size
GIANTS = [("NOITE",            2.67,  4.10, "violet", 230),
          ("PROTEGIDA?",       10.55, 12.35, "gold",   175),
          ("SUSTO",            17.45, 18.70, "white",  240),
          ("SEGUNDAS\\NCHANCES", 22.43, 24.05, "violet", 170),
          ("TECNOLOGIA\\NCERTA", 31.90, 33.40, "gold",   165),
          ("VOLTAGEM",         44.45, 46.10, "violet", 190),
          ("ATERRAMENTO",      52.55, 54.00, "white",  145),
          ("INÚTIL",           62.05, 63.60, "white",  225),
          ("LIMITE",           71.09, 72.30, "violet", 230),
          ("ELECTROCUTADO",    73.63, 74.70, "white",  135),
          ("100%\\NBLINDADO",  78.45, 80.20, "gold",   185),
          ("ORGULHO\\NENORME", 83.43, 85.60, "gold",   180),
          ("COMEÇAM",          88.61, 89.78, "gold",   200)]

GOLD = "&H0000A8F8&"; WHITE = "&H00FFFFFF&"; VIOLET = "&H0000A8F8&"; VIOLET_DEEP = "&H00000000&"   # brand: orange #F8A800, white, black


def ts(x):
    x = max(0.0, x); h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60
    return f"{h}:{m:02d}:{s:05.2f}"


head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Rail,Montserrat ExtraBold,104,{GOLD},&H000000FF&,{VIOLET_DEEP},&H64000000&,0,0,0,0,100,100,1,0,1,6,5,2,60,60,330,1
Style: Glow,Montserrat ExtraBold,104,&HFF000000&,&H000000FF&,&H60B43CFF&,&HFF000000&,0,0,0,0,100,100,1,0,1,16,0,2,70,70,330,1
Style: Giant,Oswald,200,{WHITE},&H000000FF&,{VIOLET_DEEP},&H80000000&,-1,0,0,0,100,100,4,0,1,9,7,5,40,40,0,1
Style: GiantGlow,Oswald,200,&HFF000000&,&H000000FF&,&H40FF5AB4&,&HFF000000&,0,0,0,0,100,100,6,0,1,22,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
starts = [p[0] for p in PHRASES] + [999]
for i, (a, b, words) in enumerate(PHRASES):
    end = min(b + 0.45, starts[i + 1] - 0.02)
    parts, glow = [], []
    for w, wt in words:
        d = int((wt - a) * 1000)
        hook = w.startswith("*"); w = w.lstrip("*")
        if hook:
            tag = (f"{{\\fnMontserrat ExtraBold\\fs122\\c{WHITE}\\3c{VIOLET_DEEP}\\alpha&HFF&\\fscx70\\fscy70"
                   f"\\t({d},{d + 1},\\alpha&H00&)\\t({d},{d + 130},\\fscx122\\fscy122)\\t({d + 130},{d + 280},\\fscx100\\fscy100)}}")
            gtag = f"{{\\fnMontserrat ExtraBold\\fs122\\alpha&HFF&\\t({d},{d + 1},\\alpha&H50&)}}"
        else:
            tag = (f"{{\\fnMontserrat ExtraBold\\fs104\\c{GOLD}\\3c{VIOLET_DEEP}\\alpha&HFF&\\fscx80\\fscy80"
                   f"\\t({d},{d + 1},\\alpha&H00&)\\t({d},{d + 140},\\fscx100\\fscy100)}}")
            gtag = f"{{\\fnMontserrat ExtraBold\\fs104\\alpha&HFF&}}"
        parts.append(tag + w); glow.append(gtag + w)
    mv = f"{{\\fad(70,140)\\move(540,1610,540,1590,0,220)\\blur1.2}}"
    ev.append(f"Dialogue: 1,{ts(a)},{ts(end)},Rail,,0,0,0,,{mv}" + " ".join(parts))

from PIL import ImageFont
def fit(text, size):
    while size > 60:
        f = ImageFont.truetype(f"{A}/fonts/Oswald-Bold.ttf", size)
        wmax = max(f.getlength(line) + 4 * (len(line) - 1) for line in text.split("\\N"))
        if wmax <= 960: return size
        size -= 5
    return size
for text, a, b, col, size in GIANTS:
    size = fit(text, size)
    dur = int((b - a) * 1000)
    c = {"gold": GOLD, "white": WHITE, "violet": GOLD}[col]
    glowc = {"gold": "&H60000000&", "white": "&H3000A8F8&", "violet": "&H60000000&"}[col]
    anim = (f"\\an5\\pos(540,760)\\fs{size}\\fscx160\\fscy160\\fsp30\\blur14\\alpha&HFF&\\frx25"
            f"\\t(0,260,0.5,\\fscx100\\fscy100\\fsp4\\blur1\\alpha&H00&\\frx0)"
            f"\\t({dur - 220},{dur},\\fscx115\\fscy115\\blur10\\alpha&HFF&)")
    ev.append(f"Dialogue: 2,{ts(a)},{ts(b)},GiantGlow,,0,0,0,,{{{anim}\\3c{glowc}}}{text}")
    ev.append(f"Dialogue: 3,{ts(a)},{ts(b)},Giant,,0,0,0,,{{{anim}\\c{c}}}{text}")
open(f"{A}/captions_brand.ass", "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")
print("events", len(ev))
