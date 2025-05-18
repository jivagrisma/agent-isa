#!/usr/bin/env python3
"""
Script de prueba para el generador de imágenes.
"""

import argparse
import asyncio
import json
import logging
import sys
import os
import base64
from pathlib import Path
from typing import Dict, Any, Optional, List

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos necesarios
from modules.core import ConfigManager
from modules.image import ImageGenerator

def test_generate_image(
    prompt: str,
    model: Optional[str] = None,
    style: Optional[str] = None,
    size: Optional[str] = None,
    format: Optional[str] = None,
    output_path: Optional[str] = None
):
    """
    Prueba la generación de imágenes.
    
    Args:
        prompt: Descripción textual de la imagen
        model: Modelo a utilizar
        style: Estilo de la imagen
        size: Tamaño de la imagen
        format: Formato de la imagen
        output_path: Ruta de salida para la imagen
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar generador de imágenes
        image_generator = ImageGenerator(config_manager)
        
        # Generar imagen
        print(f"\n🖼️ Generando imagen con prompt: '{prompt}'")
        if model:
            print(f"Modelo: {model}")
        if style:
            print(f"Estilo: {style}")
        if size:
            print(f"Tamaño: {size}")
        if format:
            print(f"Formato: {format}")
        print("\n")
        
        result = image_generator.generate_image(
            prompt=prompt,
            model=model,
            style=style,
            size=size,
            format=format,
            save=True
        )
        
        # Verificar resultado
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return None
        
        # Mostrar resultado
        print("✅ Imagen generada:")
        print(f"Modelo: {result['model']}")
        if "style" in result and result["style"]:
            print(f"Estilo: {result['style']}")
        print(f"Tamaño: {result['size']}")
        print(f"Formato: {result['format']}")
        
        # Guardar imagen en ruta específica si se proporciona
        if output_path and "image_data" in result:
            try:
                image_data = base64.b64decode(result["image_data"])
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"Imagen guardada en: {output_path}")
            except Exception as e:
                print(f"Error al guardar imagen en {output_path}: {e}")
        
        # Mostrar ruta de la imagen guardada
        if "image_path" in result and result["image_path"]:
            print(f"Imagen guardada en: {result['image_path']}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error en generación de imagen: {e}")
        print(f"❌ Error: {e}")
        return None

def test_edit_image(
    image_path: str,
    operations: List[Dict[str, Any]],
    format: Optional[str] = None,
    output_path: Optional[str] = None
):
    """
    Prueba la edición de imágenes.
    
    Args:
        image_path: Ruta de la imagen a editar
        operations: Lista de operaciones a aplicar
        format: Formato de salida
        output_path: Ruta de salida para la imagen
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar generador de imágenes
        image_generator = ImageGenerator(config_manager)
        
        # Editar imagen
        print(f"\n✏️ Editando imagen: {image_path}")
        print(f"Operaciones: {json.dumps(operations, indent=2)}")
        if format:
            print(f"Formato de salida: {format}")
        print("\n")
        
        result = image_generator.edit_image(
            image_data=image_path,
            operations=operations,
            format=format,
            save=True
        )
        
        # Verificar resultado
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return None
        
        # Mostrar resultado
        print("✅ Imagen editada:")
        print(f"Formato: {result['format']}")
        print(f"Dimensiones: {result['width']}x{result['height']}")
        
        # Guardar imagen en ruta específica si se proporciona
        if output_path and "image_data" in result:
            try:
                image_data = base64.b64decode(result["image_data"])
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"Imagen guardada en: {output_path}")
            except Exception as e:
                print(f"Error al guardar imagen en {output_path}: {e}")
        
        # Mostrar ruta de la imagen guardada
        if "image_path" in result and result["image_path"]:
            print(f"Imagen guardada en: {result['image_path']}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error en edición de imagen: {e}")
        print(f"❌ Error: {e}")
        return None

def test_analyze_image(image_path: str):
    """
    Prueba el análisis de imágenes.
    
    Args:
        image_path: Ruta de la imagen a analizar
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar generador de imágenes
        image_generator = ImageGenerator(config_manager)
        
        # Analizar imagen
        print(f"\n🔍 Analizando imagen: {image_path}")
        print("\n")
        
        result = image_generator.analyze_image(image_path)
        
        # Verificar resultado
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return None
        
        # Mostrar resultado
        print("✅ Análisis de imagen:")
        print(f"Formato: {result['format']}")
        print(f"Modo: {result['mode']}")
        print(f"Dimensiones: {result['width']}x{result['height']}")
        print(f"Tamaño: {result['size_bytes']} bytes")
        
        # Mostrar información EXIF si está disponible
        if "exif" in result and result["exif"]:
            print("\nInformación EXIF:")
            for key, value in result["exif"].items():
                print(f"  {key}: {value}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error en análisis de imagen: {e}")
        print(f"❌ Error: {e}")
        return None

def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Prueba del generador de imágenes")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: generate
    generate_parser = subparsers.add_parser("generate", help="Generar imagen")
    generate_parser.add_argument("prompt", help="Descripción textual de la imagen")
    generate_parser.add_argument("--model", help="Modelo a utilizar")
    generate_parser.add_argument("--style", help="Estilo de la imagen")
    generate_parser.add_argument("--size", help="Tamaño de la imagen (ej. '1024x1024')")
    generate_parser.add_argument("--format", help="Formato de la imagen (png, jpeg)")
    generate_parser.add_argument("--output", help="Ruta de salida para la imagen")
    
    # Comando: edit
    edit_parser = subparsers.add_parser("edit", help="Editar imagen")
    edit_parser.add_argument("image", help="Ruta de la imagen a editar")
    edit_parser.add_argument("--operations", type=json.loads, required=True, help="Operaciones en formato JSON")
    edit_parser.add_argument("--format", help="Formato de salida")
    edit_parser.add_argument("--output", help="Ruta de salida para la imagen")
    
    # Comando: analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analizar imagen")
    analyze_parser.add_argument("image", help="Ruta de la imagen a analizar")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        test_generate_image(
            prompt=args.prompt,
            model=args.model,
            style=args.style,
            size=args.size,
            format=args.format,
            output_path=args.output
        )
    
    elif args.command == "edit":
        test_edit_image(
            image_path=args.image,
            operations=args.operations,
            format=args.format,
            output_path=args.output
        )
    
    elif args.command == "analyze":
        test_analyze_image(image_path=args.image)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
