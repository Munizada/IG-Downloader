from __future__ import annotations

import argparse
import html
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
from urllib.request import urlopen

import requests
import imageio_ffmpeg
import yt_dlp
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


LOGIN_TEXTOS = [
    "log in",
    "entrar",
    "login",
    "mobile number, username or email",
    "telefone, nome de usuario ou email",
    "continue watching",
    "continue assistindo",
    "sign up",
    "cadastre-se",
]

PROXIMO_REGEX = re.compile(r"^(Next|Avancar|Avançar|Pr[oó]ximo)$", re.IGNORECASE)

BROWSERS = {
    "brave": {
        "nome": "Brave",
        "executaveis": [
            r"%ProgramFiles%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%ProgramFiles(x86)%\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe",
        ],
    },
    "msedge": {
        "nome": "Microsoft Edge",
        "executaveis": [
            r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
            r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
            r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe",
        ],
    },
    "chrome": {
        "nome": "Google Chrome",
        "executaveis": [
            r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
            r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
            r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
        ],
    },
}


class YtDlpSilencioso:
    def debug(self, _msg: str) -> None:
        return

    def info(self, _msg: str) -> None:
        return

    def warning(self, _msg: str) -> None:
        return

    def error(self, _msg: str) -> None:
        return


def extrair_username(entrada: str) -> str:
    valor = entrada.strip().rstrip("/")
    if not valor:
        raise ValueError("Informe um username ou URL do Instagram.")

    if "instagram.com" not in valor:
        return valor.lstrip("@")

    caminho = urlparse(valor).path.strip("/")
    if not caminho:
        raise ValueError("Nao consegui identificar o perfil na URL informada.")

    username = caminho.split("/", 1)[0].lstrip("@")
    if username.lower() in {"p", "reel", "tv", "explore"}:
        raise ValueError("A URL enviada nao parece ser de perfil.")
    return username


def slug(texto: str) -> str:
    limpo = re.sub(r"[^A-Za-z0-9._-]+", "_", texto.strip())
    return limpo.strip("._") or "arquivo"


def parse_srcset_maior(srcset: str) -> str | None:
    melhor_url = None
    melhor_largura = -1

    for parte in srcset.split(","):
        pedaco = parte.strip()
        if not pedaco:
            continue

        campos = pedaco.rsplit(" ", 1)
        url = campos[0].strip()
        largura = 0

        if len(campos) == 2 and campos[1].endswith("w"):
            try:
                largura = int(campos[1][:-1])
            except ValueError:
                largura = 0

        if largura > melhor_largura:
            melhor_largura = largura
            melhor_url = url

    return melhor_url


def perfil_url(username: str) -> str:
    return f"https://www.instagram.com/{username}/"


def post_url_absoluta(href: str) -> str:
    if href.startswith("http://") or href.startswith("https://"):
        return href
    return f"https://www.instagram.com{href}"


