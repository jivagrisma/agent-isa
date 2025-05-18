#!/usr/bin/env python3
"""
Script de prueba para el procesador de contenido multimedia.
"""

import argparse
import asyncio
import json
import logging
import sys
import os
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
from modules.content import MediaProcessor

def test_extract_text_from_image(image_path: str):
    """
    Prueba la extracción de texto de imágenes.
    
    Args:
        image_path: Ruta de la imagen
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar procesador de contenido multimedia
        media_processor = MediaProcessor(config_manager)
        
        # Extraer texto
        print(f"\n📝 Extrayendo texto de imagen: {image_path}")
        print("\n")
        
        result = media_processor.extract_text_from_image(image_path)
        
        # Verificar resultado
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return None
        
        # Mostrar resultado
        print("✅ Texto extraído:")
        print(f"Confianza: {result['confidence']:.2f}%")
        print("\nTexto completo:")
        print(result["text"])
        
        # Mostrar líneas individuales
        if "lines" in result and result["lines"]:
            print("\nLíneas detectadas:")
            for i, line in enumerate(result["lines"], 1):
                print(f"{i}. {line}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error en extracción de texto: {e}")
        print(f"❌ Error: {e}")
        return None

def test_analyze_image_content(image_path: str, features: Optional[List[str]] = None):
    """
    Prueba el análisis de contenido de imágenes.
    
    Args:
        image_path: Ruta de la imagen
        features: Características a analizar
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar procesador de contenido multimedia
        media_processor = MediaProcessor(config_manager)
        
        # Analizar imagen
        print(f"\n🔍 Analizando contenido de imagen: {image_path}")
        if features:
            print(f"Características: {', '.join(features)}")
        print("\n")
        
        result = media_processor.analyze_image_content(image_path, features)
        
        # Verificar resultado
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return None
        
        # Mostrar resultado
        print("✅ Análisis de contenido:")
        
        # Mostrar etiquetas
        if "labels" in result and result["labels"]:
            print("\nEtiquetas detectadas:")
            for i, label in enumerate(result["labels"], 1):
                print(f"{i}. {label['name']} ({label['confidence']:.2f}%)")
                if label.get("parents"):
                    print(f"   Categorías: {', '.join(label['parents'])}")
        
        # Mostrar texto detectado
        if "text_detections" in result and result["text_detections"]:
            print("\nTexto detectado:")
            for i, detection in enumerate(result["text_detections"], 1):
                if detection["type"] == "LINE":
                    print(f"{i}. {detection['text']} ({detection['confidence']:.2f}%)")
        
        # Mostrar rostros
        if "faces" in result and result["faces"]:
            print("\nRostros detectados:")
            for i, face in enumerate(result["faces"], 1):
                print(f"{i}. Confianza: {face['confidence']:.2f}%")
                if "age_range" in face:
                    print(f"   Edad estimada: {face['age_range'].get('Low', 0)}-{face['age_range'].get('High', 0)} años")
                if "gender" in face:
                    print(f"   Género: {face['gender']}")
                if "emotions" in face and face["emotions"]:
                    top_emotion = max(face["emotions"], key=lambda x: x["confidence"])
                    print(f"   Emoción principal: {top_emotion['type']} ({top_emotion['confidence']:.2f}%)")
        
        # Mostrar etiquetas de moderación
        if "moderation_labels" in result and result["moderation_labels"]:
            print("\nEtiquetas de moderación:")
            for i, label in enumerate(result["moderation_labels"], 1):
                print(f"{i}. {label['name']} ({label['confidence']:.2f}%)")
                if label.get("parent"):
                    print(f"   Categoría: {label['parent']}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error en análisis de contenido: {e}")
        print(f"❌ Error: {e}")
        return None

def test_describe_image(image_path: str, max_tokens: int = 100):
    """
    Prueba la descripción de imágenes.
    
    Args:
        image_path: Ruta de la imagen
        max_tokens: Número máximo de tokens
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar procesador de contenido multimedia
        media_processor = MediaProcessor(config_manager)
        
        # Describir imagen
        print(f"\n📷 Generando descripción de imagen: {image_path}")
        print(f"Tokens máximos: {max_tokens}")
        print("\n")
        
        result = media_processor.describe_image(image_path, max_tokens)
        
        # Verificar resultado
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return None
        
        # Mostrar resultado
        print("✅ Descripción generada:")
        print(f"Modelo: {result['model']}")
        print("\nDescripción:")
        print(result["description"])
        
        return result
    
    except Exception as e:
        logger.error(f"Error en descripción de imagen: {e}")
        print(f"❌ Error: {e}")
        return None

def test_convert_image_format(image_path: str, target_format: str, quality: Optional[int] = None):
    """
    Prueba la conversión de formato de imágenes.
    
    Args:
        image_path: Ruta de la imagen
        target_format: Formato de destino
        quality: Calidad de la imagen
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()
        
        # Inicializar procesador de contenido multimedia
        media_processor = MediaProcessor(config_manager)
        
        # Convertir formato
        print(f"\n🔄 Convirtiendo imagen a formato {target_format}: {image_path}")
        if quality:
            print(f"Calidad: {quality}")
        print("\n")
        
        result = media_processor.convert_image_format(image_path, target_format, quality)
        
        # Verificar resultado
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return None
        
        # Mostrar resultado
        print("✅ Imagen convertida:")
        print(f"Formato: {result['format']}")
        print(f"Dimensiones: {result['width']}x{result['height']}")
        print(f"Tamaño: {result['size_bytes']} bytes")
        
        # Guardar imagen convertida
        output_path = f"{os.path.splitext(image_path)[0]}_converted.{result['format']}"
        try:
            import base64
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(result["image_data"]))
            print(f"Imagen guardada en: {output_path}")
        except Exception as e:
            print(f"Error al guardar imagen: {e}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error en conversión de formato: {e}")
        print(f"❌ Error: {e}")
        return None

def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Prueba del procesador de contenido multimedia")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: ocr
    ocr_parser = subparsers.add_parser("ocr", help="Extraer texto de imagen")
    ocr_parser.add_argument("image", help="Ruta de la imagen")
    
    # Comando: analyze
    analyze_parser = subparsers.add_parser("analyze", help="Analizar contenido de imagen")
    analyze_parser.add_argument("image", help="Ruta de la imagen")
    analyze_parser.add_argument("--features", nargs="+", choices=["labels", "text", "faces", "moderation"], 
                               help="Características a analizar")
    
    # Comando: describe
    describe_parser = subparsers.add_parser("describe", help="Generar descripción de imagen")
    describe_parser.add_argument("image", help="Ruta de la imagen")
    describe_parser.add_argument("--max-tokens", type=int, default=100, help="Número máximo de tokens")
    
    # Comando: convert
    convert_parser = subparsers.add_parser("convert", help="Convertir formato de imagen")
    convert_parser.add_argument("image", help="Ruta de la imagen")
    convert_parser.add_argument("--format", required=True, choices=["png", "jpeg", "webp", "gif"], 
                               help="Formato de destino")
    convert_parser.add_argument("--quality", type=int, help="Calidad de la imagen (0-100)")
    
    args = parser.parse_args()
    
    if args.command == "ocr":
        test_extract_text_from_image(args.image)
    
    elif args.command == "analyze":
        test_analyze_image_content(args.image, args.features)
    
    elif args.command == "describe":
        test_describe_image(args.image, args.max_tokens)
    
    elif args.command == "convert":
        test_convert_image_format(args.image, args.format, args.quality)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
