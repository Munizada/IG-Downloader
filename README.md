# IG Post Downloader

Baixador de posts do Instagram em Python com navegador real, sessao persistente e organizacao automatica por post.

Descricao curta sugerida para o GitHub:
`Download de posts do Instagram com login em navegador real, sessao persistente e exportacao organizada por post.`

## O que ele faz

- baixa fotos, videos e carrosseis
- usa navegador real para login, sem janela fake
- reaproveita a sessao salva nas proximas execucoes
- organiza a saida em pastas `POST 01`, `POST 02`, `POST 03`...
- converte videos para `H.264 + AAC`, melhorando compatibilidade

## Requisitos

- Windows
- Python 3.11+
- Brave, Edge, Chrome ou Chromium instalado

## Instalacao

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

## Primeiro uso

```powershell
.\.venv\Scripts\python .\baixar_instagram.py "https://www.instagram.com/nomedoperfil/"
```

No primeiro uso o Instagram provavelmente vai pedir login. O script abre um navegador real instalado no Windows, priorizando Brave e depois Edge/Chrome, espera voce entrar na conta e salva a sessao em:

`downloads_instagram\.playwright-instagram-session\`

Depois disso, as proximas execucoes costumam funcionar sem pedir login de novo.

## Uso basico

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil
```

Por padrao ele baixa tudo: fotos, videos e carrosseis mistos.

## Exemplos

Baixar tudo:

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --midia tudo
```

Baixar so fotos:

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --midia foto
```

Baixar so videos:

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --midia video
```

Usar um navegador especifico:

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --browser brave
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --browser edge
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --browser chrome
```

Testar com poucos posts:

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --max-posts 3
```

Rodar sem abrir janela depois da sessao salva:

```powershell
.\.venv\Scripts\python .\baixar_instagram.py nomedoperfil --headless
```

## Saida

Os arquivos ficam por padrao em `downloads_instagram\<perfil>\`.

Exemplo:

```text
downloads_instagram\
  nomedoperfil\
    POST 01\
      01.mp4
    POST 02\
      01.jpg
      02.jpg
    POST 03\
      01.mp4
```

## Atalhos .bat

- `baixar_instagram.bat`: pergunta perfil, tipo de midia, navegador e limite
- `baixar_instagram_brave.bat`: fluxo direto pelo Brave
- `baixar_instagram_edge.bat`: fluxo direto pelo Edge

## Observacoes

- sem login, alguns perfis podem ficar bloqueados pelo Instagram
- a sessao, cookies e downloads ficam fora do Git por causa do `.gitignore`
- os videos saem em formato compativel para reduzir casos de video preto ou sem audio

## Publicacao

O `.gitignore` ja evita subir:

- `.venv`
- `downloads_instagram`
- cookies e sessao local
- arquivos temporarios e de debug
