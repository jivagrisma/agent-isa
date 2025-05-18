# Módulo de Almacenamiento para Agent-ISA

## Descripción

El módulo de almacenamiento proporciona capacidades avanzadas para la gestión de archivos y datos estructurados. Está diseñado para ofrecer una interfaz unificada para acceder a diferentes sistemas de almacenamiento y formatos de datos.

## Componentes Principales

### VirtualFileSystem

Sistema de archivos virtual con soporte para diferentes backends de almacenamiento.

**Características:**
- Interfaz unificada para acceso a archivos locales y remotos
- Operaciones básicas de archivos (crear, leer, escribir, eliminar)
- Soporte para diferentes sistemas de almacenamiento (local, S3, etc.)
- Capacidades de sincronización y respaldo

**Uso básico:**
```python
from modules.core import ConfigManager
from modules.storage import VirtualFileSystem

# Inicializar
config_manager = ConfigManager()
fs = VirtualFileSystem(config_manager)

# Escribir archivo
fs.write_file("datos/archivo.txt", "Contenido del archivo")

# Leer archivo
content = fs.read_file("datos/archivo.txt")
print(content)

# Listar directorio
items = fs.list_directory("datos")
for item in items:
    print(f"{item['name']} ({item['type']})")

# Obtener metadatos
metadata = fs.get_metadata("datos/archivo.txt")
print(f"Tamaño: {metadata['size']} bytes")
print(f"Modificado: {metadata['modified']}")

# Eliminar archivo
fs.delete_file("datos/archivo.txt")
```

### StructuredStorage

Sistema de almacenamiento estructurado con soporte para diferentes formatos.

**Características:**
- Interfaz para almacenamiento de datos estructurados
- Soporte para diferentes formatos (JSON, CSV, SQLite, etc.)
- Capacidades de consulta y filtrado
- Indexación y búsqueda

**Uso básico:**
```python
from modules.core import ConfigManager
from modules.storage import VirtualFileSystem, StructuredStorage

# Inicializar
config_manager = ConfigManager()
virtual_fs = VirtualFileSystem(config_manager)
storage = StructuredStorage(config_manager, virtual_fs)

# Guardar datos en JSON
data = {"nombre": "Ejemplo", "valores": [1, 2, 3]}
storage.save_json(data, "datos/ejemplo.json", pretty=True)

# Cargar datos desde JSON
loaded_data = storage.load_json("datos/ejemplo.json")
print(loaded_data)

# Crear tabla SQLite
schema = {
    "id": "INTEGER",
    "nombre": "TEXT",
    "edad": "INTEGER"
}
storage.create_table("mi_db", "usuarios", schema, primary_key="id")

# Insertar datos
usuarios = [
    {"id": 1, "nombre": "Juan", "edad": 30},
    {"id": 2, "nombre": "María", "edad": 25}
]
storage.insert_data("mi_db", "usuarios", usuarios)

# Consultar datos
results = storage.query_data("mi_db", "usuarios", conditions={"edad": 30})
print(results)
```

### CacheManager

Sistema de caché para almacenamiento temporal de datos.

**Características:**
- Almacenamiento en memoria y disco
- Políticas de expiración y limpieza
- Compresión y optimización
- Estadísticas de uso

**Uso básico:**
```python
from modules.core import ConfigManager
from modules.storage import VirtualFileSystem, CacheManager

# Inicializar
config_manager = ConfigManager()
virtual_fs = VirtualFileSystem(config_manager)
cache = CacheManager(config_manager, virtual_fs)

# Guardar en caché
cache.set("mi_clave", "Valor de ejemplo", ttl=3600)  # TTL en segundos

# Guardar en caché con namespace
cache.set("usuario", {"id": 1, "nombre": "Juan"}, namespace="usuarios")

# Leer de caché
value = cache.get("mi_clave")
print(value)

# Leer de caché con namespace
user = cache.get("usuario", namespace="usuarios")
print(user)

# Eliminar de caché
cache.delete("mi_clave")

# Limpiar namespace
cache.clear(namespace="usuarios")

# Obtener estadísticas
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

## Configuración

El módulo utiliza el sistema de configuración modular de agent-isa. La configuración se encuentra en `OpenManusWeb/config/storage.toml`.

### Opciones de Configuración

```toml
[general]
enabled = true

