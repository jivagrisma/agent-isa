#!/usr/bin/env python3
"""
Script de prueba para el módulo de búsqueda web.
"""

import argparse
import asyncio
import json
import logging
import sys
from typing import List, Dict, Any, Optional, Union

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar módulos locales
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos necesarios
from modules.core import ConfigManager
from modules.search import WebSearchEngine, HeadlessBrowser, SearchResult

async def test_web_search(
    query: str,
    num_results: int,
    engine: str,
    language: Optional[str] = None,
    country: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None
):
    """
    Prueba la funcionalidad de búsqueda web.

    Args:
        query: Consulta de búsqueda
        num_results: Número de resultados a mostrar
        engine: Motor de búsqueda a utilizar
        language: Código de idioma (ej. "es", "en")
        country: Código de país (ej. "es", "us")
        filters: Filtros adicionales para la búsqueda
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()

        # Inicializar motor de búsqueda
        search_engine = WebSearchEngine(config_manager)

        # Construir mensaje de búsqueda
        search_msg = f"\n🔍 Buscando '{query}' en {engine}"
        if language:
            search_msg += f", idioma: {language}"
        if country:
            search_msg += f", país: {country}"
        if filters:
            search_msg += f", filtros: {json.dumps(filters, ensure_ascii=False)}"
        print(search_msg + "...\n")

        # Realizar búsqueda
        results = search_engine.search(
            query=query,
            num_results=num_results,
            search_engine=engine,
            language=language,
            country=country,
            filters=filters
        )

        # Mostrar resultados
        if results:
            print(f"✅ Se encontraron {len(results)} resultados:\n")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.title}")
                print(f"   URL: {result.url}")
                print(f"   {result.snippet[:100]}...")

                # Mostrar metadatos si están disponibles
                if result.metadata:
                    metadata_str = ", ".join(f"{k}: {v}" for k, v in result.metadata.items() if v)
                    if metadata_str:
                        print(f"   Metadatos: {metadata_str}")

                print()
        else:
            print("❌ No se encontraron resultados.")

        return results

    except Exception as e:
        logger.error(f"Error en búsqueda web: {e}")
        print(f"❌ Error: {e}")
        return []

async def test_headless_browser(url: str):
    """
    Prueba la funcionalidad del navegador headless.

    Args:
        url: URL a navegar
    """
    try:
        # Inicializar gestor de configuración
        config_manager = ConfigManager()

        # Inicializar navegador headless
        browser = HeadlessBrowser(config_manager)

        try:
            # Navegar a la URL
            print(f"\n🌐 Navegando a {url}...\n")
            content = await browser.navigate(url)

            # Mostrar contenido
            print(f"✅ Contenido extraído ({len(content)} caracteres):\n")
            print(f"{content[:500]}...\n")

            return content

        finally:
            # Cerrar navegador
            await browser.close()

    except Exception as e:
        logger.error(f"Error en navegador headless: {e}")
        print(f"❌ Error: {e}")
        return ""

async def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Prueba del módulo de búsqueda web")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # Comando: search
    search_parser = subparsers.add_parser("search", help="Realizar búsqueda web")
    search_parser.add_argument("query", help="Consulta de búsqueda")
    search_parser.add_argument("--results", type=int, default=5, help="Número de resultados")
    search_parser.add_argument("--engine", default="google", help="Motor de búsqueda")
    search_parser.add_argument("--lang", help="Código de idioma (ej. 'es', 'en')")
    search_parser.add_argument("--country", help="Código de país (ej. 'es', 'us')")
    search_parser.add_argument("--site", help="Filtrar por sitio web")
    search_parser.add_argument("--filetype", help="Filtrar por tipo de archivo")
    search_parser.add_argument("--title", help="Filtrar por palabras en el título")
    search_parser.add_argument("--date", help="Filtrar por fecha (ej. 'd7' para últimos 7 días)")

    # Comando: browse
    browse_parser = subparsers.add_parser("browse", help="Navegar a una URL")
    browse_parser.add_argument("url", help="URL a navegar")

    # Comando: full
    full_parser = subparsers.add_parser("full", help="Búsqueda y navegación")
    full_parser.add_argument("query", help="Consulta de búsqueda")
    full_parser.add_argument("--results", type=int, default=1, help="Número de resultados a navegar")
    full_parser.add_argument("--engine", default="google", help="Motor de búsqueda")
    full_parser.add_argument("--lang", help="Código de idioma (ej. 'es', 'en')")
    full_parser.add_argument("--country", help="Código de país (ej. 'es', 'us')")
    full_parser.add_argument("--site", help="Filtrar por sitio web")

    # Comando: advanced
    advanced_parser = subparsers.add_parser("advanced", help="Búsqueda avanzada con extracción de contenido")
    advanced_parser.add_argument("query", help="Consulta de búsqueda")
    advanced_parser.add_argument("--results", type=int, default=3, help="Número de resultados")
    advanced_parser.add_argument("--engine", default="google", help="Motor de búsqueda")
    advanced_parser.add_argument("--lang", help="Código de idioma (ej. 'es', 'en')")
    advanced_parser.add_argument("--extract", choices=["text", "tables", "links", "all"], default="text",
                                help="Tipo de contenido a extraer")

    args = parser.parse_args()

    if args.command == "search":
        # Construir filtros
        filters = {}
        if args.site:
            filters["site"] = args.site
        if args.filetype:
            filters["file_type"] = args.filetype
        if args.title:
            filters["title_contains"] = args.title
        if args.date:
            filters["date_restrict"] = args.date

        # Realizar búsqueda
        await test_web_search(
            query=args.query,
            num_results=args.results,
            engine=args.engine,
            language=args.lang,
            country=args.country,
            filters=filters if filters else None
        )

    elif args.command == "browse":
        await test_headless_browser(args.url)

    elif args.command == "full":
        # Construir filtros
        filters = {}
        if args.site:
            filters["site"] = args.site

        # Realizar búsqueda
        results = await test_web_search(
            query=args.query,
            num_results=args.results,
            engine=args.engine,
            language=args.lang,
            country=args.country,
            filters=filters if filters else None
        )

        # Navegar al primer resultado
        if results:
            print(f"\n🔄 Navegando al primer resultado...\n")
            await test_headless_browser(results[0].url)

    elif args.command == "advanced":
        # Realizar búsqueda
        results = await test_web_search(
            query=args.query,
            num_results=args.results,
            engine=args.engine,
            language=args.lang
        )

        # Importar extractor de contenido
        from modules.content import ContentExtractor
        content_extractor = ContentExtractor()

        # Navegar y extraer contenido de los resultados
        if results:
            browser = HeadlessBrowser()
            try:
                for i, result in enumerate(results, 1):
                    print(f"\n🔄 Procesando resultado {i}: {result.title}...\n")

                    # Navegar a la URL
                    content = await browser.navigate(result.url)

                    # Extraer contenido según el tipo seleccionado
                    extracted = content_extractor.extract_from_html(content, result.url)

                    # Mostrar contenido extraído según el tipo
                    if args.extract == "text" or args.extract == "all":
                        print(f"\n📄 Contenido principal ({len(extracted['main_content'])} caracteres):")
                        print(f"{extracted['main_content'][:500]}...\n")

                    if (args.extract == "tables" or args.extract == "all") and extracted['tables']:
                        print(f"\n📊 Tablas encontradas: {len(extracted['tables'])}")
                        for j, table in enumerate(extracted['tables'][:2], 1):
                            print(f"  Tabla {j}: {table['title']} ({table['num_rows']} filas, {table['num_cols']} columnas)")

                    if (args.extract == "links" or args.extract == "all") and extracted['links']:
                        print(f"\n🔗 Enlaces encontrados: {len(extracted['links'])}")
                        for j, link in enumerate(extracted['links'][:5], 1):
                            print(f"  {j}. {link['text'][:50]}: {link['url']}")

                        if len(extracted['links']) > 5:
                            print(f"  ... y {len(extracted['links']) - 5} enlaces más")
            finally:
                await browser.close()
        else:
            print("❌ No se encontraron resultados para extraer contenido.")

    else:
        parser.print_help()

if __name__ == "__main__":
    asyncio.run(main())
