# Mistura: voz original limpa + efeitos sonoros nos momentos de cada revelacao. -14 LUFS.
import os, subprocess
SFX = os.environ.get('SFX', 'sfxlib/package/sounds'); VOZ = os.environ.get('VOZ', 'v48.wav')
VID = os.environ.get('VID', 'mudo.mp4'); OUT = os.environ.get('OUT', 'final.mp4')
EV = [(1.12, 'cinematic/swipe', -12), (3.26, 'cinematic/snap', -6), (3.6, 'cinematic/press', -12),
      (3.72, 'cinematic/press', -12), (3.96, 'cinematic/snap', -9), (7.7, 'cinematic/badge', -10),
      (13.66, 'cinematic/lock', -9), (19.48, 'cinematic/lock', -9), (29.12, 'cinematic/success', -12),
      (30.95, 'cinematic/snap', -9), (32.95, 'cinematic/press', -10),
      (33.08, 'mechanical/press', -8), (34.02, 'mechanical/press', -8), (35.62, 'mechanical/press', -8)]
for b in [8.45, 14.52, 20.72, 26.24, 29.96]: EV.append((b - 0.22, 'cinematic/swipe', -11))
NAME, ROLE = 'LOURENÇO SEBASTIÃO', 'CEO · KUKULU KUA MUKAMBU'
for k in range(1, len(NAME) + 1):
    if NAME[k-1] != ' ': EV.append((4.88 + (6.6 - 4.88) * k / len(NAME) - 0.03, 'mechanical/typing', -15))
for k in range(1, len(ROLE) + 1, 2): EV.append((7.0 + 1.2 * k / len(ROLE) - 0.03, 'mechanical/typing', -17))
ins = ['-i', VID, '-i', VOZ]; fl = ['[1:a]highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,aresample=48000[v]']
lab = ['[v]']
for n, (t, f, g) in enumerate(EV):
    ins += ['-i', f'{SFX}/{f}.mp3']
    fl.append(f'[{n+2}:a]aresample=48000,aformat=channel_layouts=mono,volume={g}dB,adelay={int(t*1000)}|{int(t*1000)}[s{n}]'); lab.append(f'[s{n}]')
fl.append(f'{"".join(lab)}amix=inputs={len(lab)}:normalize=0:duration=first,apad,atrim=0:40,afade=t=out:st=39.3:d=0.7,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[a]')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *ins, '-filter_complex', ';'.join(fl), '-map', '0:v', '-map', '[a]',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-movflags', '+faststart', '-shortest', OUT], check=True)
