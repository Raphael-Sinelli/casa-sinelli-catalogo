"""
03_gerar_catalogo.py
Gera catálogo HTML via Jinja2 e converte para PDF via WeasyPrint.
"""
import json
import os
import re
import sys
import io
import glob
import unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

CATALOG_ROOT = os.path.normpath(r"c:\Imagens\Catalogo")
PROJECT = os.path.join(CATALOG_ROOT, "_catalogo")
JSON_PATH = os.path.join(PROJECT, "dados", "produtos.json")
TEMPLATE_DIR = os.path.join(PROJECT, "templates")
CSS_PATH = os.path.join(PROJECT, "css", "estilo.css")
IMAGES_DIR = os.path.join(PROJECT, "imagens_processadas")
OUTPUT_DIR = os.path.join(PROJECT, "output")
HTML_OUTPUT = os.path.join(TEMPLATE_DIR, "catalogo_gerado.html")
PDF_OUTPUT = os.path.join(OUTPUT_DIR, "catalogo_impressao.pdf")
LOGO_PATH = os.path.join(PROJECT, "assets", "logo.png")

MAX_IMAGES = 12
PER_PAGE = 4

# Tarefa C Bloco 6: imagem fixada por (id, cor normalizada) -> seq específico.
IMAGE_PINS = {
    (123, "cinza"): 25, (123, "marrom"): 79, (123, "prata"): 49, (123, "verde"): 72,
}
PRODUCT_MAX_IMAGES = {}

# GROUP_PER_COLOR: {id: max_por_cor} — cada cor vira sua própria seção/página.
GROUP_PER_COLOR = {117: 4, 120: 4, 125: 4}
# COLOR_SORTED: 1 imagem por cor, na ordem do rodapé, paginação normal (4/página).
COLOR_SORTED = {118, 130}


def to_file_url(path):
    return "file:///" + os.path.normpath(path).replace("\\", "/")


def _norm_cor(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s.lower())


def get_processed_images(category, product_id, cores=None, origens=None):
    pattern = os.path.join(IMAGES_DIR, category, f"{product_id}_*.jpg")
    all_files = sorted(glob.glob(pattern))
    limit = PRODUCT_MAX_IMAGES.get(product_id, MAX_IMAGES)

    if not cores or not origens:
        return all_files[:limit]

    entries = []
    for f in all_files:
        seq = int(os.path.splitext(os.path.basename(f))[0].split("_")[1])
        src = origens[seq - 1] if 1 <= seq <= len(origens) else ""
        entries.append((seq, f, _norm_cor(src)))

    selected, used = [], set()
    for cor in cores:
        nc = _norm_cor(cor)
        if not nc:
            continue
        pin = IMAGE_PINS.get((product_id, nc))
        picked = False
        if pin is not None:
            for seq, fpath, npath in entries:
                if seq == pin and seq not in used:
                    selected.append((seq, fpath))
                    used.add(seq)
                    picked = True
                    break
        if not picked:
            for seq, fpath, npath in entries:
                if seq not in used and nc in npath:
                    selected.append((seq, fpath))
                    used.add(seq)
                    break

    for seq, fpath, npath in entries:
        if len(selected) >= limit:
            break
        if seq not in used:
            selected.append((seq, fpath))
            used.add(seq)

    selected.sort(key=lambda x: x[0])
    return [fpath for _, fpath in selected]


def images_grouped_by_color(category, product_id, cores, origens, max_per_color):
    """Retorna lista de grupos (1 por cor, na ordem de `cores`), cada grupo com
    até max_per_color caminhos de arquivo processado (ordem de seq)."""
    all_files = sorted(glob.glob(os.path.join(IMAGES_DIR, category, f"{product_id}_*.jpg")))
    entries = []
    for f in all_files:
        seq = int(os.path.splitext(os.path.basename(f))[0].split("_")[1])
        src = origens[seq - 1] if 1 <= seq <= len(origens) else ""
        entries.append((seq, f, _norm_cor(src)))
    entries.sort(key=lambda x: x[0])

    groups, used = [], set()
    for cor in cores:
        nc = _norm_cor(cor)
        if not nc:
            continue
        g = []
        for seq, fpath, npath in entries:
            if seq not in used and nc in npath:
                g.append(fpath)
                used.add(seq)
                if len(g) >= max_per_color:
                    break
        if g:
            groups.append(g)
    return groups


