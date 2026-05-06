@echo off
setlocal
cd /d "%~dp0"

call ".\baixar_instagram.bat" --browser brave %*
