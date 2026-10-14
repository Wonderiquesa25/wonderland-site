# Mistura v2: voz sem pausas (+OFF) + trilha jazz-funk (stems, com ducking pela voz)
# + teclas (cada letra escrita) + whoosh nos cortes. Final -14 LUFS.
import os, json, subprocess, numpy as np, soundfile as sf
SR = 48000
STEMS = os.environ.get('STEMS', 'stems'); VOZ = os.environ.get('VOZ', 'vt48.wav'); SFX = os.environ.get('SFX', 'sfxlib/package/sounds')
EV = json.load(open(os.environ.get('EVENTS', 'events.json'))); VID = os.environ.get('VID', 'mudo2.mp4'); OUT = os.environ.get('OUT', 'final2.mp4')
OFF, DUR = EV['off'], EV['dur']; N = int(DUR * SR)

def load(p):
    a, sr = sf.read(p, dtype='float32', always_2d=True)
    if sr != SR:
        a = np.stack([np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a[:, c]) for c in range(a.shape[1])], 1)
    if a.shape[1] == 1: a = np.repeat(a, 2, 1)
    return a.astype(np.float32)
def fit(a):
    out = np.zeros((N, 2), np.float32); out[:min(N, len(a))] = a[:N]; return out
def place(buf, snd, t, g):
    i = int(t * SR)
    if i >= N or i < 0: return
    n = min(len(snd), N - i); buf[i:i + n] += snd[:n] * g

# voz: limpa com ffmpeg
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', VOZ, '-af',
                'highpass=f=80,afftdn=nf=-25,equalizer=f=3000:t=q:w=1:g=2,acompressor=threshold=-20dB:ratio=3:attack=5:release=80',
                '-ar', str(SR), '_voz.wav'], check=True)
v = load('_voz.wav'); voice = np.zeros((N, 2), np.float32); place(voice, v, OFF, 1.0)
voice /= np.abs(voice).max() + 1e-9; voice *= 0.7

# trilha
G = {'drums': 0.42, 'bass': 0.75, 'rhodes': 1.5, 'guitar': 1.0, 'organ': 2.2, 'brass': 0.55, 'sax': 0.85}
mus = sum(fit(load(f'{STEMS}/{k}.wav')) * g for k, g in G.items())
mus = np.tanh(mus * 1.2) / 1.2
# ducking: envelope da voz (ataque rapido, libertacao lenta)
env = np.abs(voice[:, 0]); hop = 480
fr = np.sqrt(np.convolve(env ** 2, np.ones(hop) / hop, 'same'))[::hop]
sm = np.zeros_like(fr); a_at, a_rel = 0.5, 0.06
for i in range(1, len(fr)):
    sm[i] = sm[i - 1] + (a_at if fr[i] > sm[i - 1] else a_rel) * (fr[i] - sm[i - 1])
duck = 1 - 0.62 * np.clip(sm / (np.percentile(sm[sm > 0.01], 70) + 1e-9), 0, 1)
duck = np.interp(np.arange(N), np.arange(len(duck)) * hop, duck)[:, None].astype(np.float32)
mus *= duck * 0.42

# efeitos: teclas de teclado moderno (variacao de som/volume/afinacao)
keys = [load(f'{SFX}/mechanical/typing.mp3'), load(f'{SFX}/mechanical/press.mp3'), load(f'{SFX}/minimal/press.mp3')]
def pitched(s, r):
    idx = np.arange(0, len(s) - 1, r); return np.stack([np.interp(idx, np.arange(len(s)), s[:, c]) for c in range(2)], 1).astype(np.float32)
rng = np.random.default_rng(3); fx = np.zeros((N, 2), np.float32)
last = -1
for t in EV['keys']:
    if t - last < 0.035: continue  # teclas demasiado juntas -> uma so
    last = t
    k = keys[0] if rng.random() < 0.7 else keys[rng.integers(1, 3)]
    place(fx, pitched(k, 0.92 + 0.16 * rng.random()), t, 0.16 * (0.7 + 0.5 * rng.random()))
wh = load(f'{SFX}/cinematic/swipe.mp3')
for c in EV['cuts']: place(fx, wh, c - 0.24, 0.32)
place(fx, wh, 0.0, 0.25)

mix = voice + mus + fx
mix /= np.abs(mix).max() + 1e-9; mix *= 0.89
sf.write('_mix.wav', mix, SR)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', VID, '-i', '_mix.wav', '-filter_complex',
                f'[1:a]afade=t=out:st={DUR - 0.6}:d=0.6,loudnorm=I=-14:TP=-1.5:LRA=9,aresample={SR}[a]',
                '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-movflags', '+faststart', '-shortest', OUT], check=True)
sf.write('_music_only.wav', mus / (np.abs(mus).max() + 1e-9) * 0.9 / np.maximum(duck, 0.38), SR)
print('ok')