def chunk_images(images):
    pages = []
    for i in range(0, len(images), PER_PAGE):
        chunk = images[i:i + PER_PAGE]
        pages.append({
            "images": [to_file_url(img) for img in chunk],
            "count": len(chunk),
        })
    if not pages:
        pages.append({"images": [], "count": 0})
    return pages


def format_cores(cores):
    if not cores:
        return ""
    return ", ".join(cores)   # sem truncação — mostra todas as cores


_UNIT = r"(mm|cm|m)?"


def _to_cm(num, unit):
    v = float(num.replace(",", "."))
    if unit:
        unit = unit.lower()
    else:
        unit = "m" if v < 10 else "cm"   # sem unidade: <10 = metros, senão cm
    if unit == "mm":
        v /= 10
    elif unit == "m":
        v *= 100
    return f"{int(round(v))}cm"


def _find(text, labels):
    """Acha 'rótulo [: - –] número [unidade]' (unidade default cm)."""
    pat = r"(?:" + "|".join(labels) + r")\s*[:\-–]?\s*(\d+(?:[.,]\d+)?)\s*" + _UNIT + r"\b"
    m = re.search(pat, text, re.I)
    return _to_cm(m.group(1), m.group(2)) if m else None


def _fmt_m(v):
    s = f"{v:.2f}".replace(".", ",")
    if s.endswith("0"):
        s = s[:-1]
    if s.endswith(","):
        s = s[:-1]
    return s


def format_medidas(text):
    """Extrai Alt/Larg/Prof (tudo em cm) do medidas_texto. Ruído -> vazio."""
    if not text or not text.strip():
        return ""
    t = text.replace("×", "x").replace("\n", " ")

    alt  = _find(t, [r"altura\s*total", "altura", r"alt\.?"])
    larg = _find(t, [r"largura\s*total", "largura", "frente", r"larg\.?"])
    prof = _find(t, ["profundidade", "comprimento", r"prof\.?", r"comp\.?"])

    # padrão reverso: "121 cm de altura x 155 cm de largura x 206 cm de comprimento"
    for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?\s*de\s*"
                         r"(altura|largura|profundidade|comprimento)", t, re.I):
        val, dim = _to_cm(m.group(1), m.group(2)), m.group(3).lower()
        if dim == "altura" and not alt:
            alt = val
        elif dim == "largura" and not larg:
            larg = val
        elif dim in ("profundidade", "comprimento") and not prof:
            prof = val

    # formato "(L x A x P): 110 x 137 x 48 cm"
    m = re.search(r"L\s*x\s*A\s*x\s*P\)?\s*:?\s*(\d+(?:[.,]\d+)?)\s*x\s*"
                  r"(\d+(?:[.,]\d+)?)\s*x\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?", t, re.I)
    if m:
        u = m.group(4)
        larg = larg or _to_cm(m.group(1), u)
        alt  = alt  or _to_cm(m.group(2), u)
        prof = prof or _to_cm(m.group(3), u)

    # rótulos de uma letra "A: 0,77 | L: 0,75 | P: 1,20" (só se os três existirem)
    num = r"\s*:\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?"
    if (re.search(r"\bA" + num, t) and re.search(r"\bL" + num, t)
            and re.search(r"\bP" + num, t)):
        ma, ml, mp = (re.search(r"\b" + L + num, t) for L in "ALP")
        if ma and not alt:  alt  = _to_cm(ma.group(1), ma.group(2))
        if ml and not larg: larg = _to_cm(ml.group(1), ml.group(2))
        if mp and not prof: prof = _to_cm(mp.group(1), mp.group(2))

    # múltiplos tamanhos (sofás): faixa de larguras em metros (>= 1,3 m)
    width_tokens = re.findall(r"(\d[.,]\d{2})\s*[mM]\b", t)
    vals = sorted({float(w.replace(",", ".")) for w in width_tokens
                   if float(w.replace(",", ".")) >= 1.3})
    if len(vals) >= 3:
        larg = f"{_fmt_m(vals[0])}–{_fmt_m(vals[-1])}m"

    parts = []
    if alt:
        parts.append(f"Alt: {alt}")
    if larg:
        parts.append(f"Larg: {larg}")
    if prof:
        parts.append(f"Prof: {prof}")
    if parts:
        return "  ".join(parts)

    # largura por tamanho: "Casal: 160cm; Queen: 150cm; Solteiro: 90cm"
    first = text.split("\n")[0].strip()
    if re.fullmatch(r"(?:[\wçãáéíóú]+\s*:\s*\d+\s*cm\s*[;,]?\s*)+", first, re.I):
        return first

    return ""   # sem medidas estruturadas -> rodapé sem medidas (sem ruído)


