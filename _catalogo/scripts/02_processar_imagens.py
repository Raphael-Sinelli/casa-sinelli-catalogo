"""
02_processar_imagens.py
Normaliza imagens dos produtos para molde 4:3 (1200x900px) via ImageMagick.
"""
import json
import os
import subprocess
import sys
import io
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CATALOG_ROOT = os.path.normpath(r"c:\Imagens\Catalogo")
JSON_PATH = os.path.join(CATALOG_ROOT, "_catalogo", "dados", "produtos.json")
OUTPUT_BASE = os.path.join(CATALOG_ROOT, "_catalogo", "imagens_processadas")

WIDTH, HEIGHT = 1200, 900
QUALITY = 88
BG_COLOR = "#FFFFFF"
RATIO_THRESHOLD = 0.85

FIT_ONLY_CATEGORIES = {
    "guarda-roupas", "armarios", "cabeceiras", "camas", "comodas", "racks-e-paineis",
    # novas categorias (Tarefa B) — móveis altos, sem corte
    "cristaleiras", "fruteiras", "penteadeiras", "mesas-de-cabeceira",
    "escrivaninha", "sapateiras",
}

# Produtos específicos que devem usar fit (sem corte) mesmo fora das categorias
# FIT_ONLY — diagnóstico Tarefa D: imagens cortadas (cover+crop) cortavam o móvel.
FORCE_FIT_IDS = {14, 29, 31, 33, 46, 53, 55, 56, 57, 58, 90, 91, 92, 93, 103, 119, 132, 136}

# Produtos cuja categoria é FIT_ONLY por padrão, mas cujas fotos (mesmo ensaio,
# móvel centralizado com folga nas laterais) permitem crop-fill sem cortar o
# móvel — usado pra padronizar escala entre fotos do mesmo produto que têm
# proporção de origem diferente (ex: id 5, 3 cores do mesmo shooting).
FORCE_CROP_IDS = {5, 9, 112}

TEST_IDS = None

# Imagens técnicas (fichas com cotas/medidas) — não entram no catálogo.
# Removidas após revisão visual; ver _catalogo/imagens_processadas/_removidas/
EXCLUDE_SOURCES = {
    "c:/Imagens/Catalogo/songes/box/solteiro/solteiro.png",
    "c:/Imagens/Catalogo/kamabel/Italia/beliche/medida.png",
    "c:/Imagens/Catalogo/kamabel/palmo/medida.png",
    "c:/Imagens/Catalogo/kamabel/Italia/camaCasal/medida.png",
    "c:/Imagens/Catalogo/Cambel/CamaSolteiro/SolteiroInformaçoes.png",
    "c:/Imagens/Catalogo/Cambel/CamaSolteiro/medidasSolteiro.png",
    "c:/Imagens/Catalogo/kamabel/Italia/camaSolteiro/medida.png",
    "c:/Imagens/Catalogo/bechara/cadeira/cantiga/cadeira-cantiga-boucle-bege-madeira-maci-a-bechara-6-medidas.webp",
    "c:/Imagens/Catalogo/açoNobre/mesaComCadeiras/cadeiraMaxEmedidas.png",
    "c:/Imagens/Catalogo/bechara/rack/Juquehy/aberto.png",
}

# Imagens "sem fundo" / fundo preto removidas na revisão visual (Tarefa C Bloco 2).
# Lista mantida em dados/sem_fundo_excluir.txt para não regenerar essas processadas.
for _lst in ("sem_fundo_excluir.txt", "medidas_excluir.txt", "interna_excluir.txt",
             "descartadas_excluir.txt"):
    _p = os.path.join(CATALOG_ROOT, "_catalogo", "dados", _lst)
    if os.path.exists(_p):
        with open(_p, encoding="utf-8") as _f:
            EXCLUDE_SOURCES |= {ln.strip() for ln in _f if ln.strip()}


def get_image_ratio(path):
    try:
        result = subprocess.run(
            ["magick", "identify", "-format", "%[fx:w/h]", path],
            capture_output=True, text=True, timeout=15
        )
        return float(result.stdout.strip())
    except Exception:
        return 1.0


def process_image(src, dst, force_fit=False):
    ratio = get_image_ratio(src)

    if not force_fit and ratio >= RATIO_THRESHOLD:
        cmd = [
            "magick", src,
            "-thumbnail", f"{WIDTH}x{HEIGHT}^",
            "-gravity", "center",
            "-extent", f"{WIDTH}x{HEIGHT}",
            "-quality", str(QUALITY),
            dst
        ]
    else:
        cmd = [
            "magick", src,
            "-thumbnail", f"{WIDTH}x{HEIGHT}",
            "-gravity", "center",
            "-background", BG_COLOR,
            "-extent", f"{WIDTH}x{HEIGHT}",
            "-quality", str(QUALITY),
            dst
        ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0, result.stderr.strip()


def main():
    with open(JSON_PATH, encoding="utf-8") as f:
        products = json.load(f)

    if TEST_IDS:
        products = [p for p in products if p["id"] in TEST_IDS]
        print(f"MODO TESTE: processando {len(products)} produtos (IDs: {TEST_IDS})\n")

    total_processed = 0
    total_skipped = 0
    total_errors = 0
    errors_list = []

    for idx, product in enumerate(products, 1):
        cat = product["categoria"]
        pid = product["id"]
        images = product["imagens"]

        out_dir = os.path.join(OUTPUT_BASE, cat)
        os.makedirs(out_dir, exist_ok=True)

        processed = 0
        skipped = 0

        force_fit = (cat in FIT_ONLY_CATEGORIES or pid in FORCE_FIT_IDS) and pid not in FORCE_CROP_IDS

        for seq, img_path in enumerate(images, 1):
            if img_path in EXCLUDE_SOURCES:
                continue  # ficha técnica — não entra no catálogo

            src = img_path.replace("/", os.sep)
            dst = os.path.join(out_dir, f"{pid}_{seq:03d}.jpg")

            if os.path.exists(dst):
                skipped += 1
                total_skipped += 1
                continue

            ok, err = process_image(src, dst, force_fit=force_fit)
            if ok:
                processed += 1
                total_processed += 1
            else:
                total_errors += 1
                errors_list.append(f"  #{pid} seq {seq}: {src}\n    {err}")

        status = f"[{cat}] produto {idx}/{len(products)} (#{pid}) — "
        parts = []
        if processed:
            parts.append(f"{processed} processadas")
        if skipped:
            parts.append(f"{skipped} puladas")
        status += ", ".join(parts) if parts else "sem imagens"
        print(status)

    print(f"\n{'='*50}")
    print(f"✓ Total processadas: {total_processed}")
    print(f"✓ Total puladas (já existiam): {total_skipped}")

    if total_errors:
        print(f"\n✗ Erros: {total_errors}")
        for e in errors_list:
            print(e)
    else:
        print(f"✓ Erros: 0")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        TEST_IDS = [116, 106, 64]
    main()
