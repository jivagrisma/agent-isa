Objetivo

Modernizar la aplicación web ISA-Agent "simple_chat.py "con una interfaz de usuario inspirada en Claude Artifacts, mejorando la experiencia del usuario y optimizando la comunicación con los modelos de AWS Bedrock, especialmente (Amazon Nova Pro, Amazon Nova Lite, Claude 3.7 Sonnet)


Objetivos
- Implementar un selector de tema oscuro/claro
- Mejorar la experiencia de usuario con animaciones y transiciones
- Añadir indicadores visuales para el estado de la conexión y la escritura
- Optimizar la interfaz para dispositivos móviles (responsive)


Inspiración Principal: Claude Artifacts

La interfaz de Claude Artifacts ofrece un diseño moderno, minimalista y funcional que sirve como excelente referencia para nuestra actualización.

### Características clave a emular:

1. **Diseño limpio y espacioso**
   - Amplio espacio en blanco
   - Tipografía clara y legible
   - Contraste adecuado entre elementos

2. **Presentación de mensajes**
   - Clara distinción entre mensajes del usuario y del asistente
   - Encabezados de mensajes con iconos distintivos
   - Bordes redondeados para los contenedores de mensajes

3. **Soporte para markdown y código**
   - Bloques de código con resaltado de sintaxis
   - Botones para copiar código
   - Renderizado de markdown para listas, encabezados, etc.

4. **Tema claro/oscuro**
   - Transiciones inmediatas entre temas
   - Paleta de colores coherente en ambos modos

## Referencias Visuales

### 1. Vista General de la Interfaz

La interfaz debe tener un diseño limpio con una barra lateral para futuras funcionalidades y un área principal para la conversación:

```
+---------------------+-------------------------------------------+
|                     |                        [Tema: 🌙/☀️]     |
|  ISA-Agent          |  Nueva conversación                       |
|                     |                                           |
|  [Próximamente:     |  +-----------------------------------+   |
|   historial y       |  |                                   |   |
|   configuración]    |  |  Usuario                          |   |
|                     |  |  Hola, ¿cómo puedo ayudarte?      |   |
|                     |  |                                   |   |
|                     |  +-----------------------------------+   |
|                     |                                           |
|                     |  +-----------------------------------+   |
|                     |  |                                   |   |
|                     |  |  ISA-Agent                        |   |
|                     |  |  ¡Hola! Estoy aquí para ayudarte  |   |
|                     |  |  con cualquier pregunta sobre...  |   |
|                     |  |                                   |   |
|                     |  +-----------------------------------+   |
|                     |                                           |
|                     |  +-----------------------------------+   |
|                     |  |                                   |   |
|        |  |  Escribe tu mensaje aquí...       |   |
|                     |  |                                   |   |
|                     |  |                            Enviar |   |
|                     |  +-----------------------------------+   |
+---------------------+-------------------------------------------+
```

### 2. Mensajes con Markdown y Código

Los mensajes deben soportar markdown y mostrar código con resaltado de sintaxis:

```
+-----------------------------------+
|                                   |
|  ISA-Agent                        |
|                                   |
|  Aquí tienes un ejemplo de código |
|  en Python:                       |
|                                   |
|  ```python                        |
|  def hello_world():               |
|      print("¡Hola, mundo!")       |
|                                   |
|  hello_world()                    |
|  ```                              |
|                                   |
|  También puedes usar **negrita**  |
|  o *cursiva* en tus mensajes.     |
|                                   |
+-----------------------------------+
```

### 3. Tema Oscuro

El tema oscuro debe mantener la legibilidad y el contraste:

```
+---------------------+-------------------------------------------+
|                     |                                           |
|  ISA-Agent          |  Nueva conversación                       |
|                     |                                           |
|                     |  +-----------------------------------+   |
|                     |  |                                   |   |
|                     |  |  Usuario                          |   |
|                     |  |  ¿Puedes mostrarme un ejemplo?    |   |
|                     |  |                                   |   |
|                     |  +-----------------------------------+   |
|                     |                                           |
|                     |  +-----------------------------------+   |
|                     |  |                                   |   |
|                     |  |  ISA-Agent                        |   |
|                     |  |  Claro, aquí tienes un ejemplo    |   |
|                     |  |  de código en Python:             |   |
|                     |  |                                   |   |
|                     |  |  ```python                        |   |
|                     |  |  def ejemplo():                   |   |
|                     |  |      return "¡Esto es un ejemplo!"|   |
|                     |  |  ```                              |   |
|                     |  |                                   |   |
|                     |  +-----------------------------------+   |
|                     |                                           |
+---------------------+-------------------------------------------+
```

## Paleta de Colores

### Tema Claro
- **Fondo principal**: #f9fafb
- **Fondo de mensajes (usuario)**: #e0f2fe
- **Fondo de mensajes (bot)**: #f3f4f6
- **Texto principal**: #1f2937
- **Acento primario**: #2563eb
- **Bordes**: #e5e7eb

### Tema Oscuro
- **Fondo principal**: #111827
- **Fondo de mensajes (usuario)**: #1e40af
- **Fondo de mensajes (bot)**: #374151
- **Texto principal**: #f3f4f6
- **Acento primario**: #3b82f6
- **Bordes**: #374151

## Tipografía

- **Fuente principal**: 'Inter', sans-serif
- **Fuente para código**: 'Fira Code', monospace
- **Tamaños de fuente**:
  - Base: 16px
  - Encabezados de mensajes: 14px
  - Código: 14px

## Iconos

Utilizaremos la biblioteca Remix Icon para mantener un conjunto coherente de iconos:
- **Usuario**: ri-user-line
- **Bot**: ri-robot-line
- **Enviar**: ri-send-plane-fill
- **Tema claro**: ri-sun-line
- **Tema oscuro**: ri-moon-line
- **Copiar código**: ri-file-copy-line

## Espaciado y Dimensiones

- **Bordes redondeados**: 0.75rem para mensajes, 0.5rem para botones
- **Padding de mensajes**: 1rem
- **Espacio entre mensajes**: 1.5rem
- **Ancho máximo de mensajes**: 85% del contenedor
- **Ancho de la barra lateral**: 280px

## Animaciones y Transiciones

- **Transición de tema**: 0.3s para cambios de color
- **Aparición de mensajes**: Animación de fadeIn con ligero movimiento
- **Indicador de escritura**: Animación de pulso para los puntos

Estas referencias de diseño proporcionan una guía visual clara para implementar la actualización de UI, manteniendo un diseño moderno, minimalista y funcional inspirado en Claude Artifacts.
