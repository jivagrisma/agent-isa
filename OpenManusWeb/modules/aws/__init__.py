"""
Módulo AWS para agent-isa.
Proporciona integraciones con servicios de Amazon Web Services.
"""

from .s3_manager import S3Manager
from .cloudwatch_manager import CloudWatchManager
from .cloudwatch_logs_handler import CloudWatchLogsHandler, setup_cloudwatch_logging
from .credentials_manager import CredentialsManager

__all__ = ['S3Manager', 'CloudWatchManager', 'CloudWatchLogsHandler', 'setup_cloudwatch_logging', 'CredentialsManager']
