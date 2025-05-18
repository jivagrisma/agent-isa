"""
Motor de búsqueda web para agent-isa.
Proporciona capacidades de búsqueda en diferentes motores, incluyendo Tavily.
"""

import logging
import time
import json
import re
import os
from typing import Dict, List, Any, Optional, Union, Callable
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from ..core import PluginInterface, ConfigManager

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logger = logging.getLogger(__name__)

class SearchResult:
    """
    Representa un resultado de búsqueda.
    """

    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa un resultado de búsqueda.

        Args:
            title: Título del resultado
            url: URL del resultado
            snippet: Fragmento de texto del resultado
            source: Fuente del resultado (motor de búsqueda)
            metadata: Metadatos adicionales
        """
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el resultado a un diccionario.

        Returns:
            Diccionario con los datos del resultado
        """
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        """
        Crea un resultado a partir de un diccionario.

        Args:
            data: Diccionario con los datos del resultado

        Returns:
            Instancia de SearchResult
        """
        result = cls(
            title=data["title"],
            url=data["url"],
            snippet=data["snippet"],
            source=data["source"],
            metadata=data.get("metadata", {})
        )
        result.timestamp = data.get("timestamp", time.time())
        return result

class WebSearchEngine(PluginInterface):
    """
    Motor de búsqueda web con soporte para múltiples fuentes.

    Características:
    1. Búsqueda en múltiples motores
    2. Caché de resultados
    3. Filtrado y ranking de resultados
    """

    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager"]

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Inicializa el motor de búsqueda web.

        Args:
            config_manager: Gestor de configuración
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("search")

        # Inicializar caché
        self.cache: Dict[str, List[SearchResult]] = {}

        logger.info("Motor de búsqueda web inicializado")

    def search(
        self,
        query: str,
        num_results: int = 5,
        search_engine: Optional[str] = None,
        use_cache: bool = True,
        language: Optional[str] = None,
        country: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Realiza una búsqueda web.

        Args:
            query: Consulta de búsqueda
            num_results: Número de resultados a devolver
            search_engine: Motor de búsqueda a utilizar (None para usar el predeterminado)
            use_cache: Si debe usar la caché
            language: Código de idioma (ej. "es", "en")
            country: Código de país (ej. "es", "us")
            filters: Filtros adicionales para la búsqueda

        Returns:
            Lista de resultados de búsqueda
        """
        # Normalizar consulta para caché
        cache_params = [query.lower(), str(num_results), search_engine or 'default']
        if language:
            cache_params.append(f"lang:{language}")
        if country:
            cache_params.append(f"country:{country}")
        if filters:
            cache_params.append(f"filters:{json.dumps(filters, sort_keys=True)}")

        cache_key = ":".join(cache_params)

        # Verificar caché si está habilitada
        if use_cache and self.config.get("general.cache_results", True):
            cached_results = self._get_from_cache(cache_key)
            if cached_results:
                logger.info(f"Resultados obtenidos de caché para: {query}")
                return cached_results

        # Determinar motor de búsqueda
        engine = search_engine or self.config.get("search_engine.default", "google")

        # Realizar búsqueda según el motor
        if engine == "google":
            results = self._search_google(query, num_results, language, country, filters)
        elif engine == "bing":
            results = self._search_bing(query, num_results, language, country, filters)
        elif engine == "duckduckgo":
            results = self._search_duckduckgo(query, num_results, language, country, filters)
        else:
            logger.warning(f"Motor de búsqueda no soportado: {engine}")
            results = []

        # Aplicar filtros adicionales si es necesario
        if filters and results:
            results = self._apply_filters(results, filters)

        # Guardar en caché si está habilitada
        if self.config.get("general.cache_results", True) and results:
            self._save_to_cache(cache_key, results)

        return results

    def _search_google(
        self,
        query: str,
        num_results: int,
        language: Optional[str] = None,
        country: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Realiza una búsqueda en Google.

        Args:
            query: Consulta de búsqueda
            num_results: Número de resultados a devolver
            language: Código de idioma (ej. "es", "en")
            country: Código de país (ej. "es", "us")
            filters: Filtros adicionales para la búsqueda

        Returns:
            Lista de resultados de búsqueda
        """
        # Verificar si usar API o web scraping
        if self.config.get("search_engine.google.use_api", False):
            return self._search_google_api(query, num_results, language, country, filters)
        else:
            return self._search_google_scraping(query, num_results, language, country, filters)

    def _search_google_api(
        self,
        query: str,
        num_results: int,
        language: Optional[str] = None,
        country: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Realiza una búsqueda en Google usando la API.

        Args:
            query: Consulta de búsqueda
            num_results: Número de resultados a devolver
            language: Código de idioma (ej. "es", "en")
            country: Código de país (ej. "es", "us")
            filters: Filtros adicionales para la búsqueda

        Returns:
            Lista de resultados de búsqueda
        """
        # Implementación básica usando la API de Google Custom Search
        api_key = self.config.get("search_engine.google.api_key", "")
        cx = self.config.get("search_engine.google.cx", "")

        if not api_key or not cx:
            logger.error("Falta API key o CX para Google Custom Search")
            return []

        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": api_key,
                "cx": cx,
                "q": query,
                "num": min(num_results, 10)  # API limita a 10 resultados por página
            }

            # Añadir parámetros de idioma y país si están disponibles
            if language:
                params["lr"] = f"lang_{language}"

            if country:
                params["gl"] = country

            # Añadir filtros adicionales si están disponibles
            if filters:
                # Filtro de fecha
                if "date_restrict" in filters:
                    params["dateRestrict"] = filters["date_restrict"]

                # Filtro de tipo de archivo
                if "file_type" in filters:
                    params["fileType"] = filters["file_type"]

                # Filtro de sitio
                if "site" in filters:
                    # Añadir site: al inicio de la consulta
                    params["q"] = f"site:{filters['site']} {params['q']}"

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            if "items" in data:
                for item in data["items"]:
                    result = SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source="google",
                        metadata={
                            "displayLink": item.get("displayLink", ""),
                            "formattedUrl": item.get("formattedUrl", ""),
                            "language": language,
                            "country": country
                        }
                    )
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error en búsqueda de Google API: {e}")
            return []

    def _search_google_scraping(
        self,
        query: str,
        num_results: int,
        language: Optional[str] = None,
        country: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Realiza una búsqueda en Google usando web scraping.

        Args:
            query: Consulta de búsqueda
            num_results: Número de resultados a devolver
            language: Código de idioma (ej. "es", "en")
            country: Código de país (ej. "es", "us")
            filters: Filtros adicionales para la búsqueda

        Returns:
            Lista de resultados de búsqueda
        """
        # Implementación básica usando web scraping
        try:
            # Configurar headers para evitar bloqueos
            headers = {
                "User-Agent": self.config.get(
                    "browser.user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                ),
                "Accept-Language": language + ",en-US;q=0.9,en;q=0.8" if language else "en-US,en;q=0.9"
            }

            # Construir consulta con filtros
            search_query = query

            if filters:
                # Filtro de sitio
                if "site" in filters:
                    search_query = f"site:{filters['site']} {search_query}"

                # Filtro de tipo de archivo
                if "file_type" in filters:
                    search_query = f"filetype:{filters['file_type']} {search_query}"

                # Filtro de fecha
                if "date_restrict" in filters:
                    date_value = filters["date_restrict"]
                    if date_value in ["d", "w", "m", "y"]:
                        search_query = f"{search_query} when:{date_value}"
                    elif date_value.startswith("d"):
                        # Formato: d[número] (ej. d5 para 5 días)
                        search_query = f"{search_query} after:{date_value[1:]}"

            # Realizar solicitud
            url = "https://www.google.com/search"
            params = {
                "q": search_query,
                "num": min(num_results, 100)  # Google limita a 100 resultados por página
            }

            # Añadir parámetros de idioma y país si están disponibles
            if language:
                params["hl"] = language

            if country:
                params["gl"] = country

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            # Parsear resultados
            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # Extraer resultados (esto puede cambiar según la estructura de Google)
            for div in soup.select("div.g"):
                try:
                    title_elem = div.select_one("h3")
                    link_elem = div.select_one("a")
                    snippet_elem = div.select_one("div.VwiC3b")

                    if title_elem and link_elem and snippet_elem:
                        title = title_elem.text
                        url = link_elem["href"]
                        snippet = snippet_elem.text

                        # Verificar que la URL sea válida
                        if url.startswith("http"):
                            # Extraer metadatos adicionales
                            metadata = {
                                "language": language,
                                "country": country
                            }

                            # Extraer fecha si está disponible
                            date_elem = div.select_one("span.MUxGbd.wuQ4Ob.WZ8Tjf")
                            if date_elem:
                                metadata["date"] = date_elem.text

                            result = SearchResult(
                                title=title,
                                url=url,
                                snippet=snippet,
                                source="google",
                                metadata=metadata
                            )
                            results.append(result)

                            # Limitar número de resultados
                            if len(results) >= num_results:
                                break
                except Exception as e:
                    logger.debug(f"Error al parsear resultado: {e}")

            return results

        except Exception as e:
            logger.error(f"Error en búsqueda de Google scraping: {e}")
            return []

    def _search_bing(
        self,
        query: str,
        num_results: int,
        language: Optional[str] = None,
        country: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Realiza una búsqueda en Bing.

        Args:
            query: Consulta de búsqueda
            num_results: Número de resultados a devolver
            language: Código de idioma (ej. "es", "en")
            country: Código de país (ej. "es", "us")
            filters: Filtros adicionales para la búsqueda

        Returns:
            Lista de resultados de búsqueda
        """
        # Verificar si usar API o web scraping
        if self.config.get("search_engine.bing.use_api", False):
            return self._search_bing_api(query, num_results, language, country, filters)
        else:
            return self._search_bing_scraping(query, num_results, language, country, filters)

    def _search_bing_api(
        self,
        query: str,
        num_results: int,
        language: Optional[str] = None,
        country: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Realiza una búsqueda en Bing usando la API.

        Args:
            query: Consulta de búsqueda
            num_results: Número de resultados a devolver
            language: Código de idioma (ej. "es", "en")
            country: Código de país (ej. "es", "us")
            filters: Filtros adicionales para la búsqueda

        Returns:
            Lista de resultados de búsqueda
        """
        # Implementación básica usando la API de Bing
        api_key = self.config.get("search_engine.bing.api_key", "")

        if not api_key:
            logger.error("Falta API key para Bing Search")
            return []

        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            headers = {
                "Ocp-Apim-Subscription-Key": api_key
            }

            params = {
                "q": query,
                "count": min(num_results, 50)  # API limita a 50 resultados por página
            }

            # Añadir parámetros de idioma y país si están disponibles
            if language:
                params["setLang"] = language

            if country:
                params["mkt"] = f"{language}-{country.upper()}" if language else f"en-{country.upper()}"

            # Añadir filtros adicionales si están disponibles
            if filters:
                # Filtro de tipo de archivo
                if "file_type" in filters:
                    params["responseFilter"] = "Webpages"

                # Filtro de sitio
                if "site" in filters:
                    params["q"] = f"site:{filters['site']} {params['q']}"

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            if "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"]:
                    result = SearchResult(
                        title=item.get("name", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        source="bing",
                        metadata={
                            "language": language,
                            "country": country,
                            "id": item.get("id", "")
                        }
                    )
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error en búsqueda de Bing API: {e}")
            return []

    def _search_bing_scraping(
        self,
        query: str,
        num_results: int,
        language: Optional[str] = None,
        country: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Realiza una búsqueda en Bing usando web scraping.

        Args:
            query: Consulta de búsqueda
            num_results: Número de resultados a devolver
            language: Código de idioma (ej. "es", "en")
            country: Código de país (ej. "es", "us")
            filters: Filtros adicionales para la búsqueda

        Returns:
            Lista de resultados de búsqueda
        """
        # Implementación básica usando web scraping
        try:
            # Configurar headers para evitar bloqueos
            headers = {
                "User-Agent": self.config.get(
                    "browser.user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                ),
                "Accept-Language": language + ",en-US;q=0.9,en;q=0.8" if language else "en-US,en;q=0.9"
            }

            # Construir consulta con filtros
            search_query = query

            if filters:
                # Filtro de sitio
                if "site" in filters:
                    search_query = f"site:{filters['site']} {search_query}"

                # Filtro de tipo de archivo
                if "file_type" in filters:
                    search_query = f"filetype:{filters['file_type']} {search_query}"

            # Realizar solicitud
            url = "https://www.bing.com/search"
            params = {
                "q": search_query,
                "count": min(num_results, 50)  # Bing limita a 50 resultados por página
            }

            # Añadir parámetros de idioma y país si están disponibles
            if language:
                params["setLang"] = language

            if country:
                params["cc"] = country

            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()

            # Parsear resultados
            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # Extraer resultados (esto puede cambiar según la estructura de Bing)
            for li in soup.select("li.b_algo"):
                try:
                    title_elem = li.select_one("h2")
                    link_elem = li.select_one("h2 a")
                    snippet_elem = li.select_one("div.b_caption p")

                    if title_elem and link_elem and snippet_elem:
                        title = title_elem.text
                        url = link_elem["href"]
                        snippet = snippet_elem.text

                        # Verificar que la URL sea válida
                        if url.startswith("http"):
                            # Extraer metadatos adicionales
                            metadata = {
                                "language": language,
                                "country": country
                            }

                            # Extraer fecha si está disponible
                            date_elem = li.select_one("span.news_dt")
                            if date_elem:
                                metadata["date"] = date_elem.text

                            result = SearchResult(
                                title=title,
                                url=url,
                                snippet=snippet,
                                source="bing",
                                metadata=metadata
                            )
                            results.append(result)

                            # Limitar número de resultados
                            if len(results) >= num_results:
                                break
                except Exception as e:
                    logger.debug(f"Error al parsear resultado: {e}")

            return results

        except Exception as e:
            logger.error(f"Error en búsqueda de Bing scraping: {e}")
            return []

    def _search_duckduckgo(
        self,
        query: str,
        num_results: int,
        language: Optional[str] = None,
        country: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Realiza una búsqueda en DuckDuckGo.

        Args:
            query: Consulta de búsqueda
            num_results: Número de resultados a devolver
            language: Código de idioma (ej. "es", "en")
            country: Código de país (ej. "es", "us")
            filters: Filtros adicionales para la búsqueda

        Returns:
            Lista de resultados de búsqueda
        """
        # Implementación básica usando web scraping (DuckDuckGo no tiene API pública)
        try:
            # Configurar headers para evitar bloqueos
            headers = {
                "User-Agent": self.config.get(
                    "browser.user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                ),
                "Accept-Language": language + ",en-US;q=0.9,en;q=0.8" if language else "en-US,en;q=0.9"
            }

            # Construir consulta con filtros
            search_query = query

            if filters:
                # Filtro de sitio
                if "site" in filters:
                    search_query = f"site:{filters['site']} {search_query}"

                # Filtro de tipo de archivo
                if "file_type" in filters:
                    search_query = f"filetype:{filters['file_type']} {search_query}"

            # Realizar solicitud
            url = "https://html.duckduckgo.com/html/"
            params = {
                "q": search_query
            }

            # Añadir parámetros de región si está disponible
            if country:
                params["kl"] = f"wt-{country}"

            response = requests.post(url, data=params, headers=headers, timeout=10)
            response.raise_for_status()

            # Parsear resultados
            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            # Extraer resultados
            for result_elem in soup.select(".result"):
                try:
                    title_elem = result_elem.select_one(".result__title")
                    link_elem = result_elem.select_one(".result__url")
                    snippet_elem = result_elem.select_one(".result__snippet")

                    if title_elem and link_elem and snippet_elem:
                        title = title_elem.text.strip()
                        url = link_elem.text.strip()
                        snippet = snippet_elem.text.strip()

                        # Verificar que la URL sea válida
                        if not url.startswith(("http://", "https://")):
                            url = "https://" + url

                        # Extraer metadatos adicionales
                        metadata = {
                            "language": language,
                            "country": country
                        }

                        result = SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            source="duckduckgo",
                            metadata=metadata
                        )
                        results.append(result)

                        # Limitar número de resultados
                        if len(results) >= num_results:
                            break
                except Exception as e:
                    logger.debug(f"Error al parsear resultado: {e}")

            return results

        except Exception as e:
            logger.error(f"Error en búsqueda de DuckDuckGo: {e}")
            return []

    def _get_from_cache(self, cache_key: str) -> Optional[List[SearchResult]]:
        """
        Obtiene resultados de caché si están disponibles.

        Args:
            cache_key: Clave de caché

        Returns:
            Lista de resultados o None si no están en caché o han expirado
        """
        if cache_key not in self.cache:
            return None

        # Verificar expiración
        results = self.cache[cache_key]
        if not results:
            return None

        # Verificar tiempo de expiración
        cache_expiry = self.config.get("general.cache_expiry", 3600)  # 1 hora por defecto
        if time.time() - results[0].timestamp > cache_expiry:
            # Caché expirada
            del self.cache[cache_key]
            return None

        return results

    def _save_to_cache(self, cache_key: str, results: List[SearchResult]) -> None:
        """
        Guarda resultados en caché.

        Args:
            cache_key: Clave de caché
            results: Lista de resultados
        """
        self.cache[cache_key] = results

    def _apply_filters(self, results: List[SearchResult], filters: Dict[str, Any]) -> List[SearchResult]:
        """
        Aplica filtros adicionales a los resultados.

        Args:
            results: Lista de resultados
            filters: Filtros a aplicar

        Returns:
            Lista de resultados filtrados
        """
        filtered_results = results

        # Filtrar por dominio
        if "domain" in filters:
            domain = filters["domain"]
            filtered_results = [r for r in filtered_results if domain in r.url]

        # Filtrar por palabras clave en el título
        if "title_contains" in filters:
            title_keywords = filters["title_contains"]
            if isinstance(title_keywords, str):
                title_keywords = [title_keywords]

            filtered_results = [
                r for r in filtered_results
                if any(keyword.lower() in r.title.lower() for keyword in title_keywords)
            ]

        # Filtrar por palabras clave en el snippet
        if "snippet_contains" in filters:
            snippet_keywords = filters["snippet_contains"]
            if isinstance(snippet_keywords, str):
                snippet_keywords = [snippet_keywords]

            filtered_results = [
                r for r in filtered_results
                if any(keyword.lower() in r.snippet.lower() for keyword in snippet_keywords)
            ]

        # Filtrar por fecha (si está disponible en los metadatos)
        if "date_after" in filters and filtered_results:
            # Implementación básica - en una versión real se usaría parsing de fechas
            filtered_results = [
                r for r in filtered_results
                if "date" in r.metadata and r.metadata["date"] >= filters["date_after"]
            ]

        # Ordenar resultados
        if "sort_by" in filters:
            sort_key = filters["sort_by"]
            reverse = filters.get("sort_order", "desc").lower() == "desc"

            if sort_key == "date":
                # Ordenar por fecha (si está disponible)
                filtered_results.sort(
                    key=lambda r: r.metadata.get("date", ""),
                    reverse=reverse
                )
            elif sort_key == "relevance":
                # Ya están ordenados por relevancia
                pass

        return filtered_results
