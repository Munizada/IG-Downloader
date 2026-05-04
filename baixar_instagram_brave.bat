@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual...
  python -m venv .venv
  if errorlevel 1 goto :erro
)

echo Preparando dependencias...
".venv\Scripts\python.exe" -m pip install -q -r requirements.txt
if errorlevel 1 goto :erro

set "PERFIL="
set /p PERFIL=Perfil ou URL do Instagram: 
if not defined PERFIL goto :erro_perfil

set "HEADLESS_ARG="
if exist ".\downloads_instagram\.playwright-instagram-session\brave\Default" set "HEADLESS_ARG=--headless"

echo.
echo Baixando tudo pelo Brave...
if "%HEADLESS_ARG%"=="" echo Uma janela real do Brave vai abrir. Depois do login, deixe o perfil aberto que o bot recarrega e segue sozinho.
if not "%HEADLESS_ARG%"=="" echo Sessao encontrada. Rodando em segundo plano sem abrir janela.
".venv\Scripts\python.exe" ".\baixar_instagram.py" "%PERFIL%" --midia tudo --browser brave %HEADLESS_ARG%
if errorlevel 1 goto :erro

echo.
echo Finalizado. Pressione qualquer tecla para fechar.
pause >nul
exit /b 0

:erro_perfil
echo.
echo Voce precisa informar um perfil ou URL. Pressione qualquer tecla para fechar.
pause >nul
exit /b 1

:erro
echo.
echo Ocorreu um erro. Pressione qualquer tecla para fechar.
pause >nul
exit /b 1
