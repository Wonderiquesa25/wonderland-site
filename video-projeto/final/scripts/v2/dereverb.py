"""WPE dereverberation (nara_wpe) for a mono wav: in -> out, 48 kHz."""
import sys, subprocess, numpy as np
from nara_wpe.wpe import wpe
from nara_wpe.utils import stft, istft
src, out = sys.argv[1], sys.argv[2]; taps = int(sys.argv[3]) if len(sys.argv) > 3 else 12
SR = 48000
x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(SR), "-f", "f64le", "-"], capture_output=True).stdout, np.float64)
Y = stft(x[None], size=1024, shift=256).transpose(2, 0, 1)            # (F, D=1, T)
Z = wpe(Y, taps=taps, delay=3, iterations=5, statistics_mode='full').transpose(1, 2, 0)
z = istft(Z, size=1024, shift=256)[0][: len(x)]
z = np.pad(z, (0, len(x) - len(z)))
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f64le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "pcm_s24le", out], input=z.tobytes(), check=True)
print("wpe", src, "->", out)
