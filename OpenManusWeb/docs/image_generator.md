# Generador de Imágenes para Agent-ISA

## Descripción

El generador de imágenes proporciona capacidades para la creación y edición de imágenes a partir de descripciones textuales. Utiliza modelos de IA generativa para crear imágenes de alta calidad y ofrece herramientas para su edición y análisis.

## Componentes Principales

### ImageGenerator

Generador de imágenes con soporte para diferentes servicios y estilos.

**Características:**
- Generación de imágenes a partir de descripciones textuales
- Edición básica de imágenes
- Soporte para diferentes estilos y formatos
- Almacenamiento y gestión de imágenes generadas

**Uso básico:**
```python
from modules.core import ConfigManager
from modules.image import ImageGenerator

# Inicializar
config_manager = ConfigManager()
image_generator = ImageGenerator(config_manager)

# Generar imagen
result = image_generator.generate_image(
    prompt="Un paisaje montañoso al atardecer con un lago",
    style="realista",
    size="1024x1024",
    format="png"
)

# Verificar resultado
if "error" not in result:
    print(f"Imagen generada: {result['image_path']}")
else:
    print(f"Error: {result['error']}")

# Editar imagen
edit_result = image_generator.edit_image(
    image_data=result["image_path"],
    operations=[
        {"type": "resize", "width": 800, "height": 600},
        {"type": "adjust", "brightness": 1.2, "contrast": 1.1},
        {"type": "filter", "name": "sharpen"}
    ],
    format="jpeg"
)

# Analizar imagen
analysis = image_generator.analyze_image(result["image_path"])
print(f"Formato: {analysis['format']}")
print(f"Dimensiones: {analysis['width']}x{analysis['height']}")
```

## Configuración

El módulo utiliza el sistema de configuración modular de agent-isa. La configuración se encuentra en `OpenManusWeb/config/image.toml`.

### Opciones de Configuración

```toml
[general]
enabled = true
cache_results = true
cache_expiry = 3600  # Segundos

[aws]
region = "us-east-1"

[generation]
default_model = "amazon.titan-image-generator-v1"
default_size = "1024x1024"
default_format = "png"
quality = "standard"  # standard, premium
cfg_scale = 8.0
negative_prompt = "blurry, distorted, low quality, ugly, bad anatomy, bad proportions, deformed"

[storage]
directory = "images"
use_s3 = false
s3_bucket = ""
s3_prefix = "images"

[editing]
max_image_size = 4096  # Píxeles (ancho o alto máximo)
preserve_metadata = true
default_quality = 90  # Para formatos con compresión
```

## Modelos Soportados

El generador de imágenes soporta diferentes modelos de IA generativa:

- **amazon.titan-image-generator-v1**: Modelo Titan de Amazon para generación de imágenes
- **stability.stable-diffusion-xl-v1**: Modelo Stable Diffusion XL para generación de imágenes

## Estilos de Imagen

El generador de imágenes soporta diferentes estilos de imagen:

- **realista**: Estilo fotorrealista con detalles precisos
- **anime**: Estilo de animación japonesa
- **acuarela**: Estilo de pintura con acuarelas
- **pixel_art**: Estilo de arte pixelado
- **3d**: Estilo de renderizado 3D
- **boceto**: Estilo de dibujo a lápiz
- **abstracto**: Estilo de arte abstracto
- **vintage**: Estilo retro o vintage
- **minimalista**: Estilo minimalista con elementos simples
- **comic**: Estilo de cómic o historieta

## Operaciones de Edición

El generador de imágenes soporta diferentes operaciones de edición:

- **resize**: Cambiar el tamaño de la imagen
- **crop**: Recortar una parte de la imagen
- **rotate**: Rotar la imagen
- **flip**: Voltear la imagen horizontal o verticalmente
- **adjust**: Ajustar brillo, contraste y color
- **filter**: Aplicar filtros como desenfoque, nitidez, etc.

## Ejemplos de Uso

### Generación de Imágenes con Diferentes Estilos

```python
from modules.core import ConfigManager
from modules.image import ImageGenerator

def generate_with_styles():
    config_manager = ConfigManager()
    image_generator = ImageGenerator(config_manager)
    
    # Lista de estilos a probar
    styles = ["realista", "anime", "acuarela", "pixel_art", "3d"]
    
    # Prompt base
    base_prompt = "Un castillo medieval en una colina"
    
    # Generar imágenes con diferentes estilos
    for style in styles:
        print(f"Generando imagen en estilo {style}...")
        
        result = image_generator.generate_image(
            prompt=base_prompt,
            style=style,
            size="1024x768",
            format="png"
        )
        
        if "error" not in result:
            print(f"Imagen generada: {result['image_path']}")
        else:
            print(f"Error: {result['error']}")

# Ejecutar
generate_with_styles()
```

