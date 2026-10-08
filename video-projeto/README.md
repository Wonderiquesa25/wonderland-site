# Vídeo Kukulu Kua Mukambu — projeto de edição

Estado atual: **`render/filme_v10.mp4`** (56 s, vertical 1080×1920, 30 fps).

## Personagens (uma apresentação cada)

| Personagem | Nome no ecrã | Cargo | Apresentação (tempo no filme) |
|---|---|---|---|
| Homem que entra pela porta | Lourenço Sebastião | CEO | 0:11,0 – 0:13,3 |
| Jovem com os pés na mesa | Hilária Mukango | Secretária | 0:03,4 – 0:05,7 |
| De capacete, sentado | Joel Simão | Técnico de Segurança Electrónica | 0:37,5 – 0:39,75 |
| Ao lado do Joel no quadro / no fim a cantar | Lima | Técnico de Segurança Electrónica | 0:51,9 – 0:54,07 (congelado no fim) |

## Ordem do filme (v10)

1. 0:00 Lourenço entra pela porta → 0:00,8 Hilária com os pés na mesa → fala dela
2. 0:10,8 – 0:37,0 fala do Lourenço (punch-ins + inserts: reação da Hilária, logótipo no colete, quadro branco, Joel de capacete)
3. 0:37,0 corte seco com impacto → Joel Simão
4. 0:39,97 whip pan → Lima + Joel no quadro branco
5. 0:43,17 → Lima (fita métrica, termina congelado na apresentação)
6. 0:54,07 corte para preto → cartão com o logótipo (2,2 s)

## Look (cor)

- Clips com luz do dia: `eq=gamma=0.96:contrast=1.03,colorbalance=rm=0.025:gm=-0.01:bm=-0.01`
- Clip da Hilária (mais escuro): `eq=brightness=0.02:gamma=1.5:contrast=1.14:saturation=1.08,colorbalance=rm=0.035:gm=-0.045:bm=0.0:rs=0.015:gs=-0.02,curves=g='0/0 0.5/0.48 1/0.98'`
- Look comum: `curves=all='0/0.03 0.25/0.22 0.5/0.5 0.78/0.81 1/0.95',colorbalance=rs=-0.01:bs=0.015:rh=0.02:gh=0.005:bh=-0.02,eq=saturation=0.95,vignette=angle=PI/7,noise=alls=4:allf=t`
- Todos os clips estabilizados com `vidstabdetect`/`vidstabtransform` (smoothing 15–40, zoom 4).

## Marca

- Laranja #F8A800 (principal), branco #F8F8F8, preto. Amarelo #FFD600 só para destaques.
- Fontes: Oswald Bold (nomes), Montserrat Bold (cargos/legendas) — em `fonts/`.
- Logótipo sem fundo: `../brand/kukulu-logo@2x.png`.

## Pendente

1. **Legendas sincronizadas** (estilo da referência, laranja + destaques a amarelo): precisa de transcrição.
   Libertar `huggingface.co`, `*.huggingface.co` e `*.hf.co` na rede do ambiente (Edit → Network access → Allowed domains).
2. **Imagens de apoio (B-roll)** geradas ou de banco de imagens para ilustrar as falas (depende da transcrição para saber o que ilustrar).
3. Transições ao estilo da referência (painéis de papel, cartões de palavra gigante) depois das legendas.

## Scripts

`scripts/build.py` (montagem de imagem), `scripts/audio.py` (diálogo + efeitos sonoros originais), `scripts/intro.py`
(efeito de apresentação: congelar, recorte com contorno branco, sombra, fundo em retícula sépia, nome e cargo).
Os caminhos dentro dos scripts apontam para a pasta temporária da sessão original; ajustar para `fontes/` ao retomar.
