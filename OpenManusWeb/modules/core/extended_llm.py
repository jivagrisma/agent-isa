"""
Cliente LLM extendido para agent-isa.
Proporciona soporte para múltiples modelos y optimización de prompts.
"""

import logging
import json
import os
import time
from typing import Dict, List, Any, Optional, Union, Literal
import asyncio
from tenacity import retry, wait_random_exponential, stop_after_attempt

from ..core import PluginInterface, ConfigManager

# Configurar logging
logger = logging.getLogger(__name__)

class ExtendedLLMClient(PluginInterface):
    """
    Cliente LLM extendido con soporte para múltiples modelos.
    
    Características:
    1. Soporte para modelos adicionales
    2. Fallback automático entre modelos
    3. Optimización de prompts
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Inicializa el cliente LLM extendido.
        
        Args:
            config_manager: Gestor de configuración
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("core")
        
        # Inicializar clientes
        self.clients = {}
        self.default_client = None
        
        # Cargar configuración de modelos
        self.models_config = self.config.get("llm", {})
        self.default_model = self.models_config.get("model_id", "anthropic.claude-3-sonnet-20240229-v1:0")
        
        logger.info(f"Cliente LLM extendido inicializado con modelo por defecto: {self.default_model}")
    
    async def initialize(self):
        """
        Inicializa los clientes LLM.
        """
        # Importar módulos necesarios
        try:
            # Importar el cliente LLM original
            from OpenManusWeb.app.llm import LLM
            
            # Crear cliente por defecto
            default_config_name = "default"
            self.default_client = LLM(config_name=default_config_name)
            self.clients[default_config_name] = self.default_client
            
            logger.info("Cliente LLM por defecto inicializado")
            
            # Inicializar clientes adicionales si están configurados
            # Esto se implementará en futuras versiones
            
            return True
            
        except ImportError as e:
            logger.error(f"Error al importar módulos LLM: {e}")
            return False
        except Exception as e:
            logger.error(f"Error al inicializar clientes LLM: {e}")
            return False
    
    async def ask(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_msgs: Optional[List[Dict[str, str]]] = None,
        fallback: bool = True
    ) -> str:
        """
        Envía un prompt al LLM y obtiene la respuesta.
        
        Args:
            messages: Lista de mensajes de conversación
            model: ID del modelo a utilizar (None para usar el predeterminado)
            stream: Si debe transmitir la respuesta
            temperature: Temperatura de muestreo para la respuesta
            max_tokens: Número máximo de tokens en la respuesta
            system_msgs: Mensajes de sistema opcionales
            fallback: Si debe intentar con modelos alternativos en caso de error
            
        Returns:
            str: La respuesta generada
        """
        # Inicializar clientes si no están inicializados
        if not self.default_client:
            success = await self.initialize()
            if not success:
                return "Error al inicializar el cliente LLM"
        
        # Determinar modelo a utilizar
        model_id = model or self.default_model
        
        # Optimizar prompts según el modelo
        optimized_messages = self._optimize_prompts(messages, model_id)
        optimized_system_msgs = self._optimize_prompts(system_msgs, model_id) if system_msgs else None
        
        try:
            # Intentar con el modelo solicitado
            logger.info(f"Enviando solicitud a modelo: {model_id}")
            
            # Usar el cliente por defecto
            response = await self.default_client.ask(
                messages=optimized_messages,
                system_msgs=optimized_system_msgs,
                stream=stream,
                temperature=temperature
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error al usar modelo {model_id}: {e}")
            
            if fallback and model_id != self.default_model:
                # Intentar con el modelo por defecto como fallback
                logger.info(f"Intentando con modelo por defecto: {self.default_model}")
                try:
                    response = await self.default_client.ask(
                        messages=messages,
                        system_msgs=system_msgs,
                        stream=stream,
                        temperature=temperature
                    )
                    return response
                except Exception as fallback_error:
                    logger.error(f"Error en fallback: {fallback_error}")
            
            # Si no hay fallback o también falló, devolver mensaje de error
            return f"Lo siento, ocurrió un error al procesar tu solicitud: {str(e)}"
    
    async def ask_tool(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        temperature: Optional[float] = None,
        system_msgs: Optional[List[Dict[str, str]]] = None,
        fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Envía un prompt al LLM con herramientas y obtiene la respuesta.
        
        Args:
            messages: Lista de mensajes de conversación
            tools: Lista de herramientas disponibles
            model: ID del modelo a utilizar (None para usar el predeterminado)
            tool_choice: Estrategia de selección de herramientas
            temperature: Temperatura de muestreo para la respuesta
            system_msgs: Mensajes de sistema opcionales
            fallback: Si debe intentar con modelos alternativos en caso de error
            
        Returns:
            Dict[str, Any]: La respuesta generada con información de herramientas
        """
        # Inicializar clientes si no están inicializados
        if not self.default_client:
            success = await self.initialize()
            if not success:
                return {"response": "Error al inicializar el cliente LLM", "tool_calls": []}
        
        # Determinar modelo a utilizar
        model_id = model or self.default_model
        
        # Optimizar prompts según el modelo
        optimized_messages = self._optimize_prompts(messages, model_id)
        optimized_system_msgs = self._optimize_prompts(system_msgs, model_id) if system_msgs else None
        
        try:
            # Intentar con el modelo solicitado
            logger.info(f"Enviando solicitud con herramientas a modelo: {model_id}")
            
            # Usar el cliente por defecto
            response = await self.default_client.ask_tool(
                messages=optimized_messages,
                system_msgs=optimized_system_msgs,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error al usar modelo {model_id} con herramientas: {e}")
            
            if fallback and model_id != self.default_model:
                # Intentar con el modelo por defecto como fallback
                logger.info(f"Intentando con modelo por defecto: {self.default_model}")
                try:
                    response = await self.default_client.ask_tool(
                        messages=messages,
                        system_msgs=system_msgs,
                        tools=tools,
                        tool_choice=tool_choice,
                        temperature=temperature
                    )
                    return response
                except Exception as fallback_error:
                    logger.error(f"Error en fallback: {fallback_error}")
            
            # Si no hay fallback o también falló, devolver mensaje de error
            return {
                "response": f"Lo siento, ocurrió un error al procesar tu solicitud: {str(e)}",
                "tool_calls": []
            }
    
    def _optimize_prompts(self, messages: Optional[List[Dict[str, str]]], model_id: str) -> List[Dict[str, str]]:
        """
        Optimiza los prompts según el modelo.
        
        Args:
            messages: Lista de mensajes a optimizar
            model_id: ID del modelo
            
        Returns:
            Lista de mensajes optimizados
        """
        if not messages:
            return []
        
        # Clonar mensajes para no modificar los originales
        optimized = messages.copy()
        
        # Aplicar optimizaciones específicas según el modelo
        if "claude" in model_id.lower():
            # Optimizaciones para Claude
            for msg in optimized:
                # Asegurar que el contenido no tenga instrucciones de otros modelos
                content = msg.get("content", "")
                if isinstance(content, str):
                    # Eliminar marcadores específicos de otros modelos
                    content = content.replace("<|im_start|>", "").replace("<|im_end|>", "")
                    msg["content"] = content
        
        elif "nova" in model_id.lower():
            # Optimizaciones para Nova
            # No se requieren optimizaciones específicas por ahora
            pass
        
        return optimized
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Obtiene la lista de modelos disponibles.
        
        Returns:
            Lista de modelos disponibles con sus metadatos
        """
        # En una implementación futura, esto podría consultar la API de AWS Bedrock
        # para obtener la lista de modelos disponibles
        
        # Por ahora, devolver una lista estática
        return [
            {
                "id": "anthropic.claude-3-sonnet-20240229-v1:0",
                "name": "Claude 3.7 Sonnet",
                "provider": "Anthropic",
                "capabilities": ["chat", "tools", "vision"],
                "max_tokens": 4096
            },
            {
                "id": "amazon.nova-lite-v1",
                "name": "Amazon Nova Lite",
                "provider": "Amazon",
                "capabilities": ["chat"],
                "max_tokens": 4096
            },
            {
                "id": "amazon.nova-pro-v1",
                "name": "Amazon Nova Pro",
                "provider": "Amazon",
                "capabilities": ["chat", "tools"],
                "max_tokens": 4096
            }
        ]
