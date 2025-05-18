# Procesador de Contenido Multimedia para Agent-ISA

## Descripción

El procesador de contenido multimedia proporciona capacidades para el análisis y procesamiento de imágenes y texto. Permite extraer información de imágenes, convertir entre formatos y generar descripciones textuales de contenido visual.

## Componentes Principales

### MediaProcessor

Procesador de contenido multimedia con capacidades de análisis y conversión.

**Características:**
- Análisis de imágenes
- Extracción de texto de imágenes (OCR)
- Conversión entre formatos de contenido
- Descripción de imágenes mediante modelos multimodales

**Uso básico:**
```python
from modules.core import ConfigManager
from modules.content import MediaProcessor

# Inicializar
config_manager = ConfigManager()
media_processor = MediaProcessor(config_manager)

# Extraer texto de una imagen
ocr_result = media_processor.extract_text_from_image("ruta/a/imagen.png")
print(f"Texto extraído: {ocr_result['text']}")

# Analizar contenido de una imagen
analysis = media_processor.analyze_image_content(
    "ruta/a/imagen.jpg",
    features=["labels", "text", "faces"]
)
print(f"Etiquetas detectadas: {len(analysis['labels'])}")

# Generar descripción de una imagen
description = media_processor.describe_image("ruta/a/imagen.jpg")
print(f"Descripción: {description['description']}")

# Convertir formato de imagen
conversion = media_processor.convert_image_format(
    "ruta/a/imagen.png",
    target_format="jpeg",
    quality=85
)
```

## Configuración

El módulo utiliza el sistema de configuración modular de agent-isa. La configuración se encuentra en `OpenManusWeb/config/content.toml`.

### Opciones de Configuración

```toml
[aws]
region = "us-east-1"

[media_processing]
enable_ocr = true
enable_image_analysis = true
max_image_size = 5242880  # 5MB
supported_formats = ["png", "jpeg", "jpg", "webp", "gif"]
```

## Funcionalidades

### Extracción de Texto (OCR)

El procesador de contenido multimedia puede extraer texto de imágenes utilizando tecnología OCR (Reconocimiento Óptico de Caracteres).

```python
from modules.core import ConfigManager
from modules.content import MediaProcessor

def extract_text_example(image_path):
    config_manager = ConfigManager()
    media_processor = MediaProcessor(config_manager)

    # Extraer texto
    result = media_processor.extract_text_from_image(image_path)

    if "error" not in result:
        print(f"Texto extraído (confianza: {result['confidence']:.2f}%):")
        print(result["text"])

        # Mostrar líneas individuales
        print("\nLíneas detectadas:")
        for i, line in enumerate(result["lines"], 1):
            print(f"{i}. {line}")
    else:
        print(f"Error: {result['error']}")

# Ejecutar con una ruta de imagen
extract_text_example("ruta/a/imagen_con_texto.png")
```

### Análisis de Contenido de Imágenes

El procesador puede analizar el contenido de imágenes para detectar objetos, texto, rostros y contenido moderado.

```python
from modules.core import ConfigManager
from modules.content import MediaProcessor

def analyze_content_example(image_path):
    config_manager = ConfigManager()
    media_processor = MediaProcessor(config_manager)

    # Analizar contenido
    result = media_processor.analyze_image_content(
        image_path,
        features=["labels", "text", "faces", "moderation"]
    )

    if "error" not in result:
        # Mostrar etiquetas
        if "labels" in result:
            print("Etiquetas detectadas:")
            for label in result["labels"]:
                print(f"- {label['name']} ({label['confidence']:.2f}%)")

        # Mostrar texto
        if "text_detections" in result:
            print("\nTexto detectado:")
            for detection in result["text_detections"]:
                if detection["type"] == "LINE":
                    print(f"- {detection['text']}")

        # Mostrar rostros
        if "faces" in result:
            print(f"\nRostros detectados: {len(result['faces'])}")
            for i, face in enumerate(result["faces"], 1):
                print(f"Rostro {i}:")
                if "age_range" in face:
                    print(f"- Edad estimada: {face['age_range'].get('Low')}-{face['age_range'].get('High')} años")
                if "gender" in face:
                    print(f"- Género: {face['gender']}")

        # Mostrar etiquetas de moderación
        if "moderation_labels" in result:
            print("\nEtiquetas de moderación:")
            for label in result["moderation_labels"]:
                print(f"- {label['name']} ({label['confidence']:.2f}%)")
    else:
        print(f"Error: {result['error']}")

# Ejecutar con una ruta de imagen
analyze_content_example("ruta/a/imagen.jpg")
```

