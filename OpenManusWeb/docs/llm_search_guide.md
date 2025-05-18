# Guía de Búsqueda Web para LLM/Agentes

## Descripción

Esta guía está diseñada para modelos de lenguaje y agentes autónomos que utilizan agent-isa. Proporciona instrucciones sobre cómo utilizar el módulo de búsqueda web para obtener información de internet.

## Capacidades Disponibles

El módulo de búsqueda web proporciona las siguientes capacidades:

1. **Búsqueda en motores de búsqueda**
   - Buscar información en Google, Bing y otros motores
   - Obtener resultados con título, URL y snippet
   - Filtrar y ordenar resultados

2. **Navegación web**
   - Navegar a URLs específicas
   - Extraer contenido de páginas web
   - Interactuar con elementos de la página

3. **Extracción de contenido**
   - Extraer texto principal
   - Obtener enlaces relevantes
   - Capturar imágenes (opcional)

## Flujos de Trabajo

### Flujo 1: Búsqueda Básica

```json
{
  "task": "Búsqueda de información",
  "workflow": [
    {
      "module": "search",
      "function": "web_search",
      "inputs": ["cambio climático soluciones", 5],
      "outputs": ["search_results"]
    }
  ],
  "expected_output": "Lista de resultados de búsqueda con título, URL y snippet"
}
```

### Flujo 2: Búsqueda y Navegación

```json
{
  "task": "Búsqueda y extracción de contenido",
  "workflow": [
    {
      "module": "search",
      "function": "web_search",
      "inputs": ["cambio climático soluciones", 3],
      "outputs": ["search_results"]
    },
    {
      "module": "search",
      "function": "navigate",
      "inputs": ["search_results[0].url"],
      "outputs": ["page_content"]
    }
  ],
  "expected_output": "Contenido extraído de la primera página de resultados"
}
```

### Flujo 3: Búsqueda Avanzada con Filtrado

```json
{
  "task": "Búsqueda avanzada con filtrado",
  "workflow": [
    {
      "module": "search",
      "function": "web_search",
      "inputs": ["python tutorial", 10, "google"],
      "outputs": ["all_results"]
    },
    {
      "module": "core",
      "function": "filter_results",
      "inputs": ["all_results", "title contains 'principiantes'"],
      "outputs": ["filtered_results"]
    },
    {
      "module": "search",
      "function": "navigate",
      "inputs": ["filtered_results[0].url"],
      "outputs": ["tutorial_content"]
    }
  ],
  "expected_output": "Contenido de un tutorial de Python para principiantes"
}
```

## Ejemplos de Código

### Ejemplo 1: Búsqueda Simple

```python
# Búsqueda simple en Google
search_results = web_search("inteligencia artificial aplicaciones", num_results=5)

# Mostrar resultados
for result in search_results:
    print(f"Título: {result.title}")
    print(f"URL: {result.url}")
    print(f"Snippet: {result.snippet}")
    print()
```

### Ejemplo 2: Navegación a una URL

```python
# Navegar a una URL específica
content = await navigate("https://example.com")

# Procesar contenido
print(content)
```

### Ejemplo 3: Búsqueda y Navegación

```python
# Búsqueda y navegación
search_results = web_search("mejores prácticas python", num_results=3)

if search_results:
    # Navegar al primer resultado
    first_result = search_results[0]
    content = await navigate(first_result.url)
    
    # Extraer información relevante
    summary = summarize(content, max_length=200)
    print(summary)
```

## Parámetros de Funciones

### web_search

```json
{
  "function": "web_search",
  "parameters": [
    {
      "name": "query",
      "type": "string",
      "description": "Consulta de búsqueda",
      "required": true
    },
    {
      "name": "num_results",
      "type": "integer",
      "description": "Número de resultados a devolver",
      "required": false,
      "default": 5
    },
    {
      "name": "search_engine",
      "type": "string",
      "description": "Motor de búsqueda a utilizar",
      "required": false,
      "default": "google",
      "options": ["google", "bing"]
    },
    {
      "name": "use_cache",
      "type": "boolean",
      "description": "Si debe usar la caché",
      "required": false,
      "default": true
    }
  ],
  "returns": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "title": "string",
        "url": "string",
        "snippet": "string",
        "source": "string"
      }
    }
  }
}
```

### navigate

```json
{
  "function": "navigate",
  "parameters": [
    {
      "name": "url",
      "type": "string",
      "description": "URL a navegar",
      "required": true
    }
  ],
  "returns": {
    "type": "string",
    "description": "Contenido extraído de la página"
  }
}
```

## Mejores Prácticas

1. **Consultas Específicas**: Utiliza consultas de búsqueda específicas para obtener resultados más relevantes.
2. **Verificación de Fuentes**: Verifica la credibilidad de las fuentes antes de utilizar la información.
3. **Citar Fuentes**: Siempre cita las fuentes de la información obtenida.
4. **Limitar Solicitudes**: Evita realizar demasiadas solicitudes en poco tiempo para prevenir bloqueos.
5. **Manejo de Errores**: Implementa manejo de errores para casos donde la búsqueda o navegación falle.

## Solución de Problemas

### Problema: No se encuentran resultados

**Posibles causas:**
- Consulta demasiado específica o con errores ortográficos
- Problemas de conectividad
- Bloqueo por parte del motor de búsqueda

**Soluciones:**
- Reformular la consulta con términos más generales
- Verificar la conexión a internet
- Esperar un tiempo antes de intentar nuevamente

### Problema: Error al navegar a una URL

**Posibles causas:**
- URL inválida o mal formada
- Página no disponible o requiere autenticación
- Contenido cargado dinámicamente con JavaScript

**Soluciones:**
- Verificar que la URL sea correcta y esté completa
- Intentar con otra URL de los resultados de búsqueda
- Aumentar el tiempo de espera para páginas con contenido dinámico

## Limitaciones

- El módulo no puede acceder a contenido que requiere autenticación
- Algunas páginas pueden bloquear el acceso a navegadores automatizados
- La extracción de contenido puede no ser perfecta en páginas con estructuras complejas
- Los resultados de búsqueda pueden variar según la región y otros factores
