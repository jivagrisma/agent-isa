#!/usr/bin/env python3
"""
Script para verificar dependencias del sistema para agent-isa.
Verifica que todas las dependencias necesarias estén instaladas y configuradas.
"""

import os
import sys
import platform
import subprocess
import shutil
import importlib
import pkg_resources
import json
from pathlib import Path

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

def check_python_version():
    """Verifica la versión de Python."""
    log("Verificando versión de Python...")
    
    version = platform.python_version()
    version_tuple = tuple(map(int, version.split('.')))
    
    if version_tuple < (3, 8):
        error(f"Se requiere Python 3.8 o superior. Versión actual: {version}")
        return False
    
    log(f"Versión de Python: {version} ✓")
    return True

def check_system_packages():
    """Verifica paquetes del sistema."""
    log("Verificando paquetes del sistema...")
    
    required_packages = {
        "supervisor": "Supervisor (gestor de procesos)",
        "nginx": "Nginx (servidor web)",
        "git": "Git (control de versiones)"
    }
    
    missing_packages = []
    
    for package, description in required_packages.items():
        if shutil.which(package) is None:
            missing_packages.append(f"{package} ({description})")
    
    if missing_packages:
        error("Faltan los siguientes paquetes del sistema:")
        for package in missing_packages:
            error(f"  - {package}")
        
        # Sugerir comandos de instalación
        if platform.system() == "Linux":
            distro = get_linux_distro()
            if distro in ["Ubuntu", "Debian"]:
                warn("Puede instalarlos con:")
                warn(f"  sudo apt-get update && sudo apt-get install -y {' '.join(p.split()[0] for p in missing_packages)}")
            elif distro in ["CentOS", "RHEL", "Fedora", "Amazon"]:
                warn("Puede instalarlos con:")
                warn(f"  sudo yum install -y {' '.join(p.split()[0] for p in missing_packages)}")
        
        return False
    
    log("Todos los paquetes del sistema están instalados ✓")
    return True

def get_linux_distro():
    """Obtiene la distribución de Linux."""
    try:
        with open("/etc/os-release") as f:
            lines = f.readlines()
            
        os_info = {}
        for line in lines:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os_info[key] = value.strip('"')
        
        return os_info.get("NAME", "Unknown")
    except:
        return "Unknown"

