#!/usr/bin/env python3
"""
Script de prueba para el sistema de archivos virtual.
"""

import argparse
import logging
import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

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
from modules.storage import VirtualFileSystem

def test_write_file(fs: VirtualFileSystem, path: str, content: str, binary: bool = False):
    """
    Prueba la escritura de un archivo.
    
    Args:
        fs: Sistema de archivos virtual
        path: Ruta del archivo
        content: Contenido a escribir
        binary: Si debe escribir en modo binario
    """
    try:
        print(f"\n📝 Escribiendo en {path}...")
        
        # Convertir a bytes si es binario
        if binary and isinstance(content, str):
            content = content.encode("utf-8")
        
        # Escribir archivo
        success = fs.write_file(path, content, binary=binary)
        
        if success:
            print(f"✅ Archivo escrito correctamente")
        else:
            print(f"❌ Error al escribir archivo")
        
        return success
    
    except Exception as e:
        logger.error(f"Error en escritura de archivo: {e}")
        print(f"❌ Error: {e}")
        return False

def test_read_file(fs: VirtualFileSystem, path: str, binary: bool = False):
    """
    Prueba la lectura de un archivo.
    
    Args:
        fs: Sistema de archivos virtual
        path: Ruta del archivo
        binary: Si debe leer en modo binario
    """
    try:
        print(f"\n📖 Leyendo {path}...")
        
        # Leer archivo
        content = fs.read_file(path, binary=binary)
        
        # Mostrar contenido
        if binary:
            print(f"✅ Archivo leído correctamente ({len(content)} bytes)")
            # Mostrar primeros bytes en hexadecimal
            hex_content = content[:50].hex()
            print(f"Primeros bytes: {hex_content}...")
        else:
            print(f"✅ Archivo leído correctamente:")
            # Mostrar primeras líneas
            lines = content.split("\n")
            preview = "\n".join(lines[:10])
            if len(lines) > 10:
                preview += "\n..."
            print(preview)
        
        return content
    
    except Exception as e:
        logger.error(f"Error en lectura de archivo: {e}")
        print(f"❌ Error: {e}")
        return None

def test_delete_file(fs: VirtualFileSystem, path: str):
    """
    Prueba la eliminación de un archivo.
    
    Args:
        fs: Sistema de archivos virtual
        path: Ruta del archivo
    """
    try:
        print(f"\n🗑️ Eliminando {path}...")
        
        # Eliminar archivo
        success = fs.delete_file(path)
        
        if success:
            print(f"✅ Archivo eliminado correctamente")
        else:
            print(f"❌ Error al eliminar archivo")
        
        return success
    
    except Exception as e:
        logger.error(f"Error en eliminación de archivo: {e}")
        print(f"❌ Error: {e}")
        return False

def test_list_directory(fs: VirtualFileSystem, path: str):
    """
    Prueba el listado de un directorio.
    
    Args:
        fs: Sistema de archivos virtual
        path: Ruta del directorio
    """
    try:
        print(f"\n📂 Listando contenido de {path}...")
        
        # Listar directorio
        items = fs.list_directory(path)
        
        # Mostrar resultados
        print(f"✅ Directorio listado correctamente ({len(items)} elementos):")
        
        # Mostrar archivos y directorios
        for item in items:
            item_type = "📁" if item["type"] == "directory" else "📄"
            size = item["size"]
            size_str = f"{size} bytes"
            if size >= 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.2f} MB"
            elif size >= 1024:
                size_str = f"{size / 1024:.2f} KB"
            
            print(f"{item_type} {item['name']} ({size_str})")
        
        return items
    
    except Exception as e:
        logger.error(f"Error en listado de directorio: {e}")
        print(f"❌ Error: {e}")
        return None