### Descripción de Imágenes

El procesador puede generar descripciones textuales de imágenes utilizando modelos multimodales.

```python
from modules.core import ConfigManager
from modules.content import MediaProcessor

def describe_image_example(image_path):
    config_manager = ConfigManager()
    media_processor = MediaProcessor(config_manager)

    # Generar descripción
    result = media_processor.describe_image(
        image_path,
        max_tokens=150
    )

    if "error" not in result:
        print(f"Descripción generada (modelo: {result['model']}):")
        print(result["description"])
    else:
        print(f"Error: {result['error']}")

# Ejecutar con una ruta de imagen
describe_image_example("ruta/a/imagen.jpg")
```

### Conversión de Formato de Imágenes

El procesador puede convertir imágenes entre diferentes formatos.

```python
from modules.core import ConfigManager
from modules.content import MediaProcessor

def convert_format_example(image_path, target_format, quality=None):
    config_manager = ConfigManager()
    media_processor = MediaProcessor(config_manager)

    # Convertir formato
    result = media_processor.convert_image_format(
        image_path,
        target_format=target_format,
        quality=quality
    )

    if "error" not in result:
        print(f"Imagen convertida:")
        print(f"- Formato: {result['format']}")
        print(f"- Dimensiones: {result['width']}x{result['height']}")
        print(f"- Tamaño: {result['size_bytes']} bytes")

        # Guardar imagen convertida
        import base64
        output_path = f"imagen_convertida.{result['format']}"
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(result["image_data"]))
        print(f"- Guardada en: {output_path}")
    else:
        print(f"Error: {result['error']}")

# Ejecutar con una ruta de imagen
convert_format_example("ruta/a/imagen.png", "jpeg", 85)
```

## Uso desde la Línea de Comandos

El módulo incluye un script de prueba que puede ser utilizado desde la línea de comandos:

```bash
# Extraer texto de imagen
python OpenManusWeb/test_media_processor.py ocr "ruta/a/imagen_con_texto.png"

# Analizar contenido de imagen
python OpenManusWeb/test_media_processor.py analyze "ruta/a/imagen.jpg" --features labels text faces

# Generar descripción de imagen
python OpenManusWeb/test_media_processor.py describe "ruta/a/imagen.jpg" --max-tokens 150

# Convertir formato de imagen
python OpenManusWeb/test_media_processor.py convert "ruta/a/imagen.png" --format jpeg --quality 85
```

## Integración con AWS

El procesador de contenido multimedia utiliza modelos de AWS para el análisis y procesamiento de imágenes:

- **Nova Pro y Nova Lite**: Para OCR y análisis de imágenes en un solo modelo, son las opciones más completas y accesibles.
- **Nova Canvas y Nova Reel**: Para tareas especializadas en generación o manipulación de imágenes y video.
- **Amazon Bedrock**: Para generación de descripciones de imágenes

### Configuración de AWS

Para utilizar el procesador de contenido multimedia con AWS, necesitas configurar las credenciales de AWS:

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

## Dependencias

El módulo requiere las siguientes dependencias:

- boto3
- Pillow
- requests

Puedes instalarlas con:

```bash
pip install -r requirements/content.txt
```

## Limitaciones y Consideraciones

- **Tamaño de Imágenes**: Hay límites en el tamaño de las imágenes que se pueden procesar.
- **Calidad del OCR**: La extracción de texto depende de la calidad de la imagen y la claridad del texto.
- **Precisión del Análisis**: El análisis de contenido puede no ser 100% preciso en todos los casos.
- **Costos de AWS**: El uso de servicios de AWS puede generar costos.
- **Privacidad**: Las imágenes se envían a servicios en la nube para su procesamiento.

## Casos de Uso

- **Extracción de Información**: Extraer texto de documentos, recibos, tarjetas de presentación, etc.
- **Catalogación de Imágenes**: Analizar y categorizar imágenes según su contenido.
- **Accesibilidad**: Generar descripciones de imágenes para personas con discapacidad visual.
- **Moderación de Contenido**: Detectar contenido inapropiado en imágenes.
- **Optimización de Imágenes**: Convertir imágenes a formatos más eficientes para la web.
