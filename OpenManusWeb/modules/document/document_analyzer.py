"""
Módulo para análisis de documentos utilizando AWS Bedrock.
"""

import os
import json
import logging
import boto3
import base64
import hashlib
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    """
    Analizador de documentos utilizando AWS Bedrock.
    """

    def __init__(self):
        """
        Inicializa el analizador de documentos.
        """
        # Obtener credenciales de AWS
        self.aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
        self.aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")

        # Obtener IDs de modelos
        self.claude_model_id = os.environ.get("BEDROCK_MODEL_CLAUDE", "anthropic.claude-3-5-sonnet-20240620-v1:0")
        self.titan_embeddings_model_id = os.environ.get("BEDROCK_MODEL_TITAN_EMBEDDINGS", "amazon.titan-embed-image-v1")

        # Inicializar cliente de Bedrock
        self.bedrock_client = self._create_bedrock_client()

        # Inicializar caché
        self.cache = {}
        self.cache_ttl = 3600  # 1 hora en segundos
        self.cache_dir = Path(__file__).parent / "cache"
        self.cache_dir.mkdir(exist_ok=True)

        logger.info("Analizador de documentos inicializado")

    def _create_bedrock_client(self):
        """
        Crea un cliente de AWS Bedrock.

        Returns:
            Cliente de Bedrock o None si hay error
        """
        try:
            # Verificar credenciales
            if not self.aws_access_key or not self.aws_secret_key:
                logger.warning("No se encontraron credenciales de AWS")
                return None

            # Crear cliente
            client = boto3.client(
                "bedrock-runtime",
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key
            )

            return client

        except Exception as e:
            logger.error(f"Error al crear cliente de Bedrock: {e}")
            return None

    def _generate_cache_key(self, content: str, model_id: str) -> str:
        """
        Genera una clave de caché única para el contenido y modelo.

        Args:
            content: Contenido a analizar
            model_id: ID del modelo

        Returns:
            Clave de caché
        """
        # Crear hash del contenido y modelo
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        return f"{model_id}_{content_hash}"

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un resultado de la caché.

        Args:
            cache_key: Clave de caché

        Returns:
            Resultado almacenado en caché o None si no existe o ha expirado
        """
        # Verificar si existe en memoria
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            # Verificar si ha expirado
            if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                logger.info(f"Resultado obtenido de caché en memoria: {cache_key}")
                return cache_entry["result"]
            else:
                # Eliminar entrada expirada
                del self.cache[cache_key]

        # Verificar si existe en disco
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_entry = json.load(f)

                # Verificar si ha expirado
                if time.time() - cache_entry["timestamp"] < self.cache_ttl:
                    # Actualizar caché en memoria
                    self.cache[cache_key] = cache_entry
                    logger.info(f"Resultado obtenido de caché en disco: {cache_key}")
                    return cache_entry["result"]
                else:
                    # Eliminar archivo expirado
                    cache_file.unlink(missing_ok=True)
            except Exception as e:
                logger.error(f"Error al leer caché: {e}")

        return None

    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]) -> None:
        """
        Guarda un resultado en la caché.

        Args:
            cache_key: Clave de caché
            result: Resultado a guardar
        """
        # Crear entrada de caché
        cache_entry = {
            "timestamp": time.time(),
            "result": result
        }

        # Guardar en memoria
        self.cache[cache_key] = cache_entry

        # Guardar en disco
        try:
            cache_file = self.cache_dir / f"{cache_key}.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f)
            logger.info(f"Resultado guardado en caché: {cache_key}")
        except Exception as e:
            logger.error(f"Error al guardar caché: {e}")

    def analyze_text(self, text: str, prompt_template: Optional[str] = None) -> Dict[str, Any]:
        """
        Analiza un texto utilizando Claude.

        Args:
            text: Texto a analizar
            prompt_template: Plantilla de prompt opcional

        Returns:
            Resultado del análisis
        """
        if not self.bedrock_client:
            return {"error": "No se pudo crear el cliente de Bedrock"}

        # Usar plantilla por defecto si no se proporciona una
        if not prompt_template:
            prompt_template = """
            Analiza el siguiente texto y proporciona un resumen detallado.
            Incluye los puntos clave, temas principales y cualquier información relevante.

            Texto: {text}

            Análisis:
            """

        # Preparar prompt
        prompt = prompt_template.format(text=text)

        # Generar clave de caché
        cache_key = self._generate_cache_key(text, self.claude_model_id)

        # Verificar si existe en caché
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            # Preparar solicitud para Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            # Invocar modelo
            response = self.bedrock_client.invoke_model(
                modelId=self.claude_model_id,
                body=json.dumps(request_body)
            )

            # Procesar respuesta
            response_body = json.loads(response.get("body").read())

            # Extraer texto
            analysis = response_body.get("content", [{}])[0].get("text", "")

            # Crear resultado
            result = {
                "success": True,
                "analysis": analysis,
                "model": self.claude_model_id
            }

            # Guardar en caché
            self._save_to_cache(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error al analizar texto: {e}")
            return {"error": str(e)}

    def analyze_image(self, image_path: str, prompt_template: Optional[str] = None) -> Dict[str, Any]:
        """
        Analiza una imagen utilizando Claude.

        Args:
            image_path: Ruta a la imagen
            prompt_template: Plantilla de prompt opcional

        Returns:
            Resultado del análisis
        """
        if not self.bedrock_client:
            return {"error": "No se pudo crear el cliente de Bedrock"}

        # Verificar si el archivo existe
        if not os.path.exists(image_path):
            return {"error": f"No se encontró el archivo: {image_path}"}

        # Usar plantilla por defecto si no se proporciona una
        if not prompt_template:
            prompt_template = """
            Analiza esta imagen y describe detalladamente lo que ves.
            Incluye objetos, personas, escenas, colores, y cualquier texto visible.
            """

        # Generar clave de caché basada en el hash del archivo y la plantilla
        try:
            # Calcular hash del archivo
            with open(image_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            # Generar clave de caché
            template_hash = hashlib.md5(prompt_template.encode('utf-8')).hexdigest()
            cache_key = f"{self.claude_model_id}_img_{file_hash}_{template_hash}"

            # Verificar si existe en caché
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

            # Leer imagen
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode("utf-8")

            # Preparar solicitud para Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": self._get_media_type(image_path),
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt_template
                            }
                        ]
                    }
                ]
            }

            # Invocar modelo
            response = self.bedrock_client.invoke_model(
                modelId=self.claude_model_id,
                body=json.dumps(request_body)
            )

            # Procesar respuesta
            response_body = json.loads(response.get("body").read())

            # Extraer texto
            analysis = response_body.get("content", [{}])[0].get("text", "")

            # Crear resultado
            result = {
                "success": True,
                "analysis": analysis,
                "model": self.claude_model_id
            }

            # Guardar en caché
            self._save_to_cache(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error al analizar imagen: {e}")
            return {"error": str(e)}

    def _get_media_type(self, file_path: str) -> str:
        """
        Determina el tipo MIME de un archivo basado en su extensión.

        Args:
            file_path: Ruta al archivo

        Returns:
            Tipo MIME
        """
        extension = Path(file_path).suffix.lower()

        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp"
        }

        return mime_types.get(extension, "application/octet-stream")
