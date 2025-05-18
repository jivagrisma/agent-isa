#!/usr/bin/env python3
"""
Script de prueba para el gestor de credenciales de AWS.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("Variables de entorno cargadas desde .env")
except ImportError:
    logger.warning("python-dotenv no está instalado, no se pueden cargar variables desde .env")

def test_credentials():
    """
    Prueba las credenciales de AWS.

    Returns:
        True si las credenciales son válidas
    """
    print("\n=== Prueba de Credenciales de AWS ===")

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
            print("Por favor, configure las variables de entorno AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY")
            return False

        # Mostrar información
        print(f"Región: {credentials_manager.region}")
        print(f"Acceso a AWS: {'✅' if credentials_manager.access_key else '❌'}")
        print(f"Clave secreta: {'✅' if credentials_manager.secret_key else '❌'}")

        # Validar credenciales
        print("\nValidando credenciales...")
        valid = credentials_manager.validate_credentials()

        if valid:
            print("✅ Credenciales válidas")
        else:
            print("❌ Credenciales inválidas")

        return valid

    except Exception as e:
        print(f"❌ Error al probar credenciales: {e}")
        return False

def test_bedrock_models():
    """
    Prueba el acceso a los modelos de Bedrock.

    Returns:
        True si se puede acceder a los modelos
    """
    print("\n=== Prueba de Acceso a Modelos de Bedrock ===")

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

        # Mostrar información de modelos
        print(f"Modelo Nova Pro: {credentials_manager.model_nova_pro}")
        print(f"Modelo Nova Lite: {credentials_manager.model_nova_lite}")
        print(f"Modelo Titan Embeddings: {credentials_manager.model_titan_embeddings}")
        print(f"Modelo Claude: {credentials_manager.model_claude}")

        # Validar acceso a modelos
        print("\nValidando acceso a modelos...")
        results = credentials_manager.validate_bedrock_access()

        if "error" in results:
            print(f"❌ Error al validar acceso: {results['error']}")
            return False

        # Mostrar resultados
        all_ok = True
        for model, access in results.items():
            print(f"Modelo {model}: {'✅' if access else '❌'}")
            if not access:
                all_ok = False

        return all_ok

    except Exception as e:
        print(f"❌ Error al probar acceso a modelos: {e}")
        return False

def test_model_invocation(model_key: str, prompt: str):
    """
    Prueba la invocación de un modelo.

    Args:
        model_key: Clave del modelo (nova_pro, nova_lite, claude)
        prompt: Prompt para el modelo

    Returns:
        True si se pudo invocar el modelo
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

        # Mostrar modelos configurados
        print(f"Modelo Nova Pro: {os.environ.get('BEDROCK_MODEL_NOVA_PRO')}")
        print(f"Modelo Nova Lite: {os.environ.get('BEDROCK_MODEL_NOVA_LITE')}")
        print(f"Modelo Titan Embeddings: {os.environ.get('BEDROCK_MODEL_TITAN_EMBEDDINGS')}")
        print(f"Modelo Claude: {os.environ.get('BEDROCK_MODEL_CLAUDE')}")

        # Invocar modelo
        print(f"Invocando modelo {model_key} con prompt: {prompt}")

        # Obtener ID del modelo directamente de las variables de entorno
        model_id = None
        if model_key == "nova_pro":
            model_id = os.environ.get("BEDROCK_MODEL_NOVA_PRO")
        elif model_key == "nova_lite":
            model_id = os.environ.get("BEDROCK_MODEL_NOVA_LITE")
        elif model_key == "claude":
            model_id = os.environ.get("BEDROCK_MODEL_CLAUDE")

        print(f"ID del modelo: {model_id}")

        # Inicializar cliente si es necesario
        if not credentials_manager.bedrock_client:
            credentials_manager.initialize_clients()

        # Preparar parámetros según el modelo
        if "claude" in model_id:
            # Formato para Claude
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        else:
            # Formato para modelos de Amazon
            request_body = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 100,
                    "stopSequences": [],
                    "temperature": 0.7,
                    "topP": 0.9
                }
            }

        # Invocar modelo directamente
        try:
            response = credentials_manager.bedrock_client.invoke_model(
                modelId=model_id,
                body=json.dumps(request_body)
            )

            # Procesar respuesta
            response_body = json.loads(response.get("body").read())

            # Extraer texto según el modelo
            if "claude" in model_id:
                # Formato de respuesta de Claude
                result = {
                    "model": model_id,
                    "text": response_body.get("content", [{}])[0].get("text", ""),
                    "stop_reason": response_body.get("stop_reason", ""),
                    "usage": response_body.get("usage", {})
                }
            else:
                # Formato de respuesta de modelos de Amazon
                result = {
                    "model": model_id,
                    "text": response_body.get("results", [{}])[0].get("outputText", ""),
                    "completion_reason": response_body.get("completionReason", ""),
                    "amazon_bedrock_invocation_metrics": response_body.get("amazon_bedrock_invocation_metrics", {})
                }
        except Exception as e:
            print(f"❌ Error al invocar modelo directamente: {e}")
            return False

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
    parser = argparse.ArgumentParser(description="Prueba de credenciales de AWS")
    parser.add_argument("--validate", action="store_true", help="Validar credenciales")
    parser.add_argument("--models", action="store_true", help="Validar acceso a modelos")
    parser.add_argument("--invoke", choices=["nova_pro", "nova_lite", "claude"], help="Invocar modelo")
    parser.add_argument("--prompt", default="Hola, ¿cómo estás?", help="Prompt para el modelo")
    args = parser.parse_args()

    # Si no se especifica ninguna opción, ejecutar todas las pruebas
    if not (args.validate or args.models or args.invoke):
        args.validate = True
        args.models = True

    # Ejecutar pruebas
    if args.validate:
        test_credentials()

    if args.models:
        test_bedrock_models()

    if args.invoke:
        test_model_invocation(args.invoke, args.prompt)

if __name__ == "__main__":
    main()
