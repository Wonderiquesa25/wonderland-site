# Vídeo das obras (voz da Cena 1) — Kukulu Kua Mukambu

**Atual: `video_kukulu_1080p.mp4`** (1:29,8, vertical 1080×1920, 30 fps) — versão SEM o efeito Alice, a pedido:
cor natural cinematográfica, entrada com zoom, transições light-leak laranja / zoom / whip / linha laranja / flash, impulso de zoom
nas palavras-chave, raios eléctricos realistas em "choque" e "electrocutado". Legendas nas cores da marca: texto laranja #F8A800,
palavras-gancho brancas, contorno preto, palavras gigantes em Oswald (`legendas/captions_brand.ass`). Áudio: só a voz, −14 LUFS.
Scripts: `scripts/pass1.py` (NATURAL=1), `scripts/pass2_nat.py`, `scripts/captions_brand.py`.

## Versão anterior (Alice no País das Maravilhas — substituída, ficheiro removido)

- **Trilha:** a voz da Cena 1 (`../cena1/audio/cena1_audio_so_voz.mp3`), sem música nem outros sons por cima; o som das gravações foi retirado.
- **Material:** os uploads do Canva (design "Alice material": obras de cerca eléctrica, arame farpado, técnicos, máquina de solda) + a foto do técnico na escada.
- **Mundo de Alice:** céu substituído em todos os planos por céus surreais gerados no Canva (`imagens-canva/sky1.png`, `sky2.png`), a acompanhar o
  movimento da câmara; fios e arame farpado mantidos por cima do céu; gradação esmeralda/violeta/dourado; nevoeiro à noite, poeira dourada,
  raios de luz na revelação final, arcos eléctricos violeta em "voltagem", "choque" e "electrocutado".
- **Abertura e fecho:** entra-se no mundo através de um espelho mágico num jardim encantado (`imagens-canva/portal.png`) e regressa-se a ele no fim.
- **Transições:** véu de brilho, ondulação líquida, zoom dimensional, pétalas, linha dourada, flash; eco temporal em "segundas chances".
- **Legendas:** grandes e animadas palavra a palavra — texto principal amarelo-dourado da marca (Montserrat ExtraBold), palavras-gancho
  em Cinzel marfim com contorno violeta, e palavras gigantes ao centro nos momentos-chave (NOITE, PROTEGIDA?, SUSTO, SEGUNDAS CHANCES,
  TECNOLOGIA CERTA, VOLTAGEM, ATERRAMENTO, INÚTIL, LIMITE, ELECTROCUTADO, 100% BLINDADO, ORGULHO ENORME, COMEÇAM).
  Duas palavras inaudíveis não foram legendadas (o "O que?" inicial da parte 3 e uma palavra depois de "inútil").
- Sem 4K: o material vem do Canva em 1080×1920; exportar em 4K seria só ampliar.

## Versão "pop" com as obras novas (atual: `video_kukulu_pop_1080p.mp4`)

Construída sobre a versão anterior (mesmo ritmo, cortes, legendas da marca e voz), com:
- **Obras novas do Canva** (projeto "outros trabalhos de cerca electrica", fotos em `obras-canva/`): moradia cinzenta em "residência",
  fachada laranja em "empresa", técnico a instalar em "arames esticados da forma adequada", técnicos no muro em "equipa em ação",
  e uma montra de obras concluídas em "Ver o resultado final…" — 4 obras em painéis estilo banda desenhada e grelha 2×2 com ✓ em "100% blindado".
- **Grafismo original pop/BD** (`scripts/comic.py`): círculos, setas e sublinhados desenhados à mão sobre as cercas e a equipa,
  sublinhados rabiscados nas palavras gigantes, linhas de velocidade, frames de impacto em "SUSTO", "LIMITE", "ELECTROCUTADO",
  glitch curto em "choque", transição de pincelada laranja, estrelas nos painéis.
- **Som:** voz + efeitos discretos (whoosh, impacto suave, marcador, pop) ~11 dB abaixo da voz, −14 LUFS (`scripts/sfx.py`).
