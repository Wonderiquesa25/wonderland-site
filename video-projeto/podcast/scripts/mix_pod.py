# Mistura do video podcast: voz limpa + teclas das legendas + whoosh leve nos cortes. -14 LUFS.
import os, json, subprocess, numpy as np, soundfile as sf
SR = 48000
VOZ = os.environ.get('VOZ', 'a50.wav'); SFX = os.environ.get('SFX', 'sfxlib/package/sounds')
EV = json.load(open('pod_events.json')); VID = os.environ.get('VID', 'pod_mudo.mp4'); OUT = os.environ.get('OUT', 'pod_final.mp4')
SHIFT, DUR = EV['shift'], EV['dur']; N = int(DUR * SR)

def load(p):
    a, sr = sf.read(p, dtype='float32', always_2d=True)
    if sr != SR:
        a = np.stack([np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a[:, c]) for c in range(a.shape[1])], 1)
    if a.shape[1] == 1: a = np.repeat(a, 2, 1)
    return a.astype(np.float32)
def place(buf, snd, t, g):
    i = int(t * SR)
    if 0 <= i < N: n = min(len(snd), N - i); buf[i:i + n] += snd[:n] * g

subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', str(SHIFT), '-to', '50', '-i', VOZ, '-af',
                'highpass=f=80,afftdn=nf=-25,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,afade=t=out:st=%.2f:d=0.15' % (50 - SHIFT - 0.15),
                '-ar', str(SR), '_v.wav'], check=True)
voice = np.zeros((N, 2), np.float32); place(voice, load('_v.wav'), 0, 1.0)
voice /= np.abs(voice).max() + 1e-9; voice *= 0.75

keys = [load(f'{SFX}/mechanical/typing.mp3'), load(f'{SFX}/mechanical/press.mp3')]
rng = np.random.default_rng(5); fx = np.zeros((N, 2), np.float32); last = -1
def pitched(s, r):
    idx = np.arange(0, len(s) - 1, r); return np.stack([np.interp(idx, np.arange(len(s)), s[:, c]) for c in range(2)], 1).astype(np.float32)
for t in EV['keys']:
    if t - last < 0.04: continue
    last = t; k = keys[0] if rng.random() < 0.75 else keys[1]
    place(fx, pitched(k, 0.9 + 0.2 * rng.random()), t, 0.09 * (0.7 + 0.5 * rng.random()))
# teclas do cartao final
V = EV['vend']
for i in range(12): place(fx, keys[0], V + 0.3 + 0.05 * i, 0.12)
for i in range(9): place(fx, keys[0], V + 0.95 + 0.05 * i, 0.12)
for i in range(16): place(fx, keys[1], V + 1.7 + 0.044 * i, 0.12)
wh = load(f'{SFX}/cinematic/swipe.mp3')
for c in EV['cuts']: place(fx, wh, c - 0.15, 0.10)
mix = voice + fx
mix /= np.abs(mix).max() + 1e-9; mix *= 0.89
sf.write('_pmix.wav', mix, SR)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', VID, '-i', '_pmix.wav', '-filter_complex',
                f'[1:a]loudnorm=I=-14:TP=-1.5:LRA=9,aresample={SR}[a]', '-map', '0:v', '-map', '[a]', '-c:v', 'copy',
                '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-movflags', '+faststart', '-shortest', OUT], check=True)
print('ok')
