@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado. Rode baixar_instagram.bat pelo menos uma vez.
  exit /b 1
)

echo Instalando dependencias de build...
".venv\Scripts\python.exe" -m pip install -q -r requirements-build.txt
if errorlevel 1 exit /b 1

echo Gerando executavel Windows...
".venv\Scripts\python.exe" -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onedir ^
  --name IG-Downloader ^
  --collect-all playwright ^
  --collect-all yt_dlp ^
  --collect-all imageio_ffmpeg ^
  ig_downloader.py
if errorlevel 1 exit /b 1

echo.
echo Build concluido em dist\IG-Downloader\
exit /b 0