def test_get_metadata(fs: VirtualFileSystem, path: str):
    """
    Prueba la obtención de metadatos de un archivo.
    
    Args:
        fs: Sistema de archivos virtual
        path: Ruta del archivo
    """
    try:
        print(f"\n🔍 Obteniendo metadatos de {path}...")
        
        # Obtener metadatos
        metadata = fs.get_metadata(path)
        
        # Mostrar resultados
        print(f"✅ Metadatos obtenidos correctamente:")
        
        # Formatear fechas
        import datetime
        created = datetime.datetime.fromtimestamp(metadata["created"]).strftime("%Y-%m-%d %H:%M:%S") if metadata["created"] else "N/A"
        modified = datetime.datetime.fromtimestamp(metadata["modified"]).strftime("%Y-%m-%d %H:%M:%S") if metadata["modified"] else "N/A"
        accessed = datetime.datetime.fromtimestamp(metadata["accessed"]).strftime("%Y-%m-%d %H:%M:%S") if metadata["accessed"] else "N/A"
        
        # Formatear tamaño
        size = metadata["size"]
        size_str = f"{size} bytes"
        if size >= 1024 * 1024:
            size_str = f"{size / (1024 * 1024):.2f} MB"
        elif size >= 1024:
            size_str = f"{size / 1024:.2f} KB"
        
        # Mostrar metadatos
        print(f"Nombre: {metadata['name']}")
        print(f"Ruta: {metadata['path']}")
        print(f"Tipo: {metadata['type']}")
        print(f"Tamaño: {size_str}")
        print(f"Creado: {created}")
        print(f"Modificado: {modified}")
        print(f"Accedido: {accessed}")
        print(f"Hash: {metadata['hash'] or 'N/A'}")
        print(f"Tipo MIME: {metadata['mime_type'] or 'N/A'}")
        
        return metadata
    
    except Exception as e:
        logger.error(f"Error en obtención de metadatos: {e}")
        print(f"❌ Error: {e}")
        return None

def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Prueba del sistema de archivos virtual")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: write
    write_parser = subparsers.add_parser("write", help="Escribir archivo")
    write_parser.add_argument("path", help="Ruta del archivo")
    write_parser.add_argument("content", help="Contenido a escribir")
    write_parser.add_argument("--binary", action="store_true", help="Escribir en modo binario")
    
    # Comando: read
    read_parser = subparsers.add_parser("read", help="Leer archivo")
    read_parser.add_argument("path", help="Ruta del archivo")
    read_parser.add_argument("--binary", action="store_true", help="Leer en modo binario")
    
    # Comando: delete
    delete_parser = subparsers.add_parser("delete", help="Eliminar archivo")
    delete_parser.add_argument("path", help="Ruta del archivo")
    
    # Comando: list
    list_parser = subparsers.add_parser("list", help="Listar directorio")
    list_parser.add_argument("path", help="Ruta del directorio")
    
    # Comando: metadata
    metadata_parser = subparsers.add_parser("metadata", help="Obtener metadatos")
    metadata_parser.add_argument("path", help="Ruta del archivo")
    
    # Comando: test
    test_parser = subparsers.add_parser("test", help="Ejecutar prueba completa")
    test_parser.add_argument("--path", default="test", help="Directorio de prueba")
    
    args = parser.parse_args()
    
    # Inicializar sistema de archivos virtual
    config_manager = ConfigManager()
    fs = VirtualFileSystem(config_manager)
    
    if args.command == "write":
        test_write_file(fs, args.path, args.content, args.binary)
    
    elif args.command == "read":
        test_read_file(fs, args.path, args.binary)
    
    elif args.command == "delete":
        test_delete_file(fs, args.path)
    
    elif args.command == "list":
        test_list_directory(fs, args.path)
    
    elif args.command == "metadata":
        test_get_metadata(fs, args.path)
    
    elif args.command == "test":
        # Ejecutar prueba completa
        test_dir = args.path
        
        # Crear directorio de prueba
        os.makedirs(os.path.join("storage", test_dir), exist_ok=True)
        
        # Escribir archivo de texto
        text_path = f"{test_dir}/test.txt"
        test_write_file(fs, text_path, "Este es un archivo de prueba.\nLínea 2.\nLínea 3.")
        
        # Leer archivo de texto
        test_read_file(fs, text_path)
        
        # Obtener metadatos
        test_get_metadata(fs, text_path)
        
        # Escribir archivo JSON
        json_path = f"{test_dir}/test.json"
        json_content = json.dumps({
            "nombre": "Prueba",
            "valor": 123,
            "lista": [1, 2, 3],
            "objeto": {"a": 1, "b": 2}
        }, indent=2)
        test_write_file(fs, json_path, json_content)
        
        # Leer archivo JSON
        test_read_file(fs, json_path)
        
        # Escribir archivo binario
        binary_path = f"{test_dir}/test.bin"
        binary_content = bytes([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        test_write_file(fs, binary_path, binary_content, binary=True)
        
        # Leer archivo binario
        test_read_file(fs, binary_path, binary=True)
        
        # Listar directorio
        test_list_directory(fs, test_dir)
        
        # Eliminar archivos
        test_delete_file(fs, text_path)
        test_delete_file(fs, json_path)
        test_delete_file(fs, binary_path)
        
        # Listar directorio nuevamente
        test_list_directory(fs, test_dir)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
