#!/bin/bash
# Script de despliegue automatizado para agent-isa
# Despliega la aplicación en una instancia EC2 de AWS

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

# Verificar parámetros
if [ "$#" -lt 1 ]; then
    echo "Uso: $0 <host> [usuario] [clave-ssh]"
    echo "  host: Dirección IP o nombre de host de la instancia EC2"
    echo "  usuario: Usuario SSH (por defecto: ec2-user)"
    echo "  clave-ssh: Ruta a la clave SSH (por defecto: ~/.ssh/id_rsa)"
    exit 1
fi

# Parámetros
HOST=$1
USER=${2:-ec2-user}
SSH_KEY=${3:-~/.ssh/id_rsa}

# Directorios
REPO_DIR=$(git rev-parse --show-toplevel)
SCRIPTS_DIR="$REPO_DIR/OpenManusWeb/scripts"
BUILD_DIR="$REPO_DIR/build"

# Verificar que estamos en un repositorio git
if [ ! -d "$REPO_DIR/.git" ]; then
    error "No se encontró un repositorio git"
    exit 1
fi

# Verificar que la clave SSH existe
if [ ! -f "$SSH_KEY" ]; then
    error "No se encontró la clave SSH: $SSH_KEY"
    exit 1
fi

# Verificar conexión SSH
log "Verificando conexión SSH a $HOST..."
if ! ssh -i "$SSH_KEY" -o ConnectTimeout=5 -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$USER@$HOST" "echo 'Conexión exitosa'"; then
    error "No se pudo conectar a $HOST con el usuario $USER"
    exit 1
fi

# Crear directorio de build
log "Preparando archivos para despliegue..."
mkdir -p "$BUILD_DIR"

# Crear archivo de versión
VERSION=$(git describe --tags --always)
COMMIT=$(git rev-parse HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

cat > "$BUILD_DIR/version.json" << EOF
{
    "version": "$VERSION",
    "commit": "$COMMIT",
    "branch": "$BRANCH",
    "timestamp": "$TIMESTAMP",
    "build_host": "$(hostname)"
}
EOF

# Crear archivo tar con el código
log "Creando archivo de despliegue..."
cd "$REPO_DIR"
git archive --format=tar.gz --prefix=agent-isa/ -o "$BUILD_DIR/agent-isa.tar.gz" HEAD

# Copiar scripts de despliegue
cp "$SCRIPTS_DIR/ec2_setup.sh" "$BUILD_DIR/"

# Copiar archivo de versión
cp "$BUILD_DIR/version.json" "$BUILD_DIR/agent-isa/"

# Transferir archivos a la instancia EC2
log "Transfiriendo archivos a $HOST..."
scp -i "$SSH_KEY" "$BUILD_DIR/agent-isa.tar.gz" "$BUILD_DIR/ec2_setup.sh" "$USER@$HOST:~/"

# Ejecutar script de configuración
log "Ejecutando script de configuración en $HOST..."
ssh -i "$SSH_KEY" "$USER@$HOST" "sudo bash ~/ec2_setup.sh"

# Extraer código
log "Desplegando código en $HOST..."
ssh -i "$SSH_KEY" "$USER@$HOST" "sudo mkdir -p /opt/agent-isa/app && sudo tar -xzf ~/agent-isa.tar.gz -C /opt/agent-isa/app --strip-components=1"

# Configurar permisos
log "Configurando permisos..."
ssh -i "$SSH_KEY" "$USER@$HOST" "sudo chown -R agent-isa:agent-isa /opt/agent-isa && sudo chmod -R 755 /opt/agent-isa"

# Reiniciar servicios
log "Reiniciando servicios..."
ssh -i "$SSH_KEY" "$USER@$HOST" "sudo systemctl restart supervisor && sudo systemctl restart nginx"

# Verificar despliegue
log "Verificando despliegue..."
if ssh -i "$SSH_KEY" "$USER@$HOST" "curl -s http://localhost:8000/health"; then
    log "Despliegue completado exitosamente"
    log "Aplicación disponible en http://$HOST"
else
    error "Error al verificar despliegue"
    warn "Revise los logs en la instancia EC2: /var/log/agent-isa/"
    exit 1
fi

# Limpiar archivos temporales
log "Limpiando archivos temporales..."
rm -rf "$BUILD_DIR"
ssh -i "$SSH_KEY" "$USER@$HOST" "rm -f ~/agent-isa.tar.gz ~/ec2_setup.sh"

log "Despliegue completado exitosamente"
