"""
Almacenamiento estructurado para agent-isa.
Proporciona una interfaz para almacenar y consultar datos estructurados.
"""

import os
import json
import csv
import sqlite3
import logging
import time
import pickle
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Iterator, Set
import pandas as pd

from ..core import PluginInterface, ConfigManager
from .virtual_fs import VirtualFileSystem

# Configurar logging
logger = logging.getLogger(__name__)

class StructuredStorage(PluginInterface):
    """
    Sistema de almacenamiento estructurado con soporte para diferentes formatos.
    
    Características:
    1. Interfaz para almacenamiento de datos estructurados
    2. Soporte para diferentes formatos (JSON, CSV, SQLite, etc.)
    3. Capacidades de consulta y filtrado
    4. Indexación y búsqueda
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager", "storage.VirtualFileSystem"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, virtual_fs: Optional[VirtualFileSystem] = None):
        """
        Inicializa el sistema de almacenamiento estructurado.
        
        Args:
            config_manager: Gestor de configuración
            virtual_fs: Sistema de archivos virtual
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("storage")
        
        # Inicializar sistema de archivos virtual
        self.virtual_fs = virtual_fs or VirtualFileSystem(self.config_manager)
        
        # Directorio para bases de datos SQLite
        self.db_dir = Path(self.config.get("structured.db_directory", "databases"))
        os.makedirs(self.db_dir, exist_ok=True)
        
        # Caché de conexiones SQLite
        self.sqlite_connections = {}
        
        # Índices en memoria
        self.indices = {}
        
        logger.info("Sistema de almacenamiento estructurado inicializado")
    
    def save_json(self, data: Any, path: str, pretty: bool = False) -> bool:
        """
        Guarda datos en formato JSON.
        
        Args:
            data: Datos a guardar
            path: Ruta del archivo
            pretty: Si debe formatear el JSON para legibilidad
            
        Returns:
            True si se guardó correctamente
        """
        try:
            indent = 2 if pretty else None
            json_str = json.dumps(data, ensure_ascii=False, indent=indent)
            return self.virtual_fs.write_file(path, json_str)
        except Exception as e:
            logger.error(f"Error al guardar JSON en {path}: {e}")
            raise
    
    def load_json(self, path: str) -> Any:
        """
        Carga datos en formato JSON.
        
        Args:
            path: Ruta del archivo
            
        Returns:
            Datos cargados
        """
        try:
            content = self.virtual_fs.read_file(path)
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error al cargar JSON desde {path}: {e}")
            raise
    
    def save_csv(self, data: List[Dict[str, Any]], path: str, fieldnames: Optional[List[str]] = None) -> bool:
        """
        Guarda datos en formato CSV.
        
        Args:
            data: Lista de diccionarios con los datos
            path: Ruta del archivo
            fieldnames: Lista de nombres de campos (columnas)
            
        Returns:
            True si se guardó correctamente
        """
        try:
            # Determinar nombres de campos si no se proporcionan
            if not fieldnames and data:
                fieldnames = list(data[0].keys())
            
            # Crear contenido CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
            # Guardar archivo
            return self.virtual_fs.write_file(path, output.getvalue())
        except Exception as e:
            logger.error(f"Error al guardar CSV en {path}: {e}")
            raise
    
    def load_csv(self, path: str, as_dicts: bool = True) -> Union[List[Dict[str, Any]], List[List[str]]]:
        """
        Carga datos en formato CSV.
        
        Args:
            path: Ruta del archivo
            as_dicts: Si debe devolver los datos como diccionarios
            
        Returns:
            Datos cargados
        """
        try:
            content = self.virtual_fs.read_file(path)
            
            # Parsear CSV
            if as_dicts:
                reader = csv.DictReader(content.splitlines())
                return list(reader)
            else:
                reader = csv.reader(content.splitlines())
                rows = list(reader)
                return rows
        except Exception as e:
            logger.error(f"Error al cargar CSV desde {path}: {e}")
            raise
    
    def get_sqlite_connection(self, db_name: str) -> sqlite3.Connection:
        """
        Obtiene una conexión a una base de datos SQLite.
        
        Args:
            db_name: Nombre de la base de datos
            
        Returns:
            Conexión a la base de datos
        """
        if db_name in self.sqlite_connections:
            return self.sqlite_connections[db_name]
        
        # Crear directorio si no existe
        db_path = self.db_dir / f"{db_name}.db"
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Crear conexión
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Guardar conexión en caché
        self.sqlite_connections[db_name] = conn
        
        return conn
    
    def execute_query(self, db_name: str, query: str, params: Optional[Union[Tuple, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Ejecuta una consulta SQL.
        
        Args:
            db_name: Nombre de la base de datos
            query: Consulta SQL
            params: Parámetros para la consulta
            
        Returns:
            Resultados de la consulta
        """
        try:
            conn = self.get_sqlite_connection(db_name)
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Obtener resultados si es una consulta SELECT
            if query.strip().upper().startswith("SELECT"):
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                return []
        except Exception as e:
            logger.error(f"Error al ejecutar consulta en {db_name}: {e}")
            raise
    
    def create_table(self, db_name: str, table_name: str, schema: Dict[str, str], primary_key: Optional[str] = None) -> bool:
        """
        Crea una tabla en una base de datos SQLite.
        
        Args:
            db_name: Nombre de la base de datos
            table_name: Nombre de la tabla
            schema: Diccionario con nombres de columnas y tipos
            primary_key: Nombre de la columna de clave primaria
            
        Returns:
            True si se creó correctamente
        """
        try:
            # Construir consulta CREATE TABLE
            columns = []
            for column, data_type in schema.items():
                if primary_key and column == primary_key:
                    columns.append(f"{column} {data_type} PRIMARY KEY")
                else:
                    columns.append(f"{column} {data_type}")
            
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})"
            
            # Ejecutar consulta
            self.execute_query(db_name, query)
            return True
        except Exception as e:
            logger.error(f"Error al crear tabla {table_name} en {db_name}: {e}")
            raise
    
    def insert_data(self, db_name: str, table_name: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """
        Inserta datos en una tabla SQLite.
        
        Args:
            db_name: Nombre de la base de datos
            table_name: Nombre de la tabla
            data: Datos a insertar (diccionario o lista de diccionarios)
            
        Returns:
            True si se insertó correctamente
        """
        try:
            conn = self.get_sqlite_connection(db_name)
            cursor = conn.cursor()
            
            # Convertir a lista si es un solo diccionario
            if isinstance(data, dict):
                data = [data]
            
            if not data:
                return True
            
            # Obtener columnas del primer elemento
            columns = list(data[0].keys())
            placeholders = ", ".join(["?"] * len(columns))
            
            # Construir consulta INSERT
            query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Preparar valores
            values = []
            for item in data:
                row = [item.get(column) for column in columns]
                values.append(row)
            
            # Ejecutar consulta
            cursor.executemany(query, values)
            conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error al insertar datos en {table_name} ({db_name}): {e}")
            raise
    
    def query_data(self, db_name: str, table_name: str, conditions: Optional[Dict[str, Any]] = None, 
                  fields: Optional[List[str]] = None, order_by: Optional[str] = None, 
                  limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Consulta datos de una tabla SQLite.
        
        Args:
            db_name: Nombre de la base de datos
            table_name: Nombre de la tabla
            conditions: Condiciones para filtrar (columna: valor)
            fields: Campos a devolver (None para todos)
            order_by: Campo para ordenar
            limit: Límite de resultados
            
        Returns:
            Lista de resultados
        """
        try:
            # Construir consulta SELECT
            select_fields = "*"
            if fields:
                select_fields = ", ".join(fields)
            
            query = f"SELECT {select_fields} FROM {table_name}"
            
            # Añadir condiciones WHERE
            params = {}
            if conditions:
                where_clauses = []
                for column, value in conditions.items():
                    where_clauses.append(f"{column} = :{column}")
                    params[column] = value
                
                if where_clauses:
                    query += f" WHERE {' AND '.join(where_clauses)}"
            
            # Añadir ORDER BY
            if order_by:
                query += f" ORDER BY {order_by}"
            
            # Añadir LIMIT
            if limit:
                query += f" LIMIT {limit}"
            
            # Ejecutar consulta
            return self.execute_query(db_name, query, params)
        except Exception as e:
            logger.error(f"Error al consultar datos de {table_name} ({db_name}): {e}")
            raise
    
    def create_index(self, name: str, data: List[Dict[str, Any]], key_field: str) -> bool:
        """
        Crea un índice en memoria para búsqueda rápida.
        
        Args:
            name: Nombre del índice
            data: Datos a indexar
            key_field: Campo a utilizar como clave
            
        Returns:
            True si se creó correctamente
        """
        try:
            # Crear índice
            index = {}
            for item in data:
                key = item.get(key_field)
                if key is not None:
                    index[key] = item
            
            # Guardar índice
            self.indices[name] = {
                "data": index,
                "key_field": key_field,
                "timestamp": time.time()
            }
            
            logger.info(f"Índice '{name}' creado con {len(index)} elementos")
            return True
        except Exception as e:
            logger.error(f"Error al crear índice '{name}': {e}")
            raise
    
    def search_index(self, name: str, key: Any) -> Optional[Dict[str, Any]]:
        """
        Busca un elemento en un índice.
        
        Args:
            name: Nombre del índice
            key: Clave a buscar
            
        Returns:
            Elemento encontrado o None
        """
        if name not in self.indices:
            raise ValueError(f"Índice no encontrado: {name}")
        
        index = self.indices[name]["data"]
        return index.get(key)
    
    def save_pickle(self, data: Any, path: str) -> bool:
        """
        Guarda datos en formato pickle.
        
        Args:
            data: Datos a guardar
            path: Ruta del archivo
            
        Returns:
            True si se guardó correctamente
        """
        try:
            # Serializar datos
            pickle_data = pickle.dumps(data)
            
            # Guardar archivo
            return self.virtual_fs.write_file(path, pickle_data, binary=True)
        except Exception as e:
            logger.error(f"Error al guardar pickle en {path}: {e}")
            raise
    
    def load_pickle(self, path: str) -> Any:
        """
        Carga datos en formato pickle.
        
        Args:
            path: Ruta del archivo
            
        Returns:
            Datos cargados
        """
        try:
            # Leer archivo
            pickle_data = self.virtual_fs.read_file(path, binary=True)
            
            # Deserializar datos
            return pickle.loads(pickle_data)
        except Exception as e:
            logger.error(f"Error al cargar pickle desde {path}: {e}")
            raise
    
    def save_dataframe(self, df: pd.DataFrame, path: str, format: str = "csv") -> bool:
        """
        Guarda un DataFrame en diferentes formatos.
        
        Args:
            df: DataFrame a guardar
            path: Ruta del archivo
            format: Formato (csv, json, excel, parquet, pickle)
            
        Returns:
            True si se guardó correctamente
        """
        try:
            # Crear buffer en memoria
            buffer = io.BytesIO()
            
            # Guardar según formato
            if format == "csv":
                df.to_csv(buffer, index=False)
                content = buffer.getvalue().decode("utf-8")
                return self.virtual_fs.write_file(path, content)
            
            elif format == "json":
                json_str = df.to_json(orient="records")
                return self.virtual_fs.write_file(path, json_str)
            
            elif format == "excel":
                df.to_excel(buffer, index=False)
                return self.virtual_fs.write_file(path, buffer.getvalue(), binary=True)
            
            elif format == "parquet":
                df.to_parquet(buffer)
                return self.virtual_fs.write_file(path, buffer.getvalue(), binary=True)
            
            elif format == "pickle":
                df.to_pickle(buffer)
                return self.virtual_fs.write_file(path, buffer.getvalue(), binary=True)
            
            else:
                raise ValueError(f"Formato no soportado: {format}")
        except Exception as e:
            logger.error(f"Error al guardar DataFrame en {path}: {e}")
            raise
    
    def load_dataframe(self, path: str, format: Optional[str] = None) -> pd.DataFrame:
        """
        Carga un DataFrame desde diferentes formatos.
        
        Args:
            path: Ruta del archivo
            format: Formato (csv, json, excel, parquet, pickle)
            
        Returns:
            DataFrame cargado
        """
        try:
            # Determinar formato por extensión si no se especifica
            if not format:
                ext = os.path.splitext(path)[1].lower()
                if ext == ".csv":
                    format = "csv"
                elif ext == ".json":
                    format = "json"
                elif ext in (".xls", ".xlsx"):
                    format = "excel"
                elif ext == ".parquet":
                    format = "parquet"
                elif ext == ".pkl":
                    format = "pickle"
                else:
                    raise ValueError(f"No se pudo determinar el formato para {path}")
            
            # Cargar según formato
            if format == "csv":
                content = self.virtual_fs.read_file(path)
                return pd.read_csv(io.StringIO(content))
            
            elif format == "json":
                content = self.virtual_fs.read_file(path)
                return pd.read_json(content)
            
            elif format == "excel":
                content = self.virtual_fs.read_file(path, binary=True)
                return pd.read_excel(io.BytesIO(content))
            
            elif format == "parquet":
                content = self.virtual_fs.read_file(path, binary=True)
                return pd.read_parquet(io.BytesIO(content))
            
            elif format == "pickle":
                content = self.virtual_fs.read_file(path, binary=True)
                return pd.read_pickle(io.BytesIO(content))
            
            else:
                raise ValueError(f"Formato no soportado: {format}")
        except Exception as e:
            logger.error(f"Error al cargar DataFrame desde {path}: {e}")
            raise
