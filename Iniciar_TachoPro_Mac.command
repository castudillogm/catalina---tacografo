#!/bin/bash
# Tacho Pro - Camila Launcher for Mac

# Cambiar al directorio donde está el script
cd "$(dirname "$0")"

echo "============================================"
echo "      INICIANDO TACHO PRO - CAMILA (MAC)"
echo "============================================"
echo ""

# Detener instancias previas si las hay
killall webserver_mac_arm64 webserver_mac_amd64 > /dev/null 2>&1

# Detectar Arquitectura
ARCH=$(uname -m)

if [ "$ARCH" == "arm64" ]; then
    echo "[1/2] Detectado Apple Silicon (M1/M2/M3)..."
    chmod +x ./webserver_mac_arm64 ./dddparser_mac_arm64
    cp ./dddparser_mac_arm64 ./dddparser
    ./webserver_mac_arm64 &
else
    echo "[1/2] Detectado Intel Mac..."
    chmod +x ./webserver_mac_amd64 ./dddparser_mac_amd64
    cp ./dddparser_mac_amd64 ./dddparser
    ./webserver_mac_amd64 &
fi

echo "[2/2] Esperando a que el servidor arranque..."
sleep 2

echo "[!] Abriendo navegador en http://127.0.0.1:8080/"
open "http://127.0.0.1:8080/"

echo ""
echo "============================================"
echo "            PROCESO COMPLETADO"
echo "============================================"
echo "Puedes cerrar esta ventana de Terminal."
echo ""
