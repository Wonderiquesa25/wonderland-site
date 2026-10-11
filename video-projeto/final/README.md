# Kukulu Kua Mukambu — filme final

**Versão actual: sem música de fundo** (pedido do cliente) — só voz + efeitos sonoros, efeitos +3 dB
(recuam 3 dB quando há fala), impacto grave no final. Mistura: `scripts/mix_sem_musica.py`.
A versão com música (`scripts/mix_final.py`) fica como referência.

`../render/kukulu_filme_final_1080p.mp4` — 1080×1920, 30 fps, 2:27 (parte inicial HUD + cena 2).

## Pós-produção
- **Transição viagem no tempo** (`scripts/timewarp.py`, 2 s): aceleração com push-in, rebobinar da parte 1
  com pullback e túnel de frames, rastos de luz, desfoque radial, aberração cromática, flash e a cena 2 a emergir.
- **Ritmo**: parte 1 a 1,06×, cena 2 a 1,04× (rubberband, formantes preservados).
- **Voz** (`scripts/voice_master.py`): redução de ruído, EQ de correspondência com a voz da cena 2 (LTAS, 70 %),
  voz ligeiramente mais grave e cheia (pitch 0,955 com formantes preservados: a mesma voz, não outra), de-esser,
  compressão, loudness.
- **Mistura** (`scripts/mix_final.py`): música com ducking sob a fala, rebobinar/whoosh/impacto na transição,
  final com batida e cauda. Master a −14,5 LUFS, pico −1,5 dBFS.

## Música e efeitos (licenças)
- Música: faixa CC0 (domínio público) do conjunto `mrfakename/cc0-music-captioned` (Hugging Face) — descrição:
  "uplifting pop instrumental … joyful mood suitable for advertising or corporate". CC0: uso comercial livre.
- Efeitos: pacote npm `uisfx` (licença MIT, Lukas Schneider), temas scifi/cinematic + sons sintetizados.

## Capas (`capas/`, `scripts/thumb2.py`)
A partir do design Canva "Capa vertical para vídeo de marketing" (DAHVj-EL1cU), exportado em PNG.
16:9 (2560×1440 e 1280×720 para YouTube) e vertical 1080×1920.

## Limitações
- Sem modelo de remoção de reverberação; a gravação da parte 1 não tem conteúdo acima de ~4 kHz (não foi inventado).
- Bibliotecas comerciais (Pixabay, etc.) estavam bloqueadas neste ambiente; usou-se música CC0 e efeitos MIT.
- As capas foram compostas fora do Canva (não são camadas editáveis no Canva).