def prepare_data(test_mode=False):
    with open(JSON_PATH, encoding="utf-8") as f:
        products = json.load(f)

    cat_order = []
    cat_map = {}

    for p in products:
        cat = p["categoria"]
        if cat not in cat_map:
            cat_map[cat] = {
                "slug": cat,
                "display_name": p["nome_exibicao"],
                "products": [],
            }
            cat_order.append(cat)

        pid = p["id"]
        if pid in GROUP_PER_COLOR:
            # cada cor vira sua própria página (até N por cor)
            groups = images_grouped_by_color(cat, pid, p.get("cores"), p.get("imagens"),
                                             GROUP_PER_COLOR[pid])
            pages = []
            for g in groups:
                pages.extend(chunk_images(g))
            if not pages:
                pages = [{"images": [], "count": 0}]
        elif pid in COLOR_SORTED:
            # 1 por cor na ordem do rodapé, paginação normal
            groups = images_grouped_by_color(cat, pid, p.get("cores"), p.get("imagens"), 1)
            images = [f for g in groups for f in g]
            pages = chunk_images(images)
        else:
            images = get_processed_images(cat, pid, p.get("cores"), p.get("imagens"))
            pages = chunk_images(images)
        cat_map[cat]["products"].append({
            "id": p["id"],
            "pages": pages,
            "cores_text": format_cores(p["cores"]),
            "medidas_text": (p.get("medidas_rodape") or "").strip()
                            or format_medidas(p["medidas_texto"]),
            "modulado": bool(p.get("modulado")),
            "sofa_cama": bool(p.get("sofa_cama")),
            "observacao": (p.get("observacao") or "").strip(),
        })

    categories = [cat_map[c] for c in cat_order]

    if test_mode:
        first = categories[0]
        first["products"] = first["products"][:2]
        categories = [first]

    return {
        "logo_path": to_file_url(LOGO_PATH),
        "css_path": to_file_url(CSS_PATH),
        "categories": categories,
    }


def main():
    test_mode = "--test" in sys.argv

    if test_mode:
        print("MODO TESTE: capa + sumário + 1 categoria + 2 produtos\n")

    data = prepare_data(test_mode=test_mode)

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template("catalogo.html")
    html_content = template.render(**data)

    with open(HTML_OUTPUT, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✓ HTML gerado: {HTML_OUTPUT}")

    n_cats = len(data["categories"])
    n_prod_pages = sum(
        len(prod["pages"])
        for cat in data["categories"]
        for prod in cat["products"]
    )
    n_products = sum(len(cat["products"]) for cat in data["categories"])
    est_pages = 2 + n_cats + n_prod_pages
    print(f"  {n_products} produtos, {n_cats} categorias")
    print(f"  Páginas estimadas: {est_pages}")

    output_path = os.path.join(OUTPUT_DIR, "catalogo_teste.pdf") if test_mode else PDF_OUTPUT
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\nGerando PDF...")
    html = HTML(filename=HTML_OUTPUT)
    html.write_pdf(output_path)

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✓ PDF gerado: {output_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
