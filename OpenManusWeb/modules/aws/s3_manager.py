"""
Gestor de S3 para agent-isa.
Proporciona funcionalidades para interactuar con Amazon S3.
"""

import os
import logging
import boto3
import botocore
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, BinaryIO, Tuple

from ..core import PluginInterface, ConfigManager, EnvironmentManager

# Configurar logging
logger = logging.getLogger(__name__)

class S3Manager(PluginInterface):
    """
    Gestor de Amazon S3 para almacenamiento en la nube.
    
    Características:
    1. Subida y descarga de archivos
    2. Gestión de buckets y objetos
    3. Generación de URLs prefirmadas
    4. Sincronización de directorios
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager", "core.EnvironmentManager"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, env_manager: Optional[EnvironmentManager] = None):
        """
        Inicializa el gestor de S3.
        
        Args:
            config_manager: Gestor de configuración
            env_manager: Gestor de entornos
        """
        self.config_manager = config_manager or ConfigManager()
        self.env_manager = env_manager or EnvironmentManager()
        
        # Cargar configuración
        self.config = self.config_manager.get_config("aws")
        self.env_config = self.env_manager.get_config()
        
        # Inicializar cliente
        self.s3_client = None
        self.s3_resource = None
        
        # Configuración de S3
        self.default_bucket = self.env_config.get("aws", {}).get("s3", {}).get("bucket", "agent-isa")
        self.default_prefix = self.env_config.get("aws", {}).get("s3", {}).get("prefix", "")
        
        logger.info("Gestor de S3 inicializado")
    
    def initialize_client(self):
        """
        Inicializa el cliente de S3.
        
        Returns:
            True si se inicializó correctamente
        """
        try:
            # Determinar si usar perfil de instancia
            use_instance_profile = self.env_config.get("aws", {}).get("use_instance_profile", False)
            region = self.env_config.get("aws", {}).get("region", "us-east-1")
            
            # Crear cliente
            if use_instance_profile:
                # Usar perfil de instancia EC2
                self.s3_client = boto3.client("s3", region_name=region)
                self.s3_resource = boto3.resource("s3", region_name=region)
            else:
                # Usar credenciales configuradas
                self.s3_client = boto3.client(
                    "s3",
                    region_name=region,
                    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
                )
                self.s3_resource = boto3.resource(
                    "s3",
                    region_name=region,
                    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
                )
            
            logger.info("Cliente S3 inicializado")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar cliente S3: {e}")
            return False
    
    def upload_file(
        self,
        local_path: Union[str, Path],
        s3_key: Optional[str] = None,
        bucket: Optional[str] = None,
        extra_args: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Sube un archivo a S3.
        
        Args:
            local_path: Ruta local del archivo
            s3_key: Clave en S3 (None para usar el nombre del archivo)
            bucket: Nombre del bucket (None para usar el predeterminado)
            extra_args: Argumentos adicionales para la subida
            
        Returns:
            True si se subió correctamente
        """
        # Verificar cliente
        if not self.s3_client:
            if not self.initialize_client():
                return False
        
        try:
            # Convertir a Path
            local_path = Path(local_path)
            
            # Verificar que el archivo existe
            if not local_path.exists():
                logger.error(f"Archivo no encontrado: {local_path}")
                return False
            
            # Determinar bucket
            bucket_name = bucket or self.default_bucket
            
            # Determinar clave
            if not s3_key:
                s3_key = local_path.name
            
            # Añadir prefijo si existe
            if self.default_prefix:
                s3_key = f"{self.default_prefix}/{s3_key}"
            
            # Subir archivo
            self.s3_client.upload_file(
                str(local_path),
                bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Archivo subido: {local_path} -> s3://{bucket_name}/{s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error al subir archivo a S3: {e}")
            return False
    
    def download_file(
        self,
        s3_key: str,
        local_path: Union[str, Path],
        bucket: Optional[str] = None
    ) -> bool:
        """
        Descarga un archivo de S3.
        
        Args:
            s3_key: Clave en S3
            local_path: Ruta local donde guardar
            bucket: Nombre del bucket (None para usar el predeterminado)
            
        Returns:
            True si se descargó correctamente
        """
        # Verificar cliente
        if not self.s3_client:
            if not self.initialize_client():
                return False
        
        try:
            # Convertir a Path
            local_path = Path(local_path)
            
            # Crear directorio si no existe
            os.makedirs(local_path.parent, exist_ok=True)
            
            # Determinar bucket
            bucket_name = bucket or self.default_bucket
            
            # Añadir prefijo si existe y no está incluido
            if self.default_prefix and not s3_key.startswith(self.default_prefix):
                s3_key = f"{self.default_prefix}/{s3_key}"
            
            # Descargar archivo
            self.s3_client.download_file(
                bucket_name,
                s3_key,
                str(local_path)
            )
            
            logger.info(f"Archivo descargado: s3://{bucket_name}/{s3_key} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error al descargar archivo de S3: {e}")
            return False
    
    def list_objects(
        self,
        prefix: Optional[str] = None,
        bucket: Optional[str] = None,
        max_keys: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Lista objetos en un bucket.
        
        Args:
            prefix: Prefijo para filtrar objetos
            bucket: Nombre del bucket (None para usar el predeterminado)
            max_keys: Número máximo de objetos a listar
            
        Returns:
            Lista de objetos
        """
        # Verificar cliente
        if not self.s3_client:
            if not self.initialize_client():
                return []
        
        try:
            # Determinar bucket
            bucket_name = bucket or self.default_bucket
            
            # Determinar prefijo
            if prefix is None:
                prefix = self.default_prefix
            elif self.default_prefix and not prefix.startswith(self.default_prefix):
                prefix = f"{self.default_prefix}/{prefix}"
            
            # Listar objetos
            response = self.s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            # Procesar respuesta
            objects = []
            for obj in response.get("Contents", []):
                objects.append({
                    "key": obj["Key"],
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"],
                    "etag": obj["ETag"].strip('"'),
                    "storage_class": obj["StorageClass"]
                })
            
            return objects
            
        except Exception as e:
            logger.error(f"Error al listar objetos en S3: {e}")
            return []
    
    def delete_object(
        self,
        s3_key: str,
        bucket: Optional[str] = None
    ) -> bool:
        """
        Elimina un objeto de S3.
        
        Args:
            s3_key: Clave en S3
            bucket: Nombre del bucket (None para usar el predeterminado)
            
        Returns:
            True si se eliminó correctamente
        """
        # Verificar cliente
        if not self.s3_client:
            if not self.initialize_client():
                return False
        
        try:
            # Determinar bucket
            bucket_name = bucket or self.default_bucket
            
            # Añadir prefijo si existe y no está incluido
            if self.default_prefix and not s3_key.startswith(self.default_prefix):
                s3_key = f"{self.default_prefix}/{s3_key}"
            
            # Eliminar objeto
            self.s3_client.delete_object(
                Bucket=bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Objeto eliminado: s3://{bucket_name}/{s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error al eliminar objeto de S3: {e}")
            return False
    
    def generate_presigned_url(
        self,
        s3_key: str,
        bucket: Optional[str] = None,
        expiration: int = 3600,
        http_method: str = "GET"
    ) -> Optional[str]:
        """
        Genera una URL prefirmada para un objeto.
        
        Args:
            s3_key: Clave en S3
            bucket: Nombre del bucket (None para usar el predeterminado)
            expiration: Tiempo de expiración en segundos
            http_method: Método HTTP (GET, PUT)
            
        Returns:
            URL prefirmada o None si hay error
        """
        # Verificar cliente
        if not self.s3_client:
            if not self.initialize_client():
                return None
        
        try:
            # Determinar bucket
            bucket_name = bucket or self.default_bucket
            
            # Añadir prefijo si existe y no está incluido
            if self.default_prefix and not s3_key.startswith(self.default_prefix):
                s3_key = f"{self.default_prefix}/{s3_key}"
            
            # Generar URL
            url = self.s3_client.generate_presigned_url(
                ClientMethod="get_object" if http_method == "GET" else "put_object",
                Params={
                    "Bucket": bucket_name,
                    "Key": s3_key
                },
                ExpiresIn=expiration
            )
            
            return url
            
        except Exception as e:
            logger.error(f"Error al generar URL prefirmada: {e}")
            return None
    
    def sync_directory(
        self,
        local_dir: Union[str, Path],
        s3_prefix: Optional[str] = None,
        bucket: Optional[str] = None,
        delete: bool = False
    ) -> bool:
        """
        Sincroniza un directorio local con S3.
        
        Args:
            local_dir: Directorio local
            s3_prefix: Prefijo en S3 (None para usar el nombre del directorio)
            bucket: Nombre del bucket (None para usar el predeterminado)
            delete: Si debe eliminar archivos que no existen localmente
            
        Returns:
            True si se sincronizó correctamente
        """
        # Verificar cliente
        if not self.s3_client:
            if not self.initialize_client():
                return False
        
        try:
            # Convertir a Path
            local_dir = Path(local_dir)
            
            # Verificar que el directorio existe
            if not local_dir.is_dir():
                logger.error(f"Directorio no encontrado: {local_dir}")
                return False
            
            # Determinar bucket
            bucket_name = bucket or self.default_bucket
            
            # Determinar prefijo
            if not s3_prefix:
                s3_prefix = local_dir.name
            
            # Añadir prefijo global si existe
            if self.default_prefix:
                s3_prefix = f"{self.default_prefix}/{s3_prefix}"
            
            # Listar archivos locales
            local_files = []
            for root, _, files in os.walk(local_dir):
                for file in files:
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(local_dir)
                    local_files.append(str(rel_path))
            
            # Listar objetos en S3
            s3_objects = self.list_objects(s3_prefix, bucket_name)
            s3_keys = [obj["key"] for obj in s3_objects]
            
            # Subir archivos nuevos o modificados
            for file in local_files:
                s3_key = f"{s3_prefix}/{file}"
                local_path = local_dir / file
                
                # Verificar si el archivo existe en S3
                if s3_key in s3_keys:
                    # Verificar si el archivo ha sido modificado
                    s3_obj = next((obj for obj in s3_objects if obj["key"] == s3_key), None)
                    if s3_obj:
                        local_size = local_path.stat().st_size
                        local_mtime = local_path.stat().st_mtime
                        
                        # Si el tamaño es diferente o la fecha de modificación es más reciente, subir
                        if local_size != s3_obj["size"] or local_mtime > s3_obj["last_modified"].timestamp():
                            self.upload_file(local_path, s3_key, bucket_name)
                else:
                    # Archivo nuevo, subir
                    self.upload_file(local_path, s3_key, bucket_name)
            
            # Eliminar archivos que no existen localmente
            if delete:
                for obj in s3_objects:
                    s3_key = obj["key"]
                    if s3_key.startswith(s3_prefix + "/"):
                        rel_key = s3_key[len(s3_prefix) + 1:]
                        if rel_key not in local_files:
                            self.delete_object(s3_key, bucket_name)
            
            logger.info(f"Directorio sincronizado: {local_dir} -> s3://{bucket_name}/{s3_prefix}")
            return True
            
        except Exception as e:
            logger.error(f"Error al sincronizar directorio con S3: {e}")
            return False
