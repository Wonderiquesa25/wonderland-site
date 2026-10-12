# Reunião (vídeo WhatsApp de 09/10) — versão melhorada

**Final escolhido: `render/kukulu_reuniao_v3.mp4`** — montagem da 1.ª versão (`scripts/build_v1.py`) sobre imagem melhorada
(`scripts/enhance.py`: limpeza de ruído, upscale 1080p, sombras levantadas, luz extra só na pele dos rostos, restauro CodeFormer estável).

Alternativa sem efeitos do CapCut: `render/kukulu_reuniao_v2.mp4` (47,1 s, 1080×1920, −14 LUFS).

Mantidos: as falas e a música originais (a música está na entrada do prédio). Melhorado no estilo do filme da equipa:
- v2 (limpa): retirados os efeitos do CapCut — rebobinar P&B, flashes brancos, recorte P&B do Eric, desfoques de transição,
  desenhos animados (ladrão e "problemas") — trocados por imagem real das pessoas; entrada em câmara lenta sem sobreposições.
- Enquadramento 9:16 que esconde as legendas antigas do CapCut e a marca de água; cor igual ao filme da equipa.
- Apresentações novas com nome digitado e som de teclado: Eric Oldcash (Gestor de Marketing), Joel Simão
  (Técnico de Segurança Electrónica), Alberto Domingos (Soldador Industrial). A fala pára durante cada cartão.
- Pausas encurtadas (cortes com punch-in alternado), legendas animadas palavra a palavra (laranja da marca, destaques a branco).
- Final com o cartão do logótipo do filme da equipa.

Scripts: `scripts/cards.py` (cartões), `scripts/build.py` (montagem, som, legendas).
