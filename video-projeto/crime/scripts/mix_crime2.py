# Mistura v2: voz (comeca em "Na madrugada") + Sonata ao Luar no ritmo + efeitos do inicio ao fim
# (sirenes, arrombamento, vidros, fotografias da policia/jornalistas, choro de familias e criancas),
# teclas das legendas, whoosh nos cortes e impactos dos recortes. Musica e efeitos baixam quando ha voz. -14 LUFS.
import os, json, subprocess, numpy as np, soundfile as sf
SR = 48000
VOZ = os.environ.get('VOZ', 'voz2.wav'); MUSICA = os.environ.get('MUSICA', 'musica.wav')
SFX = os.environ.get('SFX', '../sfxlib/package/sounds'); FX = os.environ.get('FX', 'sfx')
EV = json.load(open(os.environ.get('EVENTS', 'crime_events.json')))
VID = os.environ.get('VID', 'crime_mudo.mp4'); OUT = os.environ.get('OUT', 'crime_final.mp4')
N = int(EV['dur'] * SR); VEND = EV['vend']; WORDS = EV['words']; TQ = EV['T']
rng = np.random.default_rng(5)
def load(p):
    a, sr = sf.read(p, dtype='float32', always_2d=True)
    if a.shape[1] > 2: a = a[:, :2]
    if sr != SR:
        a = np.stack([np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a[:, c]) for c in range(a.shape[1])], 1)
    if a.shape[1] == 1: a = np.repeat(a, 2, 1)
    a = a.astype(np.float32); return a / (np.abs(a).max() + 1e-9)
def place(buf, snd, t, g, pan=0.0):
    i = int(t * SR)
    if i < 0: snd = snd[-i:]; i = 0
    if i < N:
        n = min(len(snd), N - i); lr = np.float32([1 - max(pan, 0), 1 + min(pan, 0)])
        buf[i:i + n] += snd[:n] * g * lr
def bed(snd, t0, t1, g, fade=1.5):  # som em loop entre t0 e t1 com fades
    n = int((t1 - t0) * SR); reps = int(np.ceil(n / len(snd))) + 1
    x = np.concatenate([snd] * reps)[:n].copy(); f = min(int(fade * SR), n // 2)
    x[:f] *= np.linspace(0, 1, f)[:, None]; x[-f:] *= np.linspace(1, 0, f)[:, None]
    return x, g
def w(word, after=0.0):
    for s, e, ww in WORDS:
        if s >= after and ww.lower().strip('.,?!') == word: return s
    raise KeyError(word)
# ---- voz ----
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', VOZ, '-af',
                'highpass=f=80,afftdn=nf=-25,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80',
                '-ar', str(SR), '_vc2.wav'], check=True)
