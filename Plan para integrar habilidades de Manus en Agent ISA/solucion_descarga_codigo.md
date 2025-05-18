# Solución para Descarga del Código del Proyecto

## Introducción

Este documento presenta una solución alternativa a la sección de "Despliegue y Publicación" originalmente propuesta en el plan de integración. En lugar de implementar módulos para el despliegue de aplicaciones o sitios web, se propone una solución centrada en facilitar la descarga del código del proyecto integrado, permitiendo a los usuarios ejecutarlo localmente o implementar sus propias soluciones de despliegue.

## Propuesta de Solución

### 1. Repositorio de Código Centralizado

#### 1.1 Estructura del Repositorio

Se propone crear un repositorio Git centralizado que contenga:

- Código fuente completo del proyecto integrado
- Documentación detallada
- Scripts de instalación y configuración
- Ejemplos de uso
- Pruebas automatizadas

#### 1.2 Organización de Ramas

- `main`: Versión estable del proyecto
- `develop`: Rama de desarrollo activo
- `feature/*`: Ramas para nuevas características
- `release/*`: Ramas para preparación de versiones
- `hotfix/*`: Ramas para correcciones urgentes

### 2. Empaquetado del Código

#### 2.1 Paquete Python

Crear un paquete Python instalable mediante pip:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="agent-isa-manus",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "boto3>=1.28.0",
        "openai>=1.0.0",
        "flask>=2.0.0",
        # Otras dependencias según módulos habilitados
    ],
    extras_require={
        "search": ["requests", "beautifulsoup4"],
        "image": ["pillow", "numpy"],
        "dev": ["pytest", "black", "flake8"],
        # Paquetes opcionales por funcionalidad
    },
    entry_points={
        "console_scripts": [
            "agent-isa=agent_isa.cli:main",
        ],
    },
)
```

#### 2.2 Archivo de Requerimientos Modular

Crear archivos de requerimientos separados por módulo:

```
requirements/
├── base.txt         # Dependencias básicas
├── search.txt       # Dependencias para búsqueda web
├── image.txt        # Dependencias para procesamiento de imágenes
├── development.txt  # Herramientas de desarrollo
└── test.txt         # Dependencias para pruebas
```

#### 2.3 Script de Instalación Personalizable

Desarrollar un script que permita instalación selectiva de módulos:

```bash
#!/bin/bash
# install.sh

# Configuración por defecto
INSTALL_SEARCH=0
INSTALL_IMAGE=0
INSTALL_DEV=0

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --search)
        INSTALL_SEARCH=1
        shift
        ;;
        --image)
        INSTALL_IMAGE=1
        shift
        ;;
        --dev)
        INSTALL_DEV=1
        shift
        ;;
        *)
        shift
        ;;
    esac
done

# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias base
pip install -r requirements/base.txt

# Instalar módulos opcionales
if [ $INSTALL_SEARCH -eq 1 ]; then
    pip install -r requirements/search.txt
fi

if [ $INSTALL_IMAGE -eq 1 ]; then
    pip install -r requirements/image.txt
fi

if [ $INSTALL_DEV -eq 1 ]; then
    pip install -r requirements/development.txt
    pip install -r requirements/test.txt
fi

# Instalar el paquete en modo desarrollo
pip install -e .

echo "Instalación completada."
```

### 3. Distribución del Código

#### 3.1 Releases en GitHub

- Publicar releases periódicas en GitHub
- Incluir binarios precompilados para plataformas comunes
- Proporcionar checksums para verificación de integridad
- Mantener un registro de cambios detallado

#### 3.2 Paquete PyPI

- Publicar el paquete en PyPI para instalación mediante pip
- Mantener versiones compatibles con diferentes entornos
- Documentar claramente las dependencias y requisitos

#### 3.3 Archivo Comprimido

- Proporcionar archivos ZIP/TAR con el código fuente completo
- Incluir documentación offline
- Añadir scripts de configuración inicial

### 4. Documentación para Descarga e Instalación

#### 4.1 Guía de Inicio Rápido

```markdown
# Guía de Inicio Rápido

## Requisitos Previos
- Python 3.12 o superior
- pip (gestor de paquetes de Python)
- Credenciales de AWS para acceso a Bedrock (opcional)

## Instalación desde PyPI
```bash
pip install agent-isa-manus
```

## Instalación desde GitHub
```bash
git clone https://github.com/jivagrisma/agent-isa-manus.git
cd agent-isa-manus
./install.sh --search --image  # Instalar con módulos de búsqueda e imágenes
```

## Configuración
1. Copie el archivo `config/config.example.toml` a `config/config.toml`
2. Edite `config.toml` con sus credenciales y preferencias
3. Configure las variables de entorno necesarias:
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_REGION=your_region
   ```

## Ejecución
```bash
# Interfaz web
agent-isa web

# Interfaz de línea de comandos
agent-isa cli
```
```

#### 4.2 Documentación Detallada

Crear documentación exhaustiva que incluya:

- Proceso de instalación paso a paso
- Configuración de entorno
- Habilitación de módulos específicos
- Solución de problemas comunes
- Ejemplos de uso para diferentes escenarios

### 5. Verificación de Integridad

