# Mistura: voz original (tratada) + teclas das legendas + whoosh nos cortes + impacto seco quando cai cada recorte.
# Sem musica. -14 LUFS.
import os, json, subprocess, numpy as np, soundfile as sf
SR = 48000
VOZ = os.environ.get('VOZ', 'voz.wav'); SFX = os.environ.get('SFX', '../sfxlib/package/sounds')
EV = json.load(open(os.environ.get('EVENTS', 'crime_events.json'))); VID = os.environ.get('VID', 'crime_mudo.mp4')
OUT = os.environ.get('OUT', 'crime_final.mp4')
N = int(EV['dur'] * SR)
def load(p):
    a, sr = sf.read(p, dtype='float32', always_2d=True)
    if sr != SR:
        a = np.stack([np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a[:, c]) for c in range(a.shape[1])], 1)
    if a.shape[1] == 1: a = np.repeat(a, 2, 1)
    return a.astype(np.float32)
def place(buf, snd, t, g):
    i = int(t * SR)
    if 0 <= i < N: n = min(len(snd), N - i); buf[i:i + n] += snd[:n] * g
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', VOZ, '-af',
                'highpass=f=80,afftdn=nf=-25,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80',
                '-ar', str(SR), '_vc.wav'], check=True)
voice = np.zeros((N, 2), np.float32); place(voice, load('_vc.wav'), 0, 1.0)
voice /= np.abs(voice).max() + 1e-9; voice *= 0.75
rng = np.random.default_rng(5)
# impacto: grave curto (55 Hz a cair) + estalo de papel
tt = np.arange(int(0.55 * SR)) / SR
boom = np.sin(2 * np.pi * (55 * tt - 18 * tt ** 2)) * np.exp(-tt * 9)
crack = rng.normal(0, 1, len(tt)) * np.exp(-tt * 60)
crack = np.convolve(crack, np.ones(6) / 6, 'same')
thump = np.stack([boom * 0.9 + crack * 0.35] * 2, 1).astype(np.float32)
# whoosh: ruido filtrado com envolvente em sino
tw = np.arange(int(0.32 * SR)) / SR
nz = rng.normal(0, 1, len(tw)); env = np.sin(np.pi * tw / tw[-1]) ** 2
k = 1; out = np.zeros_like(nz)
for i in range(1, len(nz)):  # passa-baixo que abre e fecha (varrimento)
    a_ = 0.04 + 0.30 * env[i]; out[i] = out[i - 1] + a_ * (nz[i] - out[i - 1])
whoosh = np.stack([out * env, np.roll(out, 90) * env], 1).astype(np.float32); whoosh /= np.abs(whoosh).max()
fx = np.zeros((N, 2), np.float32)
keys = [load(f'{SFX}/mechanical/typing.mp3'), load(f'{SFX}/mechanical/press.mp3')]
def pitched(s, r):
    idx = np.arange(0, len(s) - 1, r); return np.stack([np.interp(idx, np.arange(len(s)), s[:, c]) for c in range(2)], 1).astype(np.float32)
last = -1
for t in sorted(EV['keys'] + EV['endkeys']):
    if t - last < 0.04: continue
    last = t; kk = keys[0] if rng.random() < 0.75 else keys[1]
    place(fx, pitched(kk, 0.9 + 0.2 * rng.random()), t, 0.085 * (0.7 + 0.5 * rng.random()))
for c in EV['cuts']: place(fx, whoosh, c - 0.16, 0.10)
for i, t in enumerate(EV['impacts']): place(fx, thump, t, 0.42 if i < 5 else 0.22)
mix = voice + fx; mix /= np.abs(mix).max() + 1e-9; mix *= 0.89
sf.write('_cmix.wav', mix, SR)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', VID, '-i', '_cmix.wav', '-filter_complex',
                f'[1:a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample={SR}[a]', '-map', '0:v', '-map', '[a]', '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-movflags', '+faststart', '-shortest', OUT], check=True)
print('ok')