voice = np.zeros((N, 2), np.float32); place(voice, load('_vc2.wav'), 0, 0.75)
env = np.sqrt(np.convolve(voice[:, 0] ** 2, np.ones(SR // 50) / (SR // 50), 'same'))
act = np.clip((20 * np.log10(env + 1e-9) + 42) / 14, 0, 1)            # 0 silencio .. 1 fala
k_up, k_dn = 1 - np.exp(-1 / (0.06 * SR)), 1 - np.exp(-1 / (0.45 * SR))
duck = np.zeros(N, np.float32); d = 0.0
step = 48
for i in range(0, N, step):                                            # seguidor de envolvente (ataque rapido, saida lenta)
    a_ = act[i]; d += ((k_up if a_ > d else k_dn) * step) * (a_ - d); duck[i:i + step] = d
# ---- musica ----
mus = np.zeros((N, 2), np.float32); place(mus, load(MUSICA), 0, 1.0)
tt = np.arange(N) / SR
mg = 0.40 * (1 - 0.45 * duck) * np.where(tt < VEND, 1.0, 1.0 + 0.9 * np.clip((tt - VEND) / 0.8, 0, 1))
mus *= mg[:, None]
# ---- efeitos ----
S = {k: load(f'{FX}/{f}.wav') for k, f in dict(wail='159753', yelp='223824', away='159745', mulher='364481', sob='319019',
     menina='243661', bebe1='425002', bebe2='402835', crianca='136480', mulher2='9428', crash1='249873', crash2='367624',
     vidro1='173601', vidro2='173559', porta='218888', foto1='270871', foto2='409096', foto3='72714').items()}
fx = np.zeros((N, 2), np.float32)
amb = np.zeros((N, 2), np.float32)
# camas continuas do inicio ao fim: sirenes ao longe + choro abafado (mais baixos na chamada para accao)
t_cta = EV['t_nao']
for snd, t0, t1, g, pan in [(S['wail'], 0, t_cta + 1, 0.10, -0.4), (S['away'], 2.0, t_cta + 1, 0.07, 0.5),
                            (S['menina'], 3.0, t_cta + 0.5, 0.06, 0.3), (S['wail'], t_cta, EV['dur'], 0.04, 0.0),
                            (S['menina'], t_cta, VEND + 1.5, 0.025, -0.3)]:
    x, gg = bed(snd, t0, t1, g); place(amb, x, t0, gg, pan)
lp = np.zeros_like(amb); a_ = 0.18                                     # ao longe: passa-baixo leve
for c in range(2):
    from scipy.signal import lfilter
    lp[:, c] = lfilter([a_], [1, a_ - 1], amb[:, c])
amb = lp * 2.0
def shutters(t, n, g=0.32):  # rajada de fotografias (policia / jornalistas) no ritmo da tercina
    for k in range(n): place(fx, S[('foto1', 'foto2', 'foto3')[k % 3]], t + k * TQ * (0.5 if k % 2 else 1) * 0.9, g * (0.8 + 0.3 * rng.random()), rng.uniform(-0.7, 0.7))
place(fx, S['yelp'][:int(4.5 * SR)], 0.0, 0.16)                       # abertura: sirene de invasao
place(fx, S['porta'], w('assaltantes') + 0.1, 0.55, -0.2)              # arrombamento da porta
place(fx, S['crash1'], w('armados') + 0.3, 0.38, 0.3)                  # coisas a partir
place(fx, S['porta'], w('invadido') + 0.05, 0.45, 0.25)
place(fx, S['crash2'], w('invadido') + 0.45, 0.35, -0.3)
shutters(w('o', 16.4) + 0.2, 6)                                         # cena do crime: fotografias
place(fx, S['vidro1'], w('morto'), 0.30, 0.2)
place(fx, S['yelp'][int(5 * SR):int(9 * SR)], w('esposa') - 0.2, 0.14, 0.4)
place(fx, S['mulher2'], w('baleados') - 0.1, 0.30, -0.3)                # choro das familias
place(fx, S['bebe1'], w('baleados') + 0.6, 0.24, 0.4)
place(fx, S['crianca'], w('família', w('pense')), 0.16, 0.35)
place(fx, S['vidro2'], w('tragédia') - 0.1, 0.34, -0.2)
place(fx, S['yelp'][int(9 * SR):int(12 * SR)], w('tragédia') + 0.3, 0.12, 0.3)
place(fx, S['porta'], w('fechar') + 0.4, 0.22, 0.3)
shutters(w('investigação') + 0.1, 7, 0.28)
place(fx, S['mulher'], w('dor') - 0.2, 0.30, -0.25)
place(fx, S['sob'], w('perdeu') - 0.1, 0.26, 0.3)
place(fx, S['bebe2'], w('alguém') + 0.1, 0.20, 0.45)
place(fx, S['crianca'][int(2 * SR):], w('trágica'), 0.12, -0.4)
place(fx, S['foto2'], w('câmaras') + 0.1, 0.30, 0.3)
tz = np.arange(int(0.5 * SR)) / SR                                     # estalo electrico da cerca (sintetizado)
zap = (np.sign(np.sin(2 * np.pi * 120 * tz)) * 0.5 + rng.normal(0, 0.6, len(tz))) * np.exp(-tz * 7) * (np.sin(2 * np.pi * 9 * tz) > -0.3)
place(fx, np.stack([zap, zap], 1).astype(np.float32), w('eléctrica') + 0.1, 0.22)
place(fx, S['yelp'][int(2 * SR):int(4 * SR)], w('alarme') + 0.1, 0.18, -0.2)
place(fx, S['porta'], w('atacar') + 0.1, 0.20, 0.2)
# teclas, whoosh nos cortes, impactos (graves) dos recortes + flash de camara
keys = [load(f'{SFX}/mechanical/typing.mp3'), load(f'{SFX}/mechanical/press.mp3')]
def pitched(s, r):
    idx = np.arange(0, len(s) - 1, r); return np.stack([np.interp(idx, np.arange(len(s)), s[:, c]) for c in range(2)], 1).astype(np.float32)
last = -1
for t in sorted(EV['keys'] + EV['endkeys']):
    if t - last < 0.04: continue
    last = t; kk = keys[0] if rng.random() < 0.75 else keys[1]
    place(fx, pitched(kk, 0.9 + 0.2 * rng.random()) * 0.6, t, 0.06 * (0.7 + 0.5 * rng.random()))
tt2 = np.arange(int(0.55 * SR)) / SR
boom = np.sin(2 * np.pi * (55 * tt2 - 18 * tt2 ** 2)) * np.exp(-tt2 * 9)
crack = np.convolve(rng.normal(0, 1, len(tt2)) * np.exp(-tt2 * 60), np.ones(6) / 6, 'same')
thump = np.stack([boom * 0.9 + crack * 0.35] * 2, 1).astype(np.float32)
tw = np.arange(int(0.32 * SR)) / SR; nz = rng.normal(0, 1, len(tw)); en = np.sin(np.pi * tw / tw[-1]) ** 2
o = np.zeros_like(nz)
for i in range(1, len(nz)): o[i] = o[i - 1] + (0.04 + 0.30 * en[i]) * (nz[i] - o[i - 1])
whoosh = np.stack([o * en, np.roll(o, 90) * en], 1).astype(np.float32); whoosh /= np.abs(whoosh).max()
for c in EV['cuts']: place(fx, whoosh, c - 0.16, 0.08)
for i, t in enumerate(EV['impacts']):
    place(fx, thump, t, 0.42 if i < 5 else 0.22); place(fx, S['foto1'], t + 0.02, 0.18, rng.uniform(-0.5, 0.5))
# efeitos baixam com a voz (para a fala ficar sempre clara)
fx *= (1 - 0.40 * duck)[:, None]; amb *= (1 - 0.35 * duck)[:, None]
mix = voice + mus + fx + amb
if os.environ.get('STEMS'):
    for nm, x in (('voz', voice), ('mus', mus), ('fx', fx), ('amb', amb)): sf.write(f'_stem_{nm}.wav', x, SR)
mix /= np.abs(mix).max() + 1e-9; mix *= 0.89
sf.write('_cmix2.wav', mix, SR)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', VID, '-i', '_cmix2.wav', '-filter_complex',
                f'[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample={SR}[a]', '-map', '0:v', '-map', '[a]', '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '256k', '-ac', '2', '-movflags', '+faststart', '-shortest', OUT], check=True)
print('ok')
