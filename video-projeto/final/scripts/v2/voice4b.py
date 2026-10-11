"""Scene-1 'scary' narrator, built from the real voice (timing untouched -> lip sync kept):
pitched down 3 semitones with formants lowered (bigger, darker body), an octave-down sub-voice underneath (menace),
a slow growl (ring-mod), tube saturation, synthesised metallic top, tiny comb, dark short room, heavy broadcast compression."""
import subprocess, sys, numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
SR = 48000; rng = np.random.default_rng(3)
def run(x, af):
    return np.frombuffer(subprocess.run(["ffmpeg","-v","error","-f","f64le","-ar",str(SR),"-ac","1","-i","-","-af",af,"-f","f64le","-"],
                         input=np.ascontiguousarray(x).tobytes(), capture_output=True).stdout, np.float64).copy()[: len(x)]
def rms(x): return np.sqrt(np.mean(x ** 2)) + 1e-12
x = np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-ac","1","-ar",str(SR),"-f","f64le","-"],capture_output=True).stdout,np.float64).copy()
n = len(x)
x = run(x, "highpass=f=75,afftdn=nr=12:nf=-45:tn=1,agate=threshold=0.015:ratio=8:attack=3:release=140:range=0.02,equalizer=f=320:t=q:w=1.2:g=-3")
main = run(x, "rubberband=pitch=0.8409:formant=preserved:pitchq=quality:transients=smooth")          # -3 st, formants down too
sub = run(x, "rubberband=pitch=0.5:formant=shifted:pitchq=quality:transients=smooth,lowpass=f=700,lowpass=f=700")   # octave down
sub *= rms(main) / rms(sub) * 10 ** (-10 / 20)
t = np.arange(n) / SR
growl = main * (1 + 0.12 * np.sin(2 * np.pi * 38 * t))                                          # subtle rasp/growl
v = growl + sub
v = np.tanh(v / (np.percentile(np.abs(v), 99.5) + 1e-9) * 1.6) * 0.7                            # saturation
v = run(v, "equalizer=f=90:t=q:w=1:g=5,equalizer=f=180:t=q:w=1:g=2,equalizer=f=450:t=q:w=1.2:g=-3,equalizer=f=2400:t=q:w=1.3:g=3")
# metallic top: harmonics of the 1.5-3.5 kHz band, only what lands > 3.5 kHz
band = run(v, "highpass=f=1500,highpass=f=1500,lowpass=f=3500,lowpass=f=3500")
k = 1 / (np.percentile(np.abs(band), 99.5) + 1e-9)
harm = run(np.tanh(band * k * 3) + 0.5 * np.abs(np.tanh(band * k * 3)), "highpass=f=3500,highpass=f=3500,highpass=f=3500,lowpass=f=8500,lowpass=f=8500")
v = v + harm * rms(v) / rms(harm) * 10 ** (-22 / 20)
v = run(v, "aecho=0.85:0.3:5|9:0.28|0.2")                                                        # metallic comb
# dark small room (0.5 s), low in level so it adds dread without the old echo problem
irt = np.arange(int(0.5 * SR)) / SR; ir = rng.standard_normal(len(irt)) * np.exp(-irt * 9)
ir = sosfilt(butter(2, 2500, "low", fs=SR, output="sos"), ir); wet = fftconvolve(v, ir)[:n]
v = v + wet * rms(v) / rms(wet) * 10 ** (-17 / 20)
v = run(v, "acompressor=threshold=-24dB:ratio=5:attack=4:release=90:makeup=6dB:knee=4,deesser=i=0.4:m=0.5:f=0.55,"
           "acompressor=threshold=-12dB:ratio=3:attack=2:release=60,asoftclip=type=tanh:threshold=0.9,alimiter=limit=0.89:attack=3:release=50")
subprocess.run(["ffmpeg","-y","-v","error","-f","f64le","-ar",str(SR),"-ac","1","-i","-","-ar",str(SR),sys.argv[2]], input=v.tobytes(), check=True)
