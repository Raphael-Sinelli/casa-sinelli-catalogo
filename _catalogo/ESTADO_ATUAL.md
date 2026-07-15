## Estado atual

Concluído:
- Tarefa 1: seleção de imagens por cor em `get_processed_images` (script 03).
- Tarefa 2: catálogo completo gerado (190 págs, pré-reorg).
- Tarefa A: varredura — nenhum produto novo; variantes A.2 e vínculos A.3 mapeados.
- Tarefa B (commit e6549e1): reorg de categorias (Cristaleiras, Fruteiras,
  Penteadeiras, Mesas de Cabeceira, Escrivaninha, Sapateiras; id 99→Multiusos),
  flag `modulado` (47-52,75), A.2 variantes incorporadas, A.3 vínculos corrigidos.
  Agora 128 produtos, 22 categorias, ~198 páginas estimadas.

- Tarefa D: diagnóstico de cortes (crop cover+extent no script 02; corrigido via FORCE_FIT_IDS).
- Tarefa C concluída em 6 blocos (commits 5a261e5, b638bae, f1f20ce, 14f90f1, e7d45bf, 248d21e):
  1. Cortes (FORCE_FIT_IDS) · 2. Sem fundo (96 imgs) · 3. Medidas (11 imgs) ·
  4. 1 interna (15 imgs) · 5. Rodapés (cores/sofá-cama) · 6. Específicos
  (id 95 removido, id 83 split em 83+129, id 123 pins, id 125 cap).
- Exclusões em dados/{sem_fundo,medidas,interna}_excluir.txt (script 02 não regenera).

## Rodada 2 de correções (commits faf6571..9910096)
- B1 cortes (FORCE_FIT 14,93) · B2 colchões/box por tamanho (15,31,35,30) ·
  B3 cores/rodapés 16 itens (reorder imagens 36,37,68,71,74,76 + 10 cores) ·
  B4 medidas mesa maior (84,86,87) · B5 sem-fundo id 97 Roma ·
  B6 reorg por cor (117,120 GROUP_PER_COLOR; 118 COLOR_SORTED) ·
  B7 substituições (20 bicama; 123 marrom=COLOCAR, cinza=11.jpg).
- Novos mecanismos script 03: IMAGE_PINS, PRODUCT_MAX_IMAGES, GROUP_PER_COLOR,
  COLOR_SORTED. Exclusões: dados/{sem_fundo,medidas,interna,descartadas}_excluir.txt.
- Catálogo regenerado: 128 produtos, 21 categorias, 172 páginas.
  output/catalogo_impressao.pdf (~75MB) + catalogo_whatsapp.pdf (~5.4MB, /screen).

## Rodada 3 de correções (commits 440938b..2471a0a)
- Bloco A (440938b): rodapés 8 itens — id5 cores; id33/34 colchão medidas;
  id90 Córdoba ordem; id96 Bari; id123 Manuela marrom→fim; id125/127 medidas.
- Bloco B (f7974a8): fundo→branco via floodfill — id31 floral (1 img) +
  rodapé; id35 turquesa (2 imgs preta/cinza). Sem exclusão.
- Bloco C (2471a0a): substituições — id69 GR Fit 3.2 (COLOQUE ESSA.png);
  id117 Aline bege troca 2 sobreexpostas; id121 courino reprocessado;
  id125 Recife cinza close→inteiro (09.17.09).
- Catálogo regenerado: 128 produtos, 21 categorias, 172 páginas.
  output/catalogo_impressao.pdf (~75MB) + catalogo_whatsapp.pdf (~5.4MB, /screen).

## Observação importante (mapeamento de páginas)
As páginas que o cliente cita vêm do visualizador com offset +1: usar
`página_do_cliente − 1` → página no mapa (scratchpad/mapa_paginas.py) → id real.
Os "id N" que o cliente escreve costumam ser o número da página, NÃO o id do JSON.
Sempre confirmar por descrição (cores/nome) além do número.

## Próximo passo
Aguardando próxima rodada de ajustes.