def detectar_total_posts_via_html(username: str) -> int | None:
    try:
        resposta = requests.get(
            perfil_url(username),
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        resposta.raise_for_status()
    except requests.RequestException:
        return None

    match = re.search(r"([0-9.,]+)\s+Posts", resposta.text, re.IGNORECASE)
    if not match:
        return None

    bruto = match.group(1).replace(".", "").replace(",", "")
    try:
        return int(bruto)
    except ValueError:
        return None


def tem_tela_de_login(page) -> bool:
    if "accounts/login" in page.url.lower():
        return True

    try:
        texto = page.locator("body").inner_text(timeout=5000).lower()
    except PlaywrightError:
        return False
    return any(chave in texto for chave in LOGIN_TEXTOS)


def contar_links_posts(page) -> int:
    try:
        return len(
            page.locator("a").evaluate_all(
                """els => els
                    .map(e => e.getAttribute('href'))
                    .filter(Boolean)
                    .filter(href => /\\/(p|reel)\\/[A-Za-z0-9_-]+\\/?$/.test(href))
                """
            )
        )
    except PlaywrightError:
        return 0


def coletar_hrefs_posts_visiveis(page, username: str) -> list[str]:
    username = username.lower().strip("@")
    try:
        hrefs = page.locator("a").evaluate_all(
            """els => els
                .map(e => e.getAttribute('href'))
                .filter(Boolean)
                .filter(href => /\\/(p|reel)\\/[A-Za-z0-9_-]+\\/?$/.test(href))
            """
        )
    except PlaywrightError:
        return []

    vistos: set[str] = set()
    saida: list[str] = []
    for href in hrefs:
        caminho = href.lower()
        if f"/{username}/p/" not in caminho and f"/{username}/reel/" not in caminho and not caminho.startswith("/p/") and not caminho.startswith("/reel/"):
            continue
        absoluto = post_url_absoluta(href)
        if absoluto not in vistos:
            vistos.add(absoluto)
            saida.append(absoluto)
    return saida


def perfil_parece_acessivel(page, username: str) -> bool:
    try:
        titulo = page.title().lower()
    except PlaywrightError:
        titulo = ""

    url_atual = page.url.lower()
    if username.lower() not in url_atual and username.lower() not in titulo:
        return False

    return not tem_tela_de_login(page)


def clicar_se_visivel(page, nomes: Iterable[str]) -> None:
    for nome in nomes:
        try:
            botao = page.get_by_role("button", name=re.compile(rf"^{re.escape(nome)}$", re.IGNORECASE))
            if botao.first.is_visible():
                botao.first.click(timeout=1500)
                page.wait_for_timeout(600)
        except PlaywrightError:
            continue


def limpar_popups(page) -> None:
    clicar_se_visivel(page, ["Not now", "Agora nao", "Agora não", "Cancel", "Close"])


def aguardar_login(page, url: str, esperar_login: bool) -> None:
    username = extrair_username(url)
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(4000)
    limpar_popups(page)

    if contar_links_posts(page) > 0 or perfil_parece_acessivel(page, username):
        print("Perfil acessivel. Continuando...")
        return

    if not esperar_login:
        raise RuntimeError(
            "O Instagram exigiu login e a execucao esta em modo nao interativo. "
            "Rode sem --nao-esperar-login para autenticar no navegador."
        )

    print(
        "\nO navegador abriu em modo normal.\n"
        "Faca login nessa janela e deixe o perfil carregar. "
        "O bot continua sozinho quando os posts aparecerem.\n"
    )

    inicio = time.time()
    ultima_navegacao = inicio

    while time.time() - inicio < 900:
        page.wait_for_timeout(2000)
        limpar_popups(page)

        if contar_links_posts(page) > 0:
            print("Login detectado. Coletando posts...")
            return

        if perfil_parece_acessivel(page, username):
            print("Login detectado. Reabrindo o perfil para puxar a grade...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)
                limpar_popups(page)
            except PlaywrightError:
                pass
            return

        if not tem_tela_de_login(page) and time.time() - ultima_navegacao > 8:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(2000)
            except PlaywrightError:
                pass
            ultima_navegacao = time.time()

    raise RuntimeError("Tempo esgotado esperando o login e a grade de posts aparecerem.")


def coletar_links_posts(page, username: str, total_esperado: int | None, max_posts: int | None) -> list[str]:
    alvo = perfil_url(username)
    links: list[str] = []
    vistos: set[str] = set()
    for tentativa in range(1, 5):
        page.goto(alvo, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(2500 + tentativa * 1000)
        limpar_popups(page)

        sem_novos = 0
        for _ in range(12):
            hrefs = coletar_hrefs_posts_visiveis(page, username)

            antes = len(links)
            for href in hrefs:
                if href not in vistos:
                    vistos.add(href)
                    links.append(href)

            if max_posts and len(links) >= max_posts:
                return links

            if total_esperado and len(links) >= total_esperado:
                return links

            if len(links) == antes:
                sem_novos += 1
            else:
                sem_novos = 0

            if len(links) >= 3 and sem_novos >= 2:
                return links

            if sem_novos >= 4:
                break

            page.mouse.wheel(0, 5000)
            page.wait_for_timeout(1800)
            limpar_popups(page)

    return links


def extrair_midias_visiveis(page) -> list[dict[str, str]]:
    return page.evaluate(
        """() => {
            const raiz = document.querySelector('article') || document.querySelector('main');
            if (!raiz) return [];

            const vistos = new Set();
            const itens = [];

            const add = (url, tipo) => {
                if (!url || vistos.has(url) || url.startsWith('data:')) return;
                vistos.add(url);
                itens.push({url, tipo});
            };

            const escolherSrc = (img) => {
                if (img.srcset) {
                    const melhor = img.srcset
                        .split(',')
                        .map(x => x.trim())
                        .map(x => {
                            const partes = x.split(/\\s+/);
                            const largura = partes[1] && partes[1].endsWith('w') ? parseInt(partes[1], 10) : 0;
                            return { url: partes[0], largura: Number.isFinite(largura) ? largura : 0 };
                        })
                        .sort((a, b) => b.largura - a.largura)[0];
                    if (melhor && melhor.url) return melhor.url;
                }
                return img.currentSrc || img.src || '';
            };

            raiz.querySelectorAll('video').forEach(video => {
                const url = video.currentSrc || video.src || video.querySelector('source')?.src || '';
                if (url) add(url, 'video');
            });

            raiz.querySelectorAll('img').forEach(img => {
                const rect = img.getBoundingClientRect();
                const largura = img.naturalWidth || rect.width || 0;
                const altura = img.naturalHeight || rect.height || 0;
                const alt = (img.getAttribute('alt') || '').toLowerCase();
                const url = escolherSrc(img);

                const pareceAvatar = alt.includes('profile picture') || alt.includes('foto do perfil');
                const ehPequena = largura < 250 && altura < 250 && rect.width < 200 && rect.height < 200;

                if (pareceAvatar && ehPequena) return;
                if (ehPequena) return;

                add(url, 'image');
            });

            return itens;
        }"""
    )


def ir_para_proximo_slide(page) -> bool:
    try:
        botao = page.get_by_role("button", name=PROXIMO_REGEX).first
        if botao.is_visible():
            botao.click(timeout=2000)
            page.wait_for_timeout(1200)
            return True
    except PlaywrightError:
        return False
    return False


def extrair_legenda(page) -> str | None:
    candidatos = [
        "article h1",
        "article ul li h1",
        "article div[role='button'] + div h1",
    ]
    for seletor in candidatos:
        try:
            texto = page.locator(seletor).first.text_content(timeout=1200)
        except PlaywrightError:
            texto = None
        if texto:
            texto = texto.strip()
            if texto:
                return texto
    return None


def extrair_videos_reais_do_html(page) -> list[str]:
    try:
        conteudo = page.content()
    except PlaywrightError:
        return []

    texto = (
        html.unescape(conteudo)
        .replace("\\u003C", "<")
        .replace("\\u003E", ">")
        .replace("\\/", "/")
    )
    matches = re.findall(r"<BaseURL>(https://[^<]+)</BaseURL>", texto)
    vistos: set[str] = set()
    saida: list[str] = []
    for url in matches:
        url_limpa = url.replace("&amp;", "&")
        if ".mp4" not in url_limpa:
            continue
        if "/o1/v/t2/" not in url_limpa:
            continue
        if url_limpa not in vistos:
            vistos.add(url_limpa)
            saida.append(url_limpa)
    return saida


def extrair_midias_do_post(page, url: str) -> tuple[list[dict[str, str]], str | None]:
    page.goto(url, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(2500)
    limpar_popups(page)

    midias: dict[str, dict[str, str]] = {}
    for _ in range(12):
        for item in extrair_midias_visiveis(page):
            midias[item["url"]] = item
        if not ir_para_proximo_slide(page):
            break

    videos_reais = extrair_videos_reais_do_html(page)
    if videos_reais:
        for video_url in videos_reais:
            midias[video_url] = {"url": video_url, "tipo": "video"}

    if "/reel/" in url:
        apenas_videos = [item for item in midias.values() if item["tipo"] == "video" and not item["url"].startswith("blob:")]
        if apenas_videos:
            return [apenas_videos[0]], extrair_legenda(page)

    midias_filtradas = [
        item
        for item in midias.values()
        if not item["url"].startswith("blob:")
        and not (
            item["tipo"] == "image"
            and "external." in item["url"]
            and "instagram." not in item["url"]
        )
    ]

    return midias_filtradas, extrair_legenda(page)


def filtrar_midias(midias: list[dict[str, str]], modo_midia: str) -> list[dict[str, str]]:
    if modo_midia == "tudo":
        return midias
    if modo_midia == "foto":
        return [item for item in midias if item["tipo"] == "image"]
    if modo_midia == "video":
        return [item for item in midias if item["tipo"] == "video"]
    raise ValueError(f"Modo de midia invalido: {modo_midia}")


def encontrar_executavel(navegador: str) -> Path | None:
    for modelo in BROWSERS[navegador]["executaveis"]:
        caminho = Path(os.path.expandvars(modelo))
        if caminho.exists():
            return caminho
    return None


def porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def esperar_cdp(porta: int, timeout_s: int = 30) -> None:
    inicio = time.time()
    while time.time() - inicio < timeout_s:
        try:
            with urlopen(f"http://127.0.0.1:{porta}/json/version", timeout=2):
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("O navegador abriu, mas o endpoint de depuracao nao respondeu a tempo.")


def abrir_contexto_navegador(playwright, user_data_dir: Path, headless: bool, navegador: str, url_inicial: str):
    candidatos = {
        "auto": ["brave", "msedge", "chrome", "chromium"],
        "brave": ["brave"],
        "edge": ["msedge"],
        "msedge": ["msedge"],
        "chrome": ["chrome"],
        "chromium": ["chromium"],
    }[navegador]

    ultimo_erro: Exception | None = None
    tentativas: list[str] = []

    for candidato in candidatos:
        pasta_sessao = user_data_dir / candidato
        pasta_sessao.mkdir(parents=True, exist_ok=True)

        if candidato == "chromium":
            tentativas.append("Chromium do Playwright")
            try:
                print("Abrindo Chromium do Playwright...")
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir=str(pasta_sessao),
                    headless=headless,
                    locale="pt-BR",
                    args=[] if headless else ["--start-maximized"],
                    viewport={"width": 1440, "height": 2200} if headless else None,
                )
                return context, None, None
            except PlaywrightError as exc:
                ultimo_erro = exc
                continue

        executavel = encontrar_executavel(candidato)
        nome = BROWSERS[candidato]["nome"]
        if not executavel:
            tentativas.append(f"{nome}: nao instalado")
            continue
        tentativas.append(f"{nome}: {executavel}")

        try:
            print(f"Abrindo {nome}...")
            if headless:
                context = playwright.chromium.launch_persistent_context(
                    executable_path=str(executavel),
                    user_data_dir=str(pasta_sessao),
                    headless=True,
                    locale="pt-BR",
                    viewport={"width": 1440, "height": 2200},
                )
                return context, None, None

            porta = porta_livre()
            processo = subprocess.Popen(
                [
                    str(executavel),
                    f"--remote-debugging-port={porta}",
                    f"--user-data-dir={pasta_sessao}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--new-window",
                    url_inicial,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            esperar_cdp(porta)
            browser_cdp = playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{porta}")
            context = browser_cdp.contexts[0] if browser_cdp.contexts else browser_cdp.new_context()
            return context, browser_cdp, processo
        except Exception as exc:
            ultimo_erro = exc

    raise RuntimeError(
        "Nao consegui abrir nenhum navegador compativel. Tentativas: "
        + " | ".join(tentativas)
    ) from ultimo_erro


def baixar_arquivo(url: str, destino: Path) -> None:
    with requests.get(url, stream=True, timeout=120, headers={"User-Agent": "Mozilla/5.0"}) as resposta:
        resposta.raise_for_status()
        with destino.open("wb") as arquivo:
            for chunk in resposta.iter_content(chunk_size=1024 * 256):
                if chunk:
                    arquivo.write(chunk)


def extensao_por_url(url: str, fallback: str) -> str:
    caminho = urlparse(url).path.lower()
    for ext in [".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov"]:
        if caminho.endswith(ext):
            return ext
    return fallback


def limpar_pasta(pasta: Path) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    for item in pasta.iterdir():
        if item.is_dir():
            for subitem in item.rglob("*"):
                if subitem.is_file():
                    subitem.unlink()
            for subitem in sorted(item.rglob("*"), reverse=True):
                if subitem.is_dir():
                    subitem.rmdir()
            item.rmdir()
        else:
            item.unlink()


def exportar_cookies_netscape(context, destino: Path) -> None:
    linhas = ["# Netscape HTTP Cookie File", "# Gerado automaticamente pelo bot"]
    for cookie in context.cookies():
        dominio = cookie.get("domain", "")
        if not dominio:
            continue
        http_only = cookie.get("httpOnly", False)
        dominio_saida = f"#HttpOnly_{dominio}" if http_only else dominio
        incluir_subdominios = "TRUE" if dominio.startswith(".") else "FALSE"
        caminho = cookie.get("path", "/") or "/"
        seguro = "TRUE" if cookie.get("secure") else "FALSE"
        expira = int(cookie.get("expires") or 0)
        if expira < 0:
            expira = 0
        nome = cookie.get("name", "")
        valor = cookie.get("value", "")
        linhas.append(
            "\t".join(
                [
                    dominio_saida,
                    incluir_subdominios,
                    caminho,
                    seguro,
                    str(expira),
                    nome,
                    valor,
                ]
            )
        )
    destino.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def remover_arquivos_fora_do_modo(pasta_post: Path, modo_midia: str) -> list[Path]:
    todos = sorted(item for item in pasta_post.iterdir() if item.is_file())
    if modo_midia == "tudo":
        return [item for item in todos if item.suffix.lower() in {".mp4", ".mov", ".jpg", ".jpeg", ".png", ".webp"}]

    extensoes_video = {".mp4", ".mov"}
    extensoes_foto = {".jpg", ".jpeg", ".png", ".webp"}
    manter = extensoes_video if modo_midia == "video" else extensoes_foto

    saida: list[Path] = []
    for item in todos:
        if item.suffix.lower() in manter:
            saida.append(item)
            continue
        item.unlink(missing_ok=True)
    return saida


def normalizar_video_para_compatibilidade(arquivo: Path) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    temporario = arquivo.with_name(f"{arquivo.stem}.compat.mp4")
    comando = [
        ffmpeg,
        "-y",
        "-i",
        str(arquivo),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-movflags",
        "+faststart",
        str(temporario),
    ]
    processo = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    if processo.returncode != 0 or not temporario.exists():
        temporario.unlink(missing_ok=True)
        raise RuntimeError(
            f"Falha ao converter video para formato compativel: {arquivo.name}\n{processo.stderr.strip()}"
        )
    arquivo.unlink(missing_ok=True)
    temporario.replace(arquivo)


def normalizar_arquivos_baixados(arquivos: list[Path]) -> list[Path]:
    for arquivo in arquivos:
        if arquivo.suffix.lower() in {".mp4", ".mov"}:
            normalizar_video_para_compatibilidade(arquivo)
    return arquivos


def baixar_post_via_playwright(page, post_url: str, pasta_post: Path, modo_midia: str) -> list[Path]:
    limpar_pasta(pasta_post)
    midias, _legenda = extrair_midias_do_post(page, post_url)
    midias = filtrar_midias(midias, modo_midia)
    if not midias:
        raise RuntimeError(f"Nao encontrei midias aproveitaveis no post {post_url}.")

    arquivos: list[Path] = []
    for indice, item in enumerate(midias, start=1):
        fallback = ".mp4" if item["tipo"] == "video" else ".jpg"
        ext = extensao_por_url(item["url"], fallback)
        destino = pasta_post / f"{indice:02d}{ext}"
        baixar_arquivo(item["url"], destino)
        arquivos.append(destino)

    return normalizar_arquivos_baixados(arquivos)


def baixar_post_com_yt_dlp(post_url: str, pasta_post: Path, cookies_path: Path, modo_midia: str) -> list[Path]:
    limpar_pasta(pasta_post)

    opcoes = {
        "cookiefile": str(cookies_path),
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "ffmpeg_location": imageio_ffmpeg.get_ffmpeg_exe(),
        "outtmpl": str(pasta_post / "%(autonumber)02d.%(ext)s"),
        "autonumber_start": 1,
        "windowsfilenames": True,
        "restrictfilenames": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "overwrites": True,
        "ignoreerrors": False,
        "noplaylist": False,
        "writethumbnail": False,
        "writeinfojson": False,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "logger": YtDlpSilencioso(),
    }

    try:
        with yt_dlp.YoutubeDL(opcoes) as ydl:
            ydl.download([post_url])
    except yt_dlp.utils.DownloadError as exc:
        raise RuntimeError(f"Falha ao baixar {post_url}: {exc}") from exc

    arquivos = remover_arquivos_fora_do_modo(pasta_post, modo_midia)
    if not arquivos:
        raise RuntimeError(f"O yt-dlp terminou, mas nao gerou midias aproveitaveis para {post_url}.")
    return normalizar_arquivos_baixados(arquivos)


def baixar_posts(
    perfil: str,
    destino: Path,
    esperar_login: bool,
    max_posts: int | None,
    headless: bool,
    modo_midia: str,
    navegador: str,
) -> int:
    username = extrair_username(perfil)
    destino_perfil = destino.resolve() / username
    destino_perfil.mkdir(parents=True, exist_ok=True)
    total_esperado = detectar_total_posts_via_html(username)

    user_data_dir = (destino.resolve() / ".playwright-instagram-session").resolve()
    user_data_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        context, browser_cdp, processo = abrir_contexto_navegador(
            playwright=playwright,
            user_data_dir=user_data_dir,
            headless=headless,
            navegador=navegador,
            url_inicial=perfil_url(username),
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            aguardar_login(page, perfil_url(username), esperar_login=esperar_login)
            cookies_path = (destino.resolve() / ".instagram-cookies.txt").resolve()
            exportar_cookies_netscape(context, cookies_path)
            links = coletar_links_posts(page, username, total_esperado=total_esperado, max_posts=max_posts)

            if not links:
                if tem_tela_de_login(page):
                    raise RuntimeError(
                        "O Instagram mostrou uma tela de bloqueio/login e nao liberou a grade de posts. "
                        "Rode de forma interativa para fazer login no navegador."
                    )
                raise RuntimeError("Nao consegui encontrar links de posts no perfil apos abrir a pagina.")

            if max_posts:
                links = links[:max_posts]

            print(f"Posts encontrados: {len(links)}")
            total_baixados = 0
            for indice, link in enumerate(links, start=1):
                print(f"Baixando post {indice}/{len(links)}...")
                pasta_post = destino_perfil / f"POST {indice:02d}"
                try:
                    arquivos = baixar_post_com_yt_dlp(link, pasta_post, cookies_path, modo_midia)
                except RuntimeError as exc:
                    print(f"Aviso: yt-dlp falhou em {link}. Tentando fallback do navegador...")
                    try:
                        arquivos = baixar_post_via_playwright(page, link, pasta_post, modo_midia)
                    except Exception as fallback_exc:
                        print(f"Aviso: {fallback_exc}", file=sys.stderr)
                        continue
                print(f"Arquivos salvos em {pasta_post.name}: {len(arquivos)}")
                total_baixados += 1

            return total_baixados
        finally:
            try:
                context.close()
            except Exception:
                pass
            if browser_cdp is not None:
                try:
                    browser_cdp.close()
                except Exception:
                    pass
            if processo is not None:
                try:
                    processo.terminate()
                    processo.wait(timeout=10)
                except Exception:
                    try:
                        processo.kill()
                    except Exception:
                        pass


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Baixa posts de um perfil do Instagram usando um navegador real."
    )
    parser.add_argument(
        "perfil",
        help="Username ou URL do perfil. Ex.: lifestyleo1k ou https://www.instagram.com/lifestyleo1k/",
    )
    parser.add_argument(
        "--destino",
        default="downloads_instagram",
        help="Pasta onde os arquivos serao salvos. Padrao: downloads_instagram",
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        help="Limita quantos posts baixar. Bom para teste.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Roda sem abrir a janela do navegador. Funciona melhor depois que a sessao ja foi salva.",
    )
    parser.add_argument(
        "--nao-esperar-login",
        action="store_true",
        help="Falha em vez de esperar voce fazer login no navegador.",
    )
    parser.add_argument(
        "--midia",
        choices=["tudo", "foto", "video"],
        default="tudo",
        help="Escolhe o tipo de midia para baixar. Padrao: tudo",
    )
    parser.add_argument(
        "--browser",
        choices=["auto", "brave", "edge", "msedge", "chrome", "chromium"],
        default="auto",
        help="Navegador usado para login/download. Padrao: auto",
    )
    return parser


def main() -> int:
    parser = montar_parser()
    args = parser.parse_args()

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
    except ValueError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2
    except (requests.RequestException, PlaywrightTimeoutError) as exc:
        print(f"Erro de rede ou timeout: {exc}", file=sys.stderr)
        return 3
    except RuntimeError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 4
    except Exception as exc:  # pragma: no cover
        print(f"Erro inesperado: {exc}", file=sys.stderr)
        return 1

    print(f"Concluido. {total} posts processados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
