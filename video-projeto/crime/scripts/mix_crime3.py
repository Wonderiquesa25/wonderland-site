# Mistura v3 — som por cena (cue sheet): cada efeito so onde a imagem o pede (sirene so com policia/ambulancia/alarme),
# musica com plano de niveis, voz sempre clara. Junta o audio aos videos ja renderizados (copia o video, sem re-encode).
#   CUES=cue_final.json (saida do desenho de som) ; SOURCED=sourced.json (ficheiros com trim)
import os, re, json, subprocess, numpy as np, soundfile as sf
from scipy.signal import lfilter
SR = 48000
VOZ = os.environ.get('VOZ', 'voz2.wav'); MUSICA = os.environ.get('MUSICA', 'musica.wav')
SFXUI = os.environ.get('SFX', '../sfxlib/package/sounds')
EV = json.load(open(os.environ.get('EVENTS', 'crime_events.json')))
CUES = json.load(open(os.environ.get('CUES', 'cue_final.json')))
SRC = {s['category']: s['picks'] for s in json.load(open(os.environ.get('SOURCED', 'sourced.json')))}
OUTS = [x.split('=') for x in os.environ.get('MUX', 'kukulu_investigacao_4K_16x9.mp4=final_4k.mp4').split(',')]
N = int(EV['dur'] * SR); VEND = EV['vend']; TQ = EV['T']
rng = np.random.default_rng(5)
def load(p, t0=0.0, t1=None):
    a, sr = sf.read(p, dtype='float32', always_2d=True)
    a = a[int(t0 * sr):(int(t1 * sr) if t1 else None), :2]
    if sr != SR:
        a = np.stack([np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a[:, c]) for c in range(a.shape[1])], 1)
    if a.shape[1] == 1: a = np.repeat(a, 2, 1)
    return a.astype(np.float32)
def place(buf, snd, t, g=1.0, pan=0.0):
    i = int(round(t * SR))
    if i < 0: snd = snd[-i:]; i = 0
    if i < N and len(snd):
        n = min(len(snd), N - i); lr = np.float32([min(1, 1 - pan), min(1, 1 + pan)])
        buf[i:i + n] += snd[:n] * g * lr
def active_rms(x):
    m = x.mean(1); h = SR // 20
    fr = np.array([np.sqrt((m[i:i + h] ** 2).mean()) for i in range(0, max(len(m) - h, 1), h)]) + 1e-9
    top = np.sort(fr)[len(fr) // 2:]                      # metade mais energica = parte activa
    return float(np.sqrt((top ** 2).mean()))
# ---- voz (mesmo tratamento) ----
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', VOZ, '-af',
                'highpass=f=80,afftdn=nf=-25,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80',
                '-ar', str(SR), '_vc3.wav'], check=True)
