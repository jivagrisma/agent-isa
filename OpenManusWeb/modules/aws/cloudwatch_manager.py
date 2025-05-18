"""
Gestor de CloudWatch para agent-isa.
Proporciona funcionalidades para monitoreo y logging en AWS CloudWatch.
"""

import os
import logging
import json
import time
import datetime
import boto3
import botocore
from typing import Dict, List, Any, Optional, Union

from ..core import PluginInterface, ConfigManager, EnvironmentManager

# Configurar logging
logger = logging.getLogger(__name__)

class CloudWatchManager(PluginInterface):
    """
    Gestor de AWS CloudWatch para monitoreo y logging.
    
    Características:
    1. Envío de logs a CloudWatch Logs
    2. Publicación de métricas personalizadas
    3. Creación de alarmas
    4. Consulta de logs y métricas
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager", "core.EnvironmentManager"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None, env_manager: Optional[EnvironmentManager] = None):
        """
        Inicializa el gestor de CloudWatch.
        
        Args:
            config_manager: Gestor de configuración
            env_manager: Gestor de entornos
        """
        self.config_manager = config_manager or ConfigManager()
        self.env_manager = env_manager or EnvironmentManager()
        
        # Cargar configuración
        self.config = self.config_manager.get_config("aws")
        self.env_config = self.env_manager.get_config()
        
        # Inicializar clientes
        self.logs_client = None
        self.cloudwatch_client = None
        
        # Configuración de CloudWatch
        self.enabled = self.env_config.get("aws", {}).get("cloudwatch", {}).get("enabled", False)
        self.log_group = self.env_config.get("aws", {}).get("cloudwatch", {}).get("log_group", "agent-isa")
        self.log_stream = self.env_config.get("aws", {}).get("cloudwatch", {}).get("log_stream", "application")
        self.metrics_namespace = self.env_config.get("aws", {}).get("cloudwatch", {}).get("metrics_namespace", "AgentISA")
        
        # Secuencia de tokens para logs
        self.sequence_token = None
        
        logger.info(f"Gestor de CloudWatch inicializado (enabled: {self.enabled})")
    
    def initialize_clients(self):
        """
        Inicializa los clientes de CloudWatch.
        
        Returns:
            True si se inicializó correctamente
        """
        if not self.enabled:
            logger.info("CloudWatch está desactivado en la configuración")
            return False
        
        try:
            # Determinar si usar perfil de instancia
            use_instance_profile = self.env_config.get("aws", {}).get("use_instance_profile", False)
            region = self.env_config.get("aws", {}).get("region", "us-east-1")
            
            # Crear clientes
            if use_instance_profile:
                # Usar perfil de instancia EC2
                self.logs_client = boto3.client("logs", region_name=region)
                self.cloudwatch_client = boto3.client("cloudwatch", region_name=region)
            else:
                # Usar credenciales configuradas
                self.logs_client = boto3.client(
                    "logs",
                    region_name=region,
                    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
                )
                self.cloudwatch_client = boto3.client(
                    "cloudwatch",
                    region_name=region,
                    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
                )
            
            # Crear grupo de logs si no existe
            try:
                self.logs_client.create_log_group(logGroupName=self.log_group)
                logger.info(f"Grupo de logs creado: {self.log_group}")
            except self.logs_client.exceptions.ResourceAlreadyExistsException:
                pass
            
            # Crear stream de logs si no existe
            try:
                self.logs_client.create_log_stream(
                    logGroupName=self.log_group,
                    logStreamName=self.log_stream
                )
                logger.info(f"Stream de logs creado: {self.log_stream}")
            except self.logs_client.exceptions.ResourceAlreadyExistsException:
                # Obtener token de secuencia actual
                response = self.logs_client.describe_log_streams(
                    logGroupName=self.log_group,
                    logStreamNamePrefix=self.log_stream
                )
                
                for stream in response.get("logStreams", []):
                    if stream["logStreamName"] == self.log_stream:
                        self.sequence_token = stream.get("uploadSequenceToken")
                        break
            
            logger.info("Clientes CloudWatch inicializados")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar clientes CloudWatch: {e}")
            return False
    
    def put_log_events(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Envía eventos de log a CloudWatch Logs.
        
        Args:
            messages: Lista de mensajes a enviar
            
        Returns:
            True si se enviaron correctamente
        """
        if not self.enabled:
            return False
        
        # Verificar clientes
        if not self.logs_client:
            if not self.initialize_clients():
                return False
        
        try:
            # Preparar eventos
            log_events = []
            for msg in messages:
                # Convertir mensaje a string si es necesario
                if isinstance(msg, dict):
                    message = json.dumps(msg)
                else:
                    message = str(msg)
                
                # Añadir timestamp si no existe
                timestamp = msg.get("timestamp") if isinstance(msg, dict) else None
                if timestamp is None:
                    timestamp = int(time.time() * 1000)
                
                log_events.append({
                    "timestamp": timestamp,
                    "message": message
                })
            
            # Ordenar eventos por timestamp
            log_events.sort(key=lambda x: x["timestamp"])
            
            # Enviar eventos
            kwargs = {
                "logGroupName": self.log_group,
                "logStreamName": self.log_stream,
                "logEvents": log_events
            }
            
            if self.sequence_token:
                kwargs["sequenceToken"] = self.sequence_token
            
            response = self.logs_client.put_log_events(**kwargs)
            
            # Actualizar token de secuencia
            self.sequence_token = response.get("nextSequenceToken")
            
            return True
            
        except self.logs_client.exceptions.InvalidSequenceTokenException as e:
            # Token de secuencia inválido, obtener el correcto
            self.sequence_token = e.response.get("expectedSequenceToken")
            
            # Reintentar con el token correcto
            return self.put_log_events(messages)
            
        except Exception as e:
            logger.error(f"Error al enviar eventos de log: {e}")
            return False
    
    def put_metric_data(
        self,
        metric_name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """
        Publica datos de métrica en CloudWatch.
        
        Args:
            metric_name: Nombre de la métrica
            value: Valor de la métrica
            unit: Unidad de la métrica
            dimensions: Dimensiones de la métrica
            
        Returns:
            True si se publicó correctamente
        """
        if not self.enabled:
            return False
        
        # Verificar clientes
        if not self.cloudwatch_client:
            if not self.initialize_clients():
                return False
        
        try:
            # Preparar datos de métrica
            metric_data = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.datetime.now()
            }
            
            if dimensions:
                metric_data["Dimensions"] = dimensions
            
            # Publicar métrica
            self.cloudwatch_client.put_metric_data(
                Namespace=self.metrics_namespace,
                MetricData=[metric_data]
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al publicar métrica: {e}")
            return False
    
    def create_alarm(
        self,
        alarm_name: str,
        metric_name: str,
        comparison_operator: str,
        threshold: float,
        evaluation_periods: int = 1,
        period: int = 60,
        statistic: str = "Average",
        dimensions: Optional[List[Dict[str, str]]] = None,
        alarm_actions: Optional[List[str]] = None
    ) -> bool:
        """
        Crea una alarma en CloudWatch.
        
        Args:
            alarm_name: Nombre de la alarma
            metric_name: Nombre de la métrica
            comparison_operator: Operador de comparación
            threshold: Umbral
            evaluation_periods: Períodos de evaluación
            period: Período en segundos
            statistic: Estadística
            dimensions: Dimensiones de la métrica
            alarm_actions: Acciones a ejecutar cuando se active la alarma
            
        Returns:
            True si se creó correctamente
        """
        if not self.enabled:
            return False
        
        # Verificar clientes
        if not self.cloudwatch_client:
            if not self.initialize_clients():
                return False
        
        try:
            # Preparar parámetros
            params = {
                "AlarmName": alarm_name,
                "MetricName": metric_name,
                "Namespace": self.metrics_namespace,
                "ComparisonOperator": comparison_operator,
                "Threshold": threshold,
                "EvaluationPeriods": evaluation_periods,
                "Period": period,
                "Statistic": statistic
            }
            
            if dimensions:
                params["Dimensions"] = dimensions
            
            if alarm_actions:
                params["AlarmActions"] = alarm_actions
            
            # Crear alarma
            self.cloudwatch_client.put_metric_alarm(**params)
            
            return True
            
        except Exception as e:
            logger.error(f"Error al crear alarma: {e}")
            return False
    
    def query_logs(
        self,
        query: str,
        start_time: Optional[Union[int, datetime.datetime]] = None,
        end_time: Optional[Union[int, datetime.datetime]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Consulta logs en CloudWatch Logs Insights.
        
        Args:
            query: Consulta de CloudWatch Logs Insights
            start_time: Tiempo de inicio (None para 1 hora atrás)
            end_time: Tiempo de fin (None para ahora)
            limit: Límite de resultados
            
        Returns:
            Lista de resultados
        """
        if not self.enabled:
            return []
        
        # Verificar clientes
        if not self.logs_client:
            if not self.initialize_clients():
                return []
        
        try:
            # Determinar tiempos
            if end_time is None:
                end_time = int(time.time())
            elif isinstance(end_time, datetime.datetime):
                end_time = int(end_time.timestamp())
            
            if start_time is None:
                start_time = end_time - 3600  # 1 hora atrás
            elif isinstance(start_time, datetime.datetime):
                start_time = int(start_time.timestamp())
            
            # Iniciar consulta
            start_query_response = self.logs_client.start_query(
                logGroupName=self.log_group,
                startTime=start_time,
                endTime=end_time,
                queryString=query,
                limit=limit
            )
            
            query_id = start_query_response["queryId"]
            
            # Esperar resultados
            response = None
            while response is None or response["status"] == "Running":
                time.sleep(1)
                response = self.logs_client.get_query_results(queryId=query_id)
            
            # Procesar resultados
            results = []
            for result in response.get("results", []):
                item = {}
                for field in result:
                    item[field["field"]] = field["value"]
                results.append(item)
            
            return results
            
        except Exception as e:
            logger.error(f"Error al consultar logs: {e}")
            return []
    
    def get_metric_statistics(
        self,
        metric_name: str,
        start_time: Optional[Union[int, datetime.datetime]] = None,
        end_time: Optional[Union[int, datetime.datetime]] = None,
        period: int = 60,
        statistics: Optional[List[str]] = None,
        dimensions: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene estadísticas de una métrica.
        
        Args:
            metric_name: Nombre de la métrica
            start_time: Tiempo de inicio (None para 1 hora atrás)
            end_time: Tiempo de fin (None para ahora)
            period: Período en segundos
            statistics: Lista de estadísticas
            dimensions: Dimensiones de la métrica
            
        Returns:
            Lista de puntos de datos
        """
        if not self.enabled:
            return []
        
        # Verificar clientes
        if not self.cloudwatch_client:
            if not self.initialize_clients():
                return []
        
        try:
            # Determinar tiempos
            if end_time is None:
                end_time = datetime.datetime.now()
            elif isinstance(end_time, int):
                end_time = datetime.datetime.fromtimestamp(end_time)
            
            if start_time is None:
                start_time = end_time - datetime.timedelta(hours=1)
            elif isinstance(start_time, int):
                start_time = datetime.datetime.fromtimestamp(start_time)
            
            # Determinar estadísticas
            if statistics is None:
                statistics = ["Average", "Minimum", "Maximum", "Sum", "SampleCount"]
            
            # Preparar parámetros
            params = {
                "Namespace": self.metrics_namespace,
                "MetricName": metric_name,
                "StartTime": start_time,
                "EndTime": end_time,
                "Period": period,
                "Statistics": statistics
            }
            
            if dimensions:
                params["Dimensions"] = dimensions
            
            # Obtener estadísticas
            response = self.cloudwatch_client.get_metric_statistics(**params)
            
            # Ordenar por timestamp
            datapoints = sorted(response.get("Datapoints", []), key=lambda x: x["Timestamp"])
            
            return datapoints
            
        except Exception as e:
            logger.error(f"Error al obtener estadísticas de métrica: {e}")
            return []
