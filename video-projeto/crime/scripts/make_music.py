# Sonata ao Luar (Beethoven, Op. 27/2, 1.o and.) a partir do MIDI do piano-midi.de (CC BY-SA, B. Krueger),
# re-temporizada para pulsacao fixa (tercina = T s) e tocada com amostras FluidR3_GM (MIT): piano + violino na
# melodia + violoncelo no baixo, com reverb. Gera musica.wav e grelha de tempos (grid.json) para sincronizar o video.
import os, sys, json, subprocess, numpy as np, soundfile as sf
SR = 48000
T = float(os.environ.get('T', '0.32')); L = float(os.environ.get('LEN', '83'))
MUS = os.environ.get('MUS', 'mus')
N = json.load(open(f'{MUS}/mond1.json'))
# ancoras: notas curtas do arpejo (tercinas continuas) -> j*T
arp = sorted({round(n['start'], 3) for n in N if 52 <= n['pitch'] <= 76 and n['end'] - n['start'] < 0.6})
anc = [arp[0]]
for t in arp[1:]:
    if t - anc[-1] > 0.2: anc.append(t)
anc = np.array(anc); idx = np.arange(len(anc)) * T
def warp(t): return float(np.interp(t, anc, idx, right=idx[-1] + (t - anc[-1])))
cache = {}
def sample(inst, p):
    k = (inst, p)
    if k not in cache:
        f = f'{MUS}/{inst}/{p}.mp3'
        raw = subprocess.run(['ffmpeg', '-loglevel', 'error', '-i', f, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'], capture_output=True).stdout
        cache[k] = np.frombuffer(raw, np.float32).copy()
    return cache[k]
out = {i: np.zeros(int((L + 6) * SR), np.float32) for i in ('pno', 'vln', 'vc')}
def put(buf, s, t0, dur, g, rel):
    n = min(len(s), int((dur + rel) * SR)); x = s[:n].copy()
    if n > int(dur * SR):
        r = n - int(dur * SR); x[-r:] *= np.exp(-np.linspace(0, 6, r))
    i = int(t0 * SR)
    if i < len(buf): m = min(n, len(buf) - i); buf[i:i + m] += x[:m] * g
def loop(s, dur):  # violino/violoncelo: prolonga amostras curtas com loop cruzado
    need = int((dur + 0.6) * SR)
    if len(s) >= need: return s
    a0, a1 = int(0.25 * len(s)), int(0.85 * len(s)); seg = s[a0:a1]; xf = min(2400, len(seg) // 4)
    o = s[:a1].copy()
    while len(o) < need:
        r = np.linspace(0, 1, xf, dtype=np.float32)
        o[-xf:] = o[-xf:] * (1 - r) + seg[:xf] * r; o = np.concatenate([o, seg[xf:]])
    return o
for n in N:
    t0 = warp(n['start']); t1 = warp(n['end'])
    if t0 > L: continue
    p, v = n['pitch'], n['velocity'] / 127
    dur = max(t1 - t0, 0.05)
    put(out['pno'], sample('acoustic_grand_piano', p), t0, max(dur, 2.4 * T), 1.6 * v ** 1.1, 0.9)
    if p >= 66 and n['end'] - n['start'] > 0.9:                       # melodia -> violino
        put(out['vln'], loop(sample('violin', p), dur), t0, dur, 0.9 * v ** 0.8, 0.5)
    if p < 50 and n['end'] - n['start'] > 0.9:                        # baixo -> violoncelo
        q = p + 12 if p < 36 else p
        put(out['vc'], loop(sample('cello', q), dur), t0, dur, 1.0 * v ** 0.8, 0.6)
mix = out['pno'] * 1.0 + out['vln'] * 0.55 + out['vc'] * 0.6
# reverb: resposta de sala sintetica (ruido com decaimento), estereo
rng = np.random.default_rng(1); ir_n = int(2.6 * SR); tt = np.arange(ir_n) / SR
irs = [rng.normal(0, 1, ir_n).astype(np.float32) * np.exp(-tt * 2.7).astype(np.float32) for _ in range(2)]
def conv(x, h):
    n = len(x) + len(h); F = 1 << int(np.ceil(np.log2(n)))
    return np.fft.irfft(np.fft.rfft(x, F) * np.fft.rfft(h, F), F)[:len(x)].astype(np.float32)
wet = [conv(mix, h) for h in irs]; wet = [w / (np.abs(w).max() + 1e-9) * np.abs(mix).max() * 0.55 for w in wet]
st = np.stack([mix + wet[0], mix + wet[1]], 1)[:int(L * SR)]
fade = int(1.4 * SR); st[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 1.5
st /= np.abs(st).max() + 1e-9; st *= 0.9
sf.write('musica.wav', st, SR)
json.dump({'T': T, 'beat': 3 * T, 'bar': 12 * T, 'len': L}, open('grid.json', 'w'))
print('musica.wav', len(st) / SR, 's  ancoras', len(anc))
