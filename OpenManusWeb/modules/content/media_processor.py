"""
Procesador de contenido multimedia para agent-isa.
Proporciona capacidades de análisis y procesamiento de imágenes y texto.
"""

import logging
import os
import json
import base64
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, BinaryIO
import boto3
import requests
from PIL import Image
import io
import re

from ..core import PluginInterface, ConfigManager

# Configurar logging
logger = logging.getLogger(__name__)

class MediaProcessor(PluginInterface):
    """
    Procesador de contenido multimedia con capacidades de análisis y conversión.

    Características:
    1. Análisis de imágenes
    2. Extracción de texto de imágenes (OCR)
    3. Conversión entre formatos de contenido
    """

    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager"]

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Inicializa el procesador de contenido multimedia.

        Args:
            config_manager: Gestor de configuración
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("content")

        # Inicializar clientes
        self.bedrock_client = None
        self.nova_client = None

        logger.info("Procesador de contenido multimedia inicializado")

    def initialize_aws_clients(self):
        """
        Inicializa los clientes de AWS.
        """
        try:
            # Inicializar cliente de Bedrock
            region = self.config.get("aws.region", "us-east-1")

            # Crear cliente de Bedrock
            self.bedrock_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=region
            )

            # Inicializar cliente de Nova
            # Nova Pro y Nova Lite para OCR y análisis de imágenes
            # Nova Canvas y Nova Reel para generación y manipulación de imágenes/video
            self.nova_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=region
            )

            logger.info("Clientes AWS inicializados")
            return True

        except Exception as e:
            logger.error(f"Error al inicializar clientes AWS: {e}")
            return False

    def extract_text_from_image(
        self,
        image_data: Union[bytes, str, Path]
    ) -> Dict[str, Any]:
        """
        Extrae texto de una imagen utilizando OCR.

        Args:
            image_data: Datos de la imagen (bytes, ruta o base64)

        Returns:
            Diccionario con el texto extraído
        """
        # Verificar cliente de Nova
        if not self.nova_client:
            success = self.initialize_aws_clients()
            if not success:
                return {"error": "No se pudo inicializar el cliente de Nova para OCR"}

        try:
            # Preparar imagen
            if isinstance(image_data, (str, Path)) and os.path.exists(image_data):
                # Cargar desde archivo
                with open(image_data, "rb") as f:
                    bytes_data = f.read()
            elif isinstance(image_data, bytes):
                # Usar bytes directamente
                bytes_data = image_data
            elif isinstance(image_data, str) and image_data.startswith("data:image"):
                # Extraer datos de data URL
                image_data = image_data.split(",")[1]
                bytes_data = base64.b64decode(image_data)
            elif isinstance(image_data, str):
                # Intentar decodificar base64
                bytes_data = base64.b64decode(image_data)
            else:
                return {"error": "Formato de imagen no soportado"}

            # Invocar Nova Pro/Lite para OCR
            request_body = {
                "modelId": "amazon.nova-pro",
                "contentType": "image/jpeg",
                "accept": "application/json",
                "task": "OCR",
                "parameters": {
                    "detail": "high",
                    "language": "auto"
                }
            }

            # Codificar imagen en base64
            image_b64 = base64.b64encode(bytes_data).decode("utf-8")
            request_body["imageData"] = image_b64

            # Invocar modelo
            response = self.nova_client.invoke_model(
                modelId="amazon.nova-pro",
                body=json.dumps(request_body)
            )

            # Procesar respuesta
            response_body = json.loads(response.get("body").read())

            # Extraer texto
            lines = []
            words = []

            if "textDetections" in response_body:
                for detection in response_body["textDetections"]:
                    if detection["type"] == "LINE":
                        lines.append(detection["text"])
                    elif detection["type"] == "WORD":
                        words.append(detection["text"])

            # Construir texto completo
            full_text = "\n".join(lines)

            # Calcular confianza promedio
            confidence = 0
            if "textDetections" in response_body and response_body["textDetections"]:
                confidence = sum(detection.get("confidence", 0) for detection in response_body["textDetections"]) / len(response_body["textDetections"])

            # Construir resultado
            result = {
                "success": True,
                "text": full_text,
                "lines": lines,
                "words": words,
                "confidence": confidence,
                "timestamp": time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error al extraer texto de imagen: {e}")
            return {"error": str(e)}

    def analyze_image_content(
        self,
        image_data: Union[bytes, str, Path],
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analiza el contenido de una imagen.

        Args:
            image_data: Datos de la imagen (bytes, ruta o base64)
            features: Características a analizar (labels, faces, text, etc.)

        Returns:
            Diccionario con el análisis de la imagen
        """
        # Verificar cliente de Nova
        if not self.nova_client:
            success = self.initialize_aws_clients()
            if not success:
                return {"error": "No se pudo inicializar el cliente de Nova para análisis de imágenes"}

        # Determinar características a analizar
        if not features:
            features = ["labels", "text"]

        try:
            # Preparar imagen
            if isinstance(image_data, (str, Path)) and os.path.exists(image_data):
                # Cargar desde archivo
                with open(image_data, "rb") as f:
                    bytes_data = f.read()
            elif isinstance(image_data, bytes):
                # Usar bytes directamente
                bytes_data = image_data
            elif isinstance(image_data, str) and image_data.startswith("data:image"):
                # Extraer datos de data URL
                image_data = image_data.split(",")[1]
                bytes_data = base64.b64decode(image_data)
            elif isinstance(image_data, str):
                # Intentar decodificar base64
                bytes_data = base64.b64decode(image_data)
            else:
                return {"error": "Formato de imagen no soportado"}

            # Inicializar resultado
            result = {
                "success": True,
                "timestamp": time.time()
            }

            # Codificar imagen en base64
            image_b64 = base64.b64encode(bytes_data).decode("utf-8")

            # Analizar imagen con Nova Pro/Lite
            request_body = {
                "modelId": "amazon.nova-pro",
                "contentType": "image/jpeg",
                "accept": "application/json",
                "task": "IMAGE_ANALYSIS",
                "parameters": {
                    "detail": "high"
                },
                "imageData": image_b64
            }

            # Invocar modelo
            response = self.nova_client.invoke_model(
                modelId="amazon.nova-pro",
                body=json.dumps(request_body)
            )

            # Procesar respuesta
            response_body = json.loads(response.get("body").read())

            # Analizar etiquetas
            if "labels" in features and "labels" in response_body:
                result["labels"] = [
                    {
                        "name": label["name"],
                        "confidence": label["confidence"],
                        "parents": label.get("parents", [])
                    }
                    for label in response_body["labels"]
                ]

            # Analizar texto
            if "text" in features and "textDetections" in response_body:
                result["text_detections"] = [
                    {
                        "text": detection["text"],
                        "type": detection["type"],
                        "confidence": detection["confidence"]
                    }
                    for detection in response_body["textDetections"]
                ]

            # Analizar rostros
            if "faces" in features and "faceDetails" in response_body:
                result["faces"] = [
                    {
                        "age_range": face.get("ageRange"),
                        "gender": face.get("gender", {}).get("value"),
                        "emotions": [
                            {
                                "type": emotion["type"],
                                "confidence": emotion["confidence"]
                            }
                            for emotion in face.get("emotions", [])
                        ],
                        "confidence": face.get("confidence", 0)
                    }
                    for face in response_body["faceDetails"]
                ]

            # Analizar contenido moderado
            if "moderation" in features and "moderationLabels" in response_body:
                result["moderation_labels"] = [
                    {
                        "name": label["name"],
                        "confidence": label["confidence"],
                        "parent": label.get("parent")
                    }
                    for label in response_body["moderationLabels"]
                ]

            return result

        except Exception as e:
            logger.error(f"Error al analizar imagen: {e}")
            return {"error": str(e)}

    def describe_image(
        self,
        image_data: Union[bytes, str, Path],
        max_tokens: int = 100
    ) -> Dict[str, Any]:
        """
        Genera una descripción textual de una imagen utilizando un modelo multimodal.

        Args:
            image_data: Datos de la imagen (bytes, ruta o base64)
            max_tokens: Número máximo de tokens para la descripción

        Returns:
            Diccionario con la descripción de la imagen
        """
        # Verificar cliente de Bedrock
        if not self.bedrock_client:
            success = self.initialize_aws_clients()
            if not success:
                return {"error": "No se pudo inicializar el cliente de AWS Bedrock"}

        try:
            # Preparar imagen
            if isinstance(image_data, (str, Path)) and os.path.exists(image_data):
                # Cargar desde archivo
                with open(image_data, "rb") as f:
                    bytes_data = f.read()
            elif isinstance(image_data, bytes):
                # Usar bytes directamente
                bytes_data = image_data
            elif isinstance(image_data, str) and image_data.startswith("data:image"):
                # Extraer datos de data URL
                image_data = image_data.split(",")[1]
                bytes_data = base64.b64decode(image_data)
            elif isinstance(image_data, str):
                # Intentar decodificar base64
                bytes_data = base64.b64decode(image_data)
            else:
                return {"error": "Formato de imagen no soportado"}

            # Convertir imagen a base64
            image_b64 = base64.b64encode(bytes_data).decode("utf-8")

            # Construir prompt
            prompt = "Describe detalladamente lo que ves en esta imagen."

            # Construir mensaje para Claude
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_b64
                            }
                        }
                    ]
                }
            ]

            # Configurar parámetros
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages
            }

            # Invocar modelo
            response = self.bedrock_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1",
                body=json.dumps(request_body)
            )

            # Procesar respuesta
            response_body = json.loads(response.get("body").read())

            description = response_body.get("content", [{}])[0].get("text", "")

            # Construir resultado
            result = {
                "success": True,
                "description": description,
                "model": "anthropic.claude-3-sonnet-20240229-v1",
                "timestamp": time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error al describir imagen: {e}")
            return {"error": str(e)}

    def convert_image_format(
        self,
        image_data: Union[bytes, str, Path],
        target_format: str,
        quality: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Convierte una imagen a otro formato.

        Args:
            image_data: Datos de la imagen (bytes, ruta o base64)
            target_format: Formato de destino (png, jpeg, webp, etc.)
            quality: Calidad de la imagen (0-100, solo para formatos con compresión)

        Returns:
            Diccionario con la imagen convertida
        """
        try:
            # Cargar imagen
            if isinstance(image_data, (str, Path)) and os.path.exists(image_data):
                # Cargar desde archivo
                img = Image.open(image_data)
            elif isinstance(image_data, bytes):
                # Cargar desde bytes
                img = Image.open(io.BytesIO(image_data))
            elif isinstance(image_data, str) and image_data.startswith("data:image"):
                # Cargar desde data URL
                image_data = image_data.split(",")[1]
                img = Image.open(io.BytesIO(base64.b64decode(image_data)))
            elif isinstance(image_data, str):
                # Intentar decodificar base64
                img = Image.open(io.BytesIO(base64.b64decode(image_data)))
            else:
                return {"error": "Formato de imagen no soportado"}

            # Normalizar formato
            target_format = target_format.upper()

            # Convertir imagen
            buffer = io.BytesIO()

            # Configurar parámetros de guardado
            save_params = {}

            # Añadir calidad si se especifica y el formato lo soporta
            if quality is not None and target_format in ["JPEG", "WEBP"]:
                save_params["quality"] = quality

            # Guardar en formato especificado
            img.save(buffer, format=target_format, **save_params)

            # Obtener datos convertidos
            converted_data = buffer.getvalue()

            # Construir resultado
            result = {
                "success": True,
                "format": target_format.lower(),
                "width": img.width,
                "height": img.height,
                "size_bytes": len(converted_data),
                "image_data": base64.b64encode(converted_data).decode("utf-8"),
                "timestamp": time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Error al convertir imagen: {e}")
            return {"error": str(e)}
