# Trilha original jazz-funk / blues anos 70 (96 BPM, Fa menor), composta na grelha do video
# para os acentos (metais, pratos, viradas) cairem nas palavras e nos cortes.
# Sintese: GeneralUser GS (SoundFont livre para uso comercial) via tinysoundfont. Saida: stems WAV.
import os, sys, numpy as np, soundfile as sf, tinysoundfont
SF2 = os.environ.get('SF2', 'GeneralUser_GS_v1_471.sf2'); OUTD = os.environ.get('OUTD', 'stems')
SR = 48000; OFF = 0.4; BEAT = 0.625; DUR = 29.0
os.makedirs(OUTD, exist_ok=True)
def T(k): return OFF + BEAT * k
SW = 0.035  # swing nas semicolcheias
def step_t(bar, st):
    k = bar * 4 + st / 4
    if st % 2 == 1: k += SW
    return T(k)

VOIC = {'Fm9': [56, 63, 67, 72], 'Bb13': [56, 62, 67, 72], 'Bb9': [56, 60, 62, 65], 'Db9': [59, 63, 65, 68],
        'C7#9': [52, 58, 63, 67], 'Dbmaj7': [60, 65, 68, 73]}
ROOT = {'Fm9': 29, 'Bb13': 34, 'Bb9': 34, 'Db9': 37, 'C7#9': 36, 'Dbmaj7': 37}
CH = {0: ['Fm9', 'Fm9'], 1: ['Fm9', 'Bb13'], 2: ['Fm9', 'Fm9'], 3: ['Bb9', 'Bb13'], 4: ['Fm9', 'Fm9'],
      5: ['Db9', 'C7#9'], 6: ['Fm9', 'Fm9'], 7: ['Bb9', 'C7#9'], 8: ['Dbmaj7', 'C7#9'], 9: ['Fm9', 'Bb13'], 10: ['Fm9', 'Fm9']}
NBARS = 11
def chord(bar, st): return CH[bar][0 if st < 8 else 1]
CUTS = [8, 14, 21, 27, 32]          # cortes de cena (em batidas)
STABS = [2, 8, 13, 14, 20, 21, 27, 32, 33.5, 36]  # "CEO", cortes, "protegida", "protegemos", CTA, "PROTEGIDA?", numero
FINAL = 44

class Part:
    def __init__(self, bank, preset, drums=False, gain=0.0):
        self.s = tinysoundfont.Synth(gain=gain, samplerate=SR)
        sid = self.s.sfload(SF2)
        self.s.program_select(0, sid, bank, preset, is_drums=drums)
        self.ev = []
    def note(self, t, key, vel, dur):
        if t < 0 or t > DUR: return
        self.ev.append((t, 1, key, int(np.clip(vel, 1, 127)))); self.ev.append((min(t + dur, DUR), 0, key, 0))
    def render(self):
        self.ev.sort(key=lambda e: (e[0], e[1]))
        out = []; cur = 0
        for t, on, key, vel in self.ev:
            n = int(t * SR) - cur
            if n > 0: out.append(np.frombuffer(self.s.generate(n), np.float32).copy()); cur += n
            if on: self.s.noteon(0, key, vel)
            else: self.s.noteoff(0, key)
        n = int(DUR * SR) - cur
        if n > 0: out.append(np.frombuffer(self.s.generate(n), np.float32).copy())
        return np.concatenate(out).reshape(-1, 2)

rng = np.random.default_rng(70)
hum = lambda v, a=8: v + rng.integers(-a, a + 1)

# ---- bateria ----
dr = Part(128, 0, drums=True)
for bar in range(NBARS):
    k0 = bar * 4
    fill = (k0 + 4) in CUTS or (k0 + 4) == FINAL - 0 or bar == 7
    for st in range(16):
        t = step_t(bar, st)
        if T(k0 + st / 4) >= T(FINAL): break
        if st in (0, 7, 10): dr.note(t, 36, hum([118, 92, 104][(0, 7, 10).index(st)]), 0.2)
        if st in (4, 12) and not (fill and st == 12): dr.note(t, 38, hum(112), 0.2)
        if st in (6, 9, 15) and not fill: dr.note(t, 38, hum(34, 5), 0.1)
        if not (fill and st >= 12):
            if st == 14: dr.note(t, 46, hum(80), 0.18)
            else: dr.note(t, 42, hum(88 if st % 2 == 0 else 58), 0.08)
        if fill and st >= 12:  # virada de caixa e tons antes do corte
            dr.note(t, [38, 50, 47, 45][st - 12], 70 + (st - 12) * 14, 0.15)
