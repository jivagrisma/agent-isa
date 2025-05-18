"""
Manejador de logs para CloudWatch Logs.
Proporciona un manejador de logging para enviar logs a CloudWatch Logs.
"""

import logging
import time
import json
import threading
import queue
from typing import Dict, List, Any, Optional, Union

from .cloudwatch_manager import CloudWatchManager

class CloudWatchLogsHandler(logging.Handler):
    """
    Manejador de logging para enviar logs a CloudWatch Logs.
    
    Características:
    1. Envío asíncrono de logs
    2. Agrupación de logs para reducir llamadas a la API
    3. Reintentos automáticos
    4. Formateo personalizable
    """
    
    def __init__(
        self,
        cloudwatch_manager: CloudWatchManager,
        batch_size: int = 10,
        batch_interval: float = 5.0,
        max_retries: int = 3,
        retry_interval: float = 1.0
    ):
        """
        Inicializa el manejador de logs para CloudWatch.
        
        Args:
            cloudwatch_manager: Gestor de CloudWatch
            batch_size: Tamaño máximo del lote de logs
            batch_interval: Intervalo máximo entre envíos (segundos)
            max_retries: Número máximo de reintentos
            retry_interval: Intervalo entre reintentos (segundos)
        """
        super().__init__()
        
        self.cloudwatch_manager = cloudwatch_manager
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        
        # Cola de mensajes
        self.log_queue = queue.Queue()
        
        # Estado del hilo
        self.running = True
        
        # Iniciar hilo de procesamiento
        self.worker_thread = threading.Thread(target=self._process_logs)
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def emit(self, record: logging.LogRecord):
        """
        Emite un registro de log.
        
        Args:
            record: Registro de log
        """
        try:
            # Formatear mensaje
            message = self.format(record)
            
            # Crear entrada de log
            log_entry = {
                "timestamp": int(record.created * 1000),
                "level": record.levelname,
                "logger": record.name,
                "message": message,
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName
            }
            
            # Añadir excepciones si existen
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            # Añadir a la cola
            self.log_queue.put(log_entry)
            
        except Exception as e:
            # Evitar recursión infinita
            self.handleError(record)
    
    def _process_logs(self):
        """
        Procesa los logs en la cola.
        """
        batch = []
        last_send_time = time.time()
        
        while self.running:
            try:
                # Intentar obtener un mensaje con timeout
                try:
                    log_entry = self.log_queue.get(timeout=0.1)
                    batch.append(log_entry)
                    self.log_queue.task_done()
                except queue.Empty:
                    # No hay mensajes nuevos
                    pass
                
                # Verificar si debemos enviar el lote
                current_time = time.time()
                batch_full = len(batch) >= self.batch_size
                timeout_reached = current_time - last_send_time >= self.batch_interval
                
                if batch and (batch_full or timeout_reached):
                    # Enviar lote
                    self._send_batch(batch)
                    batch = []
                    last_send_time = current_time
                
            except Exception as e:
                # Registrar error (en stderr para evitar recursión)
                import sys
                print(f"Error en hilo de procesamiento de logs: {e}", file=sys.stderr)
                
                # Esperar un poco antes de continuar
                time.sleep(1)
    
    def _send_batch(self, batch: List[Dict[str, Any]]):
        """
        Envía un lote de logs a CloudWatch Logs.
        
        Args:
            batch: Lote de logs
        """
        # Ordenar por timestamp
        batch.sort(key=lambda x: x["timestamp"])
        
        # Intentar enviar con reintentos
        for attempt in range(self.max_retries + 1):
            try:
                # Enviar logs
                success = self.cloudwatch_manager.put_log_events(batch)
                
                if success:
                    return
                
                # Si falla, esperar antes de reintentar
                if attempt < self.max_retries:
                    time.sleep(self.retry_interval * (2 ** attempt))  # Backoff exponencial
                
            except Exception as e:
                # Registrar error (en stderr para evitar recursión)
                import sys
                print(f"Error al enviar logs a CloudWatch (intento {attempt+1}/{self.max_retries+1}): {e}", file=sys.stderr)
                
                # Si es el último intento, registrar el error y continuar
                if attempt == self.max_retries:
                    print(f"No se pudieron enviar {len(batch)} logs a CloudWatch", file=sys.stderr)
                else:
                    # Esperar antes de reintentar
                    time.sleep(self.retry_interval * (2 ** attempt))  # Backoff exponencial
    
    def close(self):
        """
        Cierra el manejador y espera a que se procesen todos los logs.
        """
        # Marcar como no ejecutando
        self.running = False
        
        # Esperar a que se vacíe la cola
        if hasattr(self, 'log_queue'):
            self.log_queue.join()
        
        # Esperar a que termine el hilo
        if hasattr(self, 'worker_thread') and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        
        # Llamar al método close de la clase base
        super().close()

def setup_cloudwatch_logging(
    logger: logging.Logger,
    cloudwatch_manager: CloudWatchManager,
    level: int = logging.INFO,
    format_string: Optional[str] = None
):
    """
    Configura logging a CloudWatch Logs.
    
    Args:
        logger: Logger a configurar
        cloudwatch_manager: Gestor de CloudWatch
        level: Nivel de logging
        format_string: Formato de los mensajes
    """
    # Verificar si CloudWatch está habilitado
    if not cloudwatch_manager.enabled:
        return
    
    # Inicializar cliente si es necesario
    if not cloudwatch_manager.logs_client:
        cloudwatch_manager.initialize_clients()
    
    # Crear manejador
    handler = CloudWatchLogsHandler(cloudwatch_manager)
    
    # Configurar nivel
    handler.setLevel(level)
    
    # Configurar formato
    if format_string:
        formatter = logging.Formatter(format_string)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            '%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    
    # Añadir manejador al logger
    logger.addHandler(handler)
    
    return handler