[local]
root_directory = "storage"
create_if_missing = true
permissions = 0o755

[aws]
region = "us-east-1"
use_s3 = false
s3_bucket = ""
s3_prefix = "agent-isa"

[structured]
default_format = "json"
db_directory = "databases"
enable_indexing = true
auto_backup = true
backup_interval = 86400  # 24 horas

[cache]
directory = "cache"
memory_limit = 104857600  # 100 MB
disk_limit = 1073741824  # 1 GB
default_ttl = 3600  # 1 hora
cleanup_interval = 300  # 5 minutos
compression_threshold = 1024  # 1 KB
compression_level = 6  # Nivel de compresión (0-9)
```

## Sistema de Archivos Virtual

El sistema de archivos virtual proporciona una interfaz unificada para acceder a diferentes sistemas de almacenamiento.

### Backends Soportados

- **local**: Sistema de archivos local
- **s3**: Amazon S3
- **http**: Recursos web (solo lectura)

### Formato de Rutas

- **Local**: `path/to/file.txt`
- **S3**: `s3://bucket-name/path/to/file.txt`
- **HTTP**: `https://example.com/path/to/file.txt`
- **Personalizado**: `backend:path/to/file.txt`

### Operaciones Principales

- **read_file**: Lee un archivo
- **write_file**: Escribe un archivo
- **delete_file**: Elimina un archivo
- **list_directory**: Lista el contenido de un directorio
- **get_metadata**: Obtiene metadatos de un archivo

## Almacenamiento Estructurado

El almacenamiento estructurado proporciona una interfaz para almacenar y consultar datos estructurados en diferentes formatos.

### Formatos Soportados

- **JSON**: Para datos jerárquicos
- **CSV**: Para datos tabulares
- **SQLite**: Para bases de datos relacionales
- **Pickle**: Para serialización de objetos Python
- **DataFrame**: Para datos tabulares con pandas

### Operaciones Principales

- **save_json/load_json**: Guarda/carga datos en formato JSON
- **save_csv/load_csv**: Guarda/carga datos en formato CSV
- **create_table**: Crea una tabla en SQLite
- **insert_data**: Inserta datos en una tabla SQLite
- **query_data**: Consulta datos de una tabla SQLite
- **execute_query**: Ejecuta una consulta SQL personalizada
- **create_index**: Crea un índice en memoria para búsqueda rápida
- **search_index**: Busca un elemento en un índice
- **save_dataframe/load_dataframe**: Guarda/carga un DataFrame de pandas

## Sistema de Caché

El sistema de caché proporciona un mecanismo para almacenar temporalmente datos de acceso frecuente.

### Características

- **Almacenamiento en memoria y disco**: Para equilibrar velocidad y persistencia
- **Políticas de expiración**: TTL configurable por elemento
- **Namespaces**: Para organizar y gestionar la caché por categorías
- **Compresión automática**: Para optimizar el uso de memoria y disco
- **Limpieza periódica**: Para mantener el tamaño de la caché bajo control
- **Estadísticas de uso**: Para monitorear el rendimiento

### Operaciones Principales

- **set**: Guarda un valor en la caché
- **get**: Obtiene un valor de la caché
- **delete**: Elimina un valor de la caché
- **clear**: Limpia toda la caché o un namespace específico
- **cleanup**: Limpia entradas expiradas y reduce el tamaño de la caché
- **get_stats**: Obtiene estadísticas de la caché

## Ejemplos de Uso

### Gestión de Archivos

```python
from modules.core import ConfigManager
from modules.storage import VirtualFileSystem

config_manager = ConfigManager()
fs = VirtualFileSystem(config_manager)

# Crear estructura de directorios
for dir_path in ["datos", "datos/imagenes", "datos/documentos"]:
    os.makedirs(os.path.join("storage", dir_path), exist_ok=True)

# Escribir archivos
fs.write_file("datos/config.json", '{"version": "1.0", "debug": true}')
fs.write_file("datos/log.txt", "Inicio de sesión\nAcción realizada\nCierre de sesión")

# Listar directorio
items = fs.list_directory("datos")
print("Contenido del directorio:")
for item in items:
    print(f"- {item['name']} ({item['type']})")

# Leer y modificar archivo JSON
content = fs.read_file("datos/config.json")
config = json.loads(content)
config["debug"] = False
fs.write_file("datos/config.json", json.dumps(config, indent=2))

# Descargar archivo de internet
web_content = fs.read_file("https://example.com/robots.txt")
fs.write_file("datos/robots.txt", web_content)
```

