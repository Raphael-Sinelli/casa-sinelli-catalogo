import subprocess
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def check_command(name, cmd, parse_version):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        output = (result.stdout + result.stderr).strip()
        version = parse_version(output)
        print(f"✓ {name} v{version} — OK")
        return True
    except FileNotFoundError:
        print(f"✗ {name} — NÃO ENCONTRADO")
        return False
    except Exception as e:
        print(f"✗ {name} — ERRO: {e}")
        return False


def check_python_module(name, module, version_attr="__version__"):
    try:
        mod = __import__(module)
        version = getattr(mod, version_attr, "?")
        print(f"✓ {name} v{version} — OK")
        return True
    except ImportError:
        print(f"✗ {name} — NÃO ENCONTRADO")
        return False


def main():
    print("=== Validação do ambiente ===\n")
    results = []

    results.append(("Python", True))
    print(f"✓ Python v{sys.version.split()[0]} — OK")

    results.append(("ImageMagick", check_command(
        "ImageMagick",
        ["magick", "--version"],
        lambda out: out.splitlines()[0].split()[2] if out else "?"
    )))

    results.append(("Ghostscript", check_command(
        "Ghostscript",
        ["gswin64c", "--version"],
        lambda out: out.splitlines()[0].strip() if out else "?"
    )))

    results.append(("Poppler", check_command(
        "Poppler",
        ["pdftoppm", "-v"],
        lambda out: out.splitlines()[0].split()[-1] if out else "?"
    )))

    results.append(("WeasyPrint", check_python_module("WeasyPrint", "weasyprint")))
    results.append(("Pillow", check_python_module("Pillow", "PIL")))

    failed = [name for name, ok in results if not ok]
    print()
    if not failed:
        print("Ambiente pronto para o catálogo.")
    else:
        print(f"Faltam {len(failed)} ferramenta(s): {', '.join(failed)}")


if __name__ == "__main__":
    main()
