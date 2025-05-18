"""
Generador de texto avanzado para agent-isa.
Proporciona capacidades de generación de texto con diferentes estilos y formatos.
"""

import logging
import re
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
import markdown
import html2text

from ..core import PluginInterface, ConfigManager, ExtendedLLMClient

# Configurar logging
logger = logging.getLogger(__name__)

class TextGenerator(PluginInterface):
    """
    Generador de texto avanzado con soporte para diferentes estilos y formatos.
    
    Características:
    1. Sistema de plantillas para diferentes tipos de contenido
    2. Soporte para diferentes estilos y tonos de escritura
    3. Capacidades de formateo avanzado (Markdown, HTML, etc.)
    4. Sistema de revisión y corrección automática
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager", "core.ExtendedLLMClient"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, llm_client: Optional[ExtendedLLMClient] = None):
        """
        Inicializa el generador de texto.
        
        Args:
            config_manager: Gestor de configuración
            llm_client: Cliente LLM extendido
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("content")
        
        # Inicializar cliente LLM
        self.llm_client = llm_client
        
        # Cargar plantillas
        self.templates = self._load_templates()
        
        logger.info("Generador de texto inicializado")
    
    async def initialize(self):
        """
        Inicializa el generador de texto si es necesario.
        """
        if not self.llm_client:
            # Importar e inicializar cliente LLM
            from ..core import ExtendedLLMClient
            self.llm_client = ExtendedLLMClient(self.config_manager)
            await self.llm_client.initialize()
    
    async def generate_text(
        self,
        prompt: str,
        style: Optional[str] = None,
        format_type: Optional[str] = None,
        template: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Genera texto basado en un prompt.
        
        Args:
            prompt: Prompt para la generación de texto
            style: Estilo de escritura (formal, informal, técnico, etc.)
            format_type: Tipo de formato (markdown, html, texto plano)
            template: Nombre de la plantilla a utilizar
            max_tokens: Número máximo de tokens
            temperature: Temperatura de muestreo
            variables: Variables para la plantilla
            
        Returns:
            Texto generado
        """
        # Inicializar si es necesario
        if not self.llm_client:
            await self.initialize()
        
        # Construir prompt completo
        full_prompt = self._build_prompt(prompt, style, format_type, template, variables)
        
        # Configurar parámetros
        if not temperature:
            temperature = self.config.get("text_generation.temperature", 0.7)
        
        # Crear mensaje para el LLM
        messages = [{"role": "user", "content": full_prompt}]
        
        # Generar texto
        response = await self.llm_client.ask(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Procesar respuesta según el formato
        processed_text = self._process_response(response, format_type)
        
        return processed_text
    
    async def revise_text(
        self,
        text: str,
        instructions: Optional[str] = None,
        format_type: Optional[str] = None
    ) -> str:
        """
        Revisa y corrige un texto.
        
        Args:
            text: Texto a revisar
            instructions: Instrucciones específicas para la revisión
            format_type: Tipo de formato (markdown, html, texto plano)
            
        Returns:
            Texto revisado
        """
        # Inicializar si es necesario
        if not self.llm_client:
            await self.initialize()
        
        # Construir prompt para revisión
        revision_prompt = self._build_revision_prompt(text, instructions, format_type)
        
        # Crear mensaje para el LLM
        messages = [{"role": "user", "content": revision_prompt}]
        
        # Generar revisión
        response = await self.llm_client.ask(
            messages=messages,
            temperature=0.3  # Temperatura baja para revisiones
        )
        
        # Procesar respuesta según el formato
        processed_text = self._process_response(response, format_type)
        
        return processed_text
    
    async def generate_from_template(
        self,
        template_name: str,
        variables: Dict[str, Any],
        style: Optional[str] = None,
        format_type: Optional[str] = None
    ) -> str:
        """
        Genera texto a partir de una plantilla.
        
        Args:
            template_name: Nombre de la plantilla
            variables: Variables para la plantilla
            style: Estilo de escritura
            format_type: Tipo de formato
            
        Returns:
            Texto generado
        """
        # Verificar si la plantilla existe
        if template_name not in self.templates:
            logger.error(f"Plantilla no encontrada: {template_name}")
            return f"Error: Plantilla '{template_name}' no encontrada"
        
        # Obtener plantilla
        template = self.templates[template_name]
        
        # Construir prompt
        prompt = template.get("prompt", "")
        
        # Generar texto
        return await self.generate_text(
            prompt=prompt,
            style=style or template.get("default_style"),
            format_type=format_type or template.get("default_format"),
            variables=variables,
            temperature=template.get("temperature")
        )
    
    def convert_format(
        self,
        text: str,
        source_format: str,
        target_format: str
    ) -> str:
        """
        Convierte texto entre diferentes formatos.
        
        Args:
            text: Texto a convertir
            source_format: Formato de origen (markdown, html, texto plano)
            target_format: Formato de destino
            
        Returns:
            Texto convertido
        """
        # Convertir a formato intermedio (HTML)
        if source_format == "markdown":
            html = markdown.markdown(text)
        elif source_format == "html":
            html = text
        else:  # texto plano
            # Escapar caracteres especiales y convertir saltos de línea
            html = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html = f"<pre>{html}</pre>"
        
        # Convertir de HTML al formato de destino
        if target_format == "markdown":
            h2t = html2text.HTML2Text()
            h2t.body_width = 0  # No wrap
            return h2t.handle(html)
        elif target_format == "html":
            return html
        else:  # texto plano
            # Eliminar etiquetas HTML
            text_maker = html2text.HTML2Text()
            text_maker.ignore_links = True
            text_maker.ignore_images = True
            text_maker.ignore_emphasis = True
            text_maker.ignore_tables = True
            return text_maker.handle(html)
    
    def _build_prompt(
        self,
        prompt: str,
        style: Optional[str] = None,
        format_type: Optional[str] = None,
        template: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construye un prompt completo con instrucciones de estilo y formato.
        
        Args:
            prompt: Prompt base
            style: Estilo de escritura
            format_type: Tipo de formato
            template: Nombre de la plantilla
            variables: Variables para la plantilla
            
        Returns:
            Prompt completo
        """
        # Inicializar prompt completo
        full_prompt = prompt
        
        # Añadir instrucciones de plantilla si se especifica
        if template and template in self.templates:
            template_data = self.templates[template]
            template_prompt = template_data.get("prompt", "")
            
            # Reemplazar variables en la plantilla
            if variables:
                for key, value in variables.items():
                    placeholder = f"{{{key}}}"
                    template_prompt = template_prompt.replace(placeholder, str(value))
            
            full_prompt = template_prompt
            
            # Usar estilo y formato de la plantilla si no se especifican
            if not style and "default_style" in template_data:
                style = template_data["default_style"]
            
            if not format_type and "default_format" in template_data:
                format_type = template_data["default_format"]
        
        # Añadir instrucciones de estilo
        if style:
            style_instructions = self._get_style_instructions(style)
            full_prompt = f"{full_prompt}\n\n{style_instructions}"
        
        # Añadir instrucciones de formato
        if format_type:
            format_instructions = self._get_format_instructions(format_type)
            full_prompt = f"{full_prompt}\n\n{format_instructions}"
        
        return full_prompt
    
    def _build_revision_prompt(
        self,
        text: str,
        instructions: Optional[str] = None,
        format_type: Optional[str] = None
    ) -> str:
        """
        Construye un prompt para revisión de texto.
        
        Args:
            text: Texto a revisar
            instructions: Instrucciones específicas
            format_type: Tipo de formato
            
        Returns:
            Prompt para revisión
        """
        # Prompt base para revisión
        revision_prompt = "Por favor, revisa y mejora el siguiente texto. "
        
        # Añadir instrucciones específicas
        if instructions:
            revision_prompt += f"{instructions} "
        else:
            revision_prompt += "Corrige errores gramaticales, ortográficos y de estilo. Mejora la claridad y coherencia. "
        
        # Añadir instrucciones de formato
        if format_type:
            format_instructions = self._get_format_instructions(format_type)
            revision_prompt += f"\n\n{format_instructions}"
        
        # Añadir el texto a revisar
        revision_prompt += f"\n\nTexto a revisar:\n\n{text}"
        
        return revision_prompt
    
    def _get_style_instructions(self, style: str) -> str:
        """
        Obtiene instrucciones para un estilo específico.
        
        Args:
            style: Estilo de escritura
            
        Returns:
            Instrucciones de estilo
        """
        style_instructions = {
            "formal": "Escribe en un estilo formal y profesional. Utiliza un lenguaje preciso, evita contracciones y expresiones coloquiales. Mantén un tono serio y objetivo.",
            "informal": "Escribe en un estilo informal y conversacional. Utiliza un lenguaje sencillo, contracciones y expresiones coloquiales. Mantén un tono amigable y cercano.",
            "técnico": "Escribe en un estilo técnico y especializado. Utiliza terminología específica del campo, sé preciso en las descripciones y mantén un enfoque objetivo y detallado.",
            "académico": "Escribe en un estilo académico. Utiliza un lenguaje formal, cita fuentes cuando sea necesario, y estructura el texto de manera lógica con argumentos bien desarrollados.",
            "persuasivo": "Escribe en un estilo persuasivo. Utiliza argumentos convincentes, apela a las emociones cuando sea apropiado, y dirige el texto hacia una llamada a la acción clara.",
            "narrativo": "Escribe en un estilo narrativo. Desarrolla personajes, escenarios y una trama coherente. Utiliza técnicas literarias como el diálogo y la descripción detallada.",
            "instructivo": "Escribe en un estilo instructivo. Proporciona pasos claros y concisos, utiliza imperativos, y organiza la información de manera secuencial y lógica."
        }
        
        return style_instructions.get(style.lower(), f"Escribe en un estilo {style}.")
    
    def _get_format_instructions(self, format_type: str) -> str:
        """
        Obtiene instrucciones para un formato específico.
        
        Args:
            format_type: Tipo de formato
            
        Returns:
            Instrucciones de formato
        """
        format_instructions = {
            "markdown": "Formatea el texto utilizando Markdown. Utiliza # para títulos, ## para subtítulos, * para cursiva, ** para negrita, - para listas, etc.",
            "html": "Formatea el texto utilizando HTML. Utiliza etiquetas como <h1>, <h2>, <p>, <strong>, <em>, <ul>, <li>, etc.",
            "texto_plano": "Formatea el texto como texto plano. Utiliza espacios y saltos de línea para estructurar el contenido.",
            "json": "Formatea la respuesta como un objeto JSON válido con los campos solicitados.",
            "csv": "Formatea la respuesta como valores separados por comas (CSV), con una fila de encabezados seguida de filas de datos.",
            "tabla_markdown": "Formatea la respuesta como una tabla en Markdown, utilizando | para separar columnas y - para la fila de encabezados."
        }
        
        return format_instructions.get(format_type.lower(), f"Formatea el texto en {format_type}.")
    
    def _process_response(self, response: str, format_type: Optional[str] = None) -> str:
        """
        Procesa la respuesta según el formato.
        
        Args:
            response: Respuesta del LLM
            format_type: Tipo de formato
            
        Returns:
            Respuesta procesada
        """
        # Si no hay formato específico, devolver la respuesta tal cual
        if not format_type:
            return response
        
        # Procesar según el formato
        if format_type.lower() == "json":
            # Extraer JSON de la respuesta
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
            if json_match:
                json_str = json_match.group(1)
                try:
                    # Validar JSON
                    json_obj = json.loads(json_str)
                    return json.dumps(json_obj, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    logger.warning("JSON inválido en la respuesta")
            
            # Intentar extraer JSON sin marcadores de código
            try:
                json_obj = json.loads(response)
                return json.dumps(json_obj, ensure_ascii=False, indent=2)
            except json.JSONDecodeError:
                logger.warning("No se pudo extraer JSON de la respuesta")
        
        # Para otros formatos, devolver la respuesta tal cual
        return response
    
    def _load_templates(self) -> Dict[str, Any]:
        """
        Carga las plantillas de texto.
        
        Returns:
            Diccionario de plantillas
        """
        templates = {}
        
        # Directorio de plantillas
        templates_dir = Path(__file__).parent.parent.parent / "templates" / "text"
        
        # Verificar si el directorio existe
        if not templates_dir.exists():
            logger.warning(f"Directorio de plantillas no encontrado: {templates_dir}")
            return templates
        
        # Cargar plantillas
        for file_path in templates_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    template_data = json.load(f)
                
                template_name = file_path.stem
                templates[template_name] = template_data
                
                logger.info(f"Plantilla cargada: {template_name}")
            except Exception as e:
                logger.error(f"Error al cargar plantilla {file_path}: {e}")
        
        return templates
