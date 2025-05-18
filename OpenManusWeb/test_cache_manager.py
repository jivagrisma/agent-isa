#!/usr/bin/env python3
"""
Script de prueba para el gestor de caché.
"""

import argparse
import logging
import sys
import os
import json
import time
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
from modules.storage import VirtualFileSystem, CacheManager

def test_set_get(cache: CacheManager, key: str, value: Any, ttl: Optional[int] = None, namespace: Optional[str] = None):
    """
    Prueba la escritura y lectura de un valor en caché.
    
    Args:
        cache: Gestor de caché
        key: Clave de caché
        value: Valor a guardar
        ttl: Tiempo de vida en segundos
        namespace: Espacio de nombres
    """
    try:
        # Construir mensaje
        msg = f"\n💾 Guardando en caché: '{key}'"
        if namespace:
            msg += f" (namespace: '{namespace}')"
        if ttl:
            msg += f" (TTL: {ttl}s)"
        print(msg)
        
        # Guardar en caché
        start_time = time.time()
        success = cache.set(key, value, ttl=ttl, namespace=namespace)
        set_time = time.time() - start_time
        
        if success:
            print(f"✅ Valor guardado correctamente ({set_time:.6f}s)")
        else:
            print(f"❌ Error al guardar valor")
            return False
        
        # Leer de caché
        print(f"\n📖 Leyendo de caché: '{key}'")
        start_time = time.time()
        result = cache.get(key, namespace=namespace)
        get_time = time.time() - start_time
        
        if result is not None:
            print(f"✅ Valor leído correctamente ({get_time:.6f}s):")
            
            # Mostrar valor
            if isinstance(result, (dict, list)):
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(result)
            
            return True
        else:
            print(f"❌ Valor no encontrado")
            return False
    
    except Exception as e:
        logger.error(f"Error en operación de caché: {e}")
        print(f"❌ Error: {e}")
        return False

def test_expiry(cache: CacheManager, key: str, value: Any, ttl: int):
    """
    Prueba la expiración de un valor en caché.
    
    Args:
        cache: Gestor de caché
        key: Clave de caché
        value: Valor a guardar
        ttl: Tiempo de vida en segundos
    """
    try:
        print(f"\n⏱️ Probando expiración con TTL={ttl}s...")
        
        # Guardar en caché
        print(f"Guardando valor...")
        cache.set(key, value, ttl=ttl)
        
        # Leer inmediatamente
        print(f"Leyendo valor inmediatamente...")
        result1 = cache.get(key)
        
        if result1 is not None:
            print(f"✅ Valor leído correctamente")
        else:
            print(f"❌ Valor no encontrado")
            return False
        
        # Esperar a que expire
        wait_time = ttl + 1
        print(f"Esperando {wait_time}s para que expire...")
        time.sleep(wait_time)
        
        # Leer después de expirar
        print(f"Leyendo valor después de expirar...")
        result2 = cache.get(key)
        
        if result2 is None:
            print(f"✅ Valor expirado correctamente")
            return True
        else:
            print(f"❌ Error: valor no expiró")
            return False
    
    except Exception as e:
        logger.error(f"Error en prueba de expiración: {e}")
        print(f"❌ Error: {e}")
        return False

def test_delete(cache: CacheManager, key: str, value: Any, namespace: Optional[str] = None):
    """
    Prueba la eliminación de un valor en caché.
    
    Args:
        cache: Gestor de caché
        key: Clave de caché
        value: Valor a guardar
        namespace: Espacio de nombres
    """
    try:
        print(f"\n🗑️ Probando eliminación...")
        
        # Guardar en caché
        print(f"Guardando valor...")
        cache.set(key, value, namespace=namespace)
        
        # Verificar que existe
        result1 = cache.get(key, namespace=namespace)
        if result1 is None:
            print(f"❌ Error: valor no guardado")
            return False
        
        # Eliminar
        print(f"Eliminando valor...")
        success = cache.delete(key, namespace=namespace)
        
        if success:
            print(f"✅ Valor eliminado correctamente")
        else:
            print(f"❌ Error al eliminar valor")
            return False
        
        # Verificar que no existe
        result2 = cache.get(key, namespace=namespace)
        
        if result2 is None:
            print(f"✅ Valor eliminado correctamente")
            return True
        else:
            print(f"❌ Error: valor no se eliminó")
            return False
    
    except Exception as e:
        logger.error(f"Error en prueba de eliminación: {e}")
        print(f"❌ Error: {e}")
        return False

