# IG Post Downloader

Baixador de posts do Instagram com launcher cross-platform, auto-instalacao de dependencias, sessao persistente e exportacao organizada por post.

Descricao curta sugerida para o GitHub:
`Instagram downloader com launcher universal, login em navegador real, fallback automatico para Chromium e exportacao organizada por post.`

## O que ele faz

- baixa fotos, videos e carrosseis
- organiza a saida em pastas `POST 01`, `POST 02`, `POST 03`...
- reaproveita a sessao salva nas proximas execucoes
- usa navegador do sistema quando existir
- faz fallback automatico para Chromium do Playwright quando necessario
- converte videos para `H.264 + AAC`, melhorando compatibilidade
- cria o `.venv` e instala dependencias sozinho pelo launcher

## Plataformas

- Windows: suportado e validado localmente
- macOS: preparado no codigo e no launcher
- Linux: preparado no codigo e no launcher

Importante:

- um unico `.exe` nao roda em todos os sistemas operacionais
- o executavel gerado aqui e para Windows
- para macOS e Linux, o projeto roda pelo launcher Python ou por builds gerados no GitHub Actions
- nenhum downloader de Instagram consegue prometer `100% sem erro`, porque o proprio Instagram pode exigir login, mudar layout ou bloquear acesso

## Jeito mais facil de usar

### Windows

- clique em `baixar_instagram.bat`
- ou rode `dist\IG-Downloader\IG-Downloader.exe` depois de gerar o build

### macOS e Linux

```bash
python3 ig_downloader.py
```

Ou:

```bash
./baixar_instagram.sh
```

## Auto-instalacao

O launcher `ig_downloader.py`:

- cria `.venv` automaticamente
- instala `requirements.txt` automaticamente
- reinicia dentro do ambiente virtual
- abre um modo interativo se voce nao passar argumentos

## Exemplos

Baixar tudo:

```powershell
python ig_downloader.py nomedoperfil --midia tudo
```

Baixar so fotos:

```powershell
python ig_downloader.py nomedoperfil --midia foto
```

Baixar so videos:

```powershell
python ig_downloader.py nomedoperfil --midia video
```

Escolher navegador:

```powershell
python ig_downloader.py nomedoperfil --browser auto
python ig_downloader.py nomedoperfil --browser chrome
python ig_downloader.py nomedoperfil --browser edge
python ig_downloader.py nomedoperfil --browser brave
python ig_downloader.py nomedoperfil --browser chromium
```

Testar com poucos posts:

```powershell
python ig_downloader.py nomedoperfil --max-posts 3
```

Rodar sem abrir janela:

```powershell
python ig_downloader.py nomedoperfil --headless
```

## Navegadores

O modo `auto` tenta nesta ordem:

1. Chrome
2. Edge
3. Brave
4. Chromium do Playwright

Se a maquina nao tiver navegador compativel instalado, o fallback esperado e o `chromium`, que o Playwright instala automaticamente na versao Python.

## Saida

Os arquivos ficam por padrao em `downloads_instagram/<perfil>/`.

Exemplo:

```text
downloads_instagram/
  nomedoperfil/
    POST 01/
      01.mp4
    POST 02/
      01.jpg
      02.jpg
    POST 03/
      01.mp4
```

## Arquivos principais

- `ig_downloader.py`: launcher universal com auto-setup
- `baixar_instagram.py`: nucleo do downloader
- `baixar_instagram.bat`: atalho Windows
- `baixar_instagram.sh`: atalho Linux/macOS
- `build_windows_exe.bat`: gera o executavel Windows

## Gerar executavel Windows

```powershell
.\build_windows_exe.bat
```

Saida esperada:

```text
dist/IG-Downloader/
```

## Builds automatizados no GitHub

O workflow em `.github/workflows/build-release.yml` esta preparado para:

- Windows
- macOS
- Linux

Quando voce sobe uma tag `v*`, ele gera builds em cada sistema. Isso e o caminho certo para distribuir binarios nativos por sistema operacional.

## Observacoes reais

- sem login, alguns perfis vao continuar bloqueados pelo Instagram
- um perfil pode parar de funcionar se o Instagram mudar seletores ou politicas
- a versao Windows foi validada localmente
- a logica cross-platform foi preparada, mas macOS e Linux dependem de teste nesses sistemas

## Git e privacidade

O `.gitignore` ja evita subir:

- `.venv`
- `downloads_instagram`
- cookies e sessao local
- arquivos temporarios e de debug
