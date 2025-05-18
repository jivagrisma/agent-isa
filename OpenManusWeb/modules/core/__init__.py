"""
Módulo Core para agent-isa.
Proporciona funcionalidades básicas y servicios compartidos.
"""

from .plugin_manager import PluginManager, PluginInterface
from .config_manager import ConfigManager
from .extended_llm import ExtendedLLMClient
from .environment import EnvironmentManager

__all__ = ['PluginManager', 'PluginInterface', 'ConfigManager', 'ExtendedLLMClient', 'EnvironmentManager']
