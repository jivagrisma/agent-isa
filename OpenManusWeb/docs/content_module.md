# Módulo de Procesamiento de Contenido para Agent-ISA

## Descripción

El módulo de procesamiento de contenido proporciona capacidades para extraer y analizar contenido estructurado de páginas web. Está diseñado para trabajar en conjunto con el módulo de búsqueda web, permitiendo extraer información valiosa de los resultados de búsqueda.

## Componentes Principales

### ContentExtractor

Extractor de contenido web con capacidades de análisis.

**Características:**
- Extracción de texto estructurado
- Extracción de tablas y datos tabulares
- Extracción de metadatos
- Extracción de enlaces y imágenes
- Análisis básico de sentimiento

**Uso básico:**
```python
from modules.core import ConfigManager
from modules.content import ContentExtractor

# Inicializar
config_manager = ConfigManager()
content_extractor = ContentExtractor(config_manager)

# Extraer contenido de HTML
html = "<html>...</html>"
url = "https://example.com"
extracted = content_extractor.extract_from_html(html, url)

# Acceder a los diferentes tipos de contenido
title = extracted["title"]
main_content = extracted["main_content"]
tables = extracted["tables"]
links = extracted["links"]
images = extracted["images"]
metadata = extracted["metadata"]

# Analizar sentimiento
sentiment = content_extractor.analyze_sentiment(main_content)
```

## Configuración

El módulo utiliza el sistema de configuración modular de agent-isa. La configuración se encuentra en `OpenManusWeb/config/content.toml`.

### Opciones de Configuración

#### General
```toml
[general]
enabled = true
cache_results = true
cache_expiry = 3600  # Segundos
```

#### Extracción
```toml
[extraction]
extract_tables = true
extract_links = true
extract_images = true
extract_metadata = true
max_content_length = 50000  # Caracteres
max_tables = 10
max_links = 100
max_images = 50
```

#### Análisis
```toml
[analysis]
enable_sentiment_analysis = true
enable_entity_extraction = false  # Requiere bibliotecas adicionales
enable_summarization = false  # Requiere bibliotecas adicionales
enable_keyword_extraction = true
```

#### Tablas
```toml
[tables]
normalize_headers = true
max_rows = 100
max_cols = 20
```

#### Procesamiento de Texto
```toml
[text_processing]
remove_boilerplate = true
clean_whitespace = true
preserve_paragraphs = true
min_paragraph_length = 20  # Caracteres
```

## Ejemplos de Uso

### Extracción de Contenido Completo

```python
import asyncio
from modules.core import ConfigManager
from modules.search import WebSearchEngine, HeadlessBrowser
from modules.content import ContentExtractor

async def search_and_extract(query, num_results=1):
    # Inicializar componentes
    config_manager = ConfigManager()
    search_engine = WebSearchEngine(config_manager)
    browser = HeadlessBrowser(config_manager)
    content_extractor = ContentExtractor(config_manager)
    
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
        
        html = await browser.navigate(first_result.url)
        
        # Extraer contenido
        extracted = content_extractor.extract_from_html(html, first_result.url)
        
        # Mostrar información extraída
        print(f"Título: {extracted['title']}")
        print(f"Contenido principal ({len(extracted['main_content'])} caracteres):")
        print(extracted['main_content'][:500] + "...")
        
        # Mostrar tablas si hay
        if extracted['tables']:
            print(f"\nTablas encontradas: {len(extracted['tables'])}")
            for i, table in enumerate(extracted['tables'], 1):
                print(f"Tabla {i}: {table['title']} ({table['num_rows']} filas, {table['num_cols']} columnas)")
        
        # Mostrar enlaces
        if extracted['links']:
            print(f"\nEnlaces encontrados: {len(extracted['links'])}")
            for i, link in enumerate(extracted['links'][:5], 1):
                print(f"{i}. {link['text']}: {link['url']}")
            
            if len(extracted['links']) > 5:
                print(f"... y {len(extracted['links']) - 5} enlaces más")
        
        # Analizar sentimiento
        sentiment = content_extractor.analyze_sentiment(extracted['main_content'])
        print(f"\nAnálisis de sentimiento: {sentiment['sentiment']} (score: {sentiment['score']:.2f})")
        
    finally:
        # Cerrar navegador
        await browser.close()

# Ejecutar
asyncio.run(search_and_extract("inteligencia artificial"))
```

### Extracción de Tablas

```python
import asyncio
import pandas as pd
from modules.core import ConfigManager
from modules.search import HeadlessBrowser
from modules.content import ContentExtractor

async def extract_tables(url):
    # Inicializar componentes
    config_manager = ConfigManager()
    browser = HeadlessBrowser(config_manager)
    content_extractor = ContentExtractor(config_manager)
    
    try:
        # Navegar a la URL
        html = await browser.navigate(url)
        
        # Extraer contenido
        extracted = content_extractor.extract_from_html(html, url)
        
        # Procesar tablas
        if not extracted['tables']:
            print("No se encontraron tablas en la página")
            return []
        
        print(f"Se encontraron {len(extracted['tables'])} tablas")
        
        # Convertir a DataFrames
        dataframes = []
        for i, table in enumerate(extracted['tables'], 1):
            print(f"Tabla {i}: {table['title']}")
            
            # Crear DataFrame
            if table['headers'] and table['data']:
                df = pd.DataFrame(table['data'])
                dataframes.append((table['title'], df))
        
        return dataframes
        
    finally:
        # Cerrar navegador
        await browser.close()

# Ejecutar
asyncio.run(extract_tables("https://example.com/page-with-tables"))
```

## Uso desde la Línea de Comandos

El módulo incluye un comando en el script de prueba que puede ser utilizado desde la línea de comandos:

```bash
# Búsqueda avanzada con extracción de contenido
python OpenManusWeb/test_search.py advanced "inteligencia artificial" --results 3 --extract all

# Extraer solo texto
python OpenManusWeb/test_search.py advanced "python tutorial" --extract text

# Extraer solo tablas
python OpenManusWeb/test_search.py advanced "estadísticas población" --extract tables

# Extraer solo enlaces
python OpenManusWeb/test_search.py advanced "recursos programación" --extract links
```

## Dependencias

El módulo requiere las siguientes dependencias:

- beautifulsoup4
- pandas
- requests

Puedes instalarlas con:

```bash
pip install -r requirements/content.txt
```

O usando el script de instalación:

```bash
./install.sh --content
```

## Limitaciones y Consideraciones

- **Estructura de Páginas**: La extracción de contenido depende de la estructura HTML de las páginas, que puede variar significativamente entre sitios web.
- **Tablas Complejas**: Las tablas con celdas combinadas o estructuras anidadas pueden no extraerse correctamente.
- **Contenido Dinámico**: El contenido cargado dinámicamente con JavaScript puede no estar disponible en el HTML inicial.
- **Análisis de Sentimiento**: El análisis de sentimiento implementado es básico y puede no ser preciso para todos los idiomas o contextos.

## Desarrollo Futuro

- Soporte para extracción de contenido estructurado (JSON-LD, microdata)
- Mejora en el análisis de sentimiento con modelos de ML
- Extracción de entidades nombradas
- Generación automática de resúmenes
- Soporte para más idiomas
