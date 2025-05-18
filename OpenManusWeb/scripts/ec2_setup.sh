#!/bin/bash
# Script de configuración inicial para instancias EC2
# Instala dependencias y configura el entorno para agent-isa

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

# Directorio de instalación
INSTALL_DIR="/opt/agent-isa"
DATA_DIR="/opt/agent-isa/data"
LOG_DIR="/var/log/agent-isa"
CONFIG_DIR="/etc/agent-isa"

# Verificar distribución
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
    log "Sistema operativo detectado: $OS $VERSION"
else
    error "No se pudo determinar la distribución"
    exit 1
fi

# Actualizar sistema
log "Actualizando sistema..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt-get update
    apt-get upgrade -y
elif [[ "$OS" == *"Amazon"* ]]; then
    yum update -y
else
    warn "Distribución no reconocida. Saltando actualización del sistema."
fi

# Instalar dependencias
log "Instalando dependencias del sistema..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    apt-get install -y python3 python3-pip python3-venv supervisor nginx git
elif [[ "$OS" == *"Amazon"* ]]; then
    yum install -y python3 python3-pip supervisor nginx git
else
    error "Distribución no soportada"
    exit 1
fi

# Crear directorios
log "Creando directorios..."
mkdir -p $INSTALL_DIR
mkdir -p $DATA_DIR
mkdir -p $DATA_DIR/storage
mkdir -p $DATA_DIR/cache
mkdir -p $LOG_DIR
mkdir -p $CONFIG_DIR

# Crear usuario de servicio
log "Creando usuario de servicio..."
if ! id -u agent-isa &>/dev/null; then
    useradd -r -s /bin/false -d $INSTALL_DIR agent-isa
fi

# Clonar repositorio
log "Clonando repositorio..."
if [ -d "$INSTALL_DIR/app" ]; then
    log "El repositorio ya existe, actualizando..."
    cd $INSTALL_DIR/app
    git pull
else
    git clone https://github.com/jivagrisma/agent-isa.git $INSTALL_DIR/app
fi

# Crear entorno virtual
log "Creando entorno virtual..."
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias de Python
log "Instalando dependencias de Python..."
cd $INSTALL_DIR/app
pip install --upgrade pip
pip install -r requirements.txt

# Configurar variables de entorno
log "Configurando variables de entorno..."
cat > $CONFIG_DIR/agent-isa.env << EOF
AGENT_ISA_ENV=production
PYTHONPATH=$INSTALL_DIR/app
JWT_SECRET=$(openssl rand -hex 32)
EOF

# Configurar supervisor
log "Configurando supervisor..."
cat > /etc/supervisor/conf.d/agent-isa.conf << EOF
[program:agent-isa]
command=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/app/OpenManusWeb/app.py
directory=$INSTALL_DIR/app
user=agent-isa
environment=AGENT_ISA_ENV="production",PYTHONPATH="$INSTALL_DIR/app"
autostart=true
autorestart=true
startretries=3
stderr_logfile=$LOG_DIR/supervisor-error.log
stdout_logfile=$LOG_DIR/supervisor-output.log
EOF

# Configurar Nginx
log "Configurando Nginx..."
cat > /etc/nginx/sites-available/agent-isa << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $INSTALL_DIR/app/OpenManusWeb/static;
        expires 30d;
    }
}
EOF

# Habilitar sitio en Nginx
if [ -d "/etc/nginx/sites-enabled" ]; then
    ln -sf /etc/nginx/sites-available/agent-isa /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
fi

# Configurar permisos
log "Configurando permisos..."
chown -R agent-isa:agent-isa $INSTALL_DIR
chown -R agent-isa:agent-isa $DATA_DIR
chown -R agent-isa:agent-isa $LOG_DIR
chmod -R 755 $INSTALL_DIR
chmod -R 755 $DATA_DIR
chmod -R 755 $LOG_DIR

# Reiniciar servicios
log "Reiniciando servicios..."
systemctl restart supervisor
systemctl restart nginx

# Verificar instalación
log "Verificando instalación..."
if systemctl is-active --quiet supervisor && systemctl is-active --quiet nginx; then
    log "Servicios iniciados correctamente"
else
    error "Error al iniciar servicios"
    exit 1
fi

log "Configuración completada. Agent-ISA está instalado en $INSTALL_DIR"
log "Logs disponibles en $LOG_DIR"
log "Configuración en $CONFIG_DIR"
log "Acceda a la aplicación en http://[IP-SERVIDOR]"
