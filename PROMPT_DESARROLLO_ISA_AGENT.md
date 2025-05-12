# Prompt para el Desarrollo de Actualizaciones a ISA-Agent

## Contexto

ISA-Agent es una bifurcación de OpenManusWeb con integración a AWS Bedrock que soporta los modelos Amazon Nova Pro, Amazon Nova Lite y Claude 3.7 Sonnet. El objetivo es actualizar la interfaz web actual por un diseño y funcionamiento similar a la interfaz de usuario Artifacts de Anthropic en su aplicación de chat Claude, siguiendo las mejores prácticas para una comunicación eficiente con el modelo Claude 3.7 Sonnet.

## Objetivo

Desarrollar una interfaz web moderna, eficiente y fácil de usar para ISA-Agent que:
1. Se asemeje visualmente a Claude Artifacts
2. Implemente las mejores prácticas para comunicación con modelos LLM
3. Mantenga la integración existente con AWS Bedrock
4. Mejore la experiencia de usuario con características avanzadas

## Instrucciones Detalladas

### Análisis y Planificación

1. **Analiza el repositorio actual de ISA-Agent**
   - Examina la estructura del código
   - Identifica los componentes clave
   - Evalúa la integración con AWS Bedrock

2. **Estudia el repositorio Clone-Claude**
   - Identifica los componentes y patrones de diseño
   - Analiza la arquitectura y flujos de usuario
   - Determina qué elementos pueden ser adaptados

3. **Desarrolla un plan detallado**
   - Define la nueva arquitectura
   - Establece fases de implementación
   - Identifica dependencias y requisitos

### Implementación

4. **Configura el entorno de desarrollo**
   - Integra Next.js, TailwindCSS y shadcn/ui
   - Establece la estructura de directorios
   - Configura herramientas de desarrollo

5. **Desarrolla los componentes core**
   - Implementa componentes UI base
   - Desarrolla la interfaz de chat
   - Adapta la integración con AWS Bedrock

6. **Añade características avanzadas**
   - Implementa visualización y ejecución de código
   - Desarrolla gestión de archivos
   - Crea sistema de historial de conversaciones

7. **Optimiza y pule**
   - Mejora el rendimiento
   - Asegura la accesibilidad
   - Realiza pruebas y depuración

8. **Documenta y despliega**
   - Actualiza la documentación
   - Prepara para producción
   - Implementa estrategia de CI/CD

### Mejores Prácticas para Claude 3.7 Sonnet

9. **Implementa estructuración de prompts**
   - Usa encabezados jerárquicos
   - Implementa listas numeradas para procesos secuenciales
   - Utiliza viñetas para elementos no secuenciales

10. **Optimiza el contexto**
    - Proporciona contexto relevante en cada interacción
    - Mantén historial de conversación accesible
    - Implementa sistema de gestión de tokens

11. **Formatea respuestas adecuadamente**
    - Implementa plantillas específicas para diferentes consultas
    - Optimiza visualización de código y datos técnicos
    - Facilita navegación en respuestas largas

12. **Mejora el manejo de errores**
    - Implementa sistema de recuperación
    - Proporciona feedback claro
    - Ofrece alternativas cuando sea posible

## Entregables Esperados

1. **Código fuente completo**
   - Componentes React/Next.js
   - Estilos con TailwindCSS
   - Integración con AWS Bedrock

2. **Documentación**
   - README actualizado
   - Guía de desarrollo
   - Documentación de mejores prácticas para prompts

3. **Pruebas**
   - Pruebas unitarias
   - Pruebas de integración
   - Pruebas de usuario

## Consideraciones Técnicas

- Utiliza React.js y Next.js para el frontend
- Mantén la integración existente con AWS Bedrock
- Implementa TailwindCSS para estilos consistentes
- Asegura compatibilidad con navegadores modernos
- Optimiza para dispositivos móviles y de escritorio
- Sigue principios de diseño accesible

## Recursos

- Repositorio ISA-Agent: https://github.com/jivagrisma/agent-isa.git
- Repositorio Clone-Claude: https://github.com/jivagrisma/Clone-Claude.git
- Mejores prácticas para Claude: CLAUDE_BEST_PRACTICES.md

## Formato de Comunicación

Al desarrollar este proyecto, sigue estas directrices para una comunicación eficiente:

1. **Estructura tus mensajes** con encabezados claros y jerarquía lógica
2. **Proporciona contexto** relevante en cada interacción
3. **Usa listas numeradas** para procesos secuenciales
4. **Utiliza viñetas** para elementos no secuenciales
5. **Incluye ejemplos de código** con sintaxis highlighting
6. **Explica tu razonamiento** detrás de decisiones importantes
7. **Anticipa problemas** y ofrece soluciones alternativas

## Criterios de Éxito

El proyecto se considerará exitoso cuando:

1. La interfaz web se asemeje visualmente a Claude Artifacts
2. La comunicación con los modelos LLM sea eficiente y efectiva
3. Se mantenga la integración existente con AWS Bedrock
4. La experiencia de usuario sea superior a la versión actual
5. El código sea mantenible, escalable y bien documentado
