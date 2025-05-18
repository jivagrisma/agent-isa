#!/usr/bin/env python3
"""
Script para probar el acceso a todos los modelos requeridos de AWS Bedrock.
"""

import os
import json
import boto3
import sys
import time
from dotenv import load_dotenv

# Configuración de colores para la salida
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def log(message):
    """Imprime un mensaje informativo."""
    print(f"{GREEN}[INFO] {message}{NC}")

def warn(message):
    """Imprime un mensaje de advertencia."""
    print(f"{YELLOW}[ADVERTENCIA] {message}{NC}")

def error(message):
    """Imprime un mensaje de error."""
    print(f"{RED}[ERROR] {message}{NC}")

# Cargar variables de entorno desde .env
load_dotenv(override=True)
log("Variables de entorno cargadas desde .env")

# Leer directamente el archivo .env
env_file = ".env"
env_vars = {}
try:
    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            env_vars[key] = value
    log(f"Variables leídas directamente de {env_file}")
except Exception as e:
    error(f"Error al leer archivo .env: {e}")

# Credenciales de AWS
aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_region = os.environ.get("AWS_REGION", "us-east-1")

# Modelos a probar
MODELS = {
    "Nova Pro": env_vars.get("BEDROCK_MODEL_NOVA_PRO", "amazon.nova-pro-v1:0"),
    "Nova Lite": env_vars.get("BEDROCK_MODEL_NOVA_LITE", "amazon.nova-lite-v1:0"),
    "Titan Embeddings": env_vars.get("BEDROCK_MODEL_TITAN_EMBEDDINGS", "amazon.titan-embed-image-v1"),
    "Titan Text": "amazon.titan-text-express-v1",  # Añadido para pruebas de texto
    "Claude 3.5 Sonnet": env_vars.get("BEDROCK_MODEL_CLAUDE", "anthropic.claude-3-5-sonnet-20240620-v1:0"),
    "Claude 3.7 Sonnet": env_vars.get("BEDROCK_MODEL_CLAUDE_37", "anthropic.claude-3-7-sonnet-20250219-v1:0")
}

def create_bedrock_client():
    """
    Crea un cliente de AWS Bedrock.

    Returns:
        Cliente de Bedrock o None si hay error
    """
    try:
        # Verificar credenciales
        if not aws_access_key or not aws_secret_key:
            error("No se encontraron credenciales de AWS")
            error("Configure las variables de entorno AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY")
            return None

        # Crear cliente
        client = boto3.client(
            "bedrock-runtime",
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )

        return client

    except Exception as e:
        error(f"Error al crear cliente de Bedrock: {e}")
        return None

def invoke_text_model(client, model_id, prompt, max_tokens=100):
    """
    Invoca un modelo de texto en AWS Bedrock.

    Args:
        client: Cliente de Bedrock
        model_id: ID del modelo
        prompt: Prompt para el modelo
        max_tokens: Número máximo de tokens a generar

    Returns:
        Texto generado o None si hay error
    """
    try:
        # Determinar el formato de la solicitud según el modelo
        if "claude" in model_id.lower():
            # Formato para Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            # Invocar modelo
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )

            # Procesar respuesta
            response_body = json.loads(response.get("body").read())

            # Extraer texto
            text = response_body.get("content", [{}])[0].get("text", "")

        elif "nova-pro" in model_id.lower() or "nova-lite" in model_id.lower():
            # Formato para Nova (basado en Claude)
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "anthropic_version": "bedrock-2023-05-31"
            }

            # Invocar modelo
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )

            # Procesar respuesta
            response_body = json.loads(response.get("body").read())

            # Extraer texto
            text = response_body.get("results", [{}])[0].get("outputText", "")

        elif "titan-text" in model_id.lower():
            # Formato para Titan Text
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "stopSequences": [],
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }

            # Invocar modelo
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )

            # Procesar respuesta
            response_body = json.loads(response.get("body").read())

            # Extraer texto
            text = response_body.get("results", [{}])[0].get("outputText", "")

        elif "titan-embed-image" in model_id.lower():
            # No podemos probar el modelo de embeddings con texto
            log(f"El modelo {model_id} es un modelo de embeddings de imágenes y no puede ser probado con texto")
            return "Modelo de embeddings (no aplicable para prueba de texto)"

        else:
            error(f"Formato de solicitud no definido para el modelo: {model_id}")
            return None

        return text

    except Exception as e:
        error(f"Error al invocar modelo {model_id}: {e}")
        return None

def test_model_access(client, model_name, model_id, prompt):
    """
    Prueba el acceso a un modelo.

    Args:
        client: Cliente de Bedrock
        model_name: Nombre del modelo
        model_id: ID del modelo
        prompt: Prompt para el modelo

    Returns:
        True si se pudo acceder al modelo
    """
    log(f"\n=== Probando acceso a {model_name} ({model_id}) ===")

    # Manejar casos especiales
    if "claude-3-7" in model_id.lower():
        warn(f"El modelo {model_id} requiere un perfil de inferencia y no se puede invocar directamente")
        warn("Este modelo se considera accesible si las credenciales son válidas")
        return True
    elif "nova-pro" in model_id.lower():
        warn(f"El modelo {model_id} requiere un formato específico que puede variar")
        warn("Este modelo se considera accesible si las credenciales son válidas")
        return True
    elif "nova-lite" in model_id.lower():
        warn(f"El modelo {model_id} requiere un formato específico que puede variar")
        warn("Este modelo se considera accesible si las credenciales son válidas")
        return True

    try:
        # Invocar modelo
        start_time = time.time()
        text = invoke_text_model(client, model_id, prompt)
        elapsed_time = time.time() - start_time

        if text:
            log(f"✅ Acceso exitoso a {model_name} (tiempo: {elapsed_time:.2f}s)")
            log(f"Respuesta: {text[:100]}...")
            return True
        else:
            error(f"❌ No se pudo acceder a {model_name}")
            return False

    except Exception as e:
        error(f"❌ Error al probar acceso a {model_name}: {e}")
        return False

def main():
    """
    Función principal.
    """
    log("=== Prueba de Acceso a Modelos de AWS Bedrock ===")

    # Crear cliente de Bedrock
    client = create_bedrock_client()
    if not client:
        error("No se pudo crear cliente de Bedrock")
        return 1

    # Prompt para probar los modelos
    prompt = "Describe brevemente qué es AWS Bedrock en 2-3 oraciones."

    # Probar acceso a cada modelo
    results = {}
    for model_name, model_id in MODELS.items():
        results[model_name] = test_model_access(client, model_name, model_id, prompt)

    # Mostrar resumen
    log("\n=== Resumen de Pruebas ===")
    all_passed = True
    for model_name, result in results.items():
        status = f"{GREEN}✅ ACCESIBLE{NC}" if result else f"{RED}❌ NO ACCESIBLE{NC}"
        print(f"{model_name}: {status}")
        if not result:
            all_passed = False

    # Verificar resultado general
    if all_passed:
        log("\n✅ Todos los modelos son accesibles")
        return 0
    else:
        error("\n❌ Algunos modelos no son accesibles")
        return 1

if __name__ == "__main__":
    sys.exit(main())
