"""
Extractor de contenido para agent-isa.
Proporciona capacidades de extracción y análisis de contenido web.
"""

import logging
import re
import json
from typing import Dict, List, Any, Optional, Union, Tuple
from bs4 import BeautifulSoup, Tag
import pandas as pd
from urllib.parse import urljoin

from ..core import PluginInterface, ConfigManager

# Configurar logging
logger = logging.getLogger(__name__)

class ContentExtractor(PluginInterface):
    """
    Extractor de contenido web con capacidades de análisis.
    
    Características:
    1. Extracción de texto estructurado
    2. Extracción de tablas y datos tabulares
    3. Extracción de metadatos
    4. Análisis básico de contenido
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Inicializa el extractor de contenido.
        
        Args:
            config_manager: Gestor de configuración
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("content")
        
        logger.info("Extractor de contenido inicializado")
    
    def extract_from_html(self, html: str, url: str = "") -> Dict[str, Any]:
        """
        Extrae contenido estructurado de HTML.
        
        Args:
            html: Contenido HTML
            url: URL de origen (para resolver enlaces relativos)
            
        Returns:
            Diccionario con el contenido extraído
        """
        try:
            # Parsear HTML
            soup = BeautifulSoup(html, "html.parser")
            
            # Extraer diferentes tipos de contenido
            title = self._extract_title(soup)
            metadata = self._extract_metadata(soup)
            main_content = self._extract_main_content(soup)
            tables = self._extract_tables(soup, url)
            links = self._extract_links(soup, url)
            images = self._extract_images(soup, url)
            
            # Construir resultado
            result = {
                "title": title,
                "metadata": metadata,
                "main_content": main_content,
                "tables": tables,
                "links": links,
                "images": images
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error al extraer contenido: {e}")
            return {
                "title": "",
                "metadata": {},
                "main_content": f"Error al extraer contenido: {str(e)}",
                "tables": [],
                "links": [],
                "images": []
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extrae el título de la página.
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Título de la página
        """
        # Intentar con la etiqueta title
        title_tag = soup.title
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        
        # Intentar con h1
        h1_tag = soup.find("h1")
        if h1_tag and h1_tag.get_text():
            return h1_tag.get_text().strip()
        
        # Intentar con otros encabezados
        for tag_name in ["h2", "h3"]:
            header_tag = soup.find(tag_name)
            if header_tag and header_tag.get_text():
                return header_tag.get_text().strip()
        
        return "Sin título"
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extrae metadatos de la página.
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Diccionario con metadatos
        """
        metadata = {}
        
        # Extraer metaetiquetas
        meta_tags = soup.find_all("meta")
        for tag in meta_tags:
            # Extraer nombre/propiedad y contenido
            name = tag.get("name") or tag.get("property")
            content = tag.get("content")
            
            if name and content:
                metadata[name] = content
        
        return metadata
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extrae el contenido principal de la página.
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Contenido principal como texto
        """
        # Intentar con diferentes selectores comunes para contenido principal
        main_content = ""
        
        # Lista de selectores comunes para contenido principal
        selectors = [
            "main", "article", "#content", ".content", 
            "[role='main']", ".main-content", "#main-content"
        ]
        
        # Intentar cada selector
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    content = element.get_text(separator="\n", strip=True)
                    if content and len(content) > len(main_content):
                        main_content = content
            except Exception:
                continue
        
        # Si no se encontró contenido, usar el body
        if not main_content:
            body = soup.find("body")
            if body:
                # Eliminar scripts, estilos y otros elementos no deseados
                for tag in body.find_all(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                
                main_content = body.get_text(separator="\n", strip=True)
        
        # Limpiar el contenido
        main_content = self._clean_text(main_content)
        
        return main_content
    
    def _extract_tables(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extrae tablas de la página.
        
        Args:
            soup: Objeto BeautifulSoup
            base_url: URL base para resolver enlaces relativos
            
        Returns:
            Lista de tablas extraídas
        """
        tables = []
        
        # Encontrar todas las tablas
        table_tags = soup.find_all("table")
        
        for i, table_tag in enumerate(table_tags):
            try:
                # Extraer título de la tabla
                table_title = ""
                
                # Buscar caption
                caption = table_tag.find("caption")
                if caption:
                    table_title = caption.get_text(strip=True)
                
                # Si no hay caption, buscar un encabezado cercano
                if not table_title:
                    prev_tag = table_tag.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
                    if prev_tag and prev_tag.get_text():
                        table_title = prev_tag.get_text(strip=True)
                
                # Si aún no hay título, usar un título genérico
                if not table_title:
                    table_title = f"Tabla {i+1}"
                
                # Extraer encabezados
                headers = []
                header_row = table_tag.find("thead")
                if header_row:
                    th_tags = header_row.find_all("th")
                    if th_tags:
                        headers = [th.get_text(strip=True) for th in th_tags]
                
                # Si no hay encabezados en thead, buscar en la primera fila
                if not headers:
                    first_row = table_tag.find("tr")
                    if first_row:
                        th_tags = first_row.find_all("th")
                        if th_tags:
                            headers = [th.get_text(strip=True) for th in th_tags]
                        else:
                            # Usar celdas td si no hay th
                            td_tags = first_row.find_all("td")
                            if td_tags:
                                headers = [td.get_text(strip=True) for td in td_tags]
                
                # Extraer filas
                rows = []
                for row in table_tag.find_all("tr")[1:] if headers else table_tag.find_all("tr"):
                    cells = row.find_all(["td", "th"])
                    if cells:
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        rows.append(row_data)
                
                # Crear DataFrame
                if headers and rows:
                    # Asegurar que todas las filas tengan la misma longitud que los encabezados
                    normalized_rows = []
                    for row in rows:
                        if len(row) < len(headers):
                            # Añadir celdas vacías si faltan
                            row = row + [""] * (len(headers) - len(row))
                        elif len(row) > len(headers):
                            # Truncar si hay demasiadas celdas
                            row = row[:len(headers)]
                        normalized_rows.append(row)
                    
                    df = pd.DataFrame(normalized_rows, columns=headers)
                    
                    # Convertir a formato JSON
                    table_data = json.loads(df.to_json(orient="records"))
                elif rows:
                    # Sin encabezados, usar índices numéricos
                    df = pd.DataFrame(rows)
                    table_data = json.loads(df.to_json(orient="records"))
                else:
                    table_data = []
                
                # Añadir tabla al resultado
                tables.append({
                    "title": table_title,
                    "headers": headers,
                    "data": table_data,
                    "num_rows": len(rows),
                    "num_cols": len(headers) if headers else (len(rows[0]) if rows else 0)
                })
                
            except Exception as e:
                logger.error(f"Error al extraer tabla {i}: {e}")
        
        return tables
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extrae enlaces de la página.
        
        Args:
            soup: Objeto BeautifulSoup
            base_url: URL base para resolver enlaces relativos
            
        Returns:
            Lista de enlaces extraídos
        """
        links = []
        
        # Encontrar todos los enlaces
        for a_tag in soup.find_all("a", href=True):
            try:
                href = a_tag["href"]
                text = a_tag.get_text(strip=True)
                
                # Resolver URL relativa
                if href and not href.startswith(("http://", "https://", "mailto:", "tel:", "#")):
                    href = urljoin(base_url, href)
                
                # Añadir enlace si es válido
                if href and href.startswith(("http://", "https://")):
                    links.append({
                        "url": href,
                        "text": text or href
                    })
            except Exception:
                continue
        
        return links
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extrae imágenes de la página.
        
        Args:
            soup: Objeto BeautifulSoup
            base_url: URL base para resolver enlaces relativos
            
        Returns:
            Lista de imágenes extraídas
        """
        images = []
        
        # Encontrar todas las imágenes
        for img_tag in soup.find_all("img", src=True):
            try:
                src = img_tag["src"]
                alt = img_tag.get("alt", "")
                title = img_tag.get("title", "")
                
                # Resolver URL relativa
                if src and not src.startswith(("http://", "https://", "data:")):
                    src = urljoin(base_url, src)
                
                # Añadir imagen si es válida
                if src:
                    images.append({
                        "url": src,
                        "alt": alt,
                        "title": title or alt
                    })
            except Exception:
                continue
        
        return images
    
    def _clean_text(self, text: str) -> str:
        """
        Limpia el texto extraído.
        
        Args:
            text: Texto a limpiar
            
        Returns:
            Texto limpio
        """
        # Eliminar espacios en blanco múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # Eliminar líneas en blanco múltiples
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Eliminar caracteres no imprimibles
        text = ''.join(c for c in text if c.isprintable() or c in ['\n', '\t'])
        
        return text.strip()
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analiza el sentimiento del texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con análisis de sentimiento
        """
        # Implementación básica de análisis de sentimiento
        # En una implementación real, se usaría una biblioteca como NLTK, TextBlob o un modelo de ML
        
        # Palabras positivas y negativas para análisis simple
        positive_words = [
            "bueno", "excelente", "genial", "increíble", "maravilloso", "fantástico",
            "positivo", "agradable", "feliz", "contento", "satisfecho", "encantado",
            "good", "excellent", "great", "amazing", "wonderful", "fantastic",
            "positive", "nice", "happy", "glad", "satisfied", "delighted"
        ]
        
        negative_words = [
            "malo", "terrible", "horrible", "pésimo", "negativo", "desagradable",
            "triste", "enojado", "frustrado", "decepcionado", "insatisfecho",
            "bad", "terrible", "horrible", "awful", "negative", "unpleasant",
            "sad", "angry", "frustrated", "disappointed", "unsatisfied"
        ]
        
        # Convertir a minúsculas y tokenizar
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        # Contar palabras positivas y negativas
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Calcular puntuación de sentimiento (-1 a 1)
        total_count = positive_count + negative_count
        if total_count > 0:
            sentiment_score = (positive_count - negative_count) / total_count
        else:
            sentiment_score = 0
        
        # Determinar sentimiento
        if sentiment_score > 0.2:
            sentiment = "positive"
        elif sentiment_score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        return {
            "sentiment": sentiment,
            "score": sentiment_score,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "confidence": abs(sentiment_score) if abs(sentiment_score) > 0.5 else 0.5
        }
