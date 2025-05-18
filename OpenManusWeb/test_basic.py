#!/usr/bin/env python3
"""
Script de prueba básica para verificar la funcionalidad de los módulos.
"""

import os
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_core_modules():
    """Prueba los módulos core."""
    print("\n=== Prueba de Módulos Core ===")
    
    try:
        from modules.core import ConfigManager
        
        # Crear instancia
        config_manager = ConfigManager()
        
        # Obtener configuración
        config = config_manager.get_config("search")
        
        print("✅ ConfigManager funciona correctamente")
        print(f"Configuración cargada: {config.keys()}")
        
        return True
    except Exception as e:
        print(f"❌ Error en módulos core: {e}")
        return False

def test_environment_manager():
    """Prueba el gestor de entornos."""
    print("\n=== Prueba de Environment Manager ===")
    
    try:
        from modules.core import EnvironmentManager
        
        # Crear instancia
        env_manager = EnvironmentManager()
        
        # Obtener entorno actual
        env_name = env_manager.get_env_name()
        
        # Cargar configuración
        config = env_manager.load_config()
        
        print(f"✅ EnvironmentManager funciona correctamente")
        print(f"Entorno actual: {env_name}")
        print(f"Configuración cargada: {list(config.keys()) if config else 'Ninguna'}")
        
        return True
    except Exception as e:
        print(f"❌ Error en EnvironmentManager: {e}")
        return False

def test_storage_modules():
    """Prueba los módulos de almacenamiento."""
    print("\n=== Prueba de Módulos de Almacenamiento ===")
    
    try:
        # Importar módulos
        from modules.core import ConfigManager
        from modules.storage import VirtualFileSystem
        
        # Crear instancias
        config_manager = ConfigManager()
        fs = VirtualFileSystem(config_manager)
        
        # Crear directorio de prueba
        test_dir = "test_storage"
        os.makedirs(os.path.join("storage", test_dir), exist_ok=True)
        
        # Escribir archivo
        test_content = "Este es un archivo de prueba."
        fs.write_file(f"{test_dir}/test.txt", test_content)
        
        # Leer archivo
        read_content = fs.read_file(f"{test_dir}/test.txt")
        
        # Verificar contenido
        if read_content == test_content:
            print("✅ VirtualFileSystem funciona correctamente")
            print(f"Contenido leído: {read_content}")
        else:
            print("❌ Error en VirtualFileSystem: contenido no coincide")
            print(f"Esperado: {test_content}")
            print(f"Obtenido: {read_content}")
        
        # Eliminar archivo
        fs.delete_file(f"{test_dir}/test.txt")
        
        return True
    except Exception as e:
        print(f"❌ Error en módulos de almacenamiento: {e}")
        return False

def test_aws_modules():
    """Prueba los módulos de AWS."""
    print("\n=== Prueba de Módulos AWS ===")
    
    try:
        # Importar módulos
        from modules.core import ConfigManager, EnvironmentManager
        from modules.aws import S3Manager, CloudWatchManager
        
        # Crear instancias
        config_manager = ConfigManager()
        env_manager = EnvironmentManager()
        
        # Crear gestor de S3
        s3_manager = S3Manager(config_manager, env_manager)
        
        # Crear gestor de CloudWatch
        cloudwatch_manager = CloudWatchManager(config_manager, env_manager)
        
        print("✅ Módulos AWS inicializados correctamente")
        print(f"S3 Manager: {s3_manager}")
        print(f"CloudWatch Manager: {cloudwatch_manager}")
        
        return True
    except Exception as e:
        print(f"❌ Error en módulos AWS: {e}")
        return False

def main():
    """Función principal."""
    print("=== Pruebas Básicas de Agent-ISA ===")
    
    # Ejecutar pruebas
    core_ok = test_core_modules()
    env_ok = test_environment_manager()
    storage_ok = test_storage_modules()
    aws_ok = test_aws_modules()
    
    # Mostrar resumen
    print("\n=== Resumen de Pruebas ===")
    print(f"Módulos Core: {'✅' if core_ok else '❌'}")
    print(f"Environment Manager: {'✅' if env_ok else '❌'}")
    print(f"Módulos de Almacenamiento: {'✅' if storage_ok else '❌'}")
    print(f"Módulos AWS: {'✅' if aws_ok else '❌'}")
    
    # Determinar resultado
    if core_ok and env_ok and storage_ok and aws_ok:
        print("\n✅ Todas las pruebas pasaron exitosamente")
        return 0
    else:
        print("\n❌ Algunas pruebas fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main())