def check_python_packages():
    """Verifica paquetes de Python."""
    log("Verificando paquetes de Python...")
    
    # Leer requirements.txt
    repo_dir = Path(__file__).parent.parent.parent
    requirements_files = list(repo_dir.glob("**/requirements*.txt"))
    
    if not requirements_files:
        warn("No se encontraron archivos requirements.txt")
        return True
    
    # Combinar todos los requirements
    required_packages = set()
    for req_file in requirements_files:
        try:
            with open(req_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Eliminar versiones y comentarios
                        package = line.split("==")[0].split(">=")[0].split(">")[0].split("<")[0].split("#")[0].strip()
                        if package:
                            required_packages.add(package)
        except Exception as e:
            warn(f"Error al leer {req_file}: {e}")
    
    # Verificar paquetes instalados
    installed_packages = {pkg.key for pkg in pkg_resources.working_set}
    missing_packages = [pkg for pkg in required_packages if pkg.lower() not in installed_packages]
    
    if missing_packages:
        error("Faltan los siguientes paquetes de Python:")
        for package in missing_packages:
            error(f"  - {package}")
        
        warn("Puede instalarlos con:")
        warn(f"  pip install {' '.join(missing_packages)}")
        
        return False
    
    log("Todos los paquetes de Python están instalados ✓")
    return True

def check_aws_credentials():
    """Verifica credenciales de AWS."""
    log("Verificando credenciales de AWS...")
    
    # Verificar variables de entorno
    aws_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region = os.environ.get("AWS_REGION")
    
    if aws_key and aws_secret:
        log("Credenciales de AWS encontradas en variables de entorno ✓")
        return True
    
    # Verificar archivo de credenciales
    home = Path.home()
    aws_creds_file = home / ".aws" / "credentials"
    aws_config_file = home / ".aws" / "config"
    
    if aws_creds_file.exists():
        log("Archivo de credenciales de AWS encontrado ✓")
        return True
    
    # Verificar perfil de instancia EC2
    try:
        import requests
        response = requests.get("http://169.254.169.254/latest/meta-data/iam/info", timeout=1)
        if response.status_code == 200:
            log("Perfil de instancia EC2 encontrado ✓")
            return True
    except:
        pass
    
    warn("No se encontraron credenciales de AWS")
    warn("Puede configurarlas con:")
    warn("  1. Variables de entorno: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION")
    warn("  2. Archivo de credenciales: ~/.aws/credentials")
    warn("  3. Perfil de instancia EC2")
    
    return False

def check_network_connectivity():
    """Verifica conectividad de red."""
    log("Verificando conectividad de red...")
    
    # Lista de servicios a verificar
    services = [
        ("AWS S3", "s3.amazonaws.com", 443),
        ("AWS CloudWatch", "monitoring.amazonaws.com", 443),
        ("AWS Bedrock", "bedrock-runtime.us-east-1.amazonaws.com", 443),
        ("GitHub", "github.com", 443)
    ]
    
    failed_services = []
    
    for service, host, port in services:
        try:
            # Intentar conexión TCP
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                log(f"Conectividad a {service} ({host}:{port}) ✓")
            else:
                failed_services.append((service, host, port))
        except Exception as e:
            failed_services.append((service, host, port))
    
    if failed_services:
        error("Problemas de conectividad con los siguientes servicios:")
        for service, host, port in failed_services:
            error(f"  - {service} ({host}:{port})")
        
        return False
    
    log("Conectividad de red verificada ✓")
    return True

def check_disk_space():
    """Verifica espacio en disco."""
    log("Verificando espacio en disco...")
    
    # Obtener espacio en disco
    if platform.system() == "Windows":
        # En Windows
        free_bytes = shutil.disk_usage("/").free
    else:
        # En Unix/Linux
        stat = os.statvfs("/")
        free_bytes = stat.f_bavail * stat.f_frsize
    
    # Convertir a GB
    free_gb = free_bytes / (1024 ** 3)
    
    # Verificar espacio mínimo (2 GB)
    if free_gb < 2:
        error(f"Espacio en disco insuficiente: {free_gb:.2f} GB (mínimo recomendado: 2 GB)")
        return False
    
    log(f"Espacio en disco disponible: {free_gb:.2f} GB ✓")
    return True

def check_permissions():
    """Verifica permisos de directorios."""
    log("Verificando permisos de directorios...")
    
    # Directorios a verificar
    directories = [
        "/opt/agent-isa" if platform.system() != "Windows" else "C:\\agent-isa",
        "/var/log/agent-isa" if platform.system() != "Windows" else "C:\\agent-isa\\logs"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        
        # Verificar si existe
        if not dir_path.exists():
            warn(f"El directorio {directory} no existe")
            continue
        
        # Verificar permisos de escritura
        if not os.access(directory, os.W_OK):
            error(f"No tiene permisos de escritura en {directory}")
            return False
    
    log("Permisos de directorios verificados ✓")
    return True

def generate_report():
    """Genera un reporte de verificación."""
    log("Generando reporte de verificación...")
    
    report = {
        "system": {
            "os": platform.system(),
            "os_version": platform.version(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        },
        "checks": {
            "python_version": check_python_version(),
            "system_packages": check_system_packages(),
            "python_packages": check_python_packages(),
            "aws_credentials": check_aws_credentials(),
            "network_connectivity": check_network_connectivity(),
            "disk_space": check_disk_space(),
            "permissions": check_permissions()
        },
        "timestamp": import_module("datetime").datetime.now().isoformat()
    }
    
    # Guardar reporte
    report_path = Path("dependency_check_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    log(f"Reporte guardado en {report_path.absolute()}")
    
    # Verificar resultado general
    all_passed = all(report["checks"].values())
    
    if all_passed:
        log("Todas las verificaciones pasaron exitosamente ✓")
    else:
        error("Algunas verificaciones fallaron. Revise el reporte para más detalles.")
    
    return all_passed

def import_module(module_name):
    """Importa un módulo de forma segura."""
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None

def main():
    """Función principal."""
    log("Iniciando verificación de dependencias para agent-isa...")
    
    # Ejecutar verificaciones
    python_ok = check_python_version()
    system_packages_ok = check_system_packages()
    python_packages_ok = check_python_packages()
    aws_credentials_ok = check_aws_credentials()
    network_ok = check_network_connectivity()
    disk_space_ok = check_disk_space()
    permissions_ok = check_permissions()
    
    # Verificar resultado general
    all_passed = (
        python_ok and
        system_packages_ok and
        python_packages_ok and
        aws_credentials_ok and
        network_ok and
        disk_space_ok and
        permissions_ok
    )
    
    if all_passed:
        log("Todas las dependencias están correctamente configuradas ✓")
        return 0
    else:
        error("Algunas dependencias no están correctamente configuradas")
        return 1

if __name__ == "__main__":
    sys.exit(main())
