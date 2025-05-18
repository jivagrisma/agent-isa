#!/usr/bin/env python3
"""
Script de prueba para el generador de texto.
"""

import argparse
import asyncio
import json
import logging
import sys
from typing import Dict, Any, Optional

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
from modules.core import ConfigManager
from modules.content import TextGenerator

async def test_generate_text(
    prompt: str,
    style: Optional[str] = None,
    format_type: Optional[str] = None,
    temperature: Optional[float] = None
):
    """
    Prueba la generación de texto.
    
    Args:
        prompt: Prompt para la generación
        style: Estilo de escritura
        format_type: Tipo de formato
        temperature: Temperatura de muestreo
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar generador de texto
        text_generator = TextGenerator(config_manager)
        
        # Generar texto
        print(f"\n📝 Generando texto con prompt: '{prompt}'")
        if style:
            print(f"Estilo: {style}")
        if format_type:
            print(f"Formato: {format_type}")
        if temperature:
            print(f"Temperatura: {temperature}")
        print("\n")
        
        text = await text_generator.generate_text(
            prompt=prompt,
            style=style,
            format_type=format_type,
            temperature=temperature
        )
        
        # Mostrar resultado
        print("✅ Texto generado:\n")
        print(text)
        
        return text
    
    except Exception as e:
        logger.error(f"Error en generación de texto: {e}")
        print(f"❌ Error: {e}")
        return str(e)

async def test_revise_text(
    text: str,
    instructions: Optional[str] = None,
    format_type: Optional[str] = None
):
    """
    Prueba la revisión de texto.
    
    Args:
        text: Texto a revisar
        instructions: Instrucciones específicas
        format_type: Tipo de formato
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar generador de texto
        text_generator = TextGenerator(config_manager)
        
        # Revisar texto
        print(f"\n🔍 Revisando texto...")
        if instructions:
            print(f"Instrucciones: {instructions}")
        if format_type:
            print(f"Formato: {format_type}")
        print("\n")
        
        revised_text = await text_generator.revise_text(
            text=text,
            instructions=instructions,
            format_type=format_type
        )
        
        # Mostrar resultado
        print("✅ Texto revisado:\n")
        print(revised_text)
        
        return revised_text
    
    except Exception as e:
        logger.error(f"Error en revisión de texto: {e}")
        print(f"❌ Error: {e}")
        return str(e)

async def test_generate_from_template(
    template_name: str,
    variables: Dict[str, Any],
    style: Optional[str] = None,
    format_type: Optional[str] = None
):
    """
    Prueba la generación de texto a partir de una plantilla.
    
    Args:
        template_name: Nombre de la plantilla
        variables: Variables para la plantilla
        style: Estilo de escritura
        format_type: Tipo de formato
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar generador de texto
        text_generator = TextGenerator(config_manager)
        
        # Generar texto
        print(f"\n📋 Generando texto con plantilla: '{template_name}'")
        print(f"Variables: {json.dumps(variables, ensure_ascii=False, indent=2)}")
        if style:
            print(f"Estilo: {style}")
        if format_type:
            print(f"Formato: {format_type}")
        print("\n")
        
        text = await text_generator.generate_from_template(
            template_name=template_name,
            variables=variables,
            style=style,
            format_type=format_type
        )
        
        # Mostrar resultado
        print("✅ Texto generado:\n")
        print(text)
        
        return text
    
    except Exception as e:
        logger.error(f"Error en generación con plantilla: {e}")
        print(f"❌ Error: {e}")
        return str(e)

async def test_convert_format(
    text: str,
    source_format: str,
    target_format: str
):
    """
    Prueba la conversión de formato de texto.
    
    Args:
        text: Texto a convertir
        source_format: Formato de origen
        target_format: Formato de destino
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar generador de texto
        text_generator = TextGenerator(config_manager)
        
        # Convertir formato
        print(f"\n🔄 Convirtiendo texto de {source_format} a {target_format}...")
        print("\n")
        
        converted_text = text_generator.convert_format(
            text=text,
            source_format=source_format,
            target_format=target_format
        )
        
        # Mostrar resultado
        print("✅ Texto convertido:\n")
        print(converted_text)
        
        return converted_text
    
    except Exception as e:
        logger.error(f"Error en conversión de formato: {e}")
        print(f"❌ Error: {e}")
        return str(e)

async def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Prueba del generador de texto")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: generate
    generate_parser = subparsers.add_parser("generate", help="Generar texto")
    generate_parser.add_argument("prompt", help="Prompt para la generación")
    generate_parser.add_argument("--style", help="Estilo de escritura")
    generate_parser.add_argument("--format", dest="format_type", help="Tipo de formato")
    generate_parser.add_argument("--temperature", type=float, help="Temperatura de muestreo")
    
    # Comando: revise
    revise_parser = subparsers.add_parser("revise", help="Revisar texto")
    revise_parser.add_argument("text", help="Texto a revisar")
    revise_parser.add_argument("--instructions", help="Instrucciones específicas")
    revise_parser.add_argument("--format", dest="format_type", help="Tipo de formato")
    
    # Comando: template
    template_parser = subparsers.add_parser("template", help="Generar texto con plantilla")
    template_parser.add_argument("template", help="Nombre de la plantilla")
    template_parser.add_argument("--variables", type=json.loads, help="Variables en formato JSON")
    template_parser.add_argument("--style", help="Estilo de escritura")
    template_parser.add_argument("--format", dest="format_type", help="Tipo de formato")
    
    # Comando: convert
    convert_parser = subparsers.add_parser("convert", help="Convertir formato de texto")
    convert_parser.add_argument("text", help="Texto a convertir")
    convert_parser.add_argument("--from", dest="source_format", required=True, help="Formato de origen")
    convert_parser.add_argument("--to", dest="target_format", required=True, help="Formato de destino")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        await test_generate_text(
            prompt=args.prompt,
            style=args.style,
            format_type=args.format_type,
            temperature=args.temperature
        )
    
    elif args.command == "revise":
        await test_revise_text(
            text=args.text,
            instructions=args.instructions,
            format_type=args.format_type
        )
    
    elif args.command == "template":
        if not args.variables:
            print("❌ Error: Se requieren variables para la plantilla")
            return
        
        await test_generate_from_template(
            template_name=args.template,
            variables=args.variables,
            style=args.style,
            format_type=args.format_type
        )
    
    elif args.command == "convert":
        await test_convert_format(
            text=args.text,
            source_format=args.source_format,
            target_format=args.target_format
        )
    
    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
