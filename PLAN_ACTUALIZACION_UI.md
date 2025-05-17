# Plan de Acción para Actualización del Diseño UI de ISA-Agent

## Análisis de la Situación Actual

Tras revisar el archivo `simple_chat.py` y los requisitos especificados en `PROMPT_DESARROLLO_UI_ISA_AGENT.md`, puedo identificar que la interfaz actual es funcional pero carece de elementos modernos y de diseño que se solicitan en la inspiración de Claude Artifacts. La interfaz actual:

- Utiliza un diseño básico con colores planos
- No tiene soporte para temas claro/oscuro
- No tiene soporte para renderizado de Markdown o resaltado de código
- Tiene limitadas animaciones o transiciones

## Estrategia de Actualización

La estrategia consistirá en actualizar el HTML embebido en `simple_chat.py` manteniendo la misma estructura de endpoints FastAPI y WebSockets, sin alterar la funcionalidad existente.

## Plan de Implementación

### Fase 1: Preparación de Recursos Externos

1. **Incorporar bibliotecas externas:**
   - Añadir Font Inter para tipografía principal
   - Añadir Fira Code para bloques de código
   - Incorporar Remix Icon para iconografía
   - Incorporar Highlight.js para resaltado de sintaxis
   - Añadir Marked.js para renderizado de Markdown

2. **Preparar estructura de archivos estáticos:**
   - Separar CSS a un archivo externo para mejor mantenimiento
   - Crear archivos JS separados para la lógica de la UI

### Fase 2: Actualización del Diseño Base

3. **Implementar el layout base:**
   - Crear estructura con dos columnas: barra lateral y área principal
   - Implementar encabezado con selector de tema
   - Diseñar el área de chat con espacio adecuado

4. **Desarrollar sistema de temas:**
   - Implementar variables CSS para ambos temas (claro/oscuro)
   - Crear switch para alternar entre temas
   - Almacenar preferencia de tema en localStorage

### Fase 3: Actualización de Componentes de Chat

5. **Rediseñar contenedores de mensajes:**
   - Implementar distinción clara entre mensajes del usuario y del asistente
   - Añadir iconos y encabezados a cada mensaje
   - Aplicar bordes redondeados y sombras según la guía

6. **Implementar soporte para contenido rico:**
   - Integrar renderizado de Markdown en mensajes
   - Añadir bloques de código con resaltado de sintaxis
   - Implementar botón de copia para bloques de código

### Fase 4: Mejoras de UX y Animaciones

7. **Implementar indicadores de estado mejorados:**
   - Crear animación de "escribiendo..." más visual
   - Mejorar la visualización de errores y estados de conexión
   - Añadir transiciones suaves para cambios de estado

8. **Añadir animaciones y transiciones:**
   - Implementar animación de aparición para nuevos mensajes
   - Añadir transiciones suaves para cambios de tema
   - Implementar micro-interacciones para mejorar la experiencia

### Fase 5: Optimización Mobile y Responsive

9. **Mejorar la adaptabilidad móvil:**
   - Implementar media queries para diferentes tamaños de pantalla
   - Optimizar la experiencia táctil para dispositivos móviles
   - Ajustar tamaños de fuente y espaciado para pantallas pequeñas

### Fase 6: Pruebas y Refinamiento

10. **Realizar pruebas exhaustivas:**
    - Verificar que la funcionalidad WebSockets se mantiene intacta
    - Comprobar la compatibilidad con diferentes navegadores
    - Verificar el comportamiento responsive en diferentes dispositivos

## Código a Implementar

A continuación muestro el esquema básico de los cambios que realizaré en el HTML embebido:

