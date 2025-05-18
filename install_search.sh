#!/bin/bash
# Script de instalación para el módulo de búsqueda web de agent-isa

# Colores para mensajes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración por defecto
PYTHON_VERSION="3.12"
VENV_NAME="venv"
INSTALL_PLAYWRIGHT=1

# Función para mostrar ayuda
show_help() {
    echo -e "${BLUE}Script de instalación para el módulo de búsqueda web de agent-isa${NC}"
    echo ""
    echo "Uso: ./install_search.sh [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --help                Muestra esta ayuda"
    echo "  --python VERSION      Especifica la versión de Python (por defecto: 3.12)"
    echo "  --venv NOMBRE         Especifica el nombre del entorno virtual (por defecto: venv)"
    echo "  --no-playwright       No instala Playwright y sus dependencias"
    echo ""
    echo "Ejemplo: ./install_search.sh --python 3.11 --venv search_env"
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
        --no-playwright)
        INSTALL_PLAYWRIGHT=0
        shift
        ;;
        *)
        echo -e "${RED}Opción desconocida: $key${NC}"
        show_help
        exit 1
        ;;
    esac
done

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

# Verificar si el entorno virtual ya existe
if [ -d "$VENV_NAME" ]; then
    echo -e "${YELLOW}El entorno virtual '$VENV_NAME' ya existe.${NC}"
    read -p "¿Deseas usar el entorno existente? (s/n): " use_existing
    if [[ $use_existing != "s" && $use_existing != "S" ]]; then
        echo -e "${BLUE}Creando nuevo entorno virtual...${NC}"
        rm -rf $VENV_NAME
        $PYTHON_CMD -m venv $VENV_NAME
    fi
else
    # Crear entorno virtual
    echo -e "${BLUE}Creando entorno virtual '$VENV_NAME'...${NC}"
    $PYTHON_CMD -m venv $VENV_NAME
fi

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

# Instalar dependencias base
echo -e "${BLUE}Instalando dependencias base...${NC}"
pip install -r requirements/core.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al instalar dependencias base.${NC}"
    exit 1
fi

# Instalar dependencias de búsqueda
echo -e "${BLUE}Instalando dependencias de búsqueda web...${NC}"
pip install -r requirements/search.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Error al instalar dependencias de búsqueda web.${NC}"
    exit 1
fi

# Instalar Playwright si está habilitado
if [ $INSTALL_PLAYWRIGHT -eq 1 ]; then
    echo -e "${BLUE}Instalando Playwright...${NC}"
    pip install playwright
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error al instalar Playwright.${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Instalando navegadores para Playwright...${NC}"
    playwright install
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Advertencia: Error al instalar navegadores para Playwright.${NC}"
        echo -e "${YELLOW}Puedes instalarlos manualmente con: playwright install${NC}"
    fi
fi

# Instalar el paquete en modo desarrollo
echo -e "${BLUE}Instalando agent-isa en modo desarrollo...${NC}"
pip install -e .

# Verificar instalación
echo -e "${GREEN}¡Instalación completada!${NC}"
echo -e "${BLUE}Componentes instalados:${NC}"
echo -e "  - Core (base)"
echo -e "  - Búsqueda Web"
[ $INSTALL_PLAYWRIGHT -eq 1 ] && echo -e "  - Playwright y navegadores"

echo ""
echo -e "${BLUE}Para activar el entorno virtual:${NC}"
echo -e "  source $VENV_NAME/bin/activate"

echo ""
echo -e "${BLUE}Para probar el módulo de búsqueda:${NC}"
echo -e "  python OpenManusWeb/test_search.py search \"inteligencia artificial\" --results 5"

echo ""
echo -e "${BLUE}Para probar el navegador headless:${NC}"
echo -e "  python OpenManusWeb/test_search.py browse \"https://example.com\""
