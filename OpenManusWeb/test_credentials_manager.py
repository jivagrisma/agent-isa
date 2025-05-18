#!/usr/bin/env python3
"""
Script para probar el gestor de credenciales de AWS.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv(override=True)
logger.info("Variables de entorno cargadas desde .env")

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_invoke_model(model_key, prompt):
    """
    Prueba la invocación de un modelo usando el gestor de credenciales.
    
    Args:
        model_key: Clave del modelo (nova_pro, nova_lite, claude)
        prompt: Prompt para el modelo
    """
    print(f"\n=== Prueba de Invocación de Modelo {model_key} ===")
    
    try:
        from modules.core import ConfigManager, EnvironmentManager
        from modules.aws import CredentialsManager
        
        # Crear instancias
        config_manager = ConfigManager()
        env_manager = EnvironmentManager()
        credentials_manager = CredentialsManager(config_manager, env_manager)
        
        # Verificar si hay credenciales
        if not credentials_manager.has_credentials():
            print("❌ No hay credenciales configuradas")
            return False
        
        # Mostrar información
        model_id = credentials_manager.get_model_id(model_key)
        print(f"Modelo: {model_key}")
        print(f"ID del modelo: {model_id}")
        print(f"Prompt: {prompt}")
        
        # Invocar modelo
        print("\nInvocando modelo...")
        result = credentials_manager.invoke_model(model_key, prompt, max_tokens=500)
        
        # Verificar resultado
        if "error" in result:
            print(f"❌ Error al invocar modelo: {result['error']}")
            return False
        
        # Mostrar respuesta
        print("\nRespuesta:")
        print(result["text"])
        
        return True
        
    except Exception as e:
        print(f"❌ Error al invocar modelo: {e}")
        return False

def main():
    """
    Función principal.
    """
    # Obtener modelo y prompt de los argumentos
    model_key = "claude"
    prompt = "Describe brevemente qué es AWS Bedrock en 2-3 oraciones."
    
    if len(sys.argv) > 1:
        model_key = sys.argv[1]
    
    if len(sys.argv) > 2:
        prompt = sys.argv[2]
    
    # Probar invocación de modelo
    test_invoke_model(model_key, prompt)

if __name__ == "__main__":
    main()
