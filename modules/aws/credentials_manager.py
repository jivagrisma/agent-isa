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
            
            # Crear cliente Bedrock
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
            if not self.bedrock_client:
                if not self.initialize_clients():
                    return {"error": "No se pudo inicializar el cliente de Bedrock"}
            
            # Verificar acceso a los modelos
            models = [
                ("nova_pro", self.model_nova_pro),
                ("nova_lite", self.model_nova_lite),
                ("titan_embeddings", self.model_titan_embeddings),
                ("claude", self.model_claude)
            ]
            
            for model_key, model_id in models:
                try:
                    # Intentar listar modelos para verificar acceso
                    response = self.bedrock_client.list_foundation_models()
                    
                    # Verificar si el modelo está en la lista
                    model_found = any(model["modelId"] == model_id for model in response.get("modelSummaries", []))
                    
                    results[model_key] = model_found
                    
                    if model_found:
                        logger.info(f"Acceso verificado para modelo: {model_id}")
                    else:
                        logger.warning(f"Modelo no encontrado: {model_id}")
                
                except Exception as e:
                    logger.error(f"Error al verificar acceso al modelo {model_id}: {e}")
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
        model_map = {
            "nova_pro": self.model_nova_pro,
            "nova_lite": self.model_nova_lite,
            "titan_embeddings": self.model_titan_embeddings,
            "claude": self.model_claude
        }
        
        return model_map.get(model_key, self.model_claude)
    
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
            else:
                # Formato para modelos de Amazon
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
            
            # Extraer texto según el modelo
            if "claude" in model_id:
                # Formato de respuesta de Claude
                result = {
                    "model": model_id,
                    "text": response_body.get("content", [{}])[0].get("text", ""),
                    "stop_reason": response_body.get("stop_reason", ""),
                    "usage": response_body.get("usage", {})
                }
            else:
                # Formato de respuesta de modelos de Amazon
                result = {
                    "model": model_id,
                    "text": response_body.get("results", [{}])[0].get("outputText", ""),
                    "completion_reason": response_body.get("completionReason", ""),
                    "amazon_bedrock_invocation_metrics": response_body.get("amazon_bedrock_invocation_metrics", {})
                }
            
            return result
            
        except Exception as e:
            logger.error(f"Error al invocar modelo {model_key}: {e}")
            return {"error": str(e)}
