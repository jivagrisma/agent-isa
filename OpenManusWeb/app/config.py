import threading
import tomllib
import os
from pathlib import Path
from typing import Dict

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"


class LLMSettings(BaseModel):
    model: str = Field(..., description="Model name")
    base_url: str = Field(..., description="API base URL")
    api_key: str = Field(..., description="API key")
    max_tokens: int = Field(4096, description="Maximum number of tokens per request")
    temperature: float = Field(1.0, description="Sampling temperature")
    api_type: str = Field(..., description="API type: openai, azure, or bedrock")
    api_version: str = Field("", description="Azure OpenAI version if api_type is azure")

    # AWS Bedrock specific fields
    region: str = Field("", description="AWS region for Bedrock")
    aws_access_key_id: str = Field("", description="AWS access key ID for Bedrock")
    aws_secret_access_key: str = Field("", description="AWS secret access key for Bedrock")
    model_id: str = Field("", description="Model ID for Bedrock (e.g., anthropic.claude-3-7-sonnet-20250219-v1:0)")


class AppConfig(BaseModel):
    llm: Dict[str, LLMSettings]


class Config:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._config = None
                    self._load_initial_config()
                    self._initialized = True

    @staticmethod
    def _get_config_path() -> Path:
        root = PROJECT_ROOT
        config_path = root / "config" / "config.toml"
        if config_path.exists():
            return config_path
        example_path = root / "config" / "config.example.toml"
        if example_path.exists():
            return example_path
        raise FileNotFoundError("No configuration file found in config directory")

    def _load_config(self) -> dict:
        config_path = self._get_config_path()
        with config_path.open("rb") as f:
            return tomllib.load(f)

    def _load_initial_config(self):
        raw_config = self._load_config()
        base_llm = raw_config.get("llm", {})
        llm_overrides = {
            k: v for k, v in raw_config.get("llm", {}).items() if isinstance(v, dict)
        }

        # Cargar credenciales de AWS desde variables de entorno
        aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID", "")
        aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        aws_region = os.environ.get("AWS_REGION", "us-east-1")

        # Cargar IDs de modelos desde variables de entorno
        model_id_map = {
            "default": os.environ.get("BEDROCK_MODEL_NOVA_PRO", "amazon.nova-pro-v1:0"),
            "nova_pro": os.environ.get("BEDROCK_MODEL_NOVA_PRO", "amazon.nova-pro-v1:0"),
            "nova_lite": os.environ.get("BEDROCK_MODEL_NOVA_LITE", "amazon.nova-lite-v1:0"),
            "claude": os.environ.get("BEDROCK_MODEL_CLAUDE", "anthropic.claude-3-5-sonnet-20240620-v1:0")
        }

        default_settings = {
            "model": base_llm.get("model"),
            "base_url": base_llm.get("base_url"),
            "api_key": base_llm.get("api_key"),
            "max_tokens": base_llm.get("max_tokens", 4096),
            "temperature": base_llm.get("temperature", 1.0),
            "api_type": base_llm.get("api_type", ""),
            "api_version": base_llm.get("api_version", ""),
            # AWS Bedrock specific fields
            "region": aws_region or base_llm.get("region", ""),
            "aws_access_key_id": aws_access_key_id or base_llm.get("aws_access_key_id", ""),
            "aws_secret_access_key": aws_secret_access_key or base_llm.get("aws_secret_access_key", ""),
            "model_id": base_llm.get("model_id", ""),
        }

        # Crear configuración para cada modelo con sus IDs específicos
        llm_configs = {}

        # Configuración por defecto
        llm_configs["default"] = default_settings

        # Configuraciones específicas para cada modelo
        for name, override_config in llm_overrides.items():
            # Combinar configuración por defecto con la específica
            model_config = {**default_settings, **override_config}

            # Actualizar model_id desde variables de entorno si está disponible
            if name in model_id_map:
                model_config["model_id"] = model_id_map[name]

            llm_configs[name] = model_config

        config_dict = {
            "llm": llm_configs
        }

        self._config = AppConfig(**config_dict)

    @property
    def llm(self) -> Dict[str, LLMSettings]:
        return self._config.llm


config = Config()
