"""
script_04_comprimir.py
Comprime o catálogo PDF (saída do script 03) para envio via WhatsApp (alvo <= 15 MB).
Usa Ghostscript (gswin64c/gs no PATH). Tenta /ebook (150dpi); se ainda > alvo, /screen (72dpi).
Fallback: instruções claras se o Ghostscript não estiver instalado.

Uso:
    python script_04_comprimir.py            # entrada/saída padrão
    python script_04_comprimir.py ENTRADA.pdf SAIDA.pdf
"""
import os
import sys
import io
import shutil
import subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

PROJECT = os.path.normpath(r"c:\Imagens\Catalogo\_catalogo")
DEFAULT_INPUT = os.path.join(PROJECT, "output", "catalogo_impressao.pdf")
DEFAULT_OUTPUT = os.path.join(PROJECT, "output", "catalogo_whatsapp.pdf")
TARGET_MB = 15.0
PROFILES = ["ebook", "screen"]   # ordem: melhor qualidade primeiro


def find_ghostscript():
    for cand in ("gswin64c", "gswin32c", "gs"):
        path = shutil.which(cand)
        if path:
            return path
    return None


def mb(path):
    return os.path.getsize(path) / (1024 * 1024)


def compress(gs, src, dst, profile):
    cmd = [
        gs,
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{profile}",
        "-dNOPAUSE", "-dBATCH", "-dQUIET",
        "-dDetectDuplicateImages=true",
        "-dCompressFonts=true",
        f"-sOutputFile={dst}",
        src,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, r.stderr.strip()


def print_fallback():
    print("✗ Ghostscript não encontrado no PATH.")
    print("\nInstale o Ghostscript:")
    print("  Windows: https://www.ghostscript.com/releases/gsdnld.html (instala gswin64c)")
    print("  Depois feche/reabra o terminal e rode este script de novo.")
    print("\nOu comprima manualmente (após instalar):")
    print('  gswin64c -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH '
          f'-sOutputFile="{DEFAULT_OUTPUT}" "{DEFAULT_INPUT}"')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    src = args[0] if len(args) >= 1 else DEFAULT_INPUT
    dst = args[1] if len(args) >= 2 else DEFAULT_OUTPUT

    if not os.path.exists(src):
        print(f"✗ PDF de entrada não encontrado: {src}")
        print("  Rode o script 03 primeiro para gerar o catálogo.")
        sys.exit(1)

    gs = find_ghostscript()
    if not gs:
        print_fallback()
        sys.exit(1)

    print(f"Entrada:     {src}  ({mb(src):.1f} MB)")
    print(f"Ghostscript: {gs}")
    print(f"Alvo:        <= {TARGET_MB:.0f} MB\n")

    best = None
    for profile in PROFILES:
        ok, err = compress(gs, src, dst, profile)
        if not ok:
            print(f"  /{profile}: FALHOU — {err}")
            continue
        size = mb(dst)
        print(f"  /{profile}: {size:.1f} MB")
        best = (profile, size)
        if size <= TARGET_MB:
            print(f"\n✓ Comprimido com /{profile}: {dst} ({size:.1f} MB) — pronto para WhatsApp.")
            return

    if best is None:
        print("\n✗ Todas as tentativas falharam. Verifique a instalação do Ghostscript.")
        sys.exit(1)

    print(f"\n⚠ Menor resultado: /{best[0]} = {best[1]:.1f} MB (acima de {TARGET_MB:.0f} MB).")
    print("  Mantido em:", dst)
    print("  Sugestões: reduzir WIDTH/HEIGHT no script 02 (reprocessar imagens),")
    print("  ou dividir o catálogo em partes para envio.")


if __name__ == "__main__":
    main()
