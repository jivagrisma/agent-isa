#!/usr/bin/env python3
"""
Interfaz de línea de comandos para agent-isa.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Función principal para la interfaz de línea de comandos.
    """
    parser = argparse.ArgumentParser(description="Agent-ISA CLI")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: web
    web_parser = subparsers.add_parser("web", help="Iniciar interfaz web")
    web_parser.add_argument("--port", type=int, default=8005, help="Puerto para la aplicación web")
    web_parser.add_argument("--host", type=str, default="0.0.0.0", help="Host para la aplicación web")
    
    # Comando: chat
    chat_parser = subparsers.add_parser("chat", help="Iniciar chat en línea de comandos")
    chat_parser.add_argument("--model", type=str, default="default", help="Modelo a utilizar")
    
    # Comando: plugins
    plugins_parser = subparsers.add_parser("plugins", help="Gestionar plugins")
    plugins_parser.add_argument("--list", action="store_true", help="Listar plugins disponibles")
    plugins_parser.add_argument("--info", type=str, help="Mostrar información de un plugin")
    
    # Comando: config
    config_parser = subparsers.add_parser("config", help="Gestionar configuración")
    config_parser.add_argument("--show", type=str, help="Mostrar configuración de un módulo")
    config_parser.add_argument("--set", nargs=3, metavar=("MODULE", "KEY", "VALUE"), help="Establecer valor de configuración")
    
    # Comando: version
    version_parser = subparsers.add_parser("version", help="Mostrar versión")
    
    # Parsear argumentos
    args = parser.parse_args()
    
    # Si no se especifica comando, mostrar ayuda
    if not args.command:
        parser.print_help()
        return
    
    # Ejecutar comando
    if args.command == "web":
        run_web_interface(args.host, args.port)
    elif args.command == "chat":
        run_cli_chat(args.model)
    elif args.command == "plugins":
        manage_plugins(args)
    elif args.command == "config":
        manage_config(args)
    elif args.command == "version":
        show_version()

def run_web_interface(host, port):
    """
    Inicia la interfaz web.
    
    Args:
        host: Host para la aplicación web
        port: Puerto para la aplicación web
    """
    try:
        # Importar módulo de interfaz web
        from OpenManusWeb.simple_chat import main as web_main
        
        # Configurar argumentos
        sys.argv = [sys.argv[0], "--host", host, "--port", str(port)]
        
        # Iniciar interfaz web
        web_main()
    except ImportError:
        logger.error("No se pudo importar el módulo de interfaz web.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error al iniciar la interfaz web: {e}")
        sys.exit(1)

def run_cli_chat(model):
    """
    Inicia el chat en línea de comandos.
    
    Args:
        model: Modelo a utilizar
    """
    try:
        # Importar módulo de chat CLI
        from OpenManusWeb.test_cli import main as cli_main
        
        # Configurar argumentos
        sys.argv = [sys.argv[0], "--model", model]
        
        # Iniciar chat CLI
        cli_main()
    except ImportError:
        logger.error("No se pudo importar el módulo de chat CLI.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error al iniciar el chat CLI: {e}")
        sys.exit(1)

def manage_plugins(args):
    """
    Gestiona plugins.
    
    Args:
        args: Argumentos de línea de comandos
    """
    try:
        # Importar gestor de plugins
        from OpenManusWeb.modules.core import PluginManager
        
        # Crear gestor de plugins
        plugin_manager = PluginManager()
        
        # Descubrir plugins
        plugins = plugin_manager.discover_plugins()
        
        if args.list:
            # Listar plugins
            print("Plugins disponibles:")
            for name, plugin_class in plugins.items():
                print(f"  - {name}: {plugin_class.get_description()}")
        elif args.info:
            # Mostrar información de un plugin
            if args.info in plugins:
                plugin_class = plugins[args.info]
                print(f"Plugin: {args.info}")
                print(f"Descripción: {plugin_class.get_description()}")
                print(f"Versión: {plugin_class.get_version()}")
                print(f"Dependencias: {', '.join(plugin_class.get_dependencies()) or 'Ninguna'}")
            else:
                print(f"Plugin no encontrado: {args.info}")
        else:
            print("Uso: agent-isa plugins --list | --info PLUGIN")
    except ImportError:
        logger.error("No se pudo importar el gestor de plugins.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error al gestionar plugins: {e}")
        sys.exit(1)

def manage_config(args):
    """
    Gestiona configuración.
    
    Args:
        args: Argumentos de línea de comandos
    """
    try:
        # Importar gestor de configuración
        from OpenManusWeb.modules.core import ConfigManager
        
        # Crear gestor de configuración
        config_manager = ConfigManager()
        
        if args.show:
            # Mostrar configuración
            config = config_manager.get_config(args.show)
            if config:
                import json
                print(json.dumps(config, indent=2))
            else:
                print(f"No hay configuración para el módulo: {args.show}")
        elif args.set:
            # Establecer valor de configuración
            module, key, value = args.set
            
            # Intentar convertir el valor a tipo adecuado
            try:
                # Intentar como número
                if value.isdigit():
                    value = int(value)
                elif value.replace(".", "", 1).isdigit():
                    value = float(value)
                # Intentar como booleano
                elif value.lower() in ["true", "false"]:
                    value = value.lower() == "true"
            except:
                # Mantener como string si falla la conversión
                pass
            
            config_manager.set_config(module, key, value)
            config_manager.save_config(module)
            print(f"Configuración actualizada: {module}.{key} = {value}")
        else:
            print("Uso: agent-isa config --show MODULE | --set MODULE KEY VALUE")
    except ImportError:
        logger.error("No se pudo importar el gestor de configuración.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error al gestionar configuración: {e}")
        sys.exit(1)

def show_version():
    """
    Muestra la versión de agent-isa.
    """
    try:
        # Intentar obtener versión del paquete
        import pkg_resources
        version = pkg_resources.get_distribution("agent-isa-manus").version
    except:
        # Si falla, usar versión por defecto
        version = "0.1.0"
    
    print(f"agent-isa versión {version}")
    print("Desarrollado por Jorge Grisales (jivagrisma@gmail.com)")

if __name__ == "__main__":
    main()
