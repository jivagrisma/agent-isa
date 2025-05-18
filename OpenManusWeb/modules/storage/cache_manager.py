"""
Gestor de caché para agent-isa.
Proporciona un sistema de caché para almacenar datos temporales.
"""

import os
import json
import time
import logging
import hashlib
import pickle
import threading
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Iterator, Set
import zlib

from ..core import PluginInterface, ConfigManager
from .virtual_fs import VirtualFileSystem

# Configurar logging
logger = logging.getLogger(__name__)

class CacheManager(PluginInterface):
    """
    Sistema de caché para almacenamiento temporal de datos.
    
    Características:
    1. Almacenamiento en memoria y disco
    2. Políticas de expiración y limpieza
    3. Compresión y optimización
    4. Estadísticas de uso
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager", "storage.VirtualFileSystem"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, virtual_fs: Optional[VirtualFileSystem] = None):
        """
        Inicializa el gestor de caché.
        
        Args:
            config_manager: Gestor de configuración
            virtual_fs: Sistema de archivos virtual
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("storage")
        
        # Inicializar sistema de archivos virtual
        self.virtual_fs = virtual_fs or VirtualFileSystem(self.config_manager)
        
        # Directorio para caché en disco
        self.cache_dir = Path(self.config.get("cache.directory", "cache"))
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Caché en memoria
        self.memory_cache = {}
        
        # Estadísticas
        self.stats = {
            "hits": 0,
            "misses": 0,
            "memory_size": 0,
            "disk_size": 0,
            "items_count": 0
        }
        
        # Configuración
        self.memory_limit = self.config.get("cache.memory_limit", 100 * 1024 * 1024)  # 100 MB por defecto
        self.disk_limit = self.config.get("cache.disk_limit", 1024 * 1024 * 1024)  # 1 GB por defecto
        self.default_ttl = self.config.get("cache.default_ttl", 3600)  # 1 hora por defecto
        self.compression_threshold = self.config.get("cache.compression_threshold", 1024)  # 1 KB por defecto
        self.compression_level = self.config.get("cache.compression_level", 6)  # Nivel de compresión (0-9)
        
        # Iniciar limpieza periódica
        self._start_cleanup_thread()
        
        logger.info("Gestor de caché inicializado")
    
    def _start_cleanup_thread(self):
        """
        Inicia un hilo para limpieza periódica de la caché.
        """
        cleanup_interval = self.config.get("cache.cleanup_interval", 300)  # 5 minutos por defecto
        
        def cleanup_task():
            while True:
                try:
                    self.cleanup()
                    time.sleep(cleanup_interval)
                except Exception as e:
                    logger.error(f"Error en limpieza periódica: {e}")
                    time.sleep(cleanup_interval)
        
        # Iniciar hilo como daemon
        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
    
    def _generate_key(self, key: str, namespace: Optional[str] = None) -> str:
        """
        Genera una clave única para la caché.
        
        Args:
            key: Clave original
            namespace: Espacio de nombres
            
        Returns:
            Clave única
        """
        if namespace:
            full_key = f"{namespace}:{key}"
        else:
            full_key = key
        
        # Generar hash para claves largas
        if len(full_key) > 64:
            return hashlib.md5(full_key.encode()).hexdigest()
        
        return full_key
    
    def _get_disk_path(self, key: str) -> Path:
        """
        Obtiene la ruta en disco para una clave.
        
        Args:
            key: Clave de caché
            
        Returns:
            Ruta en disco
        """
        # Usar los primeros caracteres para subdirectorios
        if len(key) >= 4:
            subdir = key[:2]
            path = self.cache_dir / subdir / f"{key}.cache"
        else:
            path = self.cache_dir / f"{key}.cache"
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        return path
    
    def _compress_data(self, data: bytes) -> Tuple[bytes, bool]:
        """
        Comprime datos si superan el umbral.
        
        Args:
            data: Datos a comprimir
            
        Returns:
            Tupla con datos (posiblemente comprimidos) y flag de compresión
        """
        if len(data) >= self.compression_threshold:
            compressed = zlib.compress(data, self.compression_level)
            # Solo usar compresión si reduce el tamaño
            if len(compressed) < len(data):
                return compressed, True
        
        return data, False
    
    def _decompress_data(self, data: bytes, compressed: bool) -> bytes:
        """
        Descomprime datos si están comprimidos.
        
        Args:
            data: Datos a descomprimir
            compressed: Si los datos están comprimidos
            
        Returns:
            Datos descomprimidos
        """
        if compressed:
            return zlib.decompress(data)
        return data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, namespace: Optional[str] = None, 
           memory_only: bool = False, disk_only: bool = False) -> bool:
        """
        Guarda un valor en la caché.
        
        Args:
            key: Clave de caché
            value: Valor a guardar
            ttl: Tiempo de vida en segundos (None para usar el predeterminado)
            namespace: Espacio de nombres
            memory_only: Si debe guardar solo en memoria
            disk_only: Si debe guardar solo en disco
            
        Returns:
            True si se guardó correctamente
        """
        try:
            # Generar clave única
            cache_key = self._generate_key(key, namespace)
            
            # Determinar TTL
            if ttl is None:
                ttl = self.default_ttl
            
            # Calcular tiempo de expiración
            expiry = time.time() + ttl if ttl > 0 else None
            
            # Serializar valor
            serialized = pickle.dumps(value)
            
            # Comprimir si es necesario
            compressed_data, is_compressed = self._compress_data(serialized)
            
            # Crear entrada de caché
            entry = {
                "value": compressed_data,
                "expiry": expiry,
                "compressed": is_compressed,
                "size": len(serialized),
                "created": time.time(),
                "last_access": time.time(),
                "access_count": 0
            }
            
            # Guardar en memoria si no es disk_only
            if not disk_only:
                self.memory_cache[cache_key] = entry
                self.stats["memory_size"] += len(compressed_data)
            
            # Guardar en disco si no es memory_only
            if not memory_only:
                disk_path = self._get_disk_path(cache_key)
                
                # Guardar en disco
                with open(disk_path, "wb") as f:
                    pickle.dump(entry, f)
                
                self.stats["disk_size"] += os.path.getsize(disk_path)
            
            # Actualizar estadísticas
            self.stats["items_count"] += 1
            
            # Verificar límites y limpiar si es necesario
            if self.stats["memory_size"] > self.memory_limit or self.stats["disk_size"] > self.disk_limit:
                self.cleanup()
            
            return True
        
        except Exception as e:
            logger.error(f"Error al guardar en caché '{key}': {e}")
            return False
    
    def get(self, key: str, default: Any = None, namespace: Optional[str] = None, 
           update_stats: bool = True) -> Any:
        """
        Obtiene un valor de la caché.
        
        Args:
            key: Clave de caché
            default: Valor por defecto si no existe
            namespace: Espacio de nombres
            update_stats: Si debe actualizar estadísticas
            
        Returns:
            Valor almacenado o default
        """
        try:
            # Generar clave única
            cache_key = self._generate_key(key, namespace)
            
            # Verificar en memoria
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                
                # Verificar expiración
                if entry["expiry"] is not None and time.time() > entry["expiry"]:
                    # Expirado, eliminar y retornar default
                    del self.memory_cache[cache_key]
                    self.stats["memory_size"] -= len(entry["value"])
                    self.stats["items_count"] -= 1
                    
                    if update_stats:
                        self.stats["misses"] += 1
                    
                    return default
                
                # Actualizar estadísticas de acceso
                if update_stats:
                    entry["last_access"] = time.time()
                    entry["access_count"] += 1
                    self.stats["hits"] += 1
                
                # Deserializar valor
                value_data = self._decompress_data(entry["value"], entry["compressed"])
                return pickle.loads(value_data)
            
            # Verificar en disco
            disk_path = self._get_disk_path(cache_key)
            if os.path.exists(disk_path):
                try:
                    with open(disk_path, "rb") as f:
                        entry = pickle.load(f)
                    
                    # Verificar expiración
                    if entry["expiry"] is not None and time.time() > entry["expiry"]:
                        # Expirado, eliminar y retornar default
                        os.remove(disk_path)
                        self.stats["disk_size"] -= os.path.getsize(disk_path)
                        self.stats["items_count"] -= 1
                        
                        if update_stats:
                            self.stats["misses"] += 1
                        
                        return default
                    
                    # Actualizar estadísticas de acceso
                    if update_stats:
                        entry["last_access"] = time.time()
                        entry["access_count"] += 1
                        self.stats["hits"] += 1
                    
                    # Guardar en memoria para acceso más rápido
                    self.memory_cache[cache_key] = entry
                    self.stats["memory_size"] += len(entry["value"])
                    
                    # Deserializar valor
                    value_data = self._decompress_data(entry["value"], entry["compressed"])
                    return pickle.loads(value_data)
                
                except Exception as e:
                    logger.error(f"Error al leer caché de disco '{key}': {e}")
                    # Eliminar archivo corrupto
                    os.remove(disk_path)
            
            # No encontrado
            if update_stats:
                self.stats["misses"] += 1
            
            return default
        
        except Exception as e:
            logger.error(f"Error al obtener de caché '{key}': {e}")
            return default
    
    def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """
        Elimina un valor de la caché.
        
        Args:
            key: Clave de caché
            namespace: Espacio de nombres
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            # Generar clave única
            cache_key = self._generate_key(key, namespace)
            
            # Eliminar de memoria
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                self.stats["memory_size"] -= len(entry["value"])
                self.stats["items_count"] -= 1
                del self.memory_cache[cache_key]
            
            # Eliminar de disco
            disk_path = self._get_disk_path(cache_key)
            if os.path.exists(disk_path):
                self.stats["disk_size"] -= os.path.getsize(disk_path)
                os.remove(disk_path)
            
            return True
        
        except Exception as e:
            logger.error(f"Error al eliminar de caché '{key}': {e}")
            return False
    
    def clear(self, namespace: Optional[str] = None) -> bool:
        """
        Limpia toda la caché o un espacio de nombres específico.
        
        Args:
            namespace: Espacio de nombres a limpiar (None para todo)
            
        Returns:
            True si se limpió correctamente
        """
        try:
            # Limpiar memoria
            if namespace:
                # Limpiar solo el espacio de nombres
                prefix = f"{namespace}:"
                keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(prefix)]
                
                for key in keys_to_delete:
                    entry = self.memory_cache[key]
                    self.stats["memory_size"] -= len(entry["value"])
                    self.stats["items_count"] -= 1
                    del self.memory_cache[key]
            else:
                # Limpiar toda la memoria
                self.memory_cache = {}
                self.stats["memory_size"] = 0
                self.stats["items_count"] = 0
            
            # Limpiar disco
            if namespace:
                # Buscar archivos que coincidan con el espacio de nombres
                for root, _, files in os.walk(self.cache_dir):
                    for file in files:
                        if file.endswith(".cache"):
                            file_path = os.path.join(root, file)
                            try:
                                with open(file_path, "rb") as f:
                                    entry = pickle.load(f)
                                
                                # Verificar si pertenece al namespace
                                if "namespace" in entry and entry["namespace"] == namespace:
                                    self.stats["disk_size"] -= os.path.getsize(file_path)
                                    os.remove(file_path)
                            except Exception:
                                # Eliminar archivos corruptos
                                os.remove(file_path)
            else:
                # Limpiar todo el directorio
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
                self.stats["disk_size"] = 0
            
            return True
        
        except Exception as e:
            logger.error(f"Error al limpiar caché: {e}")
            return False
    
    def cleanup(self) -> int:
        """
        Limpia entradas expiradas y reduce el tamaño de la caché.
        
        Returns:
            Número de entradas eliminadas
        """
        try:
            current_time = time.time()
            removed_count = 0
            
            # Limpiar memoria
            keys_to_delete = []
            
            # Identificar entradas expiradas
            for key, entry in self.memory_cache.items():
                if entry["expiry"] is not None and current_time > entry["expiry"]:
                    keys_to_delete.append(key)
            
            # Eliminar entradas expiradas
            for key in keys_to_delete:
                entry = self.memory_cache[key]
                self.stats["memory_size"] -= len(entry["value"])
                self.stats["items_count"] -= 1
                del self.memory_cache[key]
                removed_count += 1
            
            # Si aún estamos por encima del límite, eliminar entradas menos usadas
            if self.stats["memory_size"] > self.memory_limit:
                # Ordenar por último acceso (más antiguo primero)
                sorted_entries = sorted(
                    self.memory_cache.items(),
                    key=lambda x: (x[1]["last_access"], -x[1]["access_count"])
                )
                
                # Eliminar hasta estar por debajo del límite
                for key, entry in sorted_entries:
                    if self.stats["memory_size"] <= self.memory_limit * 0.8:  # 80% del límite
                        break
                    
                    self.stats["memory_size"] -= len(entry["value"])
                    self.stats["items_count"] -= 1
                    del self.memory_cache[key]
                    removed_count += 1
            
            # Limpiar disco
            for root, _, files in os.walk(self.cache_dir):
                for file in files:
                    if file.endswith(".cache"):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, "rb") as f:
                                entry = pickle.load(f)
                            
                            # Verificar expiración
                            if entry["expiry"] is not None and current_time > entry["expiry"]:
                                self.stats["disk_size"] -= os.path.getsize(file_path)
                                os.remove(file_path)
                                removed_count += 1
                        except Exception:
                            # Eliminar archivos corruptos
                            os.remove(file_path)
                            removed_count += 1
            
            # Si aún estamos por encima del límite de disco, eliminar archivos más antiguos
            if self.stats["disk_size"] > self.disk_limit:
                # Obtener todos los archivos con su tiempo de modificación
                files_info = []
                for root, _, files in os.walk(self.cache_dir):
                    for file in files:
                        if file.endswith(".cache"):
                            file_path = os.path.join(root, file)
                            mtime = os.path.getmtime(file_path)
                            size = os.path.getsize(file_path)
                            files_info.append((file_path, mtime, size))
                
                # Ordenar por tiempo de modificación (más antiguo primero)
                files_info.sort(key=lambda x: x[1])
                
                # Eliminar hasta estar por debajo del límite
                for file_path, _, size in files_info:
                    if self.stats["disk_size"] <= self.disk_limit * 0.8:  # 80% del límite
                        break
                    
                    self.stats["disk_size"] -= size
                    os.remove(file_path)
                    removed_count += 1
            
            return removed_count
        
        except Exception as e:
            logger.error(f"Error en limpieza de caché: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de la caché.
        
        Returns:
            Diccionario con estadísticas
        """
        # Actualizar estadísticas de disco
        total_disk_size = 0
        for root, _, files in os.walk(self.cache_dir):
            for file in files:
                if file.endswith(".cache"):
                    file_path = os.path.join(root, file)
                    total_disk_size += os.path.getsize(file_path)
        
        self.stats["disk_size"] = total_disk_size
        
        # Calcular estadísticas adicionales
        hit_rate = 0
        if (self.stats["hits"] + self.stats["misses"]) > 0:
            hit_rate = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
        
        # Devolver estadísticas completas
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "memory_usage_percent": (self.stats["memory_size"] / self.memory_limit) * 100 if self.memory_limit > 0 else 0,
            "disk_usage_percent": (self.stats["disk_size"] / self.disk_limit) * 100 if self.disk_limit > 0 else 0,
            "memory_limit": self.memory_limit,
            "disk_limit": self.disk_limit,
            "memory_items": len(self.memory_cache)
        }