```html
<!DOCTYPE html>
<html lang="es" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISA-Agent</title>
    
    <!-- Fuentes -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    
    <!-- Iconos -->
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    
    <!-- Highlight.js para resaltado de código -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-light.min.css" id="code-theme-light">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css" id="code-theme-dark" disabled>
    
    <!-- Estilos CSS -->
    <style>
        /* Variables de tema claro */
        :root {
            --primary-color: #2563eb;
            --background-color: #f9fafb;
            --user-message-bg: #e0f2fe;
            --bot-message-bg: #f3f4f6;
            --text-color: #1f2937;
            --border-color: #e5e7eb;
            /* Resto de variables... */
        }
        
        /* Variables de tema oscuro */
        [data-theme="dark"] {
            --primary-color: #3b82f6;
            --background-color: #111827;
            --user-message-bg: #1e40af;
            --bot-message-bg: #374151;
            --text-color: #f3f4f6;
            --border-color: #374151;
            /* Resto de variables... */
        }
        
        /* Estilos base... */
        /* Estilos de layout... */
        /* Estilos de mensajes... */
        /* Animaciones... */
        /* Media queries... */
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Barra lateral (para futura expansión) -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <h2>ISA-Agent</h2>
            </div>
            <div class="sidebar-content">
                <!-- Contenido futuro -->
                <p class="sidebar-note">Próximamente: historial y configuración</p>
            </div>
        </aside>
        
        <!-- Contenido principal -->
        <main class="main-content">
            <header class="main-header">
                <div class="new-chat-btn">
                    <button>
                        <i class="ri-add-line"></i>
                        <span>Nueva conversación</span>
                    </button>
                </div>
                <div class="theme-toggle">
                    <button id="theme-toggle-btn">
                        <i class="ri-sun-line" id="light-icon"></i>
                        <i class="ri-moon-line" id="dark-icon"></i>
                    </button>
                </div>
            </header>
            
            <div class="chat-container">
                <div class="chat-messages" id="chat-messages">
                    <!-- Los mensajes se agregarán dinámicamente aquí -->
                </div>
                
                <div class="status-container">
                    <div class="status" id="status"></div>
                    <div class="typing-indicator" id="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                </div>
                
                <form class="message-form" id="message-form">
                    <div class="message-input-container">
                        <textarea 
                            class="message-input" 
                            id="message-input" 
                            placeholder="Escribe tu mensaje aquí..." 
                            rows="1"
                            autofocus
                        ></textarea>
                    </div>
                    <button type="submit" class="send-button" id="send-button">
                        <i class="ri-send-plane-fill"></i>
                    </button>
                </form>
            </div>
        </main>
    </div>

    <!-- Scripts para Markdown y resaltado de código -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    
    <!-- Script principal -->
    <script>
        // Configuración de Marked.js para integrar highlight.js
        marked.setOptions({
            highlight: function(code, language) {
                if (language && hljs.getLanguage(language)) {
                    return hljs.highlight(code, { language }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true,
            gfm: true
        });
        
        // Funcionalidad de tema claro/oscuro
        // Funcionalidad de WebSockets (manteniendo la actual)
        // Manejo de mensajes con soporte para Markdown
        // Animaciones y transiciones
        // Funciones auxiliares
    </script>
</body>
</html>
```

## Consideraciones Técnicas

1. **Mantenimiento de la Funcionalidad WebSocket:**
   - Se preservará la lógica de conexión y comunicación WebSocket actual
   - Se modificará únicamente la forma en que se visualizan los mensajes

2. **Rendimiento:**
   - Se cargarán recursos externos a través de CDNs para mejor rendimiento
   - Se implementará lazy-loading para componentes no críticos
   - Se optimizarán imágenes e iconos

3. **Seguridad:**
   - Se mantendrán las mismas políticas de seguridad existentes
   - No se introducirán nuevas dependencias que puedan comprometer la seguridad

4. **Compatibilidad de Navegadores:**
   - Se asegurará compatibilidad con Chrome, Firefox, Safari y Edge actualizados
   - Se usarán técnicas de progressive enhancement para navegadores antiguos

## Cronograma Estimado

1. **Fase 1 (Preparación):** 1 día
2. **Fase 2 (Diseño Base):** 2 días
3. **Fase 3 (Componentes de Chat):** 2 días
4. **Fase 4 (UX y Animaciones):** 1 día
5. **Fase 5 (Optimización Mobile):** 1 día
6. **Fase 6 (Pruebas y Refinamiento):** 1 día

**Tiempo Total Estimado:** 8 días laborables

## Conclusión

Este plan de acción permite modernizar la interfaz de usuario de ISA-Agent siguiendo la inspiración de Claude Artifacts, sin alterar la funcionalidad backend existente. La implementación se realizará de manera modular, permitiendo validar cada fase antes de avanzar a la siguiente.

Se mantendrá el mismo flujo de trabajo y las mismas características de comunicación en tiempo real, mejorando únicamente la experiencia visual y la interactividad del usuario.
