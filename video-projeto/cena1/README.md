# Cena 1 (parte inicial) — em ajuste

Ordem: `nova1` → `nova2` → `nova3` → `nova4` (originais em `fontes/`). Só se junta à Cena 2 (parte final) quando tudo estiver ajustado.

## Feito (passo "estúdio")

- Estabilização (vidstab, smoothing 25).
- Fundo trocado por escuro de estúdio: pessoa recortada quadro a quadro (rembg u2net_human_seg, suavização temporal só quando parado,
  limpeza da parede clara à volta da cabeça); fundo carvão com um vestígio desfocado da sala e brilho quente laranja atrás da cabeça.
- Luz: pretos recuperados, altas luzes da camisa comprimidas, luz principal no rosto vinda da esquerda com queda para a direita e para baixo,
  luz de recorte suave nas bordas, vinheta, grão leve. Look em `scripts/look.py`.
- Áudio: passa-altos 85 Hz, redução de ruído, menos "lama" (280 Hz), mais presença (3,2 kHz), de-esser, compressão, −16 LUFS.
- Saída vertical 1080×1920, 30 fps: `estudio/novaN_estudio.mp4` (1:45,8 no total). Versões para o repositório comprimidas (~4,5 Mbps); os masters sem compressão ficam na pasta de trabalho da sessão.