for k in [2] + CUTS + [FINAL]:
    dr.note(T(k), 49, 112, 1.5); dr.note(T(k), 36, 120, 0.3)
dr.note(T(-0.5), 38, 60, 0.1); dr.note(T(-0.25), 38, 85, 0.1)  # entrada
dr.note(T(33.5), 49, 100, 1.0); dr.note(T(33.5), 38, 110, 0.2)
# rufo final
for j in range(12): dr.note(T(FINAL - 1) + j * BEAT / 12, 38, 50 + j * 5, 0.05)

# ---- baixo (funk, Fa menor) ----
bs = Part(0, 33)
BPAT = [(0, 0, 118, 3), (3, 0, 72, 1), (4, 12, 102, 2), (6, 10, 96, 1), (7, 12, 90, 2),
        (10, 0, 108, 2), (11, 3, 86, 1), (12, 5, 98, 1), (14, 7, 102, 1), (15, 10, 92, 1)]
for bar in range(NBARS):
    for st, iv, v, d in BPAT:
        if T(bar * 4 + st / 4) >= T(FINAL): break
        r = ROOT[chord(bar, st)] + 12
        bs.note(step_t(bar, st), r + iv, hum(v, 6), d * BEAT / 4 * 0.9)
bs.note(T(-0.5), 36, 90, 0.15); bs.note(T(-0.25), 39, 100, 0.15)
bs.note(T(FINAL), 29 + 12, 120, 1.0)

# ---- Rhodes (comping) ----
ep = Part(0, 4)
for bar in range(NBARS):
    for st, v, d in [(0, 80, 0.9), (6, 72, 0.25), (11, 76, 0.3), (14, 64, 0.2)]:
        if T(bar * 4 + st / 4) >= T(FINAL): break
        for n in VOIC[chord(bar, st)]: ep.note(step_t(bar, st), n, hum(v, 6), d)
for n in VOIC['Fm9']: ep.note(T(FINAL), n, 92, 1.0)

# ---- guitarra abafada (chicken scratch) ----
gt = Part(0, 28)
for bar in range(NBARS):
    for st in (2, 6, 10, 14, 15):
        if T(bar * 4 + st / 4) >= T(FINAL): break
        top = VOIC[chord(bar, st)][-2:]
        for n in top: gt.note(step_t(bar, st), n + 12 - 12, hum(78 if st != 15 else 55), 0.07)

# ---- orgao (cama quente) ----
og = Part(0, 16)
for bar in range(NBARS):
    for half in (0, 8):
        if T(bar * 4 + half / 4) >= T(FINAL): break
        for n in VOIC[chord(bar, half)][:3]: og.note(step_t(bar, half), n - 12, 42, BEAT * 2 * 0.98)
for n in [41, 44, 48, 51]: og.note(T(FINAL), n, 60, 1.0)

# ---- metais: golpes nas palavras-chave ----
br = Part(0, 61)
for k in STABS:
    bar = int(k // 4); st = int(round((k - bar * 4) * 4))
    v = VOIC[chord(min(bar, NBARS - 1), min(st, 15))]
    for n in [v[0] + 12, v[1] + 12, v[2] + 12, v[3] + 12]: br.note(T(k), n, 112, 0.2)
for n in [68, 72, 75, 79, 84]: br.note(T(FINAL), n, 122, 1.05)

# ---- sax tenor: frase blues no fim (quando a voz acaba) ----
sx = Part(0, 66)
LICK = [(40.75, 60, .2), (41.0, 63, .2), (41.25, 65, .2), (41.5, 66, .15), (41.67, 67, .5), (42.25, 70, .3),
        (42.5, 72, .55), (43.0, 70, .2), (43.25, 67, .2), (43.5, 65, .45)]
for k, n, d in LICK: sx.note(T(k), n, hum(100, 6), d * BEAT / 0.5 * 0.5)
sx.note(T(FINAL), 72, 110, 1.05)

parts = {'drums': dr, 'bass': bs, 'rhodes': ep, 'guitar': gt, 'organ': og, 'brass': br, 'sax': sx}
for name, p in parts.items():
    a = p.render()
    sf.write(f'{OUTD}/{name}.wav', a, SR)
    print(name, f'{np.abs(a).max():.2f}')