#### 5.1 Checksums

Proporcionar checksums (SHA-256) para todos los archivos descargables:

```
agent-isa-manus-0.1.0.tar.gz: 5f8e7754cdb...
agent-isa-manus-0.1.0-py3-none-any.whl: 3a2b1c9d8e...
```

#### 5.2 Firma Digital

Implementar firma digital de releases:

```bash
# Verificación de firma
gpg --verify agent-isa-manus-0.1.0.tar.gz.asc agent-isa-manus-0.1.0.tar.gz
```

### 6. Automatización de Descarga

#### 6.1 Script de Descarga Automatizada

```python
#!/usr/bin/env python3
# download.py

import argparse
import hashlib
import os
import sys
import requests
from tqdm import tqdm

GITHUB_REPO = "jivagrisma/agent-isa-manus"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CHECKSUMS = {
    "agent-isa-manus-0.1.0.tar.gz": "5f8e7754cdb...",
    "agent-isa-manus-0.1.0-py3-none-any.whl": "3a2b1c9d8e...",
}

def download_file(url, filename):
    """Descarga un archivo con barra de progreso."""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f, tqdm(
        desc=filename,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            bar.update(size)
    
    return filename

def verify_checksum(filename):
    """Verifica el checksum de un archivo."""
    if filename not in CHECKSUMS:
        print(f"No se encontró checksum para {filename}")
        return False
    
    sha256_hash = hashlib.sha256()
    with open(filename, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    calculated_hash = sha256_hash.hexdigest()
    expected_hash = CHECKSUMS[filename]
    
    if calculated_hash != expected_hash:
        print(f"Error de verificación: {calculated_hash} != {expected_hash}")
        return False
    
    print(f"Verificación exitosa para {filename}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Descargar agent-isa-manus')
    parser.add_argument('--wheel', action='store_true', help='Descargar archivo wheel')
    parser.add_argument('--source', action='store_true', help='Descargar código fuente')
    parser.add_argument('--verify', action='store_true', help='Verificar checksums')
    
    args = parser.parse_args()
    
    if not (args.wheel or args.source):
        args.wheel = True  # Por defecto descargar wheel
    
    try:
        print("Obteniendo información de la última versión...")
        response = requests.get(GITHUB_API)
        release_data = response.json()
        
        assets = release_data.get('assets', [])
        if not assets:
            print("No se encontraron archivos para descargar")
            return 1
        
        for asset in assets:
            filename = asset['name']
            download_url = asset['browser_download_url']
            
            if args.wheel and filename.endswith('.whl'):
                print(f"Descargando {filename}...")
                download_file(download_url, filename)
                
                if args.verify:
                    verify_checksum(filename)
            
            if args.source and filename.endswith('.tar.gz'):
                print(f"Descargando {filename}...")
                download_file(download_url, filename)
                
                if args.verify:
                    verify_checksum(filename)
        
        print("Descarga completada.")
        return 0
    
    except Exception as e:
        print(f"Error durante la descarga: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

#### 6.2 Integración con Gestores de Paquetes

Proporcionar instrucciones para integración con gestores de paquetes comunes:

- pip (Python)
- conda (Anaconda)
- apt/yum/brew (sistemas operativos)

### 7. Ventajas de esta Solución

1. **Flexibilidad**: Los usuarios pueden descargar solo los componentes que necesitan.
2. **Control**: Mayor control sobre el entorno de ejecución y configuración.
3. **Seguridad**: Los usuarios pueden revisar el código antes de ejecutarlo.
4. **Personalización**: Facilita la adaptación a necesidades específicas.
5. **Independencia**: No requiere infraestructura de despliegue centralizada.
6. **Compatibilidad**: Funciona en diversos entornos y plataformas.

### 8. Implementación

#### 8.1 Tareas Necesarias

1. Configurar repositorio Git con la estructura propuesta
2. Crear archivo setup.py y estructura de paquete Python
3. Desarrollar scripts de instalación y descarga
4. Generar documentación detallada
5. Implementar sistema de verificación de integridad
6. Configurar CI/CD para generación automática de releases

#### 8.2 Cronograma

| Tarea | Duración Estimada | Dependencias |
|-------|-------------------|--------------|
| Configuración de repositorio | 1 semana | Ninguna |
| Estructura de paquete Python | 1 semana | Configuración de repositorio |
| Scripts de instalación | 1 semana | Estructura de paquete |
| Documentación | 2 semanas | Estructura de paquete |
| Sistema de verificación | 1 semana | Scripts de instalación |
| Configuración CI/CD | 1 semana | Todas las anteriores |

## Conclusión

Esta solución proporciona una alternativa efectiva a la implementación de módulos de despliegue y publicación, centrándose en facilitar la descarga, instalación y configuración del código del proyecto. Esto permite a los usuarios ejecutar el sistema en sus propios entornos, con mayor control y flexibilidad, mientras se mantiene la integridad y seguridad del código.

La implementación de esta solución requiere menos recursos que el desarrollo de módulos completos de despliegue, al tiempo que proporciona una experiencia de usuario satisfactoria para desarrolladores y usuarios técnicos que prefieren gestionar sus propios entornos de ejecución.
