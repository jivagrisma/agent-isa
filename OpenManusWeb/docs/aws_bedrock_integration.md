# Integración con AWS Bedrock en OpenManusWeb

Este documento describe la integración de OpenManusWeb con AWS Bedrock, incluyendo la configuración, uso y solución de problemas comunes.

## Índice

1. [Introducción](#introducción)
2. [Requisitos](#requisitos)
3. [Configuración](#configuración)
4. [Uso](#uso)
5. [Modelos Soportados](#modelos-soportados)
6. [Solución de Problemas](#solución-de-problemas)
7. [Mejores Prácticas](#mejores-prácticas)
8. [Referencias](#referencias)

## Introducción

AWS Bedrock es un servicio de Amazon Web Services que proporciona acceso a modelos de lenguaje de gran escala (LLMs) a través de una API unificada. OpenManusWeb integra AWS Bedrock para proporcionar capacidades avanzadas de procesamiento de lenguaje natural.

La integración permite utilizar modelos como Amazon Nova Pro y Claude 3 Sonnet directamente desde la interfaz de OpenManusWeb, aprovechando la potencia de estos modelos para diversas tareas de procesamiento de lenguaje natural.

## Requisitos

Para utilizar AWS Bedrock con OpenManusWeb, necesitarás:

1. **Cuenta de AWS** con acceso a AWS Bedrock
2. **Credenciales de AWS** (Access Key ID y Secret Access Key)
3. **Región de AWS** donde AWS Bedrock esté disponible (por ejemplo, us-east-1)
4. **Acceso a los modelos** que deseas utilizar (Amazon Nova Pro, Claude 3 Sonnet, etc.)
5. **Python 3.12** o superior
6. **Dependencias** instaladas: boto3, botocore

## Configuración

### 1. Configuración de AWS Bedrock

Antes de configurar OpenManusWeb, asegúrate de que tu cuenta de AWS tenga acceso a AWS Bedrock y a los modelos que deseas utilizar. Puedes verificar esto en la consola de AWS Bedrock.

### 2. Configuración en OpenManusWeb

La configuración de AWS Bedrock en OpenManusWeb se realiza a través del archivo `config/config.toml`. A continuación se muestra un ejemplo de configuración:

```toml
# Configuración para AWS Bedrock
[llm]
api_type = 'bedrock'
model = "Amazon Nova Pro"
model_id = "amazon.nova-pro-v1:0"
region = "us-east-1"
aws_access_key_id = "TU_ACCESS_KEY_ID"
aws_secret_access_key = "TU_SECRET_ACCESS_KEY"
max_tokens = 4096
temperature = 0.0
base_url = "https://bedrock-runtime.us-east-1.amazonaws.com"
api_key = "dummy-key-for-bedrock"
api_version = ""
```

Reemplaza `TU_ACCESS_KEY_ID` y `TU_SECRET_ACCESS_KEY` con tus credenciales de AWS.

### 3. Verificación de la Configuración

Para verificar que la configuración es correcta, puedes ejecutar el script de prueba incluido:

```bash
python test_bedrock.py
```

Este script realizará pruebas de comunicación con AWS Bedrock y verificará que todo esté configurado correctamente.

## Uso

### Uso desde la Línea de Comandos

OpenManusWeb proporciona una interfaz de línea de comandos para interactuar con AWS Bedrock. Puedes utilizarla ejecutando:

```bash
python test_cli.py
```

Este script te permitirá enviar mensajes a AWS Bedrock y recibir respuestas directamente desde la línea de comandos.

### Uso desde la Interfaz Web

La interfaz web de OpenManusWeb proporciona una forma intuitiva de interactuar con AWS Bedrock. Para iniciar la interfaz web, ejecuta:

```bash
python web_run.py
```

Luego, abre tu navegador y navega a `http://localhost:8000` para acceder a la interfaz web.

## Modelos Soportados

OpenManusWeb soporta los siguientes modelos de AWS Bedrock:

### Amazon Nova Pro

- **ID del Modelo**: amazon.nova-pro-v1:0
- **Características**: Modelo de lenguaje avanzado de Amazon con capacidades de generación de texto, respuesta a preguntas y más.
- **Formato de Mensajes**:
  ```json
  {
    "messages": [
      {
        "role": "user",
        "content": [{"text": "Tu mensaje aquí"}]
      }
    ]
  }
  ```

### Claude 3 Sonnet

- **ID del Modelo**: anthropic.claude-3-7-sonnet-20250219-v1:0
- **Características**: Modelo de lenguaje avanzado de Anthropic con capacidades de generación de texto, respuesta a preguntas y más.
- **Formato de Mensajes**:
  ```json
  {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 4096,
    "temperature": 0.7,
    "messages": [
      {"role": "user", "content": "Tu mensaje aquí"}
    ]
  }
  ```

## Solución de Problemas

### Problemas Comunes y Soluciones

#### 1. Error "First message must use the 'user' role"

**Problema**: AWS Bedrock requiere que el primer mensaje en una conversación sea de tipo "user".

**Solución**: Asegúrate de que el primer mensaje en la lista de mensajes sea de tipo "user". OpenManusWeb maneja esto automáticamente, pero si estás utilizando la API directamente, debes asegurarte de que el primer mensaje sea de tipo "user".

#### 2. Error "RetryError[<Future at 0x... state=finished raised APIConnectionError>]"

**Problema**: Este error ocurre debido a problemas de conexión con la API de AWS Bedrock.

**Solución**:
- Verifica que tus credenciales de AWS sean correctas
- Verifica que la región especificada sea correcta
- Verifica que tengas acceso a AWS Bedrock y al modelo especificado
- Aumenta los timeouts y retries en la configuración
- Implementa un mecanismo de reconexión automática

#### 3. Respuestas Vacías o Incompletas

**Problema**: A veces, AWS Bedrock puede devolver respuestas vacías o incompletas.

**Solución**:
- Verifica que el formato de los mensajes sea correcto
- Aumenta el valor de `max_tokens` para permitir respuestas más largas
- Implementa un mecanismo de fallback para proporcionar respuestas alternativas en caso de error

### Logs y Depuración

OpenManusWeb proporciona logs detallados que pueden ayudarte a identificar y solucionar problemas. Los logs se encuentran en el directorio `logs/`.

Para habilitar logs más detallados, puedes modificar el nivel de logging en el archivo `app/logging_config.py`.

## Mejores Prácticas

### 1. Manejo de Credenciales

- **No incluyas credenciales en el código**: Utiliza variables de entorno o archivos de configuración seguros.
- **Rota las credenciales regularmente**: Cambia tus credenciales de AWS regularmente para mantener la seguridad.
- **Utiliza IAM con privilegios mínimos**: Crea un usuario de IAM con acceso únicamente a AWS Bedrock.

### 2. Optimización de Rendimiento

- **Implementa caché**: Almacena en caché las respuestas para preguntas frecuentes para reducir el número de llamadas a la API.
- **Utiliza streaming**: Utiliza streaming para obtener respuestas más rápidamente y proporcionar una mejor experiencia de usuario.
- **Ajusta los timeouts**: Configura timeouts adecuados para evitar bloqueos en la aplicación.

### 3. Manejo de Errores

- **Implementa reintentos**: Utiliza un mecanismo de reintentos para manejar errores transitorios.
- **Proporciona respuestas de fallback**: En caso de error, proporciona una respuesta alternativa al usuario.
- **Monitorea los errores**: Implementa un sistema de monitoreo para detectar y solucionar errores rápidamente.

## Referencias

- [Documentación de AWS Bedrock](https://docs.aws.amazon.com/bedrock/)
- [Documentación de boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Documentación de Claude](https://docs.anthropic.com/claude/docs)
- [Documentación de Amazon Nova](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-nova.html)
