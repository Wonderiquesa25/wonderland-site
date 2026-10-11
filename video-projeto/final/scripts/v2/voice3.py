"""Scene-1 voice, YouTuber 'metallic' broadcast sound: denoise + gate, body/mud EQ, synthesised 4-10 kHz harmonics
(the recording has nothing above ~4 kHz), subtle short metallic comb, heavy compression, de-ess, limiter."""
import subprocess, sys, numpy as np
SR = 48000
def run(x, af):
    return np.frombuffer(subprocess.run(["ffmpeg","-v","error","-f","f64le","-ar",str(SR),"-ac","1","-i","-","-af",af,"-f","f64le","-"],
                         input=np.ascontiguousarray(x).tobytes(), capture_output=True).stdout, np.float64).copy()
x = np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-ac","1","-ar",str(SR),"-f","f64le","-"],capture_output=True).stdout,np.float64).copy()
x = run(x, "highpass=f=75,afftdn=nr=12:nf=-45:tn=1,agate=threshold=0.015:ratio=8:attack=3:release=140:range=0.02,"
           "equalizer=f=110:t=q:w=0.9:g=4,equalizer=f=320:t=q:w=1.2:g=-4,equalizer=f=900:t=q:w=1.5:g=-1.5,equalizer=f=2600:t=q:w=1.2:g=3")
# exciter: drive the 1.6-4 kHz band through a non-linearity -> harmonics, keep only what lands above 3.8 kHz
band = run(x, "highpass=f=1600,highpass=f=1600,lowpass=f=4000,lowpass=f=4000")
k = 1 / (np.percentile(np.abs(band), 99.5) + 1e-9)
harm = np.tanh(band * k * 3) + 0.5 * np.abs(np.tanh(band * k * 3))
harm = run(harm, "highpass=f=3800,highpass=f=3800,highpass=f=3800,lowpass=f=9000,lowpass=f=9000,equalizer=f=5000:t=q:w=1:g=3")
# level harmonics to sit ~ -16 dB below the full signal (typical bright YouTube VO)
harm *= np.sqrt(np.mean(x ** 2)) / (np.sqrt(np.mean(harm ** 2)) + 1e-12) * 10 ** (-21 / 20)
y = x + harm
y = run(y, "aecho=0.85:0.22:3|6:0.22|0.15,"                                     # tiny comb -> metallic sheen, no audible echo
           "acompressor=threshold=-24dB:ratio=5:attack=4:release=80:makeup=6dB:knee=4,deesser=i=0.45:m=0.5:f=0.55,"
           "acompressor=threshold=-12dB:ratio=3:attack=2:release=60,asoftclip=type=tanh:threshold=0.9,alimiter=limit=0.89:attack=3:release=50")
subprocess.run(["ffmpeg","-y","-v","error","-f","f64le","-ar",str(SR),"-ac","1","-i","-","-ar",str(SR),sys.argv[2]], input=y.tobytes(), check=True)
