# Casa Sinelli — Catálogo

Pipeline em Python que transforma o inventário de móveis da Casa Sinelli em um catálogo em PDF, pronto para impressão e para envio por WhatsApp.

## O que faz

1. Extrai e organiza os dados dos produtos a partir do inventário de imagens (`RV/`)
2. Processa e normaliza as imagens (corte, fundo, medidas) com ImageMagick
3. Gera o catálogo em PDF a partir de HTML/CSS + dados, usando Jinja2 e WeasyPrint
4. Comprime a versão final para envio via WhatsApp, usando Ghostscript

Pipeline completo em [`_catalogo/scripts/`](_catalogo/scripts), executado na ordem numérica (00 a 04).

## Stack

- Python
- [Jinja2](https://jinja.palletsprojects.com/) — templates HTML do catálogo
- [WeasyPrint](https://weasyprint.org/) — geração do PDF a partir de HTML/CSS
- [Pillow](https://python-pillow.org/) — manipulação de imagens
- [ImageMagick](https://imagemagick.org/) — normalização/corte de imagens (binário externo)
- [Ghostscript](https://www.ghostscript.com/) — compressão do PDF final (binário externo)
- [Poppler](https://poppler.freedesktop.org/) — utilitários de PDF (binário externo)

## Como rodar

Requer Python 3 e os binários externos (ImageMagick, Ghostscript, Poppler) instalados e no PATH.

```bash
pip install -r requirements.txt
python _catalogo/scripts/00_validar_ambiente.py   # confere se tudo está instalado
python _catalogo/scripts/01_extrair_dados.py
python _catalogo/scripts/02_processar_imagens.py
python _catalogo/scripts/03_gerar_catalogo.py
python _catalogo/scripts/script_04_comprimir.py
```

Cada script é independente e pode ser reexecutado individualmente.

## Estrutura

```
RV/                         Fotos originais do fornecedor, por categoria/modelo
_catalogo/
├── dados/                  produtos.json — fonte única de verdade dos produtos
├── templates/              Template HTML/Jinja2 do catálogo
├── css/                    Identidade visual e layout de impressão
├── assets/                 Logo (raster e vetorial)
├── imagens_processadas/    Imagens já normalizadas, por categoria
├── output/                 PDFs gerados (impressão e WhatsApp)
└── scripts/                Pipeline de processamento (00 a 04)
```

## Sobre o projeto

Ferramenta interna para a Casa Sinelli (negócio da família), usada para manter o catálogo de produtos atualizado sem depender de edição manual de PDF a cada mudança de estoque.
