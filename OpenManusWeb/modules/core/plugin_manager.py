"""
Sistema de gestión de plugins para agent-isa.
Permite el descubrimiento, carga y gestión de plugins modulares.
"""

import importlib
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Callable

# Configurar logging
logger = logging.getLogger(__name__)

class PluginInterface:
    """Interfaz base que deben implementar todos los plugins."""
    
    @classmethod
    def get_name(cls) -> str:
        """Obtiene el nombre del plugin."""
        return cls.__name__
    
    @classmethod
    def get_description(cls) -> str:
        """Obtiene la descripción del plugin."""
        return cls.__doc__ or "Sin descripción disponible"
    
    @classmethod
    def get_version(cls) -> str:
        """Obtiene la versión del plugin."""
        return getattr(cls, "VERSION", "0.1.0")
    
    @classmethod
    def get_dependencies(cls) -> List[str]:
        """Obtiene las dependencias del plugin."""
        return getattr(cls, "DEPENDENCIES", [])

class PluginManager:
    """
    Gestiona el descubrimiento y carga de plugins.
    
    Atributos:
        plugins: Diccionario de plugins cargados
        plugin_instances: Diccionario de instancias de plugins
        plugin_dirs: Lista de directorios donde buscar plugins
    """
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """
        Inicializa el gestor de plugins.
        
        Args:
            plugin_dirs: Lista de directorios donde buscar plugins
        """
        self.plugins: Dict[str, Type[PluginInterface]] = {}
        self.plugin_instances: Dict[str, PluginInterface] = {}
        
        # Configurar directorios de plugins
        self.plugin_dirs = []
        if plugin_dirs:
            self.plugin_dirs.extend(plugin_dirs)
        
        # Añadir directorio de módulos por defecto
        modules_dir = Path(__file__).parent.parent
        self.plugin_dirs.append(str(modules_dir))
        
        logger.info(f"PluginManager inicializado con directorios: {self.plugin_dirs}")
    
    def discover_plugins(self) -> Dict[str, Type[PluginInterface]]:
        """
        Descubre plugins disponibles en los directorios configurados.
        
        Returns:
            Diccionario de plugins descubiertos
        """
        discovered_plugins = {}
        
        for plugin_dir in self.plugin_dirs:
            logger.info(f"Buscando plugins en: {plugin_dir}")
            
            # Asegurar que el directorio existe
            if not os.path.exists(plugin_dir) or not os.path.isdir(plugin_dir):
                logger.warning(f"Directorio de plugins no encontrado: {plugin_dir}")
                continue
            
            # Añadir al path si no está ya
            if plugin_dir not in sys.path:
                sys.path.append(plugin_dir)
            
            # Buscar módulos en el directorio
            for item in os.listdir(plugin_dir):
                module_path = os.path.join(plugin_dir, item)
                
                # Verificar si es un directorio con __init__.py (módulo)
                if os.path.isdir(module_path) and os.path.exists(os.path.join(module_path, "__init__.py")):
                    module_name = item
                    self._scan_module(module_name, discovered_plugins)
        
        # Actualizar plugins conocidos
        self.plugins.update(discovered_plugins)
        logger.info(f"Plugins descubiertos: {list(discovered_plugins.keys())}")
        
        return discovered_plugins
    
    def _scan_module(self, module_name: str, discovered_plugins: Dict[str, Type[PluginInterface]]) -> None:
        """
        Escanea un módulo en busca de plugins.
        
        Args:
            module_name: Nombre del módulo a escanear
            discovered_plugins: Diccionario donde almacenar los plugins descubiertos
        """
        try:
            # Importar el módulo
            module = importlib.import_module(module_name)
            
            # Buscar clases que implementen PluginInterface
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, PluginInterface) and 
                    obj is not PluginInterface):
                    
                    plugin_name = obj.get_name()
                    logger.info(f"Plugin encontrado: {plugin_name} en {module_name}")
                    discovered_plugins[plugin_name] = obj
            
            # Buscar en submódulos
            if hasattr(module, "__path__"):
                for _, submodule_name, is_pkg in importlib.util.find_spec(module_name).submodule_search_locations:
                    if is_pkg:
                        full_submodule_name = f"{module_name}.{submodule_name}"
                        self._scan_module(full_submodule_name, discovered_plugins)
                        
        except Exception as e:
            logger.error(f"Error al escanear módulo {module_name}: {e}")
    
    def load_plugin(self, plugin_name: str, **kwargs) -> Optional[PluginInterface]:
        """
        Carga un plugin específico.
        
        Args:
            plugin_name: Nombre del plugin a cargar
            **kwargs: Argumentos para inicializar el plugin
            
        Returns:
            Instancia del plugin cargado o None si falla
        """
        if plugin_name not in self.plugins:
            logger.error(f"Plugin no encontrado: {plugin_name}")
            return None
        
        try:
            # Verificar dependencias
            plugin_class = self.plugins[plugin_name]
            dependencies = plugin_class.get_dependencies()
            
            for dep in dependencies:
                if dep not in self.plugin_instances:
                    logger.info(f"Cargando dependencia: {dep} para {plugin_name}")
                    self.load_plugin(dep)
            
            # Instanciar el plugin
            plugin_instance = plugin_class(**kwargs)
            self.plugin_instances[plugin_name] = plugin_instance
            
            logger.info(f"Plugin cargado: {plugin_name}")
            return plugin_instance
            
        except Exception as e:
            logger.error(f"Error al cargar plugin {plugin_name}: {e}")
            return None
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        Obtiene una instancia de un plugin.
        
        Args:
            plugin_name: Nombre del plugin
            
        Returns:
            Instancia del plugin o None si no está cargado
        """
        return self.plugin_instances.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, PluginInterface]:
        """
        Obtiene todas las instancias de plugins cargados.
        
        Returns:
            Diccionario de instancias de plugins
        """
        return self.plugin_instances
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Descarga un plugin.
        
        Args:
            plugin_name: Nombre del plugin a descargar
            
        Returns:
            True si se descargó correctamente, False en caso contrario
        """
        if plugin_name not in self.plugin_instances:
            logger.warning(f"Plugin no cargado: {plugin_name}")
            return False
        
        try:
            # Verificar si otros plugins dependen de este
            for name, plugin_class in self.plugins.items():
                if name != plugin_name and plugin_name in plugin_class.get_dependencies():
                    logger.warning(f"No se puede descargar {plugin_name}, {name} depende de él")
                    return False
            
            # Descargar el plugin
            del self.plugin_instances[plugin_name]
            logger.info(f"Plugin descargado: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error al descargar plugin {plugin_name}: {e}")
            return False
