#!/usr/bin/env python3
"""
Script para listar los modelos disponibles en AWS Bedrock.
"""

import os
import sys
import boto3
import json
from pprint import pprint

# Configurar credenciales desde variables de entorno
aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_region = os.environ.get("AWS_REGION", "us-east-1")

def list_models():
    """
    Lista los modelos disponibles en AWS Bedrock.
    """
    print("=== Modelos Disponibles en AWS Bedrock ===")

    # Verificar credenciales
    if not aws_access_key or not aws_secret_key:
        print("Error: No se encontraron credenciales de AWS")
        print("Configure las variables de entorno AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY")
        return

    try:
        # Crear cliente de Bedrock
        bedrock_client = boto3.client(
            "bedrock",
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )

        # Listar modelos
        response = bedrock_client.list_foundation_models()

        # Mostrar modelos
        print(f"Total de modelos: {len(response.get('modelSummaries', []))}")
        print("\nLista de modelos:")

        # Ordenar modelos por proveedor y nombre
        models = sorted(response.get("modelSummaries", []), key=lambda x: (x.get("providerName", ""), x.get("modelName", "")))

        # Mostrar información de cada modelo
        for i, model in enumerate(models, 1):
            model_id = model.get('modelId', 'Desconocido')
            model_name = model.get('modelName', 'Desconocido')

            print(f"\n{i}. {model_name} ({model_id})")
            print(f"   Proveedor: {model.get('providerName', 'Desconocido')}")

            # Extraer tipo de modelo de manera segura
            model_arn = model.get('modelArn', '')
            model_type = "Desconocido"
            if model_arn:
                try:
                    model_type = model_arn.split(':')[-1].split('/')[-2]
                except (IndexError, AttributeError):
                    pass

            print(f"   Tipo: {model_type}")
            print(f"   ARN: {model.get('modelArn', 'Desconocido')}")

            # Destacar modelos específicos
            if "claude" in model_id.lower():
                print(f"   *** CLAUDE MODEL: {model_id} ***")
            elif "nova" in model_id.lower():
                print(f"   *** NOVA MODEL: {model_id} ***")
            elif "titan" in model_id.lower() and "embed" in model_id.lower():
                print(f"   *** TITAN EMBEDDINGS MODEL: {model_id} ***")

            # Mostrar capacidades
            if "inferenceTypesSupported" in model:
                print(f"   Tipos de inferencia: {', '.join(model['inferenceTypesSupported'])}")

            # Mostrar estado
            if "modelLifecycle" in model:
                print(f"   Estado: {model['modelLifecycle'].get('status', 'Desconocido')}")

        return models

    except Exception as e:
        print(f"Error al listar modelos: {e}")
        return None

def main():
    """
    Función principal.
    """
    # Cargar variables de entorno desde .env si existe
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Listar modelos
    models = list_models()

    # Guardar lista de modelos en un archivo JSON
    if models:
        try:
            with open("bedrock_models.json", "w") as f:
                json.dump(models, f, indent=2, default=str)
            print("\nLista de modelos guardada en bedrock_models.json")
        except Exception as e:
            print(f"Error al guardar lista de modelos: {e}")

if __name__ == "__main__":
    main()
