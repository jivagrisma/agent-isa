# Generador de Texto para Agent-ISA

## Descripción

El generador de texto proporciona capacidades avanzadas para la creación de contenido textual con diferentes estilos y formatos. Está diseñado para trabajar con modelos de lenguaje y ofrecer una interfaz flexible para la generación de diversos tipos de contenido.

## Componentes Principales

### TextGenerator

Generador de texto avanzado con soporte para diferentes estilos y formatos.

**Características:**
- Sistema de plantillas para diferentes tipos de contenido
- Soporte para diferentes estilos y tonos de escritura
- Capacidades de formateo avanzado (Markdown, HTML, etc.)
- Sistema de revisión y corrección automática

**Uso básico:**
```python
import asyncio
from modules.core import ConfigManager
from modules.content import TextGenerator

async def generate_content():
    # Inicializar
    config_manager = ConfigManager()
    text_generator = TextGenerator(config_manager)
    
    # Generar texto con prompt
    text = await text_generator.generate_text(
        prompt="Escribe un artículo sobre inteligencia artificial",
        style="formal",
        format_type="markdown"
    )
    print(text)
    
    # Revisar y corregir texto
    revised_text = await text_generator.revise_text(
        text="Este es un texto con algunos errores gramaticales y de estilo.",
        instructions="Corrige errores y mejora la claridad"
    )
    print(revised_text)
    
    # Generar texto con plantilla
    blog_post = await text_generator.generate_from_template(
        template_name="blog_post",
        variables={
            "topic": "Inteligencia Artificial",
            "audience": "profesionales de tecnología"
        }
    )
    print(blog_post)

# Ejecutar
asyncio.run(generate_content())
```

## Configuración

El módulo utiliza el sistema de configuración modular de agent-isa. La configuración se encuentra en `OpenManusWeb/config/content.toml`.

### Opciones de Configuración

```toml
[text_generation]
temperature = 0.7
max_tokens = 1000
default_style = "formal"
default_format = "markdown"
enable_revision = true
```

## Estilos de Escritura

El generador de texto soporta diferentes estilos de escritura:

- **formal**: Estilo profesional y académico
- **informal**: Estilo conversacional y cercano
- **técnico**: Estilo especializado con terminología técnica
- **académico**: Estilo riguroso con citas y argumentación
- **persuasivo**: Estilo convincente orientado a la acción
- **narrativo**: Estilo de narración con desarrollo de historia
- **instructivo**: Estilo de guía paso a paso

## Formatos de Salida

El generador de texto soporta diferentes formatos de salida:

- **markdown**: Formato Markdown para documentación y blogs
- **html**: Formato HTML para contenido web
- **texto_plano**: Texto sin formato
- **json**: Formato JSON estructurado
- **csv**: Valores separados por comas
- **tabla_markdown**: Tablas en formato Markdown

## Sistema de Plantillas

El generador de texto incluye un sistema de plantillas para diferentes tipos de contenido. Las plantillas se encuentran en `OpenManusWeb/templates/text/` en formato JSON.

### Estructura de una Plantilla

```json
{
  "name": "nombre_plantilla",
  "description": "Descripción de la plantilla",
  "prompt": "Prompt con {variables}",
  "default_style": "estilo_predeterminado",
  "default_format": "formato_predeterminado",
  "temperature": 0.7,
  "variables": [
    {
      "name": "variable1",
      "description": "Descripción de la variable",
      "required": true
    },
    {
      "name": "variable2",
      "description": "Descripción de la variable",
      "required": false,
      "default": "valor_predeterminado"
    }
  ],
  "example_output": "Ejemplo de salida"
}
```

### Plantillas Incluidas

- **blog_post**: Plantilla para generar artículos de blog
- **product_description**: Plantilla para generar descripciones de productos
- **technical_documentation**: Plantilla para generar documentación técnica
- **social_media_post**: Plantilla para generar publicaciones para redes sociales

## Ejemplos de Uso

### Generación de Texto con Estilo

