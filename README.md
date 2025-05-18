# Agent-ISA con Integración AWS Bedrock y Habilidades de Manus

Este repositorio contiene una implementación de Agent-ISA, un proyecto basado en la bifurcación de OpenManusWeb, con integración a AWS Bedrock, permitiendo utilizar modelos de lenguaje avanzados como Amazon Nova Pro, Amazon Nova Lite y Claude 3.7 Sonnet. Además, incluye la integración de habilidades de Manus para proporcionar capacidades avanzadas a los modelos de lenguaje.

## Características

- Integración robusta con AWS Bedrock
- Interfaz de chat web moderna y responsive
- Soporte para diferentes modelos de AWS Bedrock
- Manejo de errores mejorado
- Scripts de prueba para verificar la integración
- Sistema modular para habilidades de Manus
- Capacidades de búsqueda web y navegación
- Arquitectura extensible mediante plugins

## Estructura del Repositorio

```
OpenManusWeb/
├── app/                    # Código principal de la aplicación
│   ├── config.py           # Configuración de la aplicación
│   └── llm.py              # Integración con AWS Bedrock
├── config/                 # Archivos de configuración
│   ├── config.toml         # Configuración de AWS Bedrock
│   ├── core.toml           # Configuración del módulo Core
│   └── search.toml         # Configuración del módulo de Búsqueda
├── docs/                   # Documentación
│   ├── aws_bedrock_integration.md  # Documentación de la integración con AWS Bedrock
│   ├── search_module.md    # Documentación del módulo de Búsqueda
│   └── llm_search_guide.md # Guía de búsqueda para LLM/Agentes
├── modules/                # Módulos de habilidades de Manus
│   ├── core/               # Módulo Core (configuración, plugins)
│   ├── search/             # Módulo de Búsqueda Web
│   ├── content/            # Módulo de Procesamiento de Contenido
│   ├── image/              # Módulo de Generación de Imágenes
│   ├── code/               # Módulo de Desarrollo de Código
│   ├── filesystem/         # Módulo de Sistema de Archivos
│   └── distribution/       # Módulo de Distribución
├── static/                 # Archivos estáticos para la interfaz web
├── templates/              # Plantillas HTML para la interfaz web
├── simple_chat.py          # Interfaz web de chat
├── test_bedrock.py         # Script de prueba para AWS Bedrock
├── test_cli.py             # Interfaz de línea de comandos para AWS Bedrock
├── test_search.py          # Script de prueba para el módulo de búsqueda
└── cli.py                  # Interfaz de línea de comandos unificada
```

## Requisitos

- Python 3.12 o superior
- Cuenta de AWS con acceso a AWS Bedrock
- Credenciales de AWS (Access Key ID y Secret Access Key)
- Acceso a los modelos de AWS Bedrock (Amazon Nova Pro, Amazon Nova Lite, Claude 3.7 Sonnet, etc.)

## Instalación

### Instalación Básica

1. Clona este repositorio:
   ```bash
   git clone https://github.com/jivagrisma/agent-isa.git
   cd agent-isa
   ```

2. Crea un entorno virtual y actívalo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias básicas:
   ```bash
   pip install -r requirements.txt
   ```

### Instalación con Script

Puedes utilizar el script de instalación para una configuración más personalizada:

```bash
# Instalar solo el núcleo
./install.sh

# Instalar con módulo de búsqueda web
./install.sh --search

# Instalar todos los módulos
./install.sh --all

# Ver opciones disponibles
./install.sh --help
```

### Instalación del Módulo de Búsqueda

Para instalar específicamente el módulo de búsqueda web:

```bash
# Instalar con configuración por defecto
./install_search.sh

# Ver opciones disponibles
./install_search.sh --help
```

## Uso

### Interfaz Web de Chat

Para iniciar la interfaz web de chat:

```bash
python OpenManusWeb/simple_chat.py
```

Luego, abre tu navegador y navega a:

- Interfaz básica: `http://localhost:8005`
- Interfaz mejorada: `http://localhost:8005/enhanced` (Recomendada)

### Interfaz de Línea de Comandos Unificada

La nueva interfaz de línea de comandos unificada permite acceder a todas las funcionalidades:

```bash
# Iniciar interfaz web
python OpenManusWeb/cli.py web

# Iniciar chat en línea de comandos
python OpenManusWeb/cli.py chat

# Listar plugins disponibles
python OpenManusWeb/cli.py plugins --list

# Mostrar configuración
python OpenManusWeb/cli.py config --show core

# Mostrar versión
python OpenManusWeb/cli.py version
```

### Pruebas de AWS Bedrock

Para probar la integración con AWS Bedrock:

```bash
python OpenManusWeb/test_bedrock.py
```

### Pruebas del Módulo de Búsqueda

Para probar el módulo de búsqueda web:

```bash
# Realizar búsqueda
python OpenManusWeb/test_search.py search "inteligencia artificial" --results 5

# Navegar a una URL
python OpenManusWeb/test_search.py browse "https://example.com"

# Búsqueda y navegación
python OpenManusWeb/test_search.py full "inteligencia artificial"
```

## Documentación

### Integración con AWS Bedrock
Para más información sobre la integración con AWS Bedrock, consulta la [documentación detallada](OpenManusWeb/docs/aws_bedrock_integration.md).

### Módulo de Búsqueda Web
Para información sobre el módulo de búsqueda web, consulta la [documentación del módulo](OpenManusWeb/docs/search_module.md).

### Módulo de Procesamiento de Contenido
Para información sobre el módulo de procesamiento de contenido, consulta la [documentación del módulo](OpenManusWeb/docs/content_module.md).

### Generador de Texto
Para información sobre el generador de texto, consulta la [documentación del módulo](OpenManusWeb/docs/text_generator.md).

### Generador de Imágenes
Para información sobre el generador de imágenes, consulta la [documentación del módulo](OpenManusWeb/docs/image_generator.md).

### Procesador de Contenido Multimedia
Para información sobre el procesador de contenido multimedia, consulta la [documentación del módulo](OpenManusWeb/docs/media_processor.md).

### Módulo de Almacenamiento
Para información sobre el módulo de almacenamiento, consulta la [documentación del módulo](OpenManusWeb/docs/storage_module.md).

### Cliente LLM Extendido
Para información sobre el cliente LLM extendido, consulta la [documentación del cliente](OpenManusWeb/docs/extended_llm.md).

### Interfaz de Chat Mejorada
Para información sobre la interfaz de chat mejorada, consulta la [documentación de la interfaz](OpenManusWeb/docs/enhanced_chat.md).

### Guía para LLM/Agentes
Para modelos de lenguaje y agentes autónomos, consulta la [guía de búsqueda para LLM](OpenManusWeb/docs/llm_search_guide.md).

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Jorge Grisales - jivagrisma@gmail.com

Enlace del proyecto: [https://github.com/jivagrisma/agent-isa](https://github.com/jivagrisma/agent-isa)
