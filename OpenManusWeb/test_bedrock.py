#!/usr/bin/env python3
"""
Script para probar la comunicación con AWS Bedrock directamente.
"""

import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos necesarios
from app.llm import LLM
from app.config import config

async def test_bedrock():
    """
    Prueba la comunicación con AWS Bedrock.
    """
    try:
        # Inicializar el cliente LLM
        logger.info("Inicializando cliente LLM...")
        llm = LLM(config_name="default")

        # Verificar que el cliente se ha inicializado correctamente
        if not hasattr(llm, "client"):
            logger.error("El cliente LLM no se ha inicializado correctamente")
            return False

        # Verificar que el cliente es de tipo bedrock
        if llm.api_type != "bedrock":
            logger.error(f"El cliente LLM no es de tipo bedrock, es de tipo {llm.api_type}")
            return False

        # Verificar que el modelo es correcto
        logger.info(f"Modelo: {llm.model_id}")
        logger.info(f"Tipo de modelo: {'Claude' if llm.is_claude else 'Nova' if llm.is_nova else 'Desconocido'}")

        # Crear un mensaje simple
        messages = [
            {"role": "user", "content": "Hola, ¿cómo estás? Responde en español."}
        ]

        # Enviar el mensaje a AWS Bedrock
        logger.info("Enviando mensaje a AWS Bedrock...")
        try:
            response = await llm.ask_bedrock(
                messages=messages,
                stream=False,
                temperature=0.7
            )

            logger.info(f"Respuesta recibida: {response[:100]}...")
            return True
        except Exception as e:
            logger.error(f"Error al enviar mensaje a AWS Bedrock: {e}")
            return False

    except Exception as e:
        logger.error(f"Error al inicializar cliente LLM: {e}")
        return False

async def test_bedrock_with_timeout():
    """
    Prueba la comunicación con AWS Bedrock con un timeout explícito.
    """
    try:
        # Inicializar el cliente LLM
        logger.info("Inicializando cliente LLM...")
        llm = LLM(config_name="default")

        # Crear un mensaje simple
        messages = [
            {"role": "user", "content": "Hola, ¿cómo estás? Responde en español."}
        ]

        # Enviar el mensaje a AWS Bedrock con timeout
        logger.info("Enviando mensaje a AWS Bedrock con timeout...")
        try:
            response = await asyncio.wait_for(
                llm.ask_bedrock(
                    messages=messages,
                    stream=False,
                    temperature=0.7
                ),
                timeout=30  # 30 segundos de timeout
            )

            logger.info(f"Respuesta recibida: {response[:100]}...")
            return True
        except asyncio.TimeoutError:
            logger.error("La solicitud a AWS Bedrock excedió el tiempo límite (30 segundos)")
            return False
        except Exception as e:
            logger.error(f"Error al enviar mensaje a AWS Bedrock: {e}")
            return False

    except Exception as e:
        logger.error(f"Error al inicializar cliente LLM: {e}")
        return False

async def test_bedrock_direct():
    """
    Prueba la comunicación con AWS Bedrock directamente usando boto3.
    """
    try:
        import boto3
        from botocore.config import Config

        # Obtener configuración
        region = config.llm["default"].region
        aws_access_key_id = config.llm["default"].aws_access_key_id
        aws_secret_access_key = config.llm["default"].aws_secret_access_key
        model_id = config.llm["default"].model_id

        logger.info(f"Región: {region}")
        logger.info(f"Modelo: {model_id}")

        # Configuración para cliente de AWS
        aws_config = Config(
            region_name=region,
            signature_version="v4",
            retries={
                "max_attempts": 10,
                "mode": "adaptive"
            },
            connect_timeout=10,
            read_timeout=30
        )

        # Crear cliente de bedrock runtime
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region
        )

        client = session.client(
            service_name="bedrock-runtime",
            config=aws_config
        )

        # Crear payload según el tipo de modelo
        if "anthropic" in model_id:
            # Claude
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.7,
                "messages": [
                    {"role": "user", "content": "Hola, ¿cómo estás? Responde en español."}
                ]
            }
        elif "amazon.nova" in model_id:
            # Nova Pro - Usar el formato exacto que usa la clase LLM
            formatted_messages = [
                {
                    "role": "user",
                    "content": [{"text": "Hola, ¿cómo estás? Responde en español."}]
                }
            ]

            payload = {
                "messages": formatted_messages
            }

            logger.info(f"Payload para Nova: {payload}")
        else:
            logger.error(f"Modelo no soportado: {model_id}")
            return False

        # Convertir a JSON y UTF-8
        body = json.dumps(payload).encode("utf-8")

        # Realizar la solicitud a la API Bedrock
        logger.info("Enviando solicitud directa a AWS Bedrock...")
        response = client.invoke_model(
            modelId=model_id,
            body=body
        )

        # Procesar la respuesta
        response_body = json.loads(response["body"].read().decode("utf-8"))
        logger.info(f"Respuesta recibida: {response_body}")

        return True

    except Exception as e:
        logger.error(f"Error al comunicar directamente con AWS Bedrock: {e}")
        return False

if __name__ == "__main__":
    # Ejecutar las pruebas
    logger.info("Iniciando pruebas de comunicación con AWS Bedrock...")

    # Ejecutar prueba básica
    result1 = asyncio.run(test_bedrock())
    logger.info(f"Prueba básica: {'ÉXITO' if result1 else 'FALLO'}")

    # Ejecutar prueba con timeout
    result2 = asyncio.run(test_bedrock_with_timeout())
    logger.info(f"Prueba con timeout: {'ÉXITO' if result2 else 'FALLO'}")

    # Ejecutar prueba directa
    result3 = asyncio.run(test_bedrock_direct())
    logger.info(f"Prueba directa: {'ÉXITO' if result3 else 'FALLO'}")

    # Resultado final
    if result1 and result2 and result3:
        logger.info("Todas las pruebas fueron exitosas")
    else:
        logger.error("Algunas pruebas fallaron")
