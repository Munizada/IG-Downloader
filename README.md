# IG Post Downloader

Bot em Python para baixar posts de perfis do Instagram usando um navegador real com sessao persistente.

Nome sugerido para o repositorio no GitHub: `ig-post-downloader`

## Preparacao

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Primeiro uso

```powershell
.\.venv\Scripts\python .\baixar_instagram.py "https://www.instagram.com/nomedoperfil/"
```

No primeiro uso o Instagram provavelmente vai pedir login.
O script abre um navegador real instalado no Windows, priorizando Brave e depois Edge/Chrome, espera voce entrar na sua conta e salva a sessao em uma subpasta de:

`downloads_instagram\.playwright-instagram-session\`

Depois disso, as proximas execucoes costumam funcionar sem pedir login de novo.

## Uso basico

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil
```

Por padrao ele baixa tudo: fotos, videos e carrosseis mistos.

## Escolher tipo de midia

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --midia tudo
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --midia foto
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --midia video
```

## Escolher navegador

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --browser auto
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --browser brave
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --browser edge
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --browser chrome
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --browser chromium
```

## Testar com poucos posts

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --max-posts 3
```

## Rodar headless depois da sessao salva

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --headless
```

## Falhar sem esperar login

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --headless --nao-esperar-login
```

## Saida

Os arquivos ficam por padrao em `downloads_instagram\<perfil>\`.
Cada post vira uma pasta numerada, por exemplo:

`POST 01\01.mp4`

`POST 02\01.mp4`

Dentro de cada pasta os arquivos saem numerados como `01.mp4`, `02.jpg` e assim por diante.

## Rodar com dois cliques

Use [baixar_instagram.bat](C:/Users/tutim/Documents/Codex/2026-05-04/quero-q-tu-fa-a-um/baixar_instagram.bat:1) para abrir um prompt simples, instalar o que faltar e escolher perfil, tipo de midia e limite.

Se quiser um atalho ja focado em baixar tudo pelo Brave, use [baixar_instagram_brave.bat](C:/Users/tutim/Documents/Codex/2026-05-04/quero-q-tu-fa-a-um/baixar_instagram_brave.bat:1). Ele pede o perfil e usa `--midia tudo --browser brave`.

Se preferir Edge, use [baixar_instagram_edge.bat](C:/Users/tutim/Documents/Codex/2026-05-04/quero-q-tu-fa-a-um/baixar_instagram_edge.bat:1).

## Publicar no GitHub

O projeto ja esta com `.gitignore` para nao subir:

- `.venv`
- `downloads_instagram`
- cookies e sessao local
- arquivos de debug

Com isso, seus amigos recebem so o bot, sem seu login nem os arquivos baixados.
