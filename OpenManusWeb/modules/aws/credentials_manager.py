"""
Gestor de credenciales de AWS para agent-isa.
Proporciona funcionalidades para manejar credenciales de AWS de manera segura.
"""

import os
import logging
import boto3
import json
from typing import Dict, Any, Optional

from ..core import PluginInterface, ConfigManager, EnvironmentManager

# Configurar logging
logger = logging.getLogger(__name__)

class CredentialsManager(PluginInterface):
    """
    Gestor de credenciales de AWS.

    Características:
    1. Carga segura de credenciales desde variables de entorno
    2. Validación de credenciales
    3. Gestión de modelos de Bedrock
    """

    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager", "core.EnvironmentManager"]

    def __init__(self, config_manager: Optional[ConfigManager] = None, env_manager: Optional[EnvironmentManager] = None):
        """
        Inicializa el gestor de credenciales.

        Args:
            config_manager: Gestor de configuración
            env_manager: Gestor de entornos
        """
        self.config_manager = config_manager or ConfigManager()
        self.env_manager = env_manager or EnvironmentManager()

        # Cargar configuración
        self.config = self.config_manager.get_config("aws")
        self.env_config = self.env_manager.get_config()

        # Credenciales
        self.access_key = os.environ.get("AWS_ACCESS_KEY_ID")
        self.secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.region = os.environ.get("AWS_REGION", "us-east-1")

        # Modelos de Bedrock
        self.model_nova_pro = os.environ.get("BEDROCK_MODEL_NOVA_PRO", "amazon.nova-pro")
        self.model_nova_lite = os.environ.get("BEDROCK_MODEL_NOVA_LITE", "amazon.nova-lite")
        self.model_titan_embeddings = os.environ.get("BEDROCK_MODEL_TITAN_EMBEDDINGS", "amazon.titan-embed-image-v1")
        self.model_claude = os.environ.get("BEDROCK_MODEL_CLAUDE", "anthropic.claude-3-sonnet-20240229-v1")

        # Clientes
        self.sts_client = None
        self.bedrock_client = None
        self.bedrock_management_client = None

        logger.info("Gestor de credenciales inicializado")

    def has_credentials(self) -> bool:
        """
        Verifica si hay credenciales configuradas.

        Returns:
            True si hay credenciales
        """
        return bool(self.access_key and self.secret_key)

    def initialize_clients(self) -> bool:
        """
        Inicializa los clientes de AWS.

        Returns:
            True si se inicializaron correctamente
        """
        try:
            # Determinar si usar perfil de instancia
            use_instance_profile = self.env_config.get("aws", {}).get("use_instance_profile", False)

            # Crear cliente STS
            if use_instance_profile:
                # Usar perfil de instancia EC2
                self.sts_client = boto3.client("sts", region_name=self.region)
            elif self.has_credentials():
                # Usar credenciales configuradas
                self.sts_client = boto3.client(
                    "sts",
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key
                )
            else:
                logger.warning("No hay credenciales configuradas")
                return False

            # Crear cliente Bedrock Runtime (para invocar modelos)
            if use_instance_profile:
                # Usar perfil de instancia EC2
                self.bedrock_client = boto3.client("bedrock-runtime", region_name=self.region)
            elif self.has_credentials():
                # Usar credenciales configuradas
                self.bedrock_client = boto3.client(
                    "bedrock-runtime",
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key
                )

            # Crear cliente Bedrock Management (para listar modelos)
            if use_instance_profile:
                # Usar perfil de instancia EC2
                self.bedrock_management_client = boto3.client("bedrock", region_name=self.region)
            elif self.has_credentials():
                # Usar credenciales configuradas
                self.bedrock_management_client = boto3.client(
                    "bedrock",
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key
                )

            logger.info("Clientes AWS inicializados")
            return True

        except Exception as e:
            logger.error(f"Error al inicializar clientes AWS: {e}")
            return False

    def validate_credentials(self) -> bool:
        """
        Valida las credenciales de AWS.

        Returns:
            True si las credenciales son válidas
        """
        try:
            # Inicializar cliente si es necesario
            if not self.sts_client:
                if not self.initialize_clients():
                    return False

            # Verificar identidad
            response = self.sts_client.get_caller_identity()

            # Verificar respuesta
            if "Account" in response:
                logger.info(f"Credenciales válidas para cuenta: {response['Account']}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error al validar credenciales: {e}")
            return False

    def validate_bedrock_access(self) -> Dict[str, bool]:
        """
        Valida el acceso a los modelos de Bedrock.

        Returns:
            Diccionario con resultados por modelo
        """
        results = {}

        try:
            # Inicializar cliente si es necesario
            if not self.bedrock_management_client:
                if not self.initialize_clients():
                    return {"error": "No se pudo inicializar el cliente de Bedrock"}

            # Leer variables de entorno actualizadas
            nova_pro = os.environ.get("BEDROCK_MODEL_NOVA_PRO", self.model_nova_pro)
            nova_lite = os.environ.get("BEDROCK_MODEL_NOVA_LITE", self.model_nova_lite)
            titan_embeddings = os.environ.get("BEDROCK_MODEL_TITAN_EMBEDDINGS", self.model_titan_embeddings)
            claude = os.environ.get("BEDROCK_MODEL_CLAUDE", self.model_claude)

            # Verificar acceso a los modelos
            models = [
                ("nova_pro", nova_pro),
                ("nova_lite", nova_lite),
                ("titan_embeddings", titan_embeddings),
                ("claude", claude)
            ]

            logger.info(f"Verificando acceso a modelos: {models}")

            try:
                # Listar modelos disponibles
                response = self.bedrock_management_client.list_foundation_models()
                available_models = [model["modelId"] for model in response.get("modelSummaries", [])]

                # Verificar cada modelo
                for model_key, model_id in models:
                    model_found = model_id in available_models
                    results[model_key] = model_found

                    if model_found:
                        logger.info(f"Acceso verificado para modelo: {model_id}")
                    else:
                        logger.warning(f"Modelo no encontrado: {model_id}")

            except Exception as e:
                logger.error(f"Error al listar modelos de Bedrock: {e}")
                # Intentar verificar cada modelo individualmente
                for model_key, model_id in models:
                    try:
                        # Intentar invocar el modelo con un prompt mínimo
                        self.invoke_model(model_key, "test", max_tokens=1)
                        results[model_key] = True
                        logger.info(f"Acceso verificado para modelo: {model_id}")
                    except Exception as model_e:
                        logger.error(f"Error al verificar acceso al modelo {model_id}: {model_e}")
                        results[model_key] = False

            return results

        except Exception as e:
            logger.error(f"Error al validar acceso a Bedrock: {e}")
            return {"error": str(e)}

    def get_bedrock_client(self):
        """
        Obtiene el cliente de Bedrock.

        Returns:
            Cliente de Bedrock
        """
        # Inicializar cliente si es necesario
        if not self.bedrock_client:
            self.initialize_clients()

        return self.bedrock_client

    def get_model_id(self, model_key: str) -> str:
        """
        Obtiene el ID de un modelo.

        Args:
            model_key: Clave del modelo (nova_pro, nova_lite, titan_embeddings, claude)

        Returns:
            ID del modelo
        """
        # Leer variables de entorno actualizadas
        nova_pro = os.environ.get("BEDROCK_MODEL_NOVA_PRO", self.model_nova_pro)
        nova_lite = os.environ.get("BEDROCK_MODEL_NOVA_LITE", self.model_nova_lite)
        titan_embeddings = os.environ.get("BEDROCK_MODEL_TITAN_EMBEDDINGS", self.model_titan_embeddings)
        claude = os.environ.get("BEDROCK_MODEL_CLAUDE", self.model_claude)

        model_map = {
            "nova_pro": nova_pro,
            "nova_lite": nova_lite,
            "titan_embeddings": titan_embeddings,
            "claude": claude
        }

        model_id = model_map.get(model_key, claude)
        logger.info(f"Usando modelo {model_key}: {model_id}")

        return model_id

    def invoke_model(self, model_key: str, prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Invoca un modelo de Bedrock.

        Args:
            model_key: Clave del modelo (nova_pro, nova_lite, titan_embeddings, claude)
            prompt: Prompt para el modelo
            max_tokens: Número máximo de tokens a generar

        Returns:
            Respuesta del modelo
        """
        try:
            # Obtener cliente
            client = self.get_bedrock_client()
            if not client:
                return {"error": "No se pudo obtener el cliente de Bedrock"}

            # Obtener ID del modelo
            model_id = self.get_model_id(model_key)

            # Preparar parámetros según el modelo
            if "claude" in model_id:
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
                result = {
                    "model": model_id,
                    "text": response_body.get("content", [{}])[0].get("text", ""),
                    "stop_reason": response_body.get("stop_reason", ""),
                    "usage": response_body.get("usage", {})
                }

            elif "nova-pro" in model_id or "nova-lite" in model_id:
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
                        "maxTokens": max_tokens,
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
                    text = ""
                    content_items = response_body.get("content", [])
                    for item in content_items:
                        if isinstance(item, dict) and "text" in item:
                            text += item.get("text", "")

                result = {
                    "model": model_id,
                    "text": text,
                    "stop_reason": response_body.get("stop_reason", ""),
                    "usage": response_body.get("usage", {})
                }

            elif "titan-text" in model_id:
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
                result = {
                    "model": model_id,
                    "text": response_body.get("results", [{}])[0].get("outputText", ""),
                    "completion_reason": response_body.get("completionReason", ""),
                    "amazon_bedrock_invocation_metrics": response_body.get("amazon_bedrock_invocation_metrics", {})
                }

            elif "titan-embed-image" in model_id:
                # No se puede invocar directamente con texto
                return {"error": f"El modelo {model_id} es un modelo de embeddings de imágenes y no puede ser invocado con texto"}

            else:
                return {"error": f"Formato de solicitud no definido para el modelo: {model_id}"}

            return result

        except Exception as e:
            logger.error(f"Error al invocar modelo {model_key}: {e}")
            return {"error": str(e)}
