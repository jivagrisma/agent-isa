#!/usr/bin/env python3
"""
Script de prueba para el almacenamiento estructurado.
"""

import argparse
import logging
import sys
import os
import json
import io
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

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
from modules.storage import VirtualFileSystem, StructuredStorage

def test_save_json(storage: StructuredStorage, data: Any, path: str, pretty: bool = True):
    """
    Prueba el guardado de datos en formato JSON.
    
    Args:
        storage: Sistema de almacenamiento estructurado
        data: Datos a guardar
        path: Ruta del archivo
        pretty: Si debe formatear el JSON para legibilidad
    """
    try:
        print(f"\n💾 Guardando JSON en {path}...")
        
        # Guardar datos
        success = storage.save_json(data, path, pretty=pretty)
        
        if success:
            print(f"✅ Datos guardados correctamente")
        else:
            print(f"❌ Error al guardar datos")
        
        return success
    
    except Exception as e:
        logger.error(f"Error en guardado de JSON: {e}")
        print(f"❌ Error: {e}")
        return False

def test_load_json(storage: StructuredStorage, path: str):
    """
    Prueba la carga de datos en formato JSON.
    
    Args:
        storage: Sistema de almacenamiento estructurado
        path: Ruta del archivo
    """
    try:
        print(f"\n📂 Cargando JSON desde {path}...")
        
        # Cargar datos
        data = storage.load_json(path)
        
        # Mostrar datos
        print(f"✅ Datos cargados correctamente:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        return data
    
    except Exception as e:
        logger.error(f"Error en carga de JSON: {e}")
        print(f"❌ Error: {e}")
        return None

def test_sqlite_operations(storage: StructuredStorage, db_name: str):
    """
    Prueba operaciones con SQLite.
    
    Args:
        storage: Sistema de almacenamiento estructurado
        db_name: Nombre de la base de datos
    """
    try:
        print(f"\n🗃️ Realizando operaciones SQLite en {db_name}...")
        
        # Crear tabla
        print("Creando tabla 'usuarios'...")
        schema = {
            "id": "INTEGER",
            "nombre": "TEXT",
            "edad": "INTEGER",
            "activo": "BOOLEAN"
        }
        storage.create_table(db_name, "usuarios", schema, primary_key="id")
        
        # Insertar datos
        print("Insertando datos...")
        usuarios = [
            {"id": 1, "nombre": "Juan", "edad": 30, "activo": True},
            {"id": 2, "nombre": "María", "edad": 25, "activo": True},
            {"id": 3, "nombre": "Pedro", "edad": 40, "activo": False}
        ]
        storage.insert_data(db_name, "usuarios", usuarios)
        
        # Consultar datos
        print("Consultando todos los usuarios...")
        results = storage.query_data(db_name, "usuarios")
        print(f"Resultados ({len(results)} filas):")
        for row in results:
            print(f"  {row['id']}: {row['nombre']}, {row['edad']} años, {'Activo' if row['activo'] else 'Inactivo'}")
        
        # Consultar con filtro
        print("\nConsultando usuarios activos...")
        activos = storage.query_data(db_name, "usuarios", conditions={"activo": True})
        print(f"Usuarios activos ({len(activos)} filas):")
        for row in activos:
            print(f"  {row['id']}: {row['nombre']}, {row['edad']} años")
        
        # Ejecutar consulta personalizada
        print("\nEjecutando consulta personalizada...")
        query = "SELECT nombre, edad FROM usuarios WHERE edad > ?"
        custom_results = storage.execute_query(db_name, query, (25,))
        print(f"Usuarios mayores de 25 años ({len(custom_results)} filas):")
        for row in custom_results:
            print(f"  {row['nombre']}: {row['edad']} años")
        
        return True
    
    except Exception as e:
        logger.error(f"Error en operaciones SQLite: {e}")
        print(f"❌ Error: {e}")
        return False

def test_dataframe_operations(storage: StructuredStorage, data: List[Dict[str, Any]], base_path: str):
    """
    Prueba operaciones con DataFrames.
    
    Args:
        storage: Sistema de almacenamiento estructurado
        data: Datos para el DataFrame
        base_path: Ruta base para guardar archivos
    """
    try:
        print(f"\n📊 Realizando operaciones con DataFrames...")
        
        # Crear DataFrame
        df = pd.DataFrame(data)
        print("DataFrame creado:")
        print(df)
        
        # Guardar en diferentes formatos
        formats = ["csv", "json", "pickle"]
        
        for fmt in formats:
            path = f"{base_path}.{fmt}"
            print(f"\nGuardando DataFrame en formato {fmt}...")
            success = storage.save_dataframe(df, path, format=fmt)
            
            if success:
                print(f"✅ DataFrame guardado correctamente en {path}")
                
                # Cargar DataFrame
                print(f"Cargando DataFrame desde {path}...")
                loaded_df = storage.load_dataframe(path, format=fmt)
                print("DataFrame cargado:")
                print(loaded_df)
            else:
                print(f"❌ Error al guardar DataFrame en {path}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error en operaciones con DataFrames: {e}")
        print(f"❌ Error: {e}")
        return False

def test_indexing(storage: StructuredStorage, data: List[Dict[str, Any]], index_name: str, key_field: str):
    """
    Prueba la creación y búsqueda en índices.
    
    Args:
        storage: Sistema de almacenamiento estructurado
        data: Datos para indexar
        index_name: Nombre del índice
        key_field: Campo a utilizar como clave
    """
    try:
        print(f"\n🔍 Creando índice '{index_name}' con clave '{key_field}'...")
        
        # Crear índice
        success = storage.create_index(index_name, data, key_field)
        
        if success:
            print(f"✅ Índice creado correctamente")
            
            # Buscar en índice
            for item in data:
                key = item[key_field]
                print(f"\nBuscando elemento con {key_field}='{key}'...")
                result = storage.search_index(index_name, key)
                
                if result:
                    print(f"✅ Elemento encontrado:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                else:
                    print(f"❌ Elemento no encontrado")
            
            # Buscar clave inexistente
            print("\nBuscando elemento inexistente...")
            not_found = storage.search_index(index_name, "clave_inexistente")
            
            if not_found is None:
                print(f"✅ Comportamiento correcto: elemento no encontrado")
            else:
                print(f"❌ Error: se encontró un elemento que no debería existir")
            
            return True
        else:
            print(f"❌ Error al crear índice")
            return False
    
    except Exception as e:
        logger.error(f"Error en indexación: {e}")
        print(f"❌ Error: {e}")
        return False

def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Prueba del almacenamiento estructurado")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: json
    json_parser = subparsers.add_parser("json", help="Operaciones con JSON")
    json_parser.add_argument("--save", action="store_true", help="Guardar datos")
    json_parser.add_argument("--load", action="store_true", help="Cargar datos")
    json_parser.add_argument("--path", default="test/data.json", help="Ruta del archivo")
    
    # Comando: sqlite
    sqlite_parser = subparsers.add_parser("sqlite", help="Operaciones con SQLite")
    sqlite_parser.add_argument("--db", default="test", help="Nombre de la base de datos")
    
    # Comando: dataframe
    df_parser = subparsers.add_parser("dataframe", help="Operaciones con DataFrames")
    df_parser.add_argument("--path", default="test/dataframe", help="Ruta base para archivos")
    
    # Comando: index
    index_parser = subparsers.add_parser("index", help="Operaciones con índices")
    index_parser.add_argument("--name", default="test_index", help="Nombre del índice")
    
    # Comando: test
    test_parser = subparsers.add_parser("test", help="Ejecutar prueba completa")
    test_parser.add_argument("--dir", default="test", help="Directorio de prueba")
    
    args = parser.parse_args()
    
    # Inicializar sistemas
    config_manager = ConfigManager()
    virtual_fs = VirtualFileSystem(config_manager)
    storage = StructuredStorage(config_manager, virtual_fs)
    
    # Datos de ejemplo
    example_data = {
        "nombre": "Ejemplo",
        "valores": [1, 2, 3, 4, 5],
        "objeto": {
            "clave1": "valor1",
            "clave2": "valor2"
        },
        "booleano": True,
        "nulo": None
    }
    
    # Datos para DataFrame
    df_data = [
        {"id": 1, "nombre": "Juan", "edad": 30, "ciudad": "Madrid"},
        {"id": 2, "nombre": "María", "edad": 25, "ciudad": "Barcelona"},
        {"id": 3, "nombre": "Pedro", "edad": 40, "ciudad": "Valencia"},
        {"id": 4, "nombre": "Ana", "edad": 35, "ciudad": "Sevilla"},
        {"id": 5, "nombre": "Luis", "edad": 28, "ciudad": "Madrid"}
    ]
    
    if args.command == "json":
        if args.save:
            test_save_json(storage, example_data, args.path)
        
        if args.load:
            test_load_json(storage, args.path)
        
        if not args.save and not args.load:
            test_save_json(storage, example_data, args.path)
            test_load_json(storage, args.path)
    
    elif args.command == "sqlite":
        test_sqlite_operations(storage, args.db)
    
    elif args.command == "dataframe":
        test_dataframe_operations(storage, df_data, args.path)
    
    elif args.command == "index":
        test_indexing(storage, df_data, args.name, "id")
    
    elif args.command == "test":
        # Ejecutar prueba completa
        test_dir = args.dir
        
        # Crear directorio de prueba
        os.makedirs(os.path.join("storage", test_dir), exist_ok=True)
        
        # Pruebas JSON
        json_path = f"{test_dir}/data.json"
        test_save_json(storage, example_data, json_path)
        test_load_json(storage, json_path)
        
        # Pruebas SQLite
        test_sqlite_operations(storage, f"{test_dir}_db")
        
        # Pruebas DataFrame
        test_dataframe_operations(storage, df_data, f"{test_dir}/dataframe")
        
        # Pruebas de indexación
        test_indexing(storage, df_data, f"{test_dir}_index", "id")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