```python
import asyncio
from modules.core import ConfigManager
from modules.content import TextGenerator

async def generate_with_style():
    config_manager = ConfigManager()
    text_generator = TextGenerator(config_manager)
    
    # Generar texto con estilo formal
    formal_text = await text_generator.generate_text(
        prompt="Explica los beneficios de la inteligencia artificial en la medicina",
        style="formal",
        format_type="markdown"
    )
    print("Estilo Formal:")
    print(formal_text)
    
    # Generar texto con estilo persuasivo
    persuasive_text = await text_generator.generate_text(
        prompt="Explica por qué las empresas deberían adoptar la inteligencia artificial",
        style="persuasivo",
        format_type="markdown"
    )
    print("\nEstilo Persuasivo:")
    print(persuasive_text)

# Ejecutar
asyncio.run(generate_with_style())
```

### Revisión y Corrección de Texto

```python
import asyncio
from modules.core import ConfigManager
from modules.content import TextGenerator

async def revise_text():
    config_manager = ConfigManager()
    text_generator = TextGenerator(config_manager)
    
    original_text = """
    La inteligencia artificial es una tecnologia que esta revolucionando muchas industrias.
    Tiene muchas aplicaciones como el procesamiento de lenguaje natural, vision por computadora, y aprendisaje automatico.
    Las empresas que no adopten esta tecnologia podrian quedarse atras en el futuro.
    """
    
    revised_text = await text_generator.revise_text(
        text=original_text,
        instructions="Corrige errores ortográficos y gramaticales, mejora la claridad y el estilo",
        format_type="markdown"
    )
    
    print("Texto Original:")
    print(original_text)
    print("\nTexto Revisado:")
    print(revised_text)

# Ejecutar
asyncio.run(revise_text())
```

### Uso de Plantillas

```python
import asyncio
from modules.core import ConfigManager
from modules.content import TextGenerator

async def use_templates():
    config_manager = ConfigManager()
    text_generator = TextGenerator(config_manager)
    
    # Generar artículo de blog
    blog_post = await text_generator.generate_from_template(
        template_name="blog_post",
        variables={
            "topic": "Inteligencia Artificial Ética",
            "audience": "profesionales de tecnología",
            "word_count": 600
        }
    )
    print("Artículo de Blog:")
    print(blog_post)
    
    # Generar descripción de producto
    product_description = await text_generator.generate_from_template(
        template_name="product_description",
        variables={
            "product_name": "SmartAssistant Pro",
            "features": "Asistente virtual con IA, reconocimiento de voz, integración con smart home, personalización avanzada",
            "price": "€199.99"
        },
        style="persuasivo"
    )
    print("\nDescripción de Producto:")
    print(product_description)

# Ejecutar
asyncio.run(use_templates())
```

## Uso desde la Línea de Comandos

El módulo incluye un script de prueba que puede ser utilizado desde la línea de comandos:

```bash
# Generar texto con prompt
python OpenManusWeb/test_text_generator.py generate "Escribe un artículo sobre inteligencia artificial" --style formal --format markdown

# Revisar texto
python OpenManusWeb/test_text_generator.py revise "Este es un texto con errores" --instructions "Corrige errores gramaticales"

# Generar texto con plantilla
python OpenManusWeb/test_text_generator.py template blog_post --variables '{"topic": "Inteligencia Artificial", "audience": "profesionales"}'

# Convertir formato
python OpenManusWeb/test_text_generator.py convert "# Título\n\nContenido" --from markdown --to html
```

## Dependencias

El módulo requiere las siguientes dependencias:

- markdown
- html2text

Puedes instalarlas con:

```bash
pip install -r requirements/content.txt
```

## Limitaciones y Consideraciones

- **Calidad del Contenido**: La calidad del contenido generado depende del modelo de lenguaje subyacente.
- **Contexto Limitado**: Los modelos tienen un contexto limitado y pueden no recordar información previa.
- **Creatividad vs. Precisión**: Ajustar la temperatura afecta el equilibrio entre creatividad y precisión.
- **Plantillas Personalizadas**: Las plantillas deben ser diseñadas cuidadosamente para obtener resultados óptimos.
