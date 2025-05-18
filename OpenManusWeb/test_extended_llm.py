#!/usr/bin/env python3
"""
Script de prueba para el cliente LLM extendido.
"""

import argparse
import asyncio
import logging
import sys
import json
from typing import List, Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar módulos locales
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos necesarios
from modules.core import ConfigManager, ExtendedLLMClient

async def test_ask(prompt: str, model: str = None, temperature: float = 0.7):
    """
    Prueba la funcionalidad de generación de texto.
    
    Args:
        prompt: Prompt para el LLM
        model: Modelo a utilizar (None para usar el predeterminado)
        temperature: Temperatura de muestreo
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar cliente LLM extendido
        llm_client = ExtendedLLMClient(config_manager)
        
        # Crear mensaje
        messages = [{"role": "user", "content": prompt}]
        
        # Enviar solicitud
        print(f"\n🤖 Enviando prompt al modelo {model or 'predeterminado'}...\n")
        response = await llm_client.ask(
            messages=messages,
            model=model,
            temperature=temperature
        )
        
        # Mostrar respuesta
        print(f"✅ Respuesta recibida:\n")
        print(f"{response}\n")
        
        return response
    
    except Exception as e:
        logger.error(f"Error en generación de texto: {e}")
        print(f"❌ Error: {e}")
        return str(e)

async def test_ask_tool(prompt: str, model: str = None, temperature: float = 0.7):
    """
    Prueba la funcionalidad de herramientas.
    
    Args:
        prompt: Prompt para el LLM
        model: Modelo a utilizar (None para usar el predeterminado)
        temperature: Temperatura de muestreo
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar cliente LLM extendido
        llm_client = ExtendedLLMClient(config_manager)
        
        # Definir herramientas
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Obtiene el clima actual para una ubicación",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "La ciudad y país, por ejemplo: 'Madrid, España'"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "Unidad de temperatura"
                            }
                        },
                        "required": ["location"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Busca información en la web",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "La consulta de búsqueda"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Número de resultados a devolver"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        # Crear mensaje
        messages = [{"role": "user", "content": prompt}]
        
        # Enviar solicitud
        print(f"\n🤖 Enviando prompt con herramientas al modelo {model or 'predeterminado'}...\n")
        response = await llm_client.ask_tool(
            messages=messages,
            tools=tools,
            model=model,
            temperature=temperature
        )
        
        # Mostrar respuesta
        print(f"✅ Respuesta recibida:\n")
        
        # Verificar si hay llamadas a herramientas
        if "tool_calls" in response and response["tool_calls"]:
            print("Llamadas a herramientas detectadas:")
            for tool_call in response["tool_calls"]:
                function_name = tool_call.get("function", {}).get("name", "")
                function_args = tool_call.get("function", {}).get("arguments", "{}")
                
                try:
                    args_dict = json.loads(function_args)
                    args_str = json.dumps(args_dict, indent=2, ensure_ascii=False)
                except:
                    args_str = function_args
                
                print(f"\nFunción: {function_name}")
                print(f"Argumentos: {args_str}")
            
            # Mostrar respuesta de texto si existe
            if "response" in response:
                print(f"\nRespuesta de texto: {response['response']}")
        else:
            # Solo mostrar la respuesta de texto
            print(response.get("response", response))
        
        return response
    
    except Exception as e:
        logger.error(f"Error en generación con herramientas: {e}")
        print(f"❌ Error: {e}")
        return str(e)

async def test_models():
    """
    Prueba la obtención de modelos disponibles.
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar cliente LLM extendido
        llm_client = ExtendedLLMClient(config_manager)
        
        # Obtener modelos disponibles
        models = llm_client.get_available_models()
        
        # Mostrar modelos
        print(f"\n🤖 Modelos disponibles:\n")
        for model in models:
            print(f"ID: {model['id']}")
            print(f"Nombre: {model['name']}")
            print(f"Proveedor: {model['provider']}")
            print(f"Capacidades: {', '.join(model['capabilities'])}")
            print(f"Tokens máximos: {model['max_tokens']}")
            print()
        
        return models
    
    except Exception as e:
        logger.error(f"Error al obtener modelos: {e}")
        print(f"❌ Error: {e}")
        return []

async def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Prueba del cliente LLM extendido")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: ask
    ask_parser = subparsers.add_parser("ask", help="Generar texto")
    ask_parser.add_argument("prompt", help="Prompt para el LLM")
    ask_parser.add_argument("--model", help="Modelo a utilizar")
    ask_parser.add_argument("--temperature", type=float, default=0.7, help="Temperatura de muestreo")
    
    # Comando: tool
    tool_parser = subparsers.add_parser("tool", help="Usar herramientas")
    tool_parser.add_argument("prompt", help="Prompt para el LLM")
    tool_parser.add_argument("--model", help="Modelo a utilizar")
    tool_parser.add_argument("--temperature", type=float, default=0.7, help="Temperatura de muestreo")
    
    # Comando: models
    models_parser = subparsers.add_parser("models", help="Listar modelos disponibles")
    
    args = parser.parse_args()
    
    if args.command == "ask":
        await test_ask(args.prompt, args.model, args.temperature)
    
    elif args.command == "tool":
        await test_ask_tool(args.prompt, args.model, args.temperature)
    
    elif args.command == "models":
        await test_models()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
