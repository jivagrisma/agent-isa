"""
Navegador headless para agent-isa.
Proporciona capacidades de navegación y extracción de contenido web.
"""

import logging
import os
import time
from typing import Dict, List, Any, Optional, Union
import asyncio
from urllib.parse import urlparse

from ..core import PluginInterface, ConfigManager

# Configurar logging
logger = logging.getLogger(__name__)

class HeadlessBrowser(PluginInterface):
    """
    Navegador headless para acceso y extracción de contenido web.
    
    Características:
    1. Navegación a URLs
    2. Extracción de contenido
    3. Interacción con páginas
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Inicializa el navegador headless.
        
        Args:
            config_manager: Gestor de configuración
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("search")
        
        # Inicializar atributos
        self.browser = None
        self.page = None
        self.is_initialized = False
        
        logger.info("Navegador headless inicializado")
    
    async def initialize(self):
        """
        Inicializa el navegador si no está inicializado.
        """
        if self.is_initialized:
            return
        
        try:
            # Importar playwright
            from playwright.async_api import async_playwright
            
            # Iniciar playwright
            self.playwright = await async_playwright().start()
            
            # Configurar navegador
            headless = self.config.get("browser.headless", True)
            user_agent = self.config.get(
                "browser.user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            
            # Iniciar navegador
            self.browser = await self.playwright.chromium.launch(headless=headless)
            
            # Crear contexto con user agent personalizado
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1280, "height": 800}
            )
            
            # Crear página
            self.page = await self.context.new_page()
            
            # Configurar timeouts
            timeout = self.config.get("browser.timeout", 30) * 1000  # Convertir a ms
            self.page.set_default_timeout(timeout)
            
            self.is_initialized = True
            logger.info("Navegador headless inicializado correctamente")
            
        except ImportError:
            logger.error("No se pudo importar playwright. Instálalo con: pip install playwright")
            raise
        except Exception as e:
            logger.error(f"Error al inicializar navegador headless: {e}")
            raise
    
    async def close(self):
        """
        Cierra el navegador.
        """
        if not self.is_initialized:
            return
        
        try:
            if self.browser:
                await self.browser.close()
            
            if self.playwright:
                await self.playwright.stop()
            
            self.browser = None
            self.page = None
            self.is_initialized = False
            
            logger.info("Navegador headless cerrado correctamente")
            
        except Exception as e:
            logger.error(f"Error al cerrar navegador headless: {e}")
    
    async def navigate(self, url: str) -> str:
        """
        Navega a una URL y extrae contenido.
        
        Args:
            url: URL a navegar
            
        Returns:
            Contenido extraído de la página
        """
        # Inicializar navegador si es necesario
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Navegar a la URL
            logger.info(f"Navegando a: {url}")
            await self.page.goto(url, wait_until="networkidle")
            
            # Esperar a que la página cargue completamente
            if self.config.get("browser.wait_for_selector", True):
                # Esperar a que el contenido principal esté disponible
                # Esto puede variar según el sitio web
                selectors = ["main", "article", "#content", ".content", "body"]
                for selector in selectors:
                    try:
                        await self.page.wait_for_selector(selector, timeout=5000)
                        break
                    except:
                        continue
            
            # Tomar captura de pantalla si está habilitado
            if self.config.get("browser.screenshot", False):
                # Crear directorio para capturas si no existe
                screenshots_dir = os.path.join(os.getcwd(), "screenshots")
                os.makedirs(screenshots_dir, exist_ok=True)
                
                # Generar nombre de archivo basado en la URL
                domain = urlparse(url).netloc
                timestamp = int(time.time())
                filename = f"{domain}_{timestamp}.png"
                filepath = os.path.join(screenshots_dir, filename)
                
                # Tomar captura
                await self.page.screenshot(path=filepath)
                logger.info(f"Captura guardada en: {filepath}")
            
            # Extraer contenido
            content = await self.extract_content()
            
            return content
            
        except Exception as e:
            logger.error(f"Error al navegar a {url}: {e}")
            return f"Error al navegar a la página: {str(e)}"
    
    async def extract_content(self) -> str:
        """
        Extrae contenido de la página actual.
        
        Returns:
            Contenido extraído
        """
        if not self.is_initialized or not self.page:
            return "Navegador no inicializado"
        
        try:
            # Extraer título
            title = await self.page.title()
            
            # Extraer texto
            if self.config.get("content_extraction.extract_text", True):
                # Intentar extraer el contenido principal
                content = ""
                
                # Intentar con diferentes selectores comunes para contenido principal
                selectors = ["main", "article", "#content", ".content", "body"]
                for selector in selectors:
                    try:
                        elements = await self.page.query_selector_all(selector)
                        if elements:
                            # Usar el primer elemento que encuentre
                            element_content = await elements[0].text_content()
                            if element_content and len(element_content) > len(content):
                                content = element_content
                    except:
                        continue
                
                # Si no se encontró contenido, usar todo el body
                if not content:
                    content = await self.page.evaluate("document.body.innerText")
                
                # Limitar longitud si es necesario
                max_length = self.config.get("content_extraction.max_content_length", 10000)
                if len(content) > max_length:
                    content = content[:max_length] + "..."
            else:
                content = "(Extracción de texto deshabilitada)"
            
            # Extraer enlaces si está habilitado
            links = []
            if self.config.get("content_extraction.extract_links", True):
                link_elements = await self.page.query_selector_all("a[href]")
                for link in link_elements:
                    try:
                        href = await link.get_attribute("href")
                        text = await link.text_content()
                        if href and href.startswith("http"):
                            links.append({"url": href, "text": text.strip()})
                    except:
                        continue
            
            # Formatear resultado
            result = f"# {title}\n\n{content}\n"
            
            if links:
                result += "\n## Enlaces\n"
                # Limitar número de enlaces para no sobrecargar
                for link in links[:10]:
                    result += f"- [{link['text'] or link['url']}]({link['url']})\n"
                
                if len(links) > 10:
                    result += f"- ... y {len(links) - 10} enlaces más\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error al extraer contenido: {e}")
            return f"Error al extraer contenido: {str(e)}"
    
    async def execute_script(self, script: str) -> Any:
        """
        Ejecuta un script JavaScript en la página actual.
        
        Args:
            script: Script JavaScript a ejecutar
            
        Returns:
            Resultado de la ejecución
        """
        if not self.is_initialized or not self.page:
            return None
        
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            logger.error(f"Error al ejecutar script: {e}")
            return None