def test_clear(cache: CacheManager, namespace: Optional[str] = None):
    """
    Prueba la limpieza de la caché.
    
    Args:
        cache: Gestor de caché
        namespace: Espacio de nombres a limpiar
    """
    try:
        # Construir mensaje
        msg = f"\n🧹 Probando limpieza"
        if namespace:
            msg += f" del namespace '{namespace}'"
        print(msg)
        
        # Guardar varios valores
        print(f"Guardando valores...")
        
        # Valores en el namespace a limpiar
        for i in range(5):
            key = f"test_clear_{i}"
            cache.set(key, f"Valor {i}", namespace=namespace)
        
        # Valores en otro namespace
        other_namespace = "other" if namespace else "test"
        for i in range(3):
            key = f"test_other_{i}"
            cache.set(key, f"Otro valor {i}", namespace=other_namespace)
        
        # Limpiar
        print(f"Limpiando caché...")
        success = cache.clear(namespace=namespace)
        
        if success:
            print(f"✅ Caché limpiada correctamente")
        else:
            print(f"❌ Error al limpiar caché")
            return False
        
        # Verificar que los valores del namespace limpiado no existen
        all_cleared = True
        for i in range(5):
            key = f"test_clear_{i}"
            result = cache.get(key, namespace=namespace)
            if result is not None:
                print(f"❌ Error: valor '{key}' no se eliminó")
                all_cleared = False
        
        # Verificar que los valores del otro namespace siguen existiendo
        all_preserved = True
        for i in range(3):
            key = f"test_other_{i}"
            result = cache.get(key, namespace=other_namespace)
            if result is None:
                print(f"❌ Error: valor '{key}' se eliminó incorrectamente")
                all_preserved = False
        
        if all_cleared and all_preserved:
            print(f"✅ Limpieza selectiva funcionó correctamente")
            return True
        else:
            return False
    
    except Exception as e:
        logger.error(f"Error en prueba de limpieza: {e}")
        print(f"❌ Error: {e}")
        return False

def test_stats(cache: CacheManager):
    """
    Prueba la obtención de estadísticas de la caché.
    
    Args:
        cache: Gestor de caché
    """
    try:
        print(f"\n📊 Obteniendo estadísticas de caché...")
        
        # Obtener estadísticas
        stats = cache.get_stats()
        
        # Mostrar estadísticas
        print(f"✅ Estadísticas obtenidas:")
        print(f"Hits: {stats['hits']}")
        print(f"Misses: {stats['misses']}")
        print(f"Hit rate: {stats['hit_rate']:.2%}")
        print(f"Elementos en memoria: {stats['memory_items']}")
        print(f"Elementos totales: {stats['items_count']}")
        print(f"Tamaño en memoria: {stats['memory_size']} bytes ({stats['memory_usage_percent']:.2f}%)")
        print(f"Tamaño en disco: {stats['disk_size']} bytes ({stats['disk_usage_percent']:.2f}%)")
        
        return stats
    
    except Exception as e:
        logger.error(f"Error en obtención de estadísticas: {e}")
        print(f"❌ Error: {e}")
        return None

def test_performance(cache: CacheManager, iterations: int = 1000):
    """
    Prueba el rendimiento de la caché.
    
    Args:
        cache: Gestor de caché
        iterations: Número de iteraciones
    """
    try:
        print(f"\n⚡ Probando rendimiento con {iterations} iteraciones...")
        
        # Datos de prueba
        test_data = {"value": "test", "number": 123, "list": [1, 2, 3]}
        
        # Medir tiempo de escritura
        print(f"Midiendo tiempo de escritura...")
        start_time = time.time()
        
        for i in range(iterations):
            key = f"perf_test_{i}"
            cache.set(key, test_data)
        
        write_time = time.time() - start_time
        write_ops = iterations / write_time
        
        print(f"✅ Escritura: {write_time:.3f}s ({write_ops:.2f} ops/s)")
        
        # Medir tiempo de lectura (hit)
        print(f"Midiendo tiempo de lectura (hit)...")
        start_time = time.time()
        
        for i in range(iterations):
            key = f"perf_test_{i}"
            cache.get(key)
        
        read_hit_time = time.time() - start_time
        read_hit_ops = iterations / read_hit_time
        
        print(f"✅ Lectura (hit): {read_hit_time:.3f}s ({read_hit_ops:.2f} ops/s)")
        
        # Medir tiempo de lectura (miss)
        print(f"Midiendo tiempo de lectura (miss)...")
        start_time = time.time()
        
        for i in range(iterations):
            key = f"nonexistent_key_{i}"
            cache.get(key)
        
        read_miss_time = time.time() - start_time
        read_miss_ops = iterations / read_miss_time
        
        print(f"✅ Lectura (miss): {read_miss_time:.3f}s ({read_miss_ops:.2f} ops/s)")
        
        # Medir tiempo de eliminación
        print(f"Midiendo tiempo de eliminación...")
        start_time = time.time()
        
        for i in range(iterations):
            key = f"perf_test_{i}"
            cache.delete(key)
        
        delete_time = time.time() - start_time
        delete_ops = iterations / delete_time
        
        print(f"✅ Eliminación: {delete_time:.3f}s ({delete_ops:.2f} ops/s)")
        
        # Resumen
        print(f"\nResumen de rendimiento:")
        print(f"Escritura: {write_ops:.2f} ops/s")
        print(f"Lectura (hit): {read_hit_ops:.2f} ops/s")
        print(f"Lectura (miss): {read_miss_ops:.2f} ops/s")
        print(f"Eliminación: {delete_ops:.2f} ops/s")
        
        return {
            "write_ops": write_ops,
            "read_hit_ops": read_hit_ops,
            "read_miss_ops": read_miss_ops,
            "delete_ops": delete_ops
        }
    
    except Exception as e:
        logger.error(f"Error en prueba de rendimiento: {e}")
        print(f"❌ Error: {e}")
        return None

