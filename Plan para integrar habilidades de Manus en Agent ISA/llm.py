from typing import Dict, List, Literal, Optional, Union, AsyncGenerator
import json

from openai import (
    APIError,
    AsyncAzureOpenAI,
    AsyncOpenAI,
    AuthenticationError,
    OpenAIError,
    RateLimitError,
)
from tenacity import retry, stop_after_attempt, wait_random_exponential

from app.config import LLMSettings, config
from app.logger import logger  # Assuming a logger is set up in your app
from app.schema import Message


class LLM:
    _instances: Dict[str, "LLM"] = {}

    def __new__(
        cls, config_name: str = "default", llm_config: Optional[LLMSettings] = None
    ):
        if config_name not in cls._instances:
            instance = super().__new__(cls)
            instance.__init__(config_name, llm_config)
            cls._instances[config_name] = instance
        return cls._instances[config_name]

    def __init__(
        self, config_name: str = "default", llm_config: Optional[LLMSettings] = None
    ):
        if not hasattr(self, "client"):  # Only initialize if not already initialized
            # Guardar el nombre de la configuración para uso posterior
            self.config_name = config_name

            llm_config = llm_config or config.llm
            llm_config = llm_config.get(config_name, llm_config["default"])
            self.model = llm_config.model
            self.max_tokens = llm_config.max_tokens
            self.temperature = llm_config.temperature
            self.api_type = llm_config.api_type
            self.api_key = llm_config.api_key
            self.api_version = llm_config.api_version
            self.base_url = llm_config.base_url

            # Contador de intentos de reconexión para Bedrock
            self.bedrock_reconnect_attempts = 0
            self.max_bedrock_reconnect_attempts = 5

            if self.api_type == "azure":
                self.client = AsyncAzureOpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    api_version=self.api_version,
                )
            elif self.api_type == "bedrock":
                # Si es Bedrock, almacenar información específica
                if self.api_type == "bedrock":
                    self.region = llm_config.region
                    self.aws_access_key_id = llm_config.aws_access_key_id
                    self.aws_secret_access_key = llm_config.aws_secret_access_key
                    self.model_id = llm_config.model_id

                    # Determinar el tipo de modelo
                    self.is_claude = "anthropic" in self.model_id
                    self.is_nova = "amazon.nova" in self.model_id

                # Inicializar el cliente
                self._initialize_bedrock_client()
            else:
                self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    def _initialize_bedrock_client(self):
        """
        Inicializa el cliente de AWS Bedrock con manejo de errores mejorado.
        """
        try:
            import boto3
            from botocore.config import Config
            import botocore.exceptions

            # Verificar que tenemos todos los atributos necesarios
            required_attrs = ["region", "aws_access_key_id", "aws_secret_access_key", "model_id"]
            missing_attrs = [attr for attr in required_attrs if not hasattr(self, attr)]

            if missing_attrs:
                logger.error(f"Faltan atributos necesarios para inicializar el cliente AWS Bedrock: {missing_attrs}")
                raise ValueError(f"Faltan atributos necesarios para inicializar el cliente AWS Bedrock: {missing_attrs}")

            # Verificar que el tipo de modelo está determinado
            if not hasattr(self, "is_claude") or not hasattr(self, "is_nova"):
                # Determinar el tipo de modelo
                self.is_claude = "anthropic" in self.model_id
                self.is_nova = "amazon.nova" in self.model_id

            # Configuración para cliente de AWS con timeouts y retries mejorados
            aws_config = Config(
                region_name=self.region,
                signature_version="v4",
                retries={
                    "max_attempts": 15,  # Aumentado para mayor robustez
                    "mode": "adaptive"
                },
                connect_timeout=10,  # Timeout de conexión en segundos
                read_timeout=30,     # Timeout de lectura en segundos
                max_pool_connections=50  # Aumentar el número de conexiones en el pool
            )

            # Crear cliente de bedrock runtime
            session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region
            )

            # Intentar crear el cliente con manejo de errores
            try:
                self.client = session.client(
                    service_name="bedrock-runtime",
                    config=aws_config
                )

                # No podemos verificar el cliente con list_foundation_models() porque
                # esa operación no está disponible en bedrock-runtime, solo en bedrock
                # En su lugar, simplemente registramos que el cliente se ha inicializado

                logger.info(f"Inicializado cliente AWS Bedrock para modelo {self.model_id}")
                # Resetear contador de intentos si la inicialización fue exitosa
                self.bedrock_reconnect_attempts = 0

            except botocore.exceptions.ClientError as e:
                logger.error(f"Error de cliente AWS Bedrock: {e}")
                if "ExpiredToken" in str(e) or "InvalidSignatureException" in str(e):
                    logger.error("Credenciales de AWS expiradas o inválidas")
                raise

            except botocore.exceptions.EndpointConnectionError as e:
                logger.error(f"Error de conexión al endpoint de AWS Bedrock: {e}")
                raise

        except ImportError:
            logger.error("No se pudo importar boto3. Instale boto3 con 'pip install boto3'")
            raise
        except Exception as e:
            logger.error(f"Error al inicializar cliente AWS Bedrock: {e}")
            raise

    def _reconnect_bedrock_client(self):
        """
        Intenta reconectar el cliente de AWS Bedrock en caso de error.

        Returns:
            bool: True si la reconexión fue exitosa, False en caso contrario
        """
        if self.bedrock_reconnect_attempts >= self.max_bedrock_reconnect_attempts:
            logger.error(f"Se alcanzó el número máximo de intentos de reconexión ({self.max_bedrock_reconnect_attempts})")
            return False

        logger.info(f"Intentando reconectar cliente AWS Bedrock (intento {self.bedrock_reconnect_attempts + 1}/{self.max_bedrock_reconnect_attempts})")
        self.bedrock_reconnect_attempts += 1

        try:
            # Esperar un tiempo exponencial antes de reconectar
            import time
            wait_time = 2 ** self.bedrock_reconnect_attempts
            logger.info(f"Esperando {wait_time} segundos antes de reconectar...")
            time.sleep(wait_time)

            # Reinicializar el cliente
            self._initialize_bedrock_client()
            return True
        except Exception as e:
            logger.error(f"Error al reconectar cliente AWS Bedrock: {e}")
            return False

    @staticmethod
    def format_messages(messages: List[Union[dict, Message]]) -> List[dict]:
        """
        Format messages for LLM by converting them to OpenAI message format.

        Args:
            messages: List of messages that can be either dict or Message objects

        Returns:
            List[dict]: List of formatted messages in OpenAI format

        Raises:
            ValueError: If messages are invalid or missing required fields
            TypeError: If unsupported message types are provided

        Examples:
            >>> msgs = [
            ...     Message.system_message("You are a helpful assistant"),
            ...     {"role": "user", "content": "Hello"},
            ...     Message.user_message("How are you?")
            ... ]
            >>> formatted = LLM.format_messages(msgs)
        """
        formatted_messages = []

        for message in messages:
            if isinstance(message, dict):
                # If message is already a dict, ensure it has required fields
                if "role" not in message:
                    raise ValueError("Message dict must contain 'role' field")
                formatted_messages.append(message)
            elif isinstance(message, Message):
                # If message is a Message object, convert it to dict
                formatted_messages.append(message.to_dict())
            else:
                raise TypeError(f"Unsupported message type: {type(message)}")

        # Validate all messages have required fields
        for msg in formatted_messages:
            if msg["role"] not in ["system", "user", "assistant", "tool"]:
                raise ValueError(f"Invalid role: {msg['role']}")
            if "content" not in msg and "tool_calls" not in msg:
                raise ValueError(
                    "Message must contain either 'content' or 'tool_calls'"
                )

        return formatted_messages

    def _format_claude_messages(self, messages: List[dict], temperature: Optional[float] = None) -> dict:
        """
        Formatea mensajes para el modelo Claude de Anthropic en AWS Bedrock.

        Args:
            messages: Lista de mensajes formateados
            temperature: Temperatura opcional

        Returns:
            dict: Payload formateado para Claude
        """
        # Configuración básica para Claude
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": self.max_tokens,
            "temperature": temperature or self.temperature,
            "messages": []
        }

        # Asegurarse de que haya al menos un mensaje de usuario
        has_user_message = any(msg["role"] == "user" for msg in messages)
        if not has_user_message:
            # Si no hay mensajes de usuario, añadir uno por defecto
            payload["messages"].append({
                "role": "user",
                "content": "Hola, necesito tu ayuda."
            })

        # Convertir mensajes al formato de Claude
        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")

            # Mapear roles de OpenAI a Claude
            if role == "system":
                # En Claude 3, los mensajes del sistema son mensajes del usuario con un prefijo especial
                payload["messages"].append({
                    "role": "user",
                    "content": content
                })
            elif role == "user":
                payload["messages"].append({
                    "role": "user",
                    "content": content
                })
            elif role == "assistant":
                payload["messages"].append({
                    "role": "assistant",
                    "content": content
                })
            # Claude no tiene un equivalente directo para "tool", se omite

        # Asegurarse de que el primer mensaje sea de usuario
        if payload["messages"] and payload["messages"][0]["role"] != "user":
            # Insertar un mensaje de usuario al principio
            payload["messages"].insert(0, {
                "role": "user",
                "content": "Hola, necesito tu ayuda."
            })

        return payload

    def _format_nova_messages(self, messages: List[dict], temperature: Optional[float] = None) -> dict:
        """
        Formatea mensajes para los modelos Amazon Nova en AWS Bedrock.

        Args:
            messages: Lista de mensajes formateados
            temperature: Temperatura opcional

        Returns:
            dict: Payload formateado para Nova
        """
        # Asegurarse de que haya al menos un mensaje de usuario
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        if not user_messages:
            # Si no hay mensajes de usuario, añadir uno por defecto
            messages.append({
                "role": "user",
                "content": "Hola, necesito tu ayuda."
            })

        # Convertir todos los mensajes al formato de Nova
        formatted_messages = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            formatted_messages.append({
                "role": role,
                "content": [{"text": msg["content"]}]
            })

        # Asegurarse de que el primer mensaje sea de usuario
        if formatted_messages and formatted_messages[0]["role"] != "user":
            # Insertar un mensaje de usuario al principio
            formatted_messages.insert(0, {
                "role": "user",
                "content": [{"text": "Hola, necesito tu ayuda."}]
            })

        # Configuración para Nova
        payload = {
            "messages": formatted_messages
        }

        return payload

    @retry(
        wait=wait_random_exponential(min=1, max=60),
        stop=stop_after_attempt(6),
    )
    async def ask_bedrock(
        self,
        messages: List[dict],
        stream: bool = True,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Envía un prompt a AWS Bedrock y obtiene la respuesta.

        Args:
            messages: Lista de mensajes de conversación
            stream: Si debe transmitir la respuesta
            temperature: Temperatura de muestreo para la respuesta

        Returns:
            str: La respuesta generada
        """
        # Importar aquí para evitar problemas de importación circular
        import botocore.exceptions

        # Número máximo de intentos para esta solicitud específica
        max_request_attempts = 3
        current_attempt = 0

        while current_attempt < max_request_attempts:
            current_attempt += 1

            try:
                # Formatear mensajes según el modelo (Claude vs Nova)
                if self.is_claude:
                    formatted_input = self._format_claude_messages(messages, temperature)
                elif self.is_nova:
                    formatted_input = self._format_nova_messages(messages, temperature)
                else:
                    raise ValueError(f"Modelo no soportado: {self.model_id}")

                # Convertir a JSON y UTF-8
                body = json.dumps(formatted_input).encode("utf-8")

                # Imprimir el payload para depuración
                logger.debug(f"Payload enviado a AWS Bedrock: {formatted_input}")

                # Realizar la solicitud a la API Bedrock con timeout explícito
                if stream:
                    try:
                        # Importar timeout para solicitudes
                        import socket

                        # Guardar el timeout original
                        original_timeout = socket.getdefaulttimeout()

                        # Establecer un timeout más estricto para esta solicitud
                        socket.setdefaulttimeout(15)  # 15 segundos de timeout

                        try:
                            response = self.client.invoke_model_with_response_stream(
                                modelId=self.model_id,
                                body=body
                            )
                        finally:
                            # Restaurar el timeout original
                            socket.setdefaulttimeout(original_timeout)

                        # Procesar streaming para Claude y Nova
                        collected_messages = []
                        for event in response.get("body"):
                            if "chunk" in event:
 
(Content truncated due to size limit. Use line ranges to read in chunks)