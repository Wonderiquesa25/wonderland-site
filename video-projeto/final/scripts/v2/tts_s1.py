"""Scene-1 narration with a professional TTS voice (Piper 'cadu', pt-BR male, deepest of the tested voices),
one clip per sentence, each placed on the original sentence onset so the burned-in captions stay in sync,
time-fitted to its window; then a warm, heavy broadcast chain (no reverb, no echo)."""
import subprocess, sys, numpy as np
SR = 48000; V = sys.argv[1]; OUT = sys.argv[2]; TOTAL = 81.0
LINES = [
 (0.00, 10.45, "Me diz aí... quantas vezes, de noite, com a cabeça já na almofada, ficou preocupado se a sua residência, ou a sua empresa, estava realmente protegida?"),
 (10.58, 11.30, "Ou não?"),
 (11.40, 17.45, "A maioria das pessoas só pensa em segurança depois do susto. Depois que o pior acontece."),
 (17.56, 21.85, "Mas a verdade é que a segurança não dá segundas chances."),
 (21.98, 27.95, "E segurança de verdade, hoje em dia, já não é ter muros altos, ou arames na sua residência."),
 (28.08, 31.70, "É ter a tecnologia certa, e instalada do jeito certo."),
 (31.80, 35.25, "Muitos dizem que é só esticar arame. Mas não."),
 (35.38, 38.00, "Não se trata só de ter arames esticados."),
 (38.12, 47.40, "É cálculo de voltagem adequado. É arames esticados da forma adequada. Esticadores bem calibrados. Aterramento."),
 (47.50, 56.30, "Pois uma cerca eléctrica, se não tiver aterramento, podemos afirmar categoricamente que o choque daquela cerca eléctrica é inútil."),
 (56.40, 66.85, "Mas o mais interessante não é isso. É ter a certeza que quem tentar ultrapassar aquele limite, certamente será electrocutado."),
 (66.94, 76.90, "Ver o resultado final de um perímetro cem por cento blindado, e a nossa equipa em acção, dá um orgulho enorme."),
 (77.00, 80.45, "Mas, bom... não é assim que as coisas começam."),
]
def ld(p):
    return np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",p,"-ac","1","-ar",str(SR),"-f","f64le","-"],capture_output=True).stdout,np.float64).copy()
def trim(x, th=0.01):
    i = np.where(np.abs(x) > th)[0]; return x[max(0, i[0] - 240): i[-1] + 2400] if len(i) else x
out = np.zeros(int(TOTAL * SR))
for k, (a, b, txt) in enumerate(LINES):
    f = f"tts_{k:02d}.wav"
    subprocess.run(["python3","-m","piper","-m",V,"-f",f,"--length-scale","1.12","--sentence-silence","0.35"], input=txt.encode(), capture_output=True, check=True)
    x = trim(ld(f)); win = b - a; d = len(x) / SR
    tempo = d / win if d > win else max(0.94, d / win)            # compress if too long; at most 6% slower if short
    if abs(tempo - 1) > 0.01:
        p = subprocess.run(["ffmpeg","-v","error","-f","f64le","-ar",str(SR),"-ac","1","-i","-","-af",f"rubberband=tempo={tempo:.4f}:formant=preserved:pitchq=quality","-f","f64le","-"],
                           input=x.tobytes(), capture_output=True); x = np.frombuffer(p.stdout, np.float64)
    i = int(a * SR); x = x[: len(out) - i]; out[i:i + len(x)] += x
    print(f"{k:2d} {a:6.2f}-{b:6.2f} tts {d:5.2f}s -> tempo {tempo:.3f} ({len(x)/SR:.2f}s)")
chain = ("rubberband=pitch=0.9439:formant=preserved:pitchq=quality,"               # -1 semitone: heavier
         "highpass=f=60,equalizer=f=110:t=q:w=0.9:g=4,equalizer=f=300:t=q:w=1.2:g=-2,equalizer=f=3000:t=q:w=1.2:g=2,"
         "acompressor=threshold=-22dB:ratio=3.5:attack=5:release=90:makeup=4dB:knee=4,deesser=i=0.35,alimiter=limit=0.89")
subprocess.run(["ffmpeg","-y","-v","error","-f","f64le","-ar",str(SR),"-ac","1","-i","-","-af",chain,"-ar",str(SR),OUT], input=out.tobytes(), check=True)
