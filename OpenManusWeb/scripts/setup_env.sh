#!/bin/bash
# Script para configurar variables de entorno para Agent-ISA
# IMPORTANTE: Este script debe ejecutarse con 'source' para que las variables
# se establezcan en el shell actual: source setup_env.sh

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
log() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[ADVERTENCIA] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

# Verificar si se está ejecutando con source
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    error "Este script debe ejecutarse con 'source': source ${0}"
    exit 1
fi

# Directorio del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Archivo de entorno
ENV_FILE="$PROJECT_ROOT/.env"

# Verificar si existe archivo .env
if [ -f "$ENV_FILE" ]; then
    log "Cargando variables de entorno desde $ENV_FILE"
    
    # Cargar variables de entorno
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        # Ignorar líneas vacías o comentarios
        if [[ -z "$key" || "$key" == \#* ]]; then
            continue
        fi
        
        # Eliminar comillas si existen
        value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
        
        # Exportar variable
        export "$key=$value"
        log "Variable establecida: $key"
    done < "$ENV_FILE"
else
    warn "No se encontró archivo .env, se crearán variables por defecto"
    
    # Crear archivo .env con valores por defecto
    cat > "$ENV_FILE" << EOF
# Variables de entorno para Agent-ISA
# Credenciales de AWS
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# Configuración de entorno
AGENT_ISA_ENV=development

# Configuración de modelos
BEDROCK_MODEL_NOVA_PRO=amazon.nova-pro
BEDROCK_MODEL_NOVA_LITE=amazon.nova-lite
BEDROCK_MODEL_TITAN_EMBEDDINGS=amazon.titan-embed-image-v1
BEDROCK_MODEL_CLAUDE=anthropic.claude-3-sonnet-20240229-v1

# Configuración de seguridad
JWT_SECRET=$(openssl rand -hex 32)
EOF
    
    log "Archivo .env creado en $ENV_FILE"
    log "Por favor, edite el archivo para configurar sus credenciales"
fi

# Verificar variables críticas
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    warn "Credenciales de AWS no configuradas"
    warn "Por favor, edite el archivo $ENV_FILE y ejecute este script nuevamente"
fi

# Mostrar configuración actual
log "Configuración actual:"
log "Entorno: $AGENT_ISA_ENV"
log "Región AWS: $AWS_REGION"
log "Modelo Nova Pro: $BEDROCK_MODEL_NOVA_PRO"
log "Modelo Nova Lite: $BEDROCK_MODEL_NOVA_LITE"
log "Modelo Titan Embeddings: $BEDROCK_MODEL_TITAN_EMBEDDINGS"
log "Modelo Claude: $BEDROCK_MODEL_CLAUDE"

# Verificar si las credenciales funcionan
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    log "Verificando credenciales de AWS..."
    
    # Verificar si aws-cli está instalado
    if command -v aws &> /dev/null; then
        # Verificar credenciales
        if aws sts get-caller-identity &> /dev/null; then
            log "Credenciales de AWS verificadas correctamente"
        else
            error "Las credenciales de AWS no son válidas"
        fi
    else
        warn "aws-cli no está instalado, no se pueden verificar las credenciales"
    fi
fi

log "Variables de entorno configuradas correctamente"
