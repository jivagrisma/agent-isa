"""
Gestor de entornos para agent-isa.
Proporciona funcionalidades para cargar configuraciones según el entorno.
"""

import os
import logging
import toml
from pathlib import Path
from typing import Dict, Any, Optional

# Configurar logging
logger = logging.getLogger(__name__)

class EnvironmentManager:
    """
    Gestor de entornos para cargar configuraciones específicas.
    
    Características:
    1. Carga de configuración según entorno (desarrollo, producción, etc.)
    2. Sustitución de variables de entorno en la configuración
    3. Validación de configuración
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Inicializa el gestor de entornos.
        
        Args:
            base_dir: Directorio base del proyecto
        """
        # Determinar directorio base
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Usar directorio actual o determinar automáticamente
            self.base_dir = Path(__file__).parent.parent.parent
        
        # Directorio de configuraciones de entorno
        self.env_config_dir = self.base_dir / "config" / "environments"
        
        # Entorno actual
        self.current_env = os.environ.get("AGENT_ISA_ENV", "development")
        
        # Configuración cargada
        self.config = {}
        
        logger.info(f"Gestor de entornos inicializado (entorno: {self.current_env})")
    
    def load_config(self, env: Optional[str] = None) -> Dict[str, Any]:
        """
        Carga la configuración para un entorno específico.
        
        Args:
            env: Nombre del entorno (None para usar el actual)
            
        Returns:
            Configuración cargada
        """
        # Determinar entorno
        env_name = env or self.current_env
        
        # Ruta del archivo de configuración
        config_file = self.env_config_dir / f"{env_name}.toml"
        
        if not config_file.exists():
            logger.warning(f"Archivo de configuración no encontrado: {config_file}")
            logger.warning(f"Usando configuración de desarrollo por defecto")
            config_file = self.env_config_dir / "development.toml"
            
            if not config_file.exists():
                logger.error(f"Archivo de configuración de desarrollo no encontrado")
                raise FileNotFoundError(f"No se encontró ningún archivo de configuración válido")
        
        # Cargar configuración
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = toml.load(f)
            
            # Procesar variables de entorno
            config = self._process_env_vars(config)
            
            # Guardar configuración
            self.config = config
            
            logger.info(f"Configuración cargada para entorno: {env_name}")
            return config
            
        except Exception as e:
            logger.error(f"Error al cargar configuración: {e}")
            raise
    
    def _process_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa variables de entorno en la configuración.
        
        Args:
            config: Configuración a procesar
            
        Returns:
            Configuración procesada
        """
        # Función recursiva para procesar diccionarios anidados
        def process_dict(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    process_dict(value)
                elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    # Extraer nombre de variable
                    env_var = value[2:-1]
                    
                    # Obtener valor de variable de entorno
                    env_value = os.environ.get(env_var)
                    
                    if env_value is not None:
                        d[key] = env_value
                    else:
                        logger.warning(f"Variable de entorno no encontrada: {env_var}")
        
        # Crear copia para no modificar el original
        result = config.copy()
        
        # Procesar variables
        process_dict(result)
        
        return result
    
    def get_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración actual.
        
        Returns:
            Configuración actual
        """
        if not self.config:
            return self.load_config()
        
        return self.config
    
    def is_production(self) -> bool:
        """
        Verifica si el entorno actual es producción.
        
        Returns:
            True si es producción
        """
        return self.current_env == "production"
    
    def is_development(self) -> bool:
        """
        Verifica si el entorno actual es desarrollo.
        
        Returns:
            True si es desarrollo
        """
        return self.current_env == "development"
    
    def get_env_name(self) -> str:
        """
        Obtiene el nombre del entorno actual.
        
        Returns:
            Nombre del entorno
        """
        return self.current_env
