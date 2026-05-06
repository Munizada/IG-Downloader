@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py"
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD goto :sem_python

echo Abrindo launcher universal...
%PYTHON_CMD% ".\ig_downloader.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
  echo Finalizado. Pressione qualquer tecla para fechar.
) else (
  echo Ocorreu um erro. Pressione qualquer tecla para fechar.
)
pause >nul
exit /b %EXIT_CODE%

:sem_python
echo.
echo Python nao foi encontrado no PATH.
echo Instale Python 3.11+ ou use o executavel gerado em dist\IG-Downloader\.
pause >nul
exit /b 1

:erro
echo.
echo Ocorreu um erro. Pressione qualquer tecla para fechar.
pause >nul
exit /b 1
