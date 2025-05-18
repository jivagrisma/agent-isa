"""
Módulo de Búsqueda Web para agent-isa.
Proporciona capacidades de búsqueda, navegación y extracción de contenido web.
"""

from .web_search import WebSearchEngine, SearchResult
from .headless_browser import HeadlessBrowser

__all__ = ['WebSearchEngine', 'SearchResult', 'HeadlessBrowser']
