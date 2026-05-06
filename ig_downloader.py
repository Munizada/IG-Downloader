from __future__ import annotations

import argparse
import multiprocessing
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def em_venv_do_projeto() -> bool:
    esperado = venv_python()
    try:
        return esperado.exists() and Path(sys.executable).resolve() == esperado.resolve()
    except Exception:
        return False


def garantir_venv() -> None:
    if getattr(sys, "frozen", False):
        return

    python_venv = venv_python()

    if not python_venv.exists():
        print("Criando ambiente virtual local...")
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)

    if not em_venv_do_projeto():
        print("Instalando/atualizando dependencias...")
        subprocess.run([str(python_venv), "-m", "pip", "install", "-q", "-r", str(REQUIREMENTS)], check=True)
        os.execv(str(python_venv), [str(python_venv), str(Path(__file__).resolve()), *sys.argv[1:]])


def perguntar(texto: str, padrao: str | None = None) -> str:
    sufixo = f" [{padrao}]" if padrao else ""
    valor = input(f"{texto}{sufixo}: ").strip()
    if valor:
        return valor
    return padrao or ""


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Launcher universal do IG Post Downloader."
    )
    p.add_argument("perfil", nargs="?", help="Username ou URL do perfil do Instagram")
    p.add_argument("--destino", default="downloads_instagram", help="Pasta de destino")
    p.add_argument("--midia", choices=["tudo", "foto", "video"], default="tudo", help="Tipo de midia")
    p.add_argument("--browser", choices=["auto", "brave", "edge", "msedge", "chrome", "chromium"], default="auto", help="Navegador a usar")
    p.add_argument("--max-posts", type=int, help="Limite de posts para baixar")
    p.add_argument("--headless", action="store_true", help="Roda sem abrir a janela")
    p.add_argument("--nao-esperar-login", action="store_true", help="Falha em vez de esperar login")
    p.add_argument("--nao-interativo", action="store_true", help="Nao pergunta nada faltando; falha se faltar argumento")
    return p


def completar_interativamente(args: argparse.Namespace) -> argparse.Namespace:
    if args.nao_interativo:
        if not args.perfil:
            raise SystemExit("Erro: informe o perfil ou URL, ou rode sem --nao-interativo.")
        return args

    if not args.perfil:
        print("IG Post Downloader")
        print("Se colar a URL completa do perfil, ele tambem entende.\n")
        args.perfil = perguntar("Perfil ou URL do Instagram")

    if not args.perfil:
        raise SystemExit("Erro: perfil nao informado.")

    if "--midia" not in sys.argv:
        args.midia = perguntar("Tipo de midia (tudo/foto/video)", args.midia)

    if "--browser" not in sys.argv:
        args.browser = perguntar("Navegador (auto/chrome/edge/brave/chromium)", args.browser)

    if "--max-posts" not in sys.argv:
        bruto = perguntar("Limite de posts (Enter = todos)", "")
        if bruto:
            try:
                args.max_posts = int(bruto)
            except ValueError as exc:
                raise SystemExit("Erro: limite de posts invalido.") from exc

    if "--headless" not in sys.argv and not args.nao_esperar_login:
        headless_bruto = perguntar("Rodar sem abrir janela? (s/N)", "n").lower()
        args.headless = headless_bruto in {"s", "sim", "y", "yes"}

    return args


def main() -> int:
    garantir_venv()

    from baixar_instagram import baixar_posts  # import tardio para permitir auto-setup

    args = parser().parse_args()
    args = completar_interativamente(args)

    try:
        total = baixar_posts(
            perfil=args.perfil,
            destino=Path(args.destino),
            esperar_login=not args.nao_esperar_login,
            max_posts=args.max_posts,
            headless=args.headless,
            modo_midia=args.midia,
            navegador=args.browser,
        )
    except KeyboardInterrupt:
        print("\nExecucao cancelada pelo usuario.")
        return 130
    except Exception as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    print(f"Concluido. {total} posts processados.")
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
