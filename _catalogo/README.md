# Catalogo Casa Sinelli

Projeto de geracao do catalogo de moveis em PDF.

## Estrutura

```
_catalogo/
├── dados/                      Arquivo JSON com todos os produtos (fonte unica de verdade)
├── templates/                  Template HTML/Jinja2 do catalogo
├── css/                        CSS de identidade visual e layout de impressao
├── assets/                     Logo rasterizado (logo.png) e vetorial (logo.pdf)
├── imagens_processadas/        Imagens normalizadas, organizadas por categoria
│   ├── armarios/
│   ├── balcoes/
│   ├── cabeceiras/
│   ├── cadeiras/
│   ├── camas/
│   ├── colchoes/
│   ├── comodas/
│   ├── cozinhas/
│   ├── eletrodomesticos/
│   ├── guarda-roupas/
│   ├── mesas-e-escrivaninhas/
│   ├── multiusos/
│   ├── outros/
│   ├── poltronas/
│   ├── racks-e-paineis/
│   └── sofas/
├── output/                     PDFs gerados (impressao e WhatsApp)
└── scripts/                    Pipeline de processamento
    ├── 00_validar_ambiente.py  Verifica ferramentas instaladas
    ├── 01_extrair_dados.py     Gera produtos.json a partir do inventario
    ├── 02_processar_imagens.py Normaliza imagens com ImageMagick
    ├── 03_gerar_catalogo.py    Renderiza HTML+CSS+dados em PDF via WeasyPrint
    └── 04_comprimir_whatsapp.py Comprime PDF com Ghostscript
```

## Pipeline

Executar os scripts na ordem numerica (00 a 04).
Cada script e independente e pode ser reexecutado individualmente.
