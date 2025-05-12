#!/usr/bin/env python3
"""
Configuración del logger para la aplicación.
"""

import logging
import sys

# Configurar el logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Crear un handler para la consola
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Crear un formato para los logs
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Añadir el handler al logger
logger.addHandler(console_handler)
