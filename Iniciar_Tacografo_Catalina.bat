@echo off
title Tacógrafo Catalina
echo ============================================
echo      INICIANDO TACÓGRAFO CATALINA
echo ============================================
echo.
echo [1/2] Arrancando servidor web en segundo plano...
:: Inicia el servidor en una ventana nueva para que no bloquee este script
start "SERVIDOR TACÓGRAFO CATALINA" cmd /c "webserver.exe"

echo [2/2] Esperando a que el servidor tome el control...
timeout /t 2 >nul

echo [!] Abriendo navegador en http://127.0.0.1:8080/
start http://127.0.0.1:8080/

echo.
echo ============================================
echo PROCESO FINALIZADO
echo No cierres la ventana negra del servidor
echo mientras estés usando la aplicación.
echo ============================================
echo.
pause
