"""
Módulo para búsqueda web utilizando la API de Tavily.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logger = logging.getLogger(__name__)

class TavilySearchEngine:
    """
    Motor de búsqueda web que utiliza la API de Tavily.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el motor de búsqueda Tavily.
        
        Args:
            api_key: API key de Tavily (opcional, si no se proporciona se toma de las variables de entorno)
        """
        # Obtener API key
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY", "")
        if not self.api_key:
            logger.warning("No se encontró API key para Tavily. Configure la variable de entorno TAVILY_API_KEY.")
        
        # URL base de la API
        self.api_url = "https://api.tavily.com/search"
        
        logger.info("Motor de búsqueda Tavily inicializado")
    
    def search(self, 
               query: str, 
               max_results: int = 5, 
               search_depth: str = "basic",
               include_domains: Optional[List[str]] = None,
               exclude_domains: Optional[List[str]] = None,
               include_answer: bool = True,
               include_raw_content: bool = False) -> Dict[str, Any]:
        """
        Realiza una búsqueda web utilizando la API de Tavily.
        
        Args:
            query: Consulta de búsqueda
            max_results: Número máximo de resultados (por defecto 5)
            search_depth: Profundidad de búsqueda ("basic" o "comprehensive")
            include_domains: Lista de dominios a incluir
            exclude_domains: Lista de dominios a excluir
            include_answer: Incluir respuesta generada
            include_raw_content: Incluir contenido sin procesar
            
        Returns:
            Resultados de la búsqueda
        """
        if not self.api_key:
            logger.error("No se puede realizar la búsqueda: API key de Tavily no configurada")
            return {"error": "API key de Tavily no configurada"}
        
        # Preparar parámetros
        params = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": include_answer,
            "include_raw_content": include_raw_content
        }
        
        # Añadir dominios si se proporcionan
        if include_domains:
            params["include_domains"] = include_domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains
        
        try:
            # Realizar solicitud
            response = requests.post(self.api_url, json=params)
            response.raise_for_status()
            
            # Procesar respuesta
            results = response.json()
            
            # Registrar resultados
            logger.info(f"Búsqueda completada: {query} - {len(results.get('results', []))} resultados")
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al realizar búsqueda en Tavily: {e}")
            return {"error": str(e)}
    
    def format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Formatea los resultados de la búsqueda en un formato estándar.
        
        Args:
            results: Resultados de la búsqueda
            
        Returns:
            Lista de resultados formateados
        """
        formatted_results = []
        
        # Verificar si hay error
        if "error" in results:
            return [{"title": "Error", "url": "", "snippet": results["error"], "source": "tavily"}]
        
        # Verificar si hay respuesta generada
        if "answer" in results and results["answer"]:
            formatted_results.append({
                "title": "Respuesta generada",
                "url": "",
                "snippet": results["answer"],
                "source": "tavily",
                "metadata": {"type": "answer"}
            })
        
        # Añadir resultados individuales
        for result in results.get("results", []):
            formatted_results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("content", ""),
                "source": "tavily",
                "metadata": {
                    "score": result.get("score", 0),
                    "type": "result"
                }
            })
        
        return formatted_results
