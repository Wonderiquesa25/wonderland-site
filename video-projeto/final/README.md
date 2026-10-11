# Kukulu Kua Mukambu — filme final

**Versão actual: v2** (2:23, sem música) — `scripts/v2/`:
- Transição nova **central de monitorização CCTV** (`cctv.py`): a parte 1 vira o feed CAM 01, a câmara recua para a parede de
  monitores da Kukulu (CAM 03/04 = obras reais de cerca eléctrica), o cursor laranja selecciona CAM 02 e a câmara entra na cena 2.
  Desfoque de movimento real (8 sub-frames), som: REC, zumbido da sala, glitch, whoosh, clique, estática, ligação, impacto.
- Voz sem eco: dereverberação WPE (`dereverb.py`) + supressão espectral da reverberação tardia (`dereverb_ss.py`) no áudio bruto
  (`dialogue6.py`); a MESMA cadeia aplicada ao Lourenço na cena 2 e igualada à parte 1 (±2 dB até 4 kHz) e ao mesmo nível (`voice2.py`).
- Removidos os restos do "O que?" antes de "Muitos dizem" e duas pausas reais; parte 1 a 1,09×, cena 2 a 1,06× (`assemble_a.py`).
- Nomes e cargos **digitados** letra a letra com cursor e som de tecla mecânica por letra (`intro_typed.py`, `mix_v2.py`).
- Mistura: voz por cima; efeitos +1 dB nas pausas e −7 dB quando há fala; −13,9 LUFS, pico −1,4 dBFS.
- Limitações: a gravação da parte 1 não tem agudos acima de ~4 kHz (a cena 2 foi aproximada a ela para soarem iguais);
  pronúncia não alterada (sem voz sintética).

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
