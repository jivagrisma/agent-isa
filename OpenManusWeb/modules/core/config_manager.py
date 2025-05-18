"""
Sistema de configuración modular para agent-isa.
Permite cargar y gestionar configuraciones por módulos.
"""

import json
import logging
import os
import tomli
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Configurar logging
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Gestor de configuración modular.
    
    Permite cargar configuraciones desde diferentes fuentes y formatos,
    organizadas por módulos.
    
    Atributos:
        config: Diccionario con la configuración cargada
        config_dirs: Lista de directorios donde buscar configuraciones
    """
    
    def __init__(self, config_dirs: Optional[List[str]] = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            config_dirs: Lista de directorios donde buscar configuraciones
        """
        self.config: Dict[str, Any] = {}
        
        # Configurar directorios de configuración
        self.config_dirs = []
        if config_dirs:
            self.config_dirs.extend(config_dirs)
        
        # Añadir directorio de configuración por defecto
        default_config_dir = Path(__file__).parent.parent.parent / "config"
        self.config_dirs.append(str(default_config_dir))
        
        logger.info(f"ConfigManager inicializado con directorios: {self.config_dirs}")
    
    def load_config(self, module_name: str = None) -> Dict[str, Any]:
        """
        Carga la configuración para un módulo específico o todos los módulos.
        
        Args:
            module_name: Nombre del módulo (None para cargar todos)
            
        Returns:
            Diccionario con la configuración cargada
        """
        if module_name:
            # Cargar configuración para un módulo específico
            module_config = self._load_module_config(module_name)
            self.config[module_name] = module_config
            return module_config
        else:
            # Cargar configuración para todos los módulos
            for config_dir in self.config_dirs:
                self._load_all_configs(config_dir)
            
            return self.config
    
    def _load_module_config(self, module_name: str) -> Dict[str, Any]:
        """
        Carga la configuración para un módulo específico.
        
        Args:
            module_name: Nombre del módulo
            
        Returns:
            Diccionario con la configuración del módulo
        """
        module_config = {}
        
        for config_dir in self.config_dirs:
            # Buscar archivos de configuración para el módulo
            module_dir = os.path.join(config_dir, module_name)
            if os.path.exists(module_dir) and os.path.isdir(module_dir):
                # Cargar configuraciones del directorio del módulo
                for filename in os.listdir(module_dir):
                    file_path = os.path.join(module_dir, filename)
                    if os.path.isfile(file_path):
                        config_data = self._load_config_file(file_path)
                        if config_data:
                            # Usar el nombre del archivo (sin extensión) como clave
                            key = os.path.splitext(filename)[0]
                            module_config[key] = config_data
            
            # Buscar archivo específico del módulo en el directorio principal
            for ext in ['.toml', '.yaml', '.yml', '.json']:
                file_path = os.path.join(config_dir, f"{module_name}{ext}")
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    config_data = self._load_config_file(file_path)
                    if config_data:
                        # Fusionar con la configuración existente
                        module_config.update(config_data)
        
        logger.info(f"Configuración cargada para módulo: {module_name}")
        return module_config
    
    def _load_all_configs(self, config_dir: str) -> None:
        """
        Carga todas las configuraciones de un directorio.
        
        Args:
            config_dir: Directorio de configuración
        """
        if not os.path.exists(config_dir) or not os.path.isdir(config_dir):
            logger.warning(f"Directorio de configuración no encontrado: {config_dir}")
            return
        
        # Cargar archivos de configuración del directorio principal
        for filename in os.listdir(config_dir):
            file_path = os.path.join(config_dir, filename)
            
            if os.path.isfile(file_path):
                # Cargar archivo de configuración
                config_data = self._load_config_file(file_path)
                if config_data:
                    # Usar el nombre del archivo (sin extensión) como clave de módulo
                    module_name = os.path.splitext(filename)[0]
                    self.config[module_name] = config_data
            
            elif os.path.isdir(file_path) and not filename.startswith('_'):
                # Directorio de módulo
                module_name = filename
                module_config = self._load_module_config(module_name)
                if module_config:
                    self.config[module_name] = module_config
    
    def _load_config_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Carga un archivo de configuración.
        
        Args:
            file_path: Ruta al archivo de configuración
            
        Returns:
            Diccionario con la configuración cargada o None si falla
        """
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            with open(file_path, 'rb' if ext == '.toml' else 'r') as f:
                if ext == '.toml':
                    return tomli.load(f)
                elif ext in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                elif ext == '.json':
                    return json.load(f)
                else:
                    logger.warning(f"Formato de configuración no soportado: {file_path}")
                    return None
                
        except Exception as e:
            logger.error(f"Error al cargar configuración {file_path}: {e}")
            return None
    
    def get_config(self, module_name: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Obtiene la configuración de un módulo.
        
        Args:
            module_name: Nombre del módulo
            key: Clave específica dentro de la configuración del módulo
            default: Valor por defecto si no se encuentra
            
        Returns:
            Configuración del módulo o valor por defecto
        """
        if module_name not in self.config:
            # Intentar cargar la configuración si no está cargada
            self._load_module_config(module_name)
        
        module_config = self.config.get(module_name, {})
        
        if key is None:
            return module_config
        
        # Soporte para claves anidadas con notación de punto
        if '.' in key:
            parts = key.split('.')
            value = module_config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        return module_config.get(key, default)
    
    def set_config(self, module_name: str, key: str, value: Any) -> None:
        """
        Establece un valor de configuración.
        
        Args:
            module_name: Nombre del módulo
            key: Clave de configuración
            value: Valor a establecer
        """
        if module_name not in self.config:
            self.config[module_name] = {}
        
        # Soporte para claves anidadas con notación de punto
        if '.' in key:
            parts = key.split('.')
            config = self.config[module_name]
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            config[parts[-1]] = value
        else:
            self.config[module_name][key] = value
    
    def save_config(self, module_name: str, file_path: Optional[str] = None) -> bool:
        """
        Guarda la configuración de un módulo en un archivo.
        
        Args:
            module_name: Nombre del módulo
            file_path: Ruta del archivo (None para usar la ruta por defecto)
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        if module_name not in self.config:
            logger.warning(f"No hay configuración para el módulo: {module_name}")
            return False
        
        try:
            # Determinar ruta del archivo
            if file_path is None:
                file_path = os.path.join(self.config_dirs[0], f"{module_name}.toml")
            
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Guardar según el formato
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, 'w') as f:
                if ext in ['.yaml', '.yml']:
                    yaml.dump(self.config[module_name], f)
                elif ext == '.json':
                    json.dump(self.config[module_name], f, indent=2)
                else:
                    # Por defecto usar JSON
                    json.dump(self.config[module_name], f, indent=2)
            
            logger.info(f"Configuración guardada para módulo {module_name} en {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error al guardar configuración {module_name}: {e}")
            return False
