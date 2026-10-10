# Cena 1 (parte inicial) — em ajuste

Ordem: `nova1` → `nova2` → `nova3` → `nova4` (originais em `fontes/`). Só se junta à Cena 2 (parte final) quando tudo estiver ajustado.

## Feito (v2 "estúdio", substitui a v1)

- Estabilização (vidstab, smoothing 25).
- **Fundo preto total**: recorte com Robust Video Matting (modelo de vídeo, estável quadro a quadro, sem halo nem buracos;
  usa a cor de primeiro plano do modelo para não trazer a parede branca para as bordas).
- **Filtros no rosto** (deteção de rosto YuNet, seguida no tempo): retoque de pele por separação de frequências (suaviza, mantém 35% da textura),
  luz principal no rosto com sombras levantadas e cor de pele mais rica e quente; o corpo cai para a sombra (luz de estúdio).
- Tirada a "névoa" leitosa da gravação (pontos de preto/branco esticados com pé suave), contraste e cor; luz de recorte quente no topo da cabeça.
- Áudio: mono limpo (passa-altos, redução de ruído, EQ de clareza, de-esser, compressão, −16 LUFS) copiado para os dois canais.
- Gradação feita na resolução original e ampliada para 1080×1920 com nitidez leve. Scripts em `scripts/look2.py` e `scripts/process2.py`.