v = load('_vc3.wav'); v /= np.abs(v).max() + 1e-9
voice = np.zeros((N, 2), np.float32); place(voice, v, 0, 0.75)
REF = active_rms(voice[:int(VEND * SR)])                  # 0 dB nos cues = tao forte como a voz
env = np.sqrt(np.convolve(voice[:, 0] ** 2, np.ones(SR // 50) / (SR // 50), 'same'))
act = np.clip((20 * np.log10(env + 1e-9) + 42) / 14, 0, 1)
k_up, k_dn = 1 - np.exp(-1 / (0.06 * SR)), 1 - np.exp(-1 / (0.45 * SR))
duck = np.zeros(N, np.float32); d = 0.0
for i in range(0, N, 48):
    d += ((k_up if act[i] > d else k_dn) * 48) * (act[i] - d); duck[i:i + 48] = d
# ---- musica com plano de niveis ----
LV = {'full': 0.62, 'under_voice': 0.40, 'low': 0.22, 'off': 0.0}
lvl = np.full(N, LV['under_voice'], np.float32)
for m in sorted(CUES['music'], key=lambda m: m['t0']):
    lvl[int(m['t0'] * SR):int(min(m['t1'], EV['dur']) * SR)] = LV[m['level']]
lvl = np.convolve(lvl, np.ones(SR // 2) / (SR // 2), 'same').astype(np.float32)   # rampas de 0,5 s
mus = np.zeros((N, 2), np.float32); mm = load(MUSICA); mm /= np.abs(mm).max() + 1e-9; place(mus, mm, 0)
mus *= (lvl * (1 - 0.40 * duck * (lvl > 0.3)))[:, None]
# ---- efeitos por cena ----
fx = np.zeros((N, 2), np.float32); used = {}
def pick_for(cue):
    m = re.match(r'\s*\[([^\]]+)\]', cue.get('why', ''))
    picks = SRC.get(cue['category'], [])
    if m:
        for p in picks:
            if os.path.basename(p['path']) == os.path.basename(m.group(1)): return p
        if os.path.exists(m.group(1)): return {'path': m.group(1), 'trim_start': 0, 'trim_end': None}
    return picks[0] if picks else None
for c in sorted(CUES['cues'], key=lambda c: c['t']):
    p = pick_for(c)
    if not p: print('sem ficheiro:', c['category'], c['t']); continue
    s = load(p['path'], p.get('trim_start') or 0, p.get('trim_end') or None)
    if not len(s): continue
    dur = max(0.05, float(c['dur']))
    if len(s) < dur * SR * 0.95 and dur > 2.5:             # ambiencias: loop com cruzamento
        xf = min(SR // 4, len(s) // 4); o = s.copy()
        while len(o) < dur * SR:
            r = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
            o[-xf:] = o[-xf:] * (1 - r) + s[:xf] * r; o = np.concatenate([o, s[xf:]])
        s = o
    s = s[:int(dur * SR)].copy()
    fi, fo = int(max(c.get('fade_in', 0), 0.005) * SR), int(max(c.get('fade_out', 0), 0.02) * SR)
    fi, fo = min(fi, len(s) // 2), min(fo, len(s) // 2)
    s[:fi] *= np.linspace(0, 1, fi)[:, None]; s[len(s) - fo:] *= np.linspace(1, 0, fo)[:, None]
    g = REF * 10 ** (c['gain_db'] / 20) / (active_rms(s) + 1e-9)
    place(fx, s, c['t'], g, float(np.clip(c.get('pan', 0), -1, 1)))
    used[p['path']] = p
# ---- teclas das legendas, whoosh discreto nos cortes, impactos dos recortes ----
keys = [load(f'{SFXUI}/mechanical/typing.mp3'), load(f'{SFXUI}/mechanical/press.mp3')]
keys = [k / (np.abs(k).max() + 1e-9) for k in keys]
def pitched(s, r):
    idx = np.arange(0, len(s) - 1, r); return np.stack([np.interp(idx, np.arange(len(s)), s[:, c]) for c in range(2)], 1).astype(np.float32)
ui = np.zeros((N, 2), np.float32); last = -1
for t in sorted(EV['keys'] + EV['endkeys']):
    if t - last < 0.04: continue
    last = t; kk = keys[0] if rng.random() < 0.75 else keys[1]
    place(ui, pitched(kk, 0.9 + 0.2 * rng.random()), t, 0.045 * (0.7 + 0.5 * rng.random()))
tt2 = np.arange(int(0.55 * SR)) / SR
boom = np.sin(2 * np.pi * (55 * tt2 - 18 * tt2 ** 2)) * np.exp(-tt2 * 9)
crack = np.convolve(rng.normal(0, 1, len(tt2)) * np.exp(-tt2 * 60), np.ones(6) / 6, 'same')
thump = np.stack([boom * 0.9 + crack * 0.35] * 2, 1).astype(np.float32)
tw = np.arange(int(0.32 * SR)) / SR; nz = rng.normal(0, 1, len(tw)); en = np.sin(np.pi * tw / tw[-1]) ** 2
o = np.zeros_like(nz)
for i in range(1, len(nz)): o[i] = o[i - 1] + (0.04 + 0.30 * en[i]) * (nz[i] - o[i - 1])
whoosh = np.stack([o * en, np.roll(o, 90) * en], 1).astype(np.float32); whoosh /= np.abs(whoosh).max()
for c in EV['cuts']: place(ui, whoosh, c - 0.16, 0.05)
for i, t in enumerate(EV['impacts']): place(ui, thump, t, 0.40 if i < 5 else 0.20)
fx *= (1 - 0.35 * duck)[:, None]
mix = voice + mus + fx + ui
if os.environ.get('STEMS'):
    for nm, x in (('voz', voice), ('mus', mus), ('fx', fx), ('ui', ui)): sf.write(f'_s3_{nm}.wav', x, SR)
mix /= np.abs(mix).max() + 1e-9; mix *= 0.89
sf.write('_cmix3.wav', mix, SR)
json.dump(used, open('_sfx_usados.json', 'w'), ensure_ascii=False, indent=1)
for vid, out in OUTS:   # copia o video (4K / TikTok) e poe o audio novo
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', vid, '-i', '_cmix3.wav', '-filter_complex',
                    f'[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample={SR}[a]', '-map', '0:v', '-map', '[a]', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '256k', '-ac', '2', '-movflags', '+faststart', '-shortest', out], check=True)
print('ok', len(used), 'ficheiros de efeitos')
