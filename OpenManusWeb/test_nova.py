#!/usr/bin/env python3
"""
Script para probar el acceso a los modelos Nova Pro y Nova Lite de AWS Bedrock.
"""

import os
import json
import boto3
import sys
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

# IDs de los modelos Nova
nova_pro_model_id = env_vars.get("BEDROCK_MODEL_NOVA_PRO", "amazon.nova-pro-v1:0")
nova_lite_model_id = env_vars.get("BEDROCK_MODEL_NOVA_LITE", "amazon.nova-lite-v1:0")

def invoke_nova_model(model_id, prompt):
    """
    Invoca un modelo Nova en AWS Bedrock.

    Args:
        model_id: ID del modelo
        prompt: Prompt para el modelo
    """
    log(f"Invocando modelo {model_id} con prompt: {prompt}")

    # Verificar credenciales
    if not aws_access_key or not aws_secret_key:
        error("No se encontraron credenciales de AWS")
        error("Configure las variables de entorno AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY")
        return

    try:
        # Crear cliente de Bedrock
        client = boto3.client(
            "bedrock-runtime",
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )

        # Formato para Nova Pro y Nova Lite según la documentación oficial
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 500,
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

        # Extraer texto según el formato de respuesta de Nova
        if "output" in response_body:
            # Formato de respuesta de la API Converse
            text = response_body.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
        else:
            # Intentar otros formatos posibles
            text = response_body.get("content", [{}])[0].get("text", "")

        log("\nRespuesta:")
        log(text)

        return text

    except Exception as e:
        error(f"Error al invocar modelo: {e}")
        return None

def main():
    """
    Función principal.
    """
    # Obtener prompt de los argumentos o usar uno predeterminado
    prompt = "Describe brevemente qué es AWS Bedrock en 2-3 oraciones."
    if len(sys.argv) > 1:
        prompt = sys.argv[1]

    # Obtener modelo de los argumentos o usar Nova Pro por defecto
    model = "nova_pro"
    if len(sys.argv) > 2:
        model = sys.argv[2]

    log("=== Prueba de Acceso a Modelos Nova de AWS Bedrock ===")

    # Invocar modelo según la selección
    if model.lower() == "nova_pro":
        log(f"Probando Nova Pro ({nova_pro_model_id})")
        invoke_nova_model(nova_pro_model_id, prompt)
    elif model.lower() == "nova_lite":
        log(f"Probando Nova Lite ({nova_lite_model_id})")
        invoke_nova_model(nova_lite_model_id, prompt)
    else:
        error(f"Modelo no reconocido: {model}")
        error("Modelos disponibles: nova_pro, nova_lite")

if __name__ == "__main__":
    main()
