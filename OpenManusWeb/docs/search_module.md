# Módulo de Búsqueda Web para Agent-ISA

## Descripción

El módulo de búsqueda web proporciona capacidades para buscar información en internet, navegar a páginas web y extraer contenido. Está diseñado para ser utilizado por modelos de lenguaje y agentes autónomos como parte de agent-isa.

## Componentes Principales

### WebSearchEngine

Motor de búsqueda web con soporte para múltiples fuentes.

**Características:**
- Búsqueda en múltiples motores (Google, Bing)
- Caché de resultados para mejorar rendimiento
- Filtrado y ranking de resultados

**Uso básico:**
```python
from modules.core import ConfigManager
from modules.search import WebSearchEngine

# Inicializar
config_manager = ConfigManager()
search_engine = WebSearchEngine(config_manager)

# Realizar búsqueda
results = search_engine.search("inteligencia artificial", num_results=5, search_engine="google")

# Procesar resultados
for result in results:
    print(f"Título: {result.title}")
    print(f"URL: {result.url}")
    print(f"Snippet: {result.snippet}")
    print()
```

### HeadlessBrowser

Navegador headless para acceso y extracción de contenido web.

**Características:**
- Navegación a URLs
- Extracción de contenido (texto, enlaces)
- Interacción con páginas
- Soporte para capturas de pantalla

**Uso básico:**
```python
import asyncio
from modules.core import ConfigManager
from modules.search import HeadlessBrowser

async def main():
    # Inicializar
    config_manager = ConfigManager()
    browser = HeadlessBrowser(config_manager)
    
    try:
        # Navegar a una URL
        content = await browser.navigate("https://example.com")
        
        # Procesar contenido
        print(content)
        
    finally:
        # Cerrar navegador
        await browser.close()

# Ejecutar
asyncio.run(main())
```

## Configuración

El módulo utiliza el sistema de configuración modular de agent-isa. La configuración se encuentra en `OpenManusWeb/config/search.toml`.

### Opciones de Configuración

#### General
```toml
[general]
enabled = true
cache_results = true
cache_expiry = 3600  # Segundos
```

#### Motor de Búsqueda
```toml
[search_engine]
default = "google"
results_per_page = 5
timeout = 10  # Segundos

[search_engine.google]
api_key = ""
cx = ""
use_api = false  # Si es false, usa web scraping

[search_engine.bing]
api_key = ""
use_api = false
```

#### Navegador
```toml
[browser]
headless = true
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
timeout = 30  # Segundos
wait_for_selector = true
screenshot = false
```

#### Extracción de Contenido
```toml
[content_extraction]
extract_text = true
extract_images = false
extract_links = true
max_content_length = 10000  # Caracteres
```

## Ejemplos de Uso

### Búsqueda y Navegación Completa

```python
import asyncio
from modules.core import ConfigManager
from modules.search import WebSearchEngine, HeadlessBrowser

async def search_and_browse(query, num_results=1):
    # Inicializar componentes
    config_manager = ConfigManager()
    search_engine = WebSearchEngine(config_manager)
    browser = HeadlessBrowser(config_manager)
    
    try:
        # Realizar búsqueda
        print(f"Buscando: {query}")
        results = search_engine.search(query, num_results=num_results)
        
        if not results:
            print("No se encontraron resultados")
            return
        
        # Navegar al primer resultado
        first_result = results[0]
        print(f"Navegando a: {first_result.title} ({first_result.url})")
        
        content = await browser.navigate(first_result.url)
        
        # Procesar contenido
        print(f"Contenido extraído ({len(content)} caracteres)")
        print(content[:500] + "...")
        
    finally:
        # Cerrar navegador
        await browser.close()

# Ejecutar
asyncio.run(search_and_browse("inteligencia artificial"))
```

### Uso desde la Línea de Comandos

El módulo incluye un script de prueba que puede ser utilizado desde la línea de comandos:

```bash
# Realizar búsqueda
python OpenManusWeb/test_search.py search "inteligencia artificial" --results 5 --engine google

# Navegar a una URL
python OpenManusWeb/test_search.py browse "https://example.com"

# Búsqueda y navegación
python OpenManusWeb/test_search.py full "inteligencia artificial" --results 1
```

## Dependencias

El módulo requiere las siguientes dependencias:

- requests
- beautifulsoup4
- playwright

Puedes instalarlas con:

```bash
pip install -r requirements/search.txt
```

O usando el script de instalación:

```bash
./install.sh --search
```

## Limitaciones y Consideraciones

- **Términos de Servicio**: El uso de web scraping puede violar los términos de servicio de algunos sitios web. Utiliza las APIs oficiales cuando sea posible.
- **Rate Limiting**: Implementa límites de tasa para evitar ser bloqueado por los motores de búsqueda.
- **Cambios en la Estructura**: Los selectores utilizados para extraer contenido pueden dejar de funcionar si los sitios web cambian su estructura.
- **Contenido Dinámico**: Algunas páginas web cargan contenido dinámicamente con JavaScript, lo que puede requerir esperas adicionales.

## Desarrollo Futuro

- Soporte para más motores de búsqueda
- Mejora en la extracción de contenido estructurado
- Soporte para autenticación en sitios web
- Integración con APIs de búsqueda adicionales
