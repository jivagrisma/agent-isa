# Cliente LLM Extendido para Agent-ISA

## Descripción

El cliente LLM extendido proporciona una capa de abstracción sobre los diferentes modelos de lenguaje disponibles en AWS Bedrock y otras plataformas. Está diseñado para facilitar el uso de múltiples modelos, proporcionar fallback automático y optimizar los prompts según el modelo utilizado.

## Características Principales

- **Soporte para múltiples modelos**: Permite utilizar diferentes modelos de AWS Bedrock y otras plataformas.
- **Fallback automático**: Si un modelo falla, intenta automáticamente con otro modelo.
- **Optimización de prompts**: Adapta los prompts según el modelo utilizado para obtener mejores resultados.
- **Soporte para herramientas (function calling)**: Permite utilizar herramientas con modelos que las soportan.
- **Gestión de errores mejorada**: Manejo robusto de errores y reintentos.

## Uso Básico

### Generación de Texto

```python
from modules.core import ConfigManager, ExtendedLLMClient
import asyncio

async def generate_text():
    # Inicializar
    config_manager = ConfigManager()
    llm_client = ExtendedLLMClient(config_manager)
    
    # Crear mensaje
    messages = [{"role": "user", "content": "Explica qué es la inteligencia artificial"}]
    
    # Enviar solicitud
    response = await llm_client.ask(
        messages=messages,
        model="anthropic.claude-3-sonnet-20240229-v1:0",  # Opcional, usa el predeterminado si no se especifica
        temperature=0.7
    )
    
    # Procesar respuesta
    print(response)

# Ejecutar
asyncio.run(generate_text())
```

### Uso de Herramientas (Function Calling)

```python
from modules.core import ConfigManager, ExtendedLLMClient
import asyncio
import json

async def use_tools():
    # Inicializar
    config_manager = ConfigManager()
    llm_client = ExtendedLLMClient(config_manager)
    
    # Definir herramientas
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Obtiene el clima actual para una ubicación",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "La ciudad y país, por ejemplo: 'Madrid, España'"
                        },
                        "unit": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "Unidad de temperatura"
                        }
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    # Crear mensaje
    messages = [{"role": "user", "content": "¿Cuál es el clima en Barcelona?"}]
    
    # Enviar solicitud
    response = await llm_client.ask_tool(
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
    
    # Procesar respuesta
    if "tool_calls" in response and response["tool_calls"]:
        for tool_call in response["tool_calls"]:
            function_name = tool_call.get("function", {}).get("name", "")
            function_args = tool_call.get("function", {}).get("arguments", "{}")
            
            print(f"Función: {function_name}")
            print(f"Argumentos: {function_args}")
    
    # Respuesta de texto
    print(response.get("response", ""))

# Ejecutar
asyncio.run(use_tools())
```

## Configuración

El cliente LLM extendido utiliza el sistema de configuración modular de agent-isa. La configuración se encuentra en `OpenManusWeb/config/core.toml`.

### Opciones de Configuración

```toml
[llm]
api_type = "bedrock"  # "openai", "azure", "bedrock"
model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
region = "us-east-1"

# Configuración específica para cada proveedor
[llm.providers.bedrock]
temperature = 0.7
max_tokens = 4096
top_p = 0.9

[llm.providers.openai]
api_key = ""
base_url = "https://api.openai.com/v1"
model = "gpt-4"
temperature = 0.7
max_tokens = 4096

[llm.providers.azure]
api_key = ""
base_url = ""
api_version = "2023-05-15"
deployment_name = "gpt-4"
temperature = 0.7
max_tokens = 4096
```

## Modelos Soportados

El cliente LLM extendido soporta los siguientes modelos:

- **Claude 3.7 Sonnet** (`anthropic.claude-3-sonnet-20240229-v1:0`)
  - Capacidades: chat, herramientas, visión
  - Tokens máximos: 4096

- **Amazon Nova Lite** (`amazon.nova-lite-v1`)
  - Capacidades: chat
  - Tokens máximos: 4096

- **Amazon Nova Pro** (`amazon.nova-pro-v1`)
  - Capacidades: chat, herramientas
  - Tokens máximos: 4096

## Optimización de Prompts

El cliente LLM extendido optimiza automáticamente los prompts según el modelo utilizado:

- **Claude**: Elimina marcadores específicos de otros modelos y ajusta el formato.
- **Nova**: Adapta el formato de los mensajes para el modelo de Amazon.

## Fallback Automático

Si un modelo falla, el cliente LLM extendido intentará automáticamente con el modelo predeterminado. Este comportamiento se puede desactivar estableciendo `fallback=False` en las llamadas a `ask()` y `ask_tool()`.

## Ejemplos de Uso desde la Línea de Comandos

El módulo incluye un script de prueba que puede ser utilizado desde la línea de comandos:

```bash
# Generar texto
python OpenManusWeb/test_extended_llm.py ask "Explica qué es la inteligencia artificial" --model anthropic.claude-3-sonnet-20240229-v1:0

# Usar herramientas
python OpenManusWeb/test_extended_llm.py tool "¿Cuál es el clima en Barcelona?" --temperature 0.5

# Listar modelos disponibles
python OpenManusWeb/test_extended_llm.py models
```

## Integración con Otros Módulos

El cliente LLM extendido está diseñado para integrarse con otros módulos de agent-isa:

- **Módulo de Búsqueda Web**: Permite utilizar los resultados de búsqueda como contexto para el LLM.
- **Módulo de Procesamiento de Contenido**: Facilita el análisis y generación de contenido estructurado.
- **Módulo de Generación de Imágenes**: Permite generar imágenes a partir de descripciones textuales.

## Limitaciones y Consideraciones

- **Disponibilidad de Modelos**: La disponibilidad de los modelos depende de la configuración de AWS Bedrock.
- **Cuotas y Costos**: El uso de los modelos está sujeto a las cuotas y costos de AWS Bedrock.
- **Optimización de Prompts**: La optimización de prompts es un proceso en evolución y puede requerir ajustes según el caso de uso.
- **Herramientas**: No todos los modelos soportan herramientas (function calling).
