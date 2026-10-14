# Vídeo narrado — "Estava aberto. Agora está protegido."

Voz original do CEO (gravação WhatsApp, 14/10) sobre o poster do CEO + 4 obras + CTA. 1080x1920, 30 fps, 40 s.

- `scripts/prep.py` — separa o poster em fundo / textos / pessoa (rembg `u2net_human_seg`) / logo e cria as faixas de texto das fotos.
- `scripts/render.py` — anima cada elemento no tempo exacto da palavra (faster-whisper large-v3, palavra a palavra).
- `scripts/mix.py` — voz limpa (highpass, afftdn, compressor) + efeitos, loudnorm -14 LUFS.

Resultado: `redes-sociais/tiktok/kukulu_narrado_tiktok.mp4`. Música: escolher no TikTok (som em alta, volume baixo ~15%).
