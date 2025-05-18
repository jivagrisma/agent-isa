"""
Sistema de archivos virtual para agent-isa.
Proporciona una interfaz unificada para acceder a archivos locales y remotos.
"""

import os
import io
import shutil
import logging
import json
import time
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, BinaryIO, Tuple, Iterator
import boto3
import requests
from urllib.parse import urlparse

from ..core import PluginInterface, ConfigManager

# Configurar logging
logger = logging.getLogger(__name__)

class VirtualFileSystem(PluginInterface):
    """
    Sistema de archivos virtual con soporte para diferentes backends de almacenamiento.
    
    Características:
    1. Interfaz unificada para acceso a archivos locales y remotos
    2. Operaciones básicas de archivos (crear, leer, escribir, eliminar)
    3. Soporte para diferentes sistemas de almacenamiento (local, S3, etc.)
    4. Capacidades de sincronización y respaldo
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Inicializa el sistema de archivos virtual.
        
        Args:
            config_manager: Gestor de configuración
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("storage")
        
        # Inicializar clientes
        self.s3_client = None
        
        # Directorio raíz para almacenamiento local
        self.root_dir = Path(self.config.get("local.root_directory", "storage"))
        os.makedirs(self.root_dir, exist_ok=True)
        
        # Caché de metadatos
        self.metadata_cache = {}
        self.cache_ttl = self.config.get("cache.ttl", 300)  # 5 minutos por defecto
        
        logger.info("Sistema de archivos virtual inicializado")
    
    def initialize_aws_clients(self):
        """
        Inicializa los clientes de AWS.
        """
        try:
            # Inicializar cliente de S3
            region = self.config.get("aws.region", "us-east-1")
            
            # Crear cliente de S3
            self.s3_client = boto3.client(
                service_name="s3",
                region_name=region
            )
            
            logger.info("Cliente S3 inicializado")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar cliente S3: {e}")
            return False
    
    def parse_path(self, path: str) -> Tuple[str, str]:
        """
        Parsea una ruta para determinar el backend y la ruta real.
        
        Args:
            path: Ruta a parsear
            
        Returns:
            Tupla con el backend y la ruta real
        """
        # Verificar si es una URL
        if path.startswith(("http://", "https://")):
            return "http", path
        
        # Verificar si es una ruta de S3
        if path.startswith("s3://"):
            parts = urlparse(path)
            bucket = parts.netloc
            key = parts.path.lstrip("/")
            return "s3", f"{bucket}/{key}"
        
        # Verificar si tiene un prefijo específico
        if ":" in path and not os.path.isabs(path) and not path[1:3] == ":\\":  # Evitar confundir con rutas Windows
            backend, rest = path.split(":", 1)
            return backend, rest
        
        # Por defecto, es una ruta local
        return "local", str(path)
    
    def read_file(self, path: str, binary: bool = False) -> Union[str, bytes]:
        """
        Lee un archivo.
        
        Args:
            path: Ruta del archivo
            binary: Si debe leer en modo binario
            
        Returns:
            Contenido del archivo
        """
        backend, real_path = self.parse_path(path)
        
        try:
            if backend == "local":
                full_path = self.root_dir / real_path
                mode = "rb" if binary else "r"
                with open(full_path, mode) as f:
                    return f.read()
            
            elif backend == "s3":
                if not self.s3_client:
                    self.initialize_aws_clients()
                
                bucket, key = real_path.split("/", 1)
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                content = response["Body"].read()
                
                if binary:
                    return content
                else:
                    return content.decode("utf-8")
            
            elif backend == "http":
                response = requests.get(real_path)
                response.raise_for_status()
                
                if binary:
                    return response.content
                else:
                    return response.text
            
            else:
                raise ValueError(f"Backend no soportado: {backend}")
        
        except Exception as e:
            logger.error(f"Error al leer archivo {path}: {e}")
            raise
    
    def write_file(self, path: str, content: Union[str, bytes], binary: bool = False) -> bool:
        """
        Escribe un archivo.
        
        Args:
            path: Ruta del archivo
            content: Contenido a escribir
            binary: Si debe escribir en modo binario
            
        Returns:
            True si se escribió correctamente
        """
        backend, real_path = self.parse_path(path)
        
        try:
            if backend == "local":
                full_path = self.root_dir / real_path
                
                # Crear directorios si no existen
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                mode = "wb" if binary else "w"
                with open(full_path, mode) as f:
                    f.write(content)
                
                # Invalidar caché de metadatos
                cache_key = f"{backend}:{real_path}"
                if cache_key in self.metadata_cache:
                    del self.metadata_cache[cache_key]
                
                return True
            
            elif backend == "s3":
                if not self.s3_client:
                    self.initialize_aws_clients()
                
                bucket, key = real_path.split("/", 1)
                
                # Determinar tipo de contenido
                content_type = mimetypes.guess_type(real_path)[0] or "application/octet-stream"
                
                # Preparar contenido
                if not binary and isinstance(content, str):
                    content = content.encode("utf-8")
                
                # Subir a S3
                self.s3_client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=content,
                    ContentType=content_type
                )
                
                # Invalidar caché de metadatos
                cache_key = f"{backend}:{real_path}"
                if cache_key in self.metadata_cache:
                    del self.metadata_cache[cache_key]
                
                return True
            
            else:
                raise ValueError(f"Backend no soportado para escritura: {backend}")
        
        except Exception as e:
            logger.error(f"Error al escribir archivo {path}: {e}")
            raise
    
    def delete_file(self, path: str) -> bool:
        """
        Elimina un archivo.
        
        Args:
            path: Ruta del archivo
            
        Returns:
            True si se eliminó correctamente
        """
        backend, real_path = self.parse_path(path)
        
        try:
            if backend == "local":
                full_path = self.root_dir / real_path
                
                if os.path.isfile(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                else:
                    return False
                
                # Invalidar caché de metadatos
                cache_key = f"{backend}:{real_path}"
                if cache_key in self.metadata_cache:
                    del self.metadata_cache[cache_key]
                
                return True
            
            elif backend == "s3":
                if not self.s3_client:
                    self.initialize_aws_clients()
                
                bucket, key = real_path.split("/", 1)
                
                # Eliminar de S3
                self.s3_client.delete_object(
                    Bucket=bucket,
                    Key=key
                )
                
                # Invalidar caché de metadatos
                cache_key = f"{backend}:{real_path}"
                if cache_key in self.metadata_cache:
                    del self.metadata_cache[cache_key]
                
                return True
            
            else:
                raise ValueError(f"Backend no soportado para eliminación: {backend}")
        
        except Exception as e:
            logger.error(f"Error al eliminar archivo {path}: {e}")
            raise
    
    def list_directory(self, path: str) -> List[Dict[str, Any]]:
        """
        Lista el contenido de un directorio.
        
        Args:
            path: Ruta del directorio
            
        Returns:
            Lista de archivos y directorios
        """
        backend, real_path = self.parse_path(path)
        
        try:
            if backend == "local":
                full_path = self.root_dir / real_path
                
                if not os.path.isdir(full_path):
                    raise ValueError(f"No es un directorio: {path}")
                
                result = []
                for item in os.listdir(full_path):
                    item_path = os.path.join(full_path, item)
                    is_dir = os.path.isdir(item_path)
                    
                    result.append({
                        "name": item,
                        "path": os.path.join(real_path, item),
                        "type": "directory" if is_dir else "file",
                        "size": 0 if is_dir else os.path.getsize(item_path),
                        "modified": os.path.getmtime(item_path)
                    })
                
                return result
            
            elif backend == "s3":
                if not self.s3_client:
                    self.initialize_aws_clients()
                
                bucket, prefix = real_path.split("/", 1)
                if not prefix.endswith("/"):
                    prefix += "/"
                
                # Listar objetos en S3
                response = self.s3_client.list_objects_v2(
                    Bucket=bucket,
                    Prefix=prefix,
                    Delimiter="/"
                )
                
                result = []
                
                # Añadir directorios
                for common_prefix in response.get("CommonPrefixes", []):
                    dir_name = os.path.basename(common_prefix["Prefix"].rstrip("/"))
                    result.append({
                        "name": dir_name,
                        "path": f"{bucket}/{common_prefix['Prefix']}",
                        "type": "directory",
                        "size": 0,
                        "modified": time.time()
                    })
                
                # Añadir archivos
                for content in response.get("Contents", []):
                    # Ignorar el prefijo actual
                    if content["Key"] == prefix:
                        continue
                    
                    file_name = os.path.basename(content["Key"])
                    result.append({
                        "name": file_name,
                        "path": f"{bucket}/{content['Key']}",
                        "type": "file",
                        "size": content["Size"],
                        "modified": content["LastModified"].timestamp()
                    })
                
                return result
            
            else:
                raise ValueError(f"Backend no soportado para listar directorio: {backend}")
        
        except Exception as e:
            logger.error(f"Error al listar directorio {path}: {e}")
            raise
    
    def get_metadata(self, path: str) -> Dict[str, Any]:
        """
        Obtiene metadatos de un archivo.
        
        Args:
            path: Ruta del archivo
            
        Returns:
            Diccionario con metadatos
        """
        backend, real_path = self.parse_path(path)
        
        # Verificar caché
        cache_key = f"{backend}:{real_path}"
        current_time = time.time()
        
        if cache_key in self.metadata_cache:
            cache_entry = self.metadata_cache[cache_key]
            if current_time - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["data"]
        
        try:
            if backend == "local":
                full_path = self.root_dir / real_path
                
                if not os.path.exists(full_path):
                    raise FileNotFoundError(f"Archivo no encontrado: {path}")
                
                is_dir = os.path.isdir(full_path)
                
                # Calcular hash para archivos
                file_hash = None
                if not is_dir:
                    with open(full_path, "rb") as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                
                metadata = {
                    "name": os.path.basename(real_path),
                    "path": real_path,
                    "type": "directory" if is_dir else "file",
                    "size": 0 if is_dir else os.path.getsize(full_path),
                    "created": os.path.getctime(full_path),
                    "modified": os.path.getmtime(full_path),
                    "accessed": os.path.getatime(full_path),
                    "hash": file_hash,
                    "mime_type": None if is_dir else mimetypes.guess_type(real_path)[0]
                }
                
                # Guardar en caché
                self.metadata_cache[cache_key] = {
                    "data": metadata,
                    "timestamp": current_time
                }
                
                return metadata
            
            elif backend == "s3":
                if not self.s3_client:
                    self.initialize_aws_clients()
                
                bucket, key = real_path.split("/", 1)
                
                # Verificar si es un directorio (prefijo)
                if key.endswith("/") or not key:
                    # Listar objetos para verificar si existe el prefijo
                    response = self.s3_client.list_objects_v2(
                        Bucket=bucket,
                        Prefix=key,
                        MaxKeys=1
                    )
                    
                    if "Contents" not in response:
                        raise FileNotFoundError(f"Directorio no encontrado: {path}")
                    
                    metadata = {
                        "name": os.path.basename(key.rstrip("/") or bucket),
                        "path": real_path,
                        "type": "directory",
                        "size": 0,
                        "created": None,
                        "modified": time.time(),
                        "accessed": None,
                        "hash": None,
                        "mime_type": None
                    }
                else:
                    # Obtener metadatos del objeto
                    try:
                        response = self.s3_client.head_object(
                            Bucket=bucket,
                            Key=key
                        )
                    except self.s3_client.exceptions.ClientError:
                        raise FileNotFoundError(f"Archivo no encontrado: {path}")
                    
                    metadata = {
                        "name": os.path.basename(key),
                        "path": real_path,
                        "type": "file",
                        "size": response["ContentLength"],
                        "created": None,
                        "modified": response["LastModified"].timestamp(),
                        "accessed": None,
                        "hash": response.get("ETag", "").strip('"'),
                        "mime_type": response.get("ContentType")
                    }
                
                # Guardar en caché
                self.metadata_cache[cache_key] = {
                    "data": metadata,
                    "timestamp": current_time
                }
                
                return metadata
            
            elif backend == "http":
                # Obtener metadatos mediante HEAD request
                response = requests.head(real_path)
                response.raise_for_status()
                
                metadata = {
                    "name": os.path.basename(urlparse(real_path).path),
                    "path": real_path,
                    "type": "file",
                    "size": int(response.headers.get("Content-Length", 0)),
                    "created": None,
                    "modified": None,
                    "accessed": None,
                    "hash": None,
                    "mime_type": response.headers.get("Content-Type")
                }
                
                # Guardar en caché
                self.metadata_cache[cache_key] = {
                    "data": metadata,
                    "timestamp": current_time
                }
                
                return metadata
            
            else:
                raise ValueError(f"Backend no soportado para metadatos: {backend}")
        
        except Exception as e:
            logger.error(f"Error al obtener metadatos de {path}: {e}")
            raise