def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Prueba del gestor de caché")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: set
    set_parser = subparsers.add_parser("set", help="Guardar valor en caché")
    set_parser.add_argument("key", help="Clave de caché")
    set_parser.add_argument("value", help="Valor a guardar")
    set_parser.add_argument("--ttl", type=int, help="Tiempo de vida en segundos")
    set_parser.add_argument("--namespace", help="Espacio de nombres")
    
    # Comando: get
    get_parser = subparsers.add_parser("get", help="Leer valor de caché")
    get_parser.add_argument("key", help="Clave de caché")
    get_parser.add_argument("--namespace", help="Espacio de nombres")
    
    # Comando: delete
    delete_parser = subparsers.add_parser("delete", help="Eliminar valor de caché")
    delete_parser.add_argument("key", help="Clave de caché")
    delete_parser.add_argument("--namespace", help="Espacio de nombres")
    
    # Comando: clear
    clear_parser = subparsers.add_parser("clear", help="Limpiar caché")
    clear_parser.add_argument("--namespace", help="Espacio de nombres a limpiar")
    
    # Comando: stats
    stats_parser = subparsers.add_parser("stats", help="Obtener estadísticas")
    
    # Comando: performance
    perf_parser = subparsers.add_parser("performance", help="Probar rendimiento")
    perf_parser.add_argument("--iterations", type=int, default=1000, help="Número de iteraciones")
    
    # Comando: test
    test_parser = subparsers.add_parser("test", help="Ejecutar prueba completa")
    
    args = parser.parse_args()
    
    # Inicializar sistemas
    config_manager = ConfigManager()
    virtual_fs = VirtualFileSystem(config_manager)
    cache = CacheManager(config_manager, virtual_fs)
    
    if args.command == "set":
        # Intentar convertir valor a JSON
        try:
            value = json.loads(args.value)
        except json.JSONDecodeError:
            value = args.value
        
        test_set_get(cache, args.key, value, args.ttl, args.namespace)
    
    elif args.command == "get":
        result = cache.get(args.key, namespace=args.namespace)
        
        if result is not None:
            print(f"✅ Valor encontrado:")
            if isinstance(result, (dict, list)):
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(result)
        else:
            print(f"❌ Valor no encontrado")
    
    elif args.command == "delete":
        success = cache.delete(args.key, namespace=args.namespace)
        
        if success:
            print(f"✅ Valor eliminado correctamente")
        else:
            print(f"❌ Error al eliminar valor")
    
    elif args.command == "clear":
        success = cache.clear(namespace=args.namespace)
        
        if success:
            print(f"✅ Caché limpiada correctamente")
        else:
            print(f"❌ Error al limpiar caché")
    
    elif args.command == "stats":
        test_stats(cache)
    
    elif args.command == "performance":
        test_performance(cache, args.iterations)
    
    elif args.command == "test":
        # Ejecutar prueba completa
        
        # Prueba básica de set/get
        test_set_get(cache, "test_key", "Valor de prueba")
        
        # Prueba con valor complejo
        complex_value = {
            "nombre": "Prueba",
            "valores": [1, 2, 3, 4, 5],
            "objeto": {
                "clave1": "valor1",
                "clave2": "valor2"
            }
        }
        test_set_get(cache, "test_complex", complex_value)
        
        # Prueba con namespace
        test_set_get(cache, "test_namespace", "Valor en namespace", namespace="test")
        
        # Prueba de expiración
        test_expiry(cache, "test_expiry", "Valor que expira", ttl=2)
        
        # Prueba de eliminación
        test_delete(cache, "test_delete", "Valor a eliminar")
        
        # Prueba de limpieza
        test_clear(cache, namespace="test_clear")
        
        # Prueba de estadísticas
        test_stats(cache)
        
        # Prueba de rendimiento (pocas iteraciones para que sea rápido)
        test_performance(cache, iterations=100)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