### Edición de Imágenes

```python
from modules.core import ConfigManager
from modules.image import ImageGenerator

def edit_image_example(image_path):
    config_manager = ConfigManager()
    image_generator = ImageGenerator(config_manager)
    
    # Operaciones de edición
    operations = [
        # Recortar imagen
        {
            "type": "crop",
            "left": 100,
            "top": 100,
            "right": 900,
            "bottom": 700
        },
        
        # Redimensionar
        {
            "type": "resize",
            "width": 800,
            "height": 600
        },
        
        # Ajustar brillo y contraste
        {
            "type": "adjust",
            "brightness": 1.2,
            "contrast": 1.1,
            "color": 1.1
        },
        
        # Aplicar filtro de nitidez
        {
            "type": "filter",
            "name": "sharpen"
        }
    ]
    
    # Editar imagen
    result = image_generator.edit_image(
        image_data=image_path,
        operations=operations,
        format="jpeg"
    )
    
    if "error" not in result:
        print(f"Imagen editada: {result['image_path']}")
        print(f"Dimensiones: {result['width']}x{result['height']}")
    else:
        print(f"Error: {result['error']}")

# Ejecutar con una ruta de imagen
edit_image_example("ruta/a/imagen.png")
```

### Análisis de Imágenes

```python
from modules.core import ConfigManager
from modules.image import ImageGenerator

def analyze_image_example(image_path):
    config_manager = ConfigManager()
    image_generator = ImageGenerator(config_manager)
    
    # Analizar imagen
    result = image_generator.analyze_image(image_path)
    
    if "error" not in result:
        print("Análisis de imagen:")
        print(f"Formato: {result['format']}")
        print(f"Modo: {result['mode']}")
        print(f"Dimensiones: {result['width']}x{result['height']}")
        print(f"Tamaño: {result['size_bytes']} bytes")
        
        # Mostrar información EXIF si está disponible
        if "exif" in result and result["exif"]:
            print("\nInformación EXIF:")
            for key, value in result["exif"].items():
                print(f"  {key}: {value}")
    else:
        print(f"Error: {result['error']}")

# Ejecutar con una ruta de imagen
analyze_image_example("ruta/a/imagen.jpg")
```

## Uso desde la Línea de Comandos

El módulo incluye un script de prueba que puede ser utilizado desde la línea de comandos:

```bash
# Generar imagen
python OpenManusWeb/test_image_generator.py generate "Un paisaje montañoso al atardecer" --style realista --size 1024x768 --format png

# Editar imagen
python OpenManusWeb/test_image_generator.py edit "ruta/a/imagen.png" --operations '[{"type":"resize","width":800,"height":600},{"type":"adjust","brightness":1.2}]' --format jpeg

# Analizar imagen
python OpenManusWeb/test_image_generator.py analyze "ruta/a/imagen.jpg"
```

## Dependencias

El módulo requiere las siguientes dependencias:

- boto3
- Pillow
- requests

Puedes instalarlas con:

```bash
pip install -r requirements/image.txt
```

## Integración con AWS

El generador de imágenes utiliza servicios de AWS para la generación de imágenes:

- **Amazon Bedrock**: Para acceder a modelos de IA generativa
- **Amazon S3** (opcional): Para almacenar imágenes generadas

### Configuración de AWS

Para utilizar el generador de imágenes con AWS, necesitas configurar las credenciales de AWS:

```bash
# Configurar credenciales de AWS
aws configure
```

O configurar las variables de entorno:

```bash
export AWS_ACCESS_KEY_ID=tu_access_key
export AWS_SECRET_ACCESS_KEY=tu_secret_key
export AWS_REGION=us-east-1
```

## Limitaciones y Consideraciones

- **Calidad de las Imágenes**: La calidad de las imágenes generadas depende del modelo utilizado.
- **Tiempo de Generación**: La generación de imágenes puede tomar varios segundos.
- **Costos de AWS**: El uso de servicios de AWS puede generar costos.
- **Contenido Inapropiado**: Los modelos tienen filtros para evitar contenido inapropiado.
- **Derechos de Autor**: Las imágenes generadas pueden estar sujetas a restricciones de uso.
