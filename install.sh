#!/bin/bash
# Script de instalación para agent-isa con Manus

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
PYTHON_VERSION="3.12"
VENV_NAME="venv"
INSTALL_CORE=1
INSTALL_SEARCH=0
INSTALL_CONTENT=0
INSTALL_IMAGE=0
INSTALL_CODE=0
INSTALL_FILESYSTEM=0
INSTALL_DISTRIBUTION=0
INSTALL_DEV=0
INSTALL_ALL=0

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}Script de instalación para agent-isa con Manus${NC}"
    echo ""
    echo "Uso: ./install.sh [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --help                Muestra esta ayuda"
    echo "  --python VERSION      Especifica la versión de Python (por defecto: 3.12)"
    echo "  --venv NOMBRE         Especifica el nombre del entorno virtual (por defecto: venv)"
    echo "  --all                 Instala todos los módulos"
    echo "  --search              Instala el módulo de búsqueda web"
    echo "  --content             Instala el módulo de procesamiento de contenido"
    echo "  --image               Instala el módulo de generación de imágenes"
    echo "  --code                Instala el módulo de desarrollo de código"
    echo "  --filesystem          Instala el módulo de sistema de archivos"
    echo "  --distribution        Instala el módulo de distribución"
    echo "  --dev                 Instala dependencias de desarrollo"
    echo ""
    echo "Ejemplo: ./install.sh --search --content --dev"
}

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --help)
        show_help
        exit 0
        ;;
        --python)
        PYTHON_VERSION="$2"
        shift
        shift
        ;;
        --venv)
        VENV_NAME="$2"
        shift
        shift
        ;;
        --all)
        INSTALL_ALL=1
        shift
        ;;
        --search)
        INSTALL_SEARCH=1
        shift
        ;;
        --content)
        INSTALL_CONTENT=1
        shift
        ;;
        --image)
        INSTALL_IMAGE=1
        shift
        ;;
        --code)
        INSTALL_CODE=1
        shift
        ;;
        --filesystem)
        INSTALL_FILESYSTEM=1
        shift
        ;;
        --distribution)
        INSTALL_DISTRIBUTION=1
        shift
        ;;
        --dev)
        INSTALL_DEV=1
        shift
        ;;
        *)
        echo -e "${RED}Opción desconocida: $key${NC}"
        show_help
        exit 1
        ;;
    esac
done

# Si se seleccionó --all, activar todos los módulos
if [ $INSTALL_ALL -eq 1 ]; then
    INSTALL_SEARCH=1
    INSTALL_CONTENT=1
    INSTALL_IMAGE=1
    INSTALL_CODE=1
    INSTALL_FILESYSTEM=1
    INSTALL_DISTRIBUTION=1
    INSTALL_DEV=1
fi

# Verificar que Python esté instalado
echo -e "${BLUE}Verificando Python ${PYTHON_VERSION}...${NC}"
if command -v python$PYTHON_VERSION &> /dev/null; then
    echo -e "${GREEN}Python ${PYTHON_VERSION} encontrado.${NC}"
    PYTHON_CMD="python$PYTHON_VERSION"
else
    echo -e "${YELLOW}Python ${PYTHON_VERSION} no encontrado, intentando con 'python3'...${NC}"
    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}Python3 encontrado.${NC}"
        PYTHON_CMD="python3"
    else
        echo -e "${RED}No se encontró Python. Por favor, instala Python ${PYTHON_VERSION} o superior.${NC}"
        exit 1
    fi
fi

# Verificar versión de Python
PY_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${BLUE}Versión de Python detectada: ${PY_VERSION}${NC}"

# Verificar que pip esté instalado
echo -e "${BLUE}Verificando pip...${NC}"
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo -e "${RED}pip no está instalado. Por favor, instala pip.${NC}"
    exit 1
fi

# Crear entorno virtual
echo -e "${BLUE}Creando entorno virtual '${VENV_NAME}'...${NC}"
$PYTHON_CMD -m venv $VENV_NAME
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al crear el entorno virtual.${NC}"
    exit 1
fi

# Activar entorno virtual
echo -e "${BLUE}Activando entorno virtual...${NC}"
source $VENV_NAME/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al activar el entorno virtual.${NC}"
    exit 1
fi

# Actualizar pip
echo -e "${BLUE}Actualizando pip...${NC}"
pip install --upgrade pip

# Crear directorio de requirements si no existe
mkdir -p requirements

# Instalar dependencias base (siempre)
echo -e "${BLUE}Instalando dependencias base...${NC}"
pip install -r requirements/core.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al instalar dependencias base.${NC}"
    exit 1
fi

# Instalar módulos opcionales
if [ $INSTALL_SEARCH -eq 1 ]; then
    echo -e "${BLUE}Instalando módulo de búsqueda web...${NC}"
    pip install -r requirements/search.txt
fi

if [ $INSTALL_CONTENT -eq 1 ]; then
    echo -e "${BLUE}Instalando módulo de procesamiento de contenido...${NC}"
    pip install -r requirements/content.txt
fi

if [ $INSTALL_IMAGE -eq 1 ]; then
    echo -e "${BLUE}Instalando módulo de generación de imágenes...${NC}"
    pip install -r requirements/image.txt
fi

if [ $INSTALL_CODE -eq 1 ]; then
    echo -e "${BLUE}Instalando módulo de desarrollo de código...${NC}"
    pip install -r requirements/code.txt
fi

if [ $INSTALL_FILESYSTEM -eq 1 ]; then
    echo -e "${BLUE}Instalando módulo de sistema de archivos...${NC}"
    pip install -r requirements/filesystem.txt
fi

if [ $INSTALL_DISTRIBUTION -eq 1 ]; then
    echo -e "${BLUE}Instalando módulo de distribución...${NC}"
    pip install -r requirements/distribution.txt
fi

if [ $INSTALL_DEV -eq 1 ]; then
    echo -e "${BLUE}Instalando dependencias de desarrollo...${NC}"
    pip install -r requirements/dev.txt
fi

# Instalar el paquete en modo desarrollo
echo -e "${BLUE}Instalando agent-isa en modo desarrollo...${NC}"
pip install -e .

# Verificar instalación
echo -e "${GREEN}¡Instalación completada!${NC}"
echo -e "${BLUE}Módulos instalados:${NC}"
echo -e "  - Core (base)"
[ $INSTALL_SEARCH -eq 1 ] && echo -e "  - Búsqueda Web"
[ $INSTALL_CONTENT -eq 1 ] && echo -e "  - Procesamiento de Contenido"
[ $INSTALL_IMAGE -eq 1 ] && echo -e "  - Generación de Imágenes"
[ $INSTALL_CODE -eq 1 ] && echo -e "  - Desarrollo de Código"
[ $INSTALL_FILESYSTEM -eq 1 ] && echo -e "  - Sistema de Archivos"
[ $INSTALL_DISTRIBUTION -eq 1 ] && echo -e "  - Distribución"
[ $INSTALL_DEV -eq 1 ] && echo -e "  - Herramientas de Desarrollo"

echo ""
echo -e "${BLUE}Para activar el entorno virtual:${NC}"
echo -e "  source $VENV_NAME/bin/activate"

echo ""
echo -e "${BLUE}Para iniciar la aplicación:${NC}"
echo -e "  python OpenManusWeb/simple_chat.py"
