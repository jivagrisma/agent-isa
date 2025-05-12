#!/usr/bin/env python3
"""
Script para probar la comunicación con AWS Bedrock desde la línea de comandos.
"""

import asyncio
import json
import logging
import os
import sys
from typing import List, Dict, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos necesarios
from app.llm import LLM
from app.config import config

async def main():
    """
    Función principal para probar la comunicación con AWS Bedrock.
    """
    try:
        # Inicializar el cliente LLM
        logger.info("Inicializando cliente LLM...")
        llm = LLM(config_name="default")
        
        # Verificar que el cliente se ha inicializado correctamente
        if not hasattr(llm, "client"):
            logger.error("El cliente LLM no se ha inicializado correctamente")
            return
        
        # Verificar que el cliente es de tipo bedrock
        if llm.api_type != "bedrock":
            logger.error(f"El cliente LLM no es de tipo bedrock, es de tipo {llm.api_type}")
            return
        
        # Verificar que el modelo es correcto
        logger.info(f"Modelo: {llm.model_id}")
        logger.info(f"Tipo de modelo: {'Claude' if llm.is_claude else 'Nova' if llm.is_nova else 'Desconocido'}")
        
        # Bucle interactivo
        print("\n=== Prueba de comunicación con AWS Bedrock ===")
        print("Escribe 'salir' para terminar")
        
        while True:
            # Solicitar entrada al usuario
            prompt = input("\nIngresa tu mensaje: ")
            
            # Verificar si el usuario quiere salir
            if prompt.lower() in ["salir", "exit", "quit"]:
                print("Saliendo...")
                break
            
            # Crear un mensaje simple
            messages = [
                {"role": "user", "content": prompt}
            ]
            
            # Enviar el mensaje a AWS Bedrock
            print("\nEnviando mensaje a AWS Bedrock...")
            try:
                response = await llm.ask_bedrock(
                    messages=messages,
                    stream=False,
                    temperature=0.7
                )
                
                print(f"\nRespuesta recibida:\n{response}")
            except Exception as e:
                logger.error(f"Error al enviar mensaje a AWS Bedrock: {e}")
                print(f"\nError al enviar mensaje a AWS Bedrock: {e}")
            
    except Exception as e:
        logger.error(f"Error al inicializar cliente LLM: {e}")
        print(f"Error al inicializar cliente LLM: {e}")

if __name__ == "__main__":
    # Ejecutar la función principal
    asyncio.run(main())
