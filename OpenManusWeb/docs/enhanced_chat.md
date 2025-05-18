# Interfaz de Chat Mejorada para Agent-ISA

## Descripción

La interfaz de chat mejorada proporciona una experiencia de usuario avanzada con soporte para múltiples modelos, configuración de parámetros y acceso a los módulos de habilidades de Manus. Está diseñada para ser moderna, responsive y fácil de usar.

## Características Principales

- **Soporte para múltiples modelos**: Permite seleccionar entre diferentes modelos de AWS Bedrock.
- **Configuración de temperatura**: Control deslizante para ajustar la temperatura de muestreo.
- **Barra lateral configurable**: Acceso rápido a configuraciones y módulos.
- **Tema claro/oscuro**: Cambio de tema con transiciones suaves.
- **Diseño responsive**: Adaptable a diferentes tamaños de pantalla.
- **Soporte para markdown y código**: Renderizado de markdown y resaltado de sintaxis.

## Acceso

La interfaz de chat mejorada está disponible en la ruta `/enhanced`:

```
http://localhost:8005/enhanced
```

## Componentes de la Interfaz

### Barra Lateral

La barra lateral proporciona acceso a configuraciones y módulos:

- **Selector de Modelo**: Permite elegir entre diferentes modelos de AWS Bedrock.
- **Control de Temperatura**: Ajusta la temperatura de muestreo para controlar la creatividad del modelo.
- **Lista de Módulos**: Muestra los módulos disponibles y permite activarlos/desactivarlos.
- **Información**: Muestra información sobre la versión y el proyecto.

### Encabezado

El encabezado contiene:

- **Botón de Nueva Conversación**: Inicia una nueva conversación.
- **Botón de Barra Lateral**: Muestra/oculta la barra lateral en dispositivos móviles.
- **Botón de Tema**: Cambia entre tema claro y oscuro.

### Área de Chat

El área de chat muestra la conversación entre el usuario y el asistente:

- **Mensajes del Usuario**: Alineados a la derecha con fondo azul.
- **Mensajes del Asistente**: Alineados a la izquierda con fondo gris.
- **Soporte para Markdown**: Renderiza markdown en los mensajes del asistente.
- **Resaltado de Código**: Resalta la sintaxis en bloques de código.
- **Botón de Copiar Código**: Permite copiar bloques de código al portapapeles.

### Formulario de Mensaje

El formulario de mensaje permite enviar mensajes al asistente:

- **Área de Texto**: Campo para escribir mensajes con ajuste automático de altura.
- **Botón de Subir Archivo**: Permite subir archivos (funcionalidad futura).
- **Botón de Enviar**: Envía el mensaje al asistente.

## Uso

### Selección de Modelo

1. Abre la barra lateral (en móvil, usa el botón de menú).
2. Selecciona el modelo deseado en el selector de modelo.
3. La preferencia se guarda automáticamente para futuras sesiones.

### Ajuste de Temperatura

1. Abre la barra lateral.
2. Usa el control deslizante para ajustar la temperatura:
   - Valores bajos (0.0-0.3): Respuestas más deterministas y conservadoras.
   - Valores medios (0.4-0.7): Buen equilibrio entre creatividad y coherencia.
   - Valores altos (0.8-1.0): Respuestas más creativas y diversas.

### Envío de Mensajes

1. Escribe tu mensaje en el área de texto.
2. Presiona el botón de enviar o usa Ctrl+Enter / Cmd+Enter.
3. El asistente procesará tu mensaje y responderá.

### Uso de Markdown

El asistente puede usar markdown en sus respuestas:

- **Encabezados**: `# Título`, `## Subtítulo`, etc.
- **Énfasis**: `*cursiva*`, `**negrita**`, `***negrita y cursiva***`.
- **Listas**: `- Elemento` o `1. Elemento`.
- **Enlaces**: `[texto](url)`.
- **Bloques de código**: ` ```lenguaje` para iniciar y ` ``` ` para terminar.

### Bloques de Código

Los bloques de código incluyen:

- Resaltado de sintaxis según el lenguaje.
- Nombre del lenguaje en la esquina superior izquierda.
- Botón de copiar en la esquina superior derecha.

## Integración con Módulos

La interfaz de chat mejorada está diseñada para integrarse con los módulos de habilidades de Manus:

- **Búsqueda Web**: Permite buscar información en internet.
- **Generación de Imágenes**: Permite crear imágenes a partir de descripciones textuales.
- **Desarrollo de Código**: Facilita la generación y análisis de código.
- **Sistema de Archivos**: Permite operaciones seguras de archivos.

## Personalización

La interfaz de chat mejorada guarda las preferencias del usuario en localStorage:

- **Tema**: Preferencia de tema claro/oscuro.
- **Modelo**: Último modelo seleccionado.
- **Temperatura**: Último valor de temperatura seleccionado.

## Limitaciones y Consideraciones

- **Compatibilidad de Navegadores**: Optimizada para navegadores modernos (Chrome, Firefox, Safari, Edge).
- **Módulos**: Algunos módulos pueden estar deshabilitados según la configuración del servidor.
- **Subida de Archivos**: La funcionalidad de subir archivos estará disponible en futuras versiones.
- **Modelos**: La disponibilidad de modelos depende de la configuración de AWS Bedrock.
