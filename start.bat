@echo off
title Avatar API - Servidor Django
cd /d "%~dp0"

echo.
echo  Iniciando o servidor...
echo  Feche esta janela para desligar o site.
echo.

rem Abre o navegador depois de 4 segundos (tempo do servidor subir)
start "" powershell -NoProfile -Command "Start-Sleep -Seconds 4; Start-Process 'http://127.0.0.1:8000/'"

rem Roda o servidor com o Python do ambiente virtual (0.0.0.0 = aceita outros PCs)
".venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000

rem Se chegou aqui, deu erro - mantém a janela aberta para ver
echo.
echo  O servidor parou. Se apareceu erro acima, me envie a mensagem.
pause
