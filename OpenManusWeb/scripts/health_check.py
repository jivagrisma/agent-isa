#!/usr/bin/env python3
"""
Script para verificar la salud del sistema.
Realiza verificaciones de salud y genera un informe.
"""

import os
import sys
import time
import json
import socket
import platform
import psutil
import requests
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Colores para mensajes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

def log(message):
    """Imprime un mensaje informativo."""
    print(f"{GREEN}[INFO] {message}{NC}")

def warn(message):
    """Imprime un mensaje de advertencia."""
    print(f"{YELLOW}[ADVERTENCIA] {message}{NC}")

def error(message):
    """Imprime un mensaje de error."""
    print(f"{RED}[ERROR] {message}{NC}")

def check_system_resources():
    """
    Verifica recursos del sistema.
    
    Returns:
        Diccionario con resultados
    """
    log("Verificando recursos del sistema...")
    
    # Obtener información del sistema
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Verificar umbrales
    cpu_ok = cpu_percent < 80
    memory_ok = memory.percent < 80
    disk_ok = disk.percent < 80
    
    # Mostrar resultados
    log(f"CPU: {cpu_percent:.1f}% {'✓' if cpu_ok else '✗'}")
    log(f"Memoria: {memory.percent:.1f}% ({memory.used / (1024**3):.1f} GB / {memory.total / (1024**3):.1f} GB) {'✓' if memory_ok else '✗'}")
    log(f"Disco: {disk.percent:.1f}% ({disk.used / (1024**3):.1f} GB / {disk.total / (1024**3):.1f} GB) {'✓' if disk_ok else '✗'}")
    
    # Verificar procesos
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            # Filtrar procesos relevantes
            if proc.info['cpu_percent'] > 5 or proc.info['memory_percent'] > 5:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'username': proc.info['username'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    # Ordenar por uso de CPU
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    
    # Mostrar procesos principales
    if processes:
        log("Procesos principales:")
        for i, proc in enumerate(processes[:5]):
            print(f"  {proc['name']} (PID: {proc['pid']}): CPU {proc['cpu_percent']:.1f}%, Memoria {proc['memory_percent']:.1f}%")
    
    return {
        'cpu': {
            'percent': cpu_percent,
            'ok': cpu_ok
        },
        'memory': {
            'percent': memory.percent,
            'used': memory.used,
            'total': memory.total,
            'ok': memory_ok
        },
        'disk': {
            'percent': disk.percent,
            'used': disk.used,
            'total': disk.total,
            'ok': disk_ok
        },
        'processes': processes[:5]
    }

def check_network():
    """
    Verifica conectividad de red.
    
    Returns:
        Diccionario con resultados
    """
    log("Verificando conectividad de red...")
    
    # Lista de servicios a verificar
    services = [
        ("AWS S3", "s3.amazonaws.com", 443),
        ("AWS CloudWatch", "monitoring.amazonaws.com", 443),
        ("AWS Bedrock", "bedrock-runtime.us-east-1.amazonaws.com", 443),
        ("GitHub", "github.com", 443)
    ]
    
    results = {}
    
    for service, host, port in services:
        try:
            # Medir tiempo de respuesta
            start_time = time.time()
            
            # Intentar conexión TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            # Calcular tiempo de respuesta
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Verificar resultado
            if result == 0:
                log(f"Conectividad a {service} ({host}:{port}): {response_time:.1f} ms ✓")
                status = "ok"
            else:
                error(f"No se puede conectar a {service} ({host}:{port}) ✗")
                status = "error"
            
            results[service] = {
                'host': host,
                'port': port,
                'status': status,
                'response_time': response_time if status == "ok" else None,
                'error_code': result if status == "error" else None
            }
            
        except Exception as e:
            error(f"Error al verificar {service} ({host}:{port}): {e} ✗")
            results[service] = {
                'host': host,
                'port': port,
                'status': "error",
                'response_time': None,
                'error': str(e)
            }
    
    return results

def check_application(url: str = "http://localhost:8000"):
    """
    Verifica la aplicación.
    
    Args:
        url: URL base de la aplicación
        
    Returns:
        Diccionario con resultados
    """
    log(f"Verificando aplicación en {url}...")
    
    # Endpoints a verificar
    endpoints = [
        ("/", "Página principal"),
        ("/health", "Estado de salud"),
        ("/api/status", "Estado de la API")
    ]
    
    results = {}
    
    for endpoint, description in endpoints:
        try:
            # Medir tiempo de respuesta
            start_time = time.time()
            
            # Realizar solicitud
            response = requests.get(f"{url}{endpoint}", timeout=5)
            
            # Calcular tiempo de respuesta
            response_time = (time.time() - start_time) * 1000  # ms
            
            # Verificar código de estado
            if response.status_code == 200:
                log(f"{description} ({endpoint}): {response_time:.1f} ms ✓")
                status = "ok"
            else:
                warn(f"{description} ({endpoint}): Código {response.status_code} ({response_time:.1f} ms) ⚠")
                status = "warning"
            
            # Guardar resultado
            results[endpoint] = {
                'description': description,
                'status_code': response.status_code,
                'response_time': response_time,
                'status': status
            }
            
            # Analizar respuesta JSON si es posible
            try:
                if response.headers.get('Content-Type', '').startswith('application/json'):
                    results[endpoint]['response'] = response.json()
            except:
                pass
            
        except requests.exceptions.RequestException as e:
            error(f"{description} ({endpoint}): Error de conexión: {e} ✗")
            results[endpoint] = {
                'description': description,
                'status': "error",
                'error': str(e)
            }
    
    return results

def check_services():
    """
    Verifica servicios del sistema.
    
    Returns:
        Diccionario con resultados
    """
    log("Verificando servicios del sistema...")
    
    # Lista de servicios a verificar
    services = [
        "agent-isa",
        "nginx",
        "supervisor"
    ]
    
    results = {}
    
    for service in services:
        try:
            # Verificar si el servicio está en ejecución
            if platform.system() == "Windows":
                # En Windows, usar sc query
                import subprocess
                result = subprocess.run(['sc', 'query', service], capture_output=True, text=True)
                running = "RUNNING" in result.stdout
            else:
                # En Linux, usar systemctl
                import subprocess
                result = subprocess.run(['systemctl', 'is-active', service], capture_output=True, text=True)
                running = result.stdout.strip() == "active"
            
            # Mostrar resultado
            if running:
                log(f"Servicio {service}: En ejecución ✓")
                status = "running"
            else:
                error(f"Servicio {service}: No está en ejecución ✗")
                status = "stopped"
            
            results[service] = {
                'status': status
            }
            
        except Exception as e:
            warn(f"Error al verificar servicio {service}: {e}")
            results[service] = {
                'status': "unknown",
                'error': str(e)
            }
    
    return results

def check_logs():
    """
    Verifica logs del sistema.
    
    Returns:
        Diccionario con resultados
    """
    log("Verificando logs del sistema...")
    
    # Lista de archivos de log a verificar
    log_files = [
        "/var/log/agent-isa/application.log",
        "/var/log/nginx/error.log",
        "/var/log/supervisor/supervisord.log"
    ]
    
    results = {}
    
    for log_file in log_files:
        try:
            # Verificar si el archivo existe
            if not os.path.exists(log_file):
                warn(f"Archivo de log no encontrado: {log_file}")
                results[log_file] = {
                    'exists': False
                }
                continue
            
            # Obtener tamaño y fecha de modificación
            size = os.path.getsize(log_file)
            mtime = os.path.getmtime(log_file)
            
            # Verificar si el archivo es muy grande
            size_warning = size > 100 * 1024 * 1024  # 100 MB
            
            # Verificar si el archivo es muy antiguo
            age = time.time() - mtime
            age_warning = age > 86400 * 7  # 7 días
            
            # Mostrar resultado
            log(f"Log {os.path.basename(log_file)}: {size / (1024*1024):.1f} MB, modificado hace {age / 3600:.1f} horas {'⚠' if size_warning or age_warning else '✓'}")
            
            # Buscar errores recientes
            errors = []
            try:
                with open(log_file, 'r', errors='ignore') as f:
                    # Leer las últimas 100 líneas
                    lines = f.readlines()[-100:]
                    
                    # Buscar errores
                    for line in lines:
                        if "ERROR" in line or "CRITICAL" in line or "FATAL" in line:
                            errors.append(line.strip())
            except Exception as e:
                warn(f"Error al leer archivo de log {log_file}: {e}")
            
            # Mostrar errores recientes
            if errors:
                warn(f"Errores recientes en {os.path.basename(log_file)}:")
                for i, err in enumerate(errors[-3:]):  # Mostrar los 3 últimos errores
                    print(f"  {err[:100]}...")
            
            results[log_file] = {
                'exists': True,
                'size': size,
                'size_warning': size_warning,
                'mtime': mtime,
                'age': age,
                'age_warning': age_warning,
                'recent_errors': errors[-5:]  # Guardar los 5 últimos errores
            }
            
        except Exception as e:
            warn(f"Error al verificar archivo de log {log_file}: {e}")
            results[log_file] = {
                'exists': False,
                'error': str(e)
            }
    
    return results

def generate_report(results: Dict[str, Any], output_file: Optional[str] = None):
    """
    Genera un informe de salud.
    
    Args:
        results: Resultados de las verificaciones
        output_file: Archivo de salida (None para no guardar)
    """
    log("Generando informe de salud...")
    
    # Añadir información del sistema
    results['system_info'] = {
        'hostname': socket.gethostname(),
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'timestamp': datetime.now().isoformat()
    }
    
    # Calcular estado general
    status = "ok"
    
    # Verificar recursos
    if not results.get('resources', {}).get('cpu', {}).get('ok', True) or \
       not results.get('resources', {}).get('memory', {}).get('ok', True) or \
       not results.get('resources', {}).get('disk', {}).get('ok', True):
        status = "warning"
    
    # Verificar red
    for service, service_result in results.get('network', {}).items():
        if service_result.get('status') == "error":
            status = "error"
    
    # Verificar aplicación
    for endpoint, endpoint_result in results.get('application', {}).items():
        if endpoint_result.get('status') == "error":
            status = "error"
        elif endpoint_result.get('status') == "warning" and status != "error":
            status = "warning"
    
    # Verificar servicios
    for service, service_result in results.get('services', {}).items():
        if service_result.get('status') != "running":
            status = "error"
    
    # Añadir estado general
    results['status'] = status
    
    # Mostrar estado general
    if status == "ok":
        log("Estado general: OK ✓")
    elif status == "warning":
        warn("Estado general: ADVERTENCIA ⚠")
    else:
        error("Estado general: ERROR ✗")
    
    # Guardar informe
    if output_file:
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            log(f"Informe guardado en {output_file}")
        except Exception as e:
            error(f"Error al guardar informe: {e}")
    
    return results

def main():
    """
    Función principal.
    """
    parser = argparse.ArgumentParser(description="Verificación de salud del sistema")
    parser.add_argument("--url", default="http://localhost:8000", help="URL base de la aplicación")
    parser.add_argument("--output", help="Archivo de salida para el informe")
    args = parser.parse_args()
    
    log("Iniciando verificación de salud del sistema...")
    
    # Realizar verificaciones
    results = {}
    
    # Verificar recursos
    results['resources'] = check_system_resources()
    
    # Verificar red
    results['network'] = check_network()
    
    # Verificar aplicación
    results['application'] = check_application(args.url)
    
    # Verificar servicios
    results['services'] = check_services()
    
    # Verificar logs
    results['logs'] = check_logs()
    
    # Generar informe
    generate_report(results, args.output)
    
    # Determinar código de salida
    if results['status'] == "error":
        return 1
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())
