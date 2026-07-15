"""
01_extrair_dados.py
Lê INVENTARIO_PRODUTOS_CASA_SINELLI.md e gera _catalogo/dados/produtos.json.
"""
import json
import os
import re
import sys
import io
import unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CATALOG_ROOT = os.path.normpath(r"c:\Imagens\Catalogo")
INVENTORY_PATH = os.path.join(CATALOG_ROOT, "INVENTARIO_PRODUTOS_CASA_SINELLI.md")
OUTPUT_PATH = os.path.join(CATALOG_ROOT, "_catalogo", "dados", "produtos.json")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

MANUAL_MEDIDAS = {
    12: "Casal: 160cm; Queen: 150cm; Solteiro: 90cm",
}


def slugify(text):
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_text = nfkd.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"\s+", "-", ascii_text.lower().strip())
    return re.sub(r"[^a-z0-9-]", "", slug)


def is_excluded_image(filename):
    name = os.path.splitext(filename)[0].lower().strip()
    if re.match(r"^medidas(\s*\(\d+\))?$", name):
        return True
    if name == "tabeladepeso":
        return True
    return False


def scan_images(directory):
    images = []
    for root, _, files in os.walk(directory):
        if "_lixeira_duplicatas" in root:
            continue
        for f in sorted(files):
            ext = os.path.splitext(f)[1].lower()
            if ext not in IMAGE_EXTENSIONS:
                continue
            if is_excluded_image(f):
                continue
            images.append(os.path.join(root, f).replace("\\", "/"))
    return images


def find_product_dir(ref_path_rel, expected_count):
    ref_normalized = ref_path_rel.replace("\\", os.sep).replace("/", os.sep)
    parts = ref_normalized.split(os.sep)
    min_depth = 2
    threshold = max(1, expected_count * 0.5)

    for depth in range(len(parts) - 1, min_depth - 1, -1):
        candidate = os.path.join(CATALOG_ROOT, *parts[:depth])
        if os.path.isdir(candidate) and len(scan_images(candidate)) >= threshold:
            return candidate

    return os.path.dirname(os.path.join(CATALOG_ROOT, ref_normalized))


def read_medidas_files(directory):
    texts = []
    for root, _, files in os.walk(directory):
        for f in sorted(files):
            if f.lower().startswith("medidas") and f.lower().endswith(".txt"):
                try:
                    with open(os.path.join(root, f), encoding="utf-8") as fh:
                        content = fh.read().strip()
                        if content:
                            texts.append(content)
                except Exception:
                    pass
    return "\n".join(texts)


def parse_colors(raw):
    if not raw or raw.lower() == "não especificada":
        return []
    return [c.strip() for c in re.split(r"[,;]", raw) if c.strip()]


def parse_sizes(raw):
    if not raw or "sem medida" in raw.lower():
        return [], ""
    if ";" in raw:
        items = [s.strip() for s in raw.split(";") if s.strip()]
        return items, raw
    return [], raw


def parse_inventory():
    with open(INVENTORY_PATH, encoding="utf-8") as f:
        lines = f.readlines()

    products = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if "| Nº |" in stripped:
            in_table = True
            continue
        if in_table and stripped.startswith("|---"):
            continue
        if in_table and stripped.startswith("|"):
            cols = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cols) >= 9:
                try:
                    products.append({
                        "id": int(cols[0]),
                        "categoria_original": cols[1],
                        "nome": cols[2],
                        "fabricante": cols[3],
                        "cores_raw": cols[4],
                        "tamanhos_raw": cols[5],
                        "expected_img_count": int(cols[6]),
                        "ref_path": cols[7].strip("`"),
                        "confianca": cols[8],
                    })
                except (ValueError, IndexError):
                    continue
        elif in_table and not stripped.startswith("|"):
            break

    return products


def main():
    raw = parse_inventory()
    print(f"Produtos lidos do inventário: {len(raw)}")

    results = []
    total_images = 0
    empty = []
    low_confidence = []

    for p in raw:
        cat_slug = slugify(p["categoria_original"])
        cat_display = p["categoria_original"].upper()

        cores = parse_colors(p["cores_raw"])
        tamanhos, medidas_texto = parse_sizes(p["tamanhos_raw"])

        if p["id"] in MANUAL_MEDIDAS:
            medidas_texto = MANUAL_MEDIDAS[p["id"]]
            if ";" in medidas_texto:
                tamanhos = [t.strip() for t in medidas_texto.split(";")]

        product_dir = find_product_dir(p["ref_path"], p["expected_img_count"])
        images = scan_images(product_dir)

        medidas_from_file = read_medidas_files(product_dir)
        if medidas_from_file:
            if medidas_texto:
                medidas_texto = medidas_texto + "\n" + medidas_from_file
            else:
                medidas_texto = medidas_from_file

        total_images += len(images)

        results.append({
            "id": p["id"],
            "categoria": cat_slug,
            "nome_exibicao": cat_display,
            "cores": cores,
            "tamanhos": tamanhos,
            "medidas_texto": medidas_texto,
            "descricao": "",
            "confianca": p["confianca"],
            "imagens": images,
        })

        if not images:
            empty.append(p)
        if p["confianca"] in ("Baixa", "Média"):
            low_confidence.append(p)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Produtos extraídos: {len(results)}")
    print(f"✓ Imagens encontradas: {total_images}")
    print(f"✓ JSON salvo em: {OUTPUT_PATH}")

    if empty:
        print(f"\n⚠ Produtos SEM imagens ({len(empty)}):")
        for p in empty:
            print(f"  #{p['id']} {p['nome']} ({p['categoria_original']}) — ref: {p['ref_path']}")
    else:
        print("\n✓ Todos os produtos têm pelo menos 1 imagem.")

    if low_confidence:
        print(f"\n⚠ Produtos com confiança Baixa/Média ({len(low_confidence)}):")
        for p in low_confidence:
            print(f"  #{p['id']} {p['nome']} ({p['categoria_original']}) — {p['confianca']}")


if __name__ == "__main__":
    main()
