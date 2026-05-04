@echo off
setlocal
cd /d "%~dp0"

set "PERFIL_PADRAO=%~1"
if "%PERFIL_PADRAO%"=="" set "PERFIL_PADRAO=nomedoperfil"

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  python -m venv .venv
  if errorlevel 1 goto :erro
)

echo Preparando dependencias...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 goto :erro

set "PERFIL=%PERFIL_PADRAO%"
set "PERFIL_INPUT="
set /p PERFIL_INPUT=Perfil ou URL do Instagram [padrao: %PERFIL_PADRAO%]: 
if defined PERFIL_INPUT set "PERFIL=%PERFIL_INPUT%"

set "MIDIA=tudo"
set "MIDIA_INPUT="
set /p MIDIA_INPUT=Tipo de midia [tudo/foto/video] (padrao: tudo): 
if defined MIDIA_INPUT set "MIDIA=%MIDIA_INPUT%"

set "BROWSER=brave"
set "BROWSER_INPUT="
set /p BROWSER_INPUT=Navegador [brave/edge/auto/chrome/chromium] (padrao: brave): 
if defined BROWSER_INPUT set "BROWSER=%BROWSER_INPUT%"

set "MAXPOSTS="
set /p MAXPOSTS=Limite de posts [Enter = todos]: 

echo.
echo Rodando downloader...
echo O navegador real vai abrir. Depois do login, deixe o perfil aberto que o bot recarrega e segue sozinho.
if "%MAXPOSTS%"=="" (
  ".venv\Scripts\python.exe" ".\baixar_instagram.py" "%PERFIL%" --midia "%MIDIA%" --browser "%BROWSER%"
) else (
  ".venv\Scripts\python.exe" ".\baixar_instagram.py" "%PERFIL%" --midia "%MIDIA%" --browser "%BROWSER%" --max-posts "%MAXPOSTS%"
)
if errorlevel 1 goto :erro

echo.
echo Finalizado. Pressione qualquer tecla para fechar.
pause >nul
exit /b 0

:erro
echo.
echo Ocorreu um erro. Pressione qualquer tecla para fechar.
pause >nul
exit /b 1
