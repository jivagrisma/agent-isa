#!/usr/bin/env python3
"""
Script para probar la invocación del modelo Titan Text en AWS Bedrock.
"""

import os
import json
import boto3
import sys

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)  # Forzar recarga de variables
    print("Variables de entorno cargadas desde .env")
except ImportError:
    print("python-dotenv no está instalado, no se pueden cargar variables desde .env")

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
    print(f"Variables leídas directamente de {env_file}")
except Exception as e:
    print(f"Error al leer archivo .env: {e}")

# Credenciales de AWS
aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_region = os.environ.get("AWS_REGION", "us-east-1")

def invoke_titan_text(prompt: str, max_tokens: int = 100):
    """
    Invoca el modelo Titan Text en AWS Bedrock.
    
    Args:
        prompt: Prompt para el modelo
        max_tokens: Número máximo de tokens a generar
    """
    # ID del modelo Titan Text
    model_id = "amazon.titan-text-express-v1"
    
    print(f"Invocando modelo Titan Text ({model_id}) con prompt: {prompt}")
    
    # Verificar credenciales
    if not aws_access_key or not aws_secret_key:
        print("Error: No se encontraron credenciales de AWS")
        print("Configure las variables de entorno AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY")
        return
    
    try:
        # Crear cliente de Bedrock
        bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        
        # Preparar parámetros para Titan Text
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
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )
        
        # Procesar respuesta
        response_body = json.loads(response.get("body").read())
        
        # Extraer texto
        text = response_body.get("results", [{}])[0].get("outputText", "")
        
        print("\nRespuesta:")
        print(text)
        
        return text
        
    except Exception as e:
        print(f"Error al invocar modelo: {e}")
        return None

def main():
    """
    Función principal.
    """
    # Obtener prompt de los argumentos o usar uno predeterminado
    prompt = "Describe brevemente qué es AWS Bedrock"
    if len(sys.argv) > 1:
        prompt = sys.argv[1]
    
    # Invocar modelo
    invoke_titan_text(prompt)

if __name__ == "__main__":
    main()
