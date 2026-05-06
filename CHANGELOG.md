# Changelog

## v1.1.0 - 2026-05-06

- adicionado launcher universal `ig_downloader.py`
- auto-criacao de `.venv` e instalacao de dependencias
- suporte preparado para Windows, macOS e Linux
- fallback automatico para Chromium do Playwright
- novo script `baixar_instagram.sh` para Linux e macOS
- novo script `baixar_instagram.command` para facilitar no macOS
- novo `build_windows_exe.bat` para gerar executavel Windows
- workflow do GitHub Actions para builds multi-plataforma

## v1.0.0 - 2026-05-04

- lancamento inicial do IG Post Downloader
- download de fotos, videos e carrosseis de perfis do Instagram
- login com navegador real e sessao persistente
- suporte a Brave, Edge, Chrome e Chromium
- organizacao automatica em pastas `POST 01`, `POST 02`, `POST 03`...
- conversao de videos para `H.264 + AAC` para melhorar compatibilidade
- atalhos `.bat` para uso rapido no Windows