### Almacenamiento Estructurado

```python
from modules.core import ConfigManager
from modules.storage import VirtualFileSystem, StructuredStorage
import pandas as pd

config_manager = ConfigManager()
virtual_fs = VirtualFileSystem(config_manager)
storage = StructuredStorage(config_manager, virtual_fs)

# Datos de ejemplo
usuarios = [
    {"id": 1, "nombre": "Juan", "edad": 30, "ciudad": "Madrid"},
    {"id": 2, "nombre": "María", "edad": 25, "ciudad": "Barcelona"},
    {"id": 3, "nombre": "Pedro", "edad": 40, "ciudad": "Valencia"}
]

# Guardar en diferentes formatos
storage.save_json(usuarios, "datos/usuarios.json", pretty=True)

# Crear base de datos SQLite
schema = {
    "id": "INTEGER",
    "nombre": "TEXT",
    "edad": "INTEGER",
    "ciudad": "TEXT"
}
storage.create_table("usuarios_db", "usuarios", schema, primary_key="id")
storage.insert_data("usuarios_db", "usuarios", usuarios)

# Consultar datos
mayores_30 = storage.query_data(
    "usuarios_db", 
    "usuarios", 
    conditions={"edad": 30}, 
    fields=["id", "nombre", "ciudad"]
)
print("Usuarios de 30 años o más:")
for usuario in mayores_30:
    print(f"- {usuario['nombre']} ({usuario['ciudad']})")

# Crear y usar índice
storage.create_index("usuarios_idx", usuarios, "id")
usuario = storage.search_index("usuarios_idx", 2)
print(f"Usuario encontrado: {usuario['nombre']}")

# Trabajar con DataFrames
df = pd.DataFrame(usuarios)
storage.save_dataframe(df, "datos/usuarios.csv", format="csv")
```

### Uso de Caché

```python
from modules.core import ConfigManager
from modules.storage import VirtualFileSystem, CacheManager
import time

config_manager = ConfigManager()
virtual_fs = VirtualFileSystem(config_manager)
cache = CacheManager(config_manager, virtual_fs)

# Función costosa que queremos cachear
def operacion_costosa(parametro):
    print(f"Ejecutando operación costosa con {parametro}...")
    time.sleep(2)  # Simular operación lenta
    return f"Resultado para {parametro}"

# Función con caché
def operacion_con_cache(parametro):
    # Generar clave de caché
    cache_key = f"operacion_{parametro}"
    
    # Intentar obtener de caché
    result = cache.get(cache_key)
    
    if result is None:
        # No está en caché, ejecutar operación
        print("Cache miss")
        result = operacion_costosa(parametro)
        
        # Guardar en caché para futuras llamadas
        cache.set(cache_key, result, ttl=60)  # Expira en 60 segundos
    else:
        print("Cache hit")
    
    return result

# Probar caché
for _ in range(3):
    resultado = operacion_con_cache("test")
    print(f"Resultado: {resultado}")
    time.sleep(1)

# Ver estadísticas
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

## Uso desde la Línea de Comandos

El módulo incluye scripts de prueba que pueden ser utilizados desde la línea de comandos:

```bash
# Sistema de archivos virtual
python OpenManusWeb/test_virtual_fs.py test

# Almacenamiento estructurado
python OpenManusWeb/test_structured_storage.py test

# Gestor de caché
python OpenManusWeb/test_cache_manager.py test
```

## Dependencias

El módulo requiere las siguientes dependencias:

- boto3 (para soporte de S3)
- pandas (para soporte de DataFrames)
- requests (para soporte HTTP)

Puedes instalarlas con:

```bash
pip install -r requirements/storage.txt
```

## Limitaciones y Consideraciones

- **Concurrencia**: El sistema no está diseñado para acceso concurrente intensivo.
- **Transacciones**: No hay soporte para transacciones atómicas entre diferentes backends.
- **Seguridad**: Los datos no se cifran por defecto, se recomienda configurar cifrado a nivel de backend.
- **Rendimiento**: El rendimiento puede variar según el backend y el tipo de operación.
- **Escalabilidad**: Para cargas muy grandes, considerar usar sistemas especializados.
