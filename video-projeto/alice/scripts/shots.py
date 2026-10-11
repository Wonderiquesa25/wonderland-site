"""Shot list on the voice-track timeline (seconds). src: Canva material time, or 'ladder' (the photo)."""
#        out_a  out_b  src_a   src_b   sky     mood     tol ymax  note
SHOTS = [
    (0.00,  2.85, 127.20, 129.20, "sky1", "night", 26, 1.00, "coil in the mirror (portal open)"),
    (2.85,  5.55, 15.40,  18.10,  "sky1", "night", 21, 0.31, "rooftop wire corner - de noite"),
    (5.55,  8.10, 5.00,   7.55,   "sky1", "night", 22, 0.35, "alley walls - residencia"),
    (8.10,  10.15, 132.00, 134.00, "sky1", "night", 18, 0.35, "industrial wall - empresa"),
    (10.15, 12.55, 125.00, 127.00, "sky1", "night", 24, 1.00, "protegida, ou nao?"),
    (12.55, 15.90, 25.40,  28.75,  "sky1", "day",   22, 0.25, "people / alley from above"),
    (15.90, 19.40, 33.00,  36.50,  "sky1", "cold",  26, 0.40, "graffiti wall - susto, o pior"),
    (19.40, 22.45, 128.60, 130.80, "sky1", "day",   26, 1.00, "a verdade"),
    (22.45, 24.10, 130.80, 132.00, "sky1", "day",   26, 1.00, "segundas chances (time-warp)"),
    (24.10, 27.55, 19.80,  23.25,  "sky1", "day",   22, 0.45, "seguranca de verdade"),
    (27.55, 31.25, 8.20,   11.90,  "sky1", "day",   22, 0.35, "muros altos ou arames"),
    (31.25, 33.35, 109.30, 111.40, "sky1", "day",   24, 1.00, "tecnologia certa (welder)"),
    (33.35, 35.65, "ladder", None,  "sky1", "day",   24, 0.42, "instalada do jeito certo"),
    (35.65, 39.35, 37.00,  40.70,  "sky1", "day",   24, 0.40, "esticar arame"),
    (39.35, 43.10, 45.00,  48.75,  "sky1", "day",   24, 1.00, "arames esticados"),
    (43.10, 46.25, 48.75,  51.90,  "sky1", "day",   24, 1.00, "voltagem"),
    (46.25, 50.30, 88.00,  92.05,  "sky1", "day",   26, 1.00, "da forma adequada"),
    (50.30, 52.55, 98.50,  100.75, "sky1", "day",   26, 1.00, "esticadores calibrados"),
    (52.55, 56.62, 113.00, 117.07, "sky1", "day",   26, 1.00, "aterramento"),
    (56.62, 59.10, 101.00, 103.48, "sky1", "day",   26, 1.00, "categoricamente"),
    (59.10, 63.70, 103.50, 108.10, "sky1", "day",   26, 1.00, "choque ... inutil"),
    (63.70, 68.70, 94.00,  99.00,  "sky1", "day",   26, 1.00, "o mais interessante"),
    (68.70, 71.60, 17.90,  20.80,  "sky1", "night", 20, 0.30, "ultrapassar aquele limite"),
    (71.60, 74.45, "ladder_wire", None, "sky1", "night", 24, 0.60, "electrocutado"),
    (74.45, 79.90, 77.00,  82.45,  "sky2", "gold",  26, 1.00, "resultado final, 100% blindado"),
    (79.90, 84.90, 28.80,  32.90,  "sky2", "gold",  22, 0.25, "a nossa equipa em acao"),
    (84.90, 89.78, 134.00, 137.60, "sky2", "gold",  20, 0.42, "nao e assim que as coisas comecam (portal close)"),
]
HANDLE = 0.5
TOTAL = 89.78
