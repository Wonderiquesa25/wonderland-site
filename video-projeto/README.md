# Vídeo Kukulu Kua Mukambu — projeto de edição

Estrutura: **Cena 1** (início, por fazer) → **Cena 2 = parte final (aprovada, v14)**.

Cena 2 (final): **`render/cena2_final_4K.mp4`** (64,8 s, vertical 4K 2160×3840, 30 fps, ~11 Mbps) e `render/cena2_final_1080p.mp4` (cópia leve). País: **Angola**.

Nota para a Cena 1: as quatro personagens já são apresentadas na Cena 2 (uma vez cada) — na Cena 1 não repetir apresentações; manter o mesmo look, fontes, cores de legenda e estilo de música para a junção ficar contínua.

## Personagens (uma apresentação cada)

| Personagem | Nome no ecrã | Cargo | Apresentação (tempo no filme) |
|---|---|---|---|
| Homem que entra pela porta | Lourenço Sebastião | CEO | 0:22,3 – 0:24,6 |
| Jovem com os pés na mesa | Hilária Mukango | Secretária | 0:10,3 – 0:12,6 |
| De capacete, sentado | Joel Simão | Técnico de Segurança Electrónica | 0:41,83 – 0:44,13 |
| Ao lado do Joel no quadro / no fim a cantar | Lima | Técnico de Segurança Electrónica | 1:00,31 – 1:02,61 (congelado no fim) |

## Ordem do filme (v14)

1. 0:00 Lourenço entra pela porta → Hilária com os pés na mesa → fala dela → 0:10,3 apresentação da Hilária
2. Fala do Lourenço com imagens de apoio (planeamento, moradia→loja, equipa→vigilância, consulta, monitorização); 0:22,3 apresentação do Lourenço
3. 0:41,48 corte com impacto e drop da música → Joel Simão (apresentação 0:41,83)
4. Instalação da câmara → cliente no telemóvel ("as ideias ganham vida")
5. Lima com a fita métrica ("MEDIMOS / MONTAMOS / AJUSTAMOS"), a cantar e congelado na apresentação (1:00,31)
6. 1:02,6 cartão final animado com o logótipo (2,2 s) — total 64,8 s

## Look (cor)

- Clips com luz do dia: `eq=gamma=0.96:contrast=1.03,colorbalance=rm=0.025:gm=-0.01:bm=-0.01`
- Clip da Hilária (mais escuro): `eq=brightness=0.02:gamma=1.5:contrast=1.14:saturation=1.08,colorbalance=rm=0.035:gm=-0.045:bm=0.0:rs=0.015:gs=-0.02,curves=g='0/0 0.5/0.48 1/0.98'`
- Look comum: `curves=all='0/0.03 0.25/0.22 0.5/0.5 0.78/0.81 1/0.95',colorbalance=rs=-0.01:bs=0.015:rh=0.02:gh=0.005:bh=-0.02,eq=saturation=0.95,vignette=angle=PI/7,noise=alls=4:allf=t`
- Todos os clips estabilizados com `vidstabdetect`/`vidstabtransform` (smoothing 15–40, zoom 4).

## Marca

- Laranja #F8A800 (principal), branco #F8F8F8, preto. Amarelo #FFD600 só para destaques.
- Fontes: Oswald Bold (nomes), Montserrat Bold (cargos/legendas) — em `fonts/`.
- Logótipo sem fundo: `../brand/kukulu-logo@2x.png`.

## v11 (som e legendas)

- Só as falas ficam audíveis (corte automático fora das palavras, a partir da transcrição); conversa do quadro branco removida.
- Limpeza de ruído, compressão e cada pessoa a −16 LUFS.
- As falas param durante cada apresentação (2,3 s) e retomam depois. Apresentações (tempo final): Hilária 0:10,3 · Lourenço 0:22,3 · Joel 0:42,55 · Lima 1:01,03 · cartão final 1:03,3.
- Corrigidos os cortes que comiam "solução" (Lourenço) e "vida" (Joel).
- Legendas animadas palavra a palavra (Montserrat ExtraBold, laranja da marca, destaques a amarelo): `transcricao/legendas_v11.ass`.
- Texto incerto não legendado: a 1.ª palavra do Joel e o meio da música do Lima ("segunda-feira… / Chefe …").

## v12 (imagens, foley, legendas)

- 6 imagens geradas no Canva (Angola, técnicos angolanos) em `imagens-canva/`, design Canva `DAHXhgKjAw0`:
  planeamento ("planearmos"), residência ("residências, casas"), loja ("estabelecimentos"), vigilância ("proteger os clientes"),
  consulta ("a sua problemática"), monitorização ("a solução").
- Efeitos sonoros das ações criados de raiz (`scripts/foley.py`): porta, pés da Hilária, cadeira, teclado, Lourenço a sentar-se,
  passos do Lima, saco, fita métrica a sair e a recolher.
- Legendas: texto principal amarelo da marca; ganchos em branco, maiores, com animação de crescer/encolher (`transcricao/legendas_v12.ass`).

## v13 (refinamento final)

- Espaços provisórios removidos: reação da Hilária no meio de "a melhor solução", restos do colete/quadro/Joel-teaser e a cena do quadro branco
  (substituída por instalação da câmara + cliente a ver no telemóvel, para "as ideias ganham vida").
- Novas imagens Canva: equipa angolana ("nós estamos no campo"), instalação, telemóvel.
- Música original afro-house/amapiano 120 BPM criada de raiz (`musica/`, `scripts/music.py`), com ducking automático sob as vozes.
- Transições: entradas com zoom, deslize moradia→loja, zoom equipa→câmara, whip para a instalação, tremor no corte para o Joel.
- Legendas maiores (100/140 px) com 4 animações diferentes; ganchos brancos com salto.
- Texto atrás da pessoa (recorte quadro a quadro): "A MELHOR SOLUÇÃO" (Lourenço) e "MEDIMOS / MONTAMOS / AJUSTAMOS" (Lima).

## v14 (master 4K)

- Removido o "casas" (Lourenço): "nas suas residências e estabelecimentos" (corte escondido na transição moradia→loja).
- Música eletrónica original 128 BPM (`musica/musica_eletronica_128bpm.wav`), drop no corte para o Joel, ducking sob as vozes, mistura a −14 LUFS.
- Legendas maiores (122/165 px), animações variadas; "A MELHOR SOLUÇÃO" reposicionado para ficar legível.
- Impulsos de zoom nos ganchos, cartão final animado (brilho + reflexo de luz).
- Tratamento de luz/profundidade: pessoa recortada, mais luz e nitidez; fundo ligeiramente mais escuro e desfocado; redução de ruído.
- Exportado em 2160×3840 (upscale de alta qualidade; as gravações originais têm ~480 px de largura).

## Pendente

1. Confirmar a letra completa do Lima e a primeira palavra do Joel para completar as legendas.
2. (Opcional) Trocar os efeitos sonoros sintetizados por gravações reais.

## Scripts

`scripts/build.py` (montagem de imagem), `scripts/audio.py` (diálogo + efeitos sonoros originais), `scripts/intro.py`
(efeito de apresentação: congelar, recorte com contorno branco, sombra, fundo em retícula sépia, nome e cargo).
Os caminhos dentro dos scripts apontam para a pasta temporária da sessão original; ajustar para `fontes/` ao retomar.
