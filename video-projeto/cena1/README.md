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

## v3 — restauração completa (atual: `cena1_v3.mp4`, 1:29,8, 1080×1920, 30 fps)

- **Ritmo:** silêncios do início/fim de cada parte e pausas longas encurtados (1:45,8 → 1:29,8), cortes nas pausas com margem para
  não tocar em sílabas; toques no telemóvel no fim das partes removidos. Lista de cortes em `edl.json` (de `scripts/edl.py`).
  Nada do que é dito foi removido nem reescrito.
- **Cortes disfarçados:** cada segmento alterna o enquadramento (1,00× / 1,08×, centrado no rosto) para os saltos parecerem mudanças de plano.
- **Rosto:** restauração facial CodeFormer (fidelidade alta, mistura 70%) sobre o rosto alinhado, com o detalhe suavizado no tempo
  (sem cintilação); a cor/tom vem sempre da imagem original — não muda feições nem identidade.
- **Imagem:** fundo preto (Robust Video Matting), luz de estúdio no rosto, retoque leve de pele, nitidez seletiva, grão fino.
- **Áudio:** declip, redução de ruído (FFT + NLM), EQ de clareza, de-esser, compressão; cruzamentos de 12 ms em cada corte; −14 LUFS.
- **Música:** original e discreta (`musica/musica_cena1.m4a`): noite tensa → pulsação "coração" na segurança → tic-tac na parte técnica
  → abertura calorosa em "orgulho enorme"; desce automaticamente sob a voz.
- Transcrição palavra a palavra em `transcricao/`.
- Limites honestos: a gravação original é 576×1024 com desfoque de movimento nos gestos rápidos; não há 4K real nem
  remoção de eco de sala (não há modelo de de-reverberação disponível aqui).
