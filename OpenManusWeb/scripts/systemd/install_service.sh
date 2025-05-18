#!/bin/bash
# Script para instalar el servicio systemd de agent-isa

set -e  # Salir en caso de error

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ADVERTENCIA: $1${NC}"
}

# Verificar si se está ejecutando como root
if [ "$(id -u)" -ne 0 ]; then
    error "Este script debe ejecutarse como root o con sudo"
    exit 1
fi

# Obtener directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Verificar que el archivo de servicio existe
SERVICE_FILE="$SCRIPT_DIR/agent-isa.service"
if [ ! -f "$SERVICE_FILE" ]; then
    error "No se encontró el archivo de servicio: $SERVICE_FILE"
    exit 1
fi

# Copiar archivo de servicio
log "Copiando archivo de servicio a /etc/systemd/system/..."
cp "$SERVICE_FILE" /etc/systemd/system/

# Recargar systemd
log "Recargando systemd..."
systemctl daemon-reload

# Habilitar servicio
log "Habilitando servicio..."
systemctl enable agent-isa.service

# Iniciar servicio
log "Iniciando servicio..."
systemctl start agent-isa.service

# Verificar estado
log "Verificando estado del servicio..."
if systemctl is-active --quiet agent-isa.service; then
    log "Servicio iniciado correctamente ✓"
else
    error "Error al iniciar el servicio"
    systemctl status agent-isa.service
    exit 1
fi

log "Instalación del servicio completada exitosamente"
log "Puede verificar el estado con: systemctl status agent-isa.service"
log "Puede ver los logs con: journalctl -u agent-isa.service"
