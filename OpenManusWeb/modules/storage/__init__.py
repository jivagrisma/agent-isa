"""
Módulo de Almacenamiento para agent-isa.
Proporciona capacidades de gestión de archivos y almacenamiento de datos.
"""

from .virtual_fs import VirtualFileSystem
from .structured_storage import StructuredStorage
from .cache_manager import CacheManager

__all__ = ['VirtualFileSystem', 'StructuredStorage', 'CacheManager']
