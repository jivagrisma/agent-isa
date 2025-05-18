# Guía de Monitoreo y Mantenimiento

Esta guía proporciona instrucciones detalladas para el monitoreo y mantenimiento de Agent-ISA en producción.

## Monitoreo

### CloudWatch

Agent-ISA está integrado con Amazon CloudWatch para el monitoreo de métricas y logs. A continuación se detallan las principales funcionalidades:

#### Logs en CloudWatch

Los logs de la aplicación se envían automáticamente a CloudWatch Logs cuando está habilitado en la configuración. Puede acceder a ellos desde la consola de AWS:

1. Vaya a la consola de AWS
2. Navegue a CloudWatch > Logs > Log groups
3. Busque el grupo de logs `agent-isa` (o el configurado en su entorno)

También puede consultar los logs mediante la AWS CLI:

```bash
aws logs get-log-events --log-group-name agent-isa --log-stream-name application
```

Para realizar consultas avanzadas con CloudWatch Logs Insights:

```bash
aws logs start-query \
  --log-group-name agent-isa \
  --start-time $(date -d '1 hour ago' +%s) \
  --end-time $(date +%s) \
  --query-string 'fields @timestamp, @message | filter @message like "ERROR"'
```

#### Métricas en CloudWatch

Agent-ISA publica métricas personalizadas en CloudWatch. Puede visualizarlas en:

1. Vaya a la consola de AWS
2. Navegue a CloudWatch > Metrics > All metrics
3. Seleccione el namespace `AgentISA` (o el configurado en su entorno)

Las principales métricas incluyen:

- `RequestCount`: Número de solicitudes procesadas
- `ResponseTime`: Tiempo de respuesta en milisegundos
- `ErrorCount`: Número de errores
- `CPUUtilization`: Utilización de CPU
- `MemoryUtilization`: Utilización de memoria

#### Alarmas en CloudWatch

Puede configurar alarmas en CloudWatch para recibir notificaciones cuando las métricas superen ciertos umbrales:

1. Vaya a la consola de AWS
2. Navegue a CloudWatch > Alarms > All alarms
3. Haga clic en "Create alarm"
4. Seleccione la métrica deseada
5. Configure el umbral y las acciones

Ejemplo de creación de alarma mediante AWS CLI:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name "HighErrorRate" \
  --alarm-description "Alarma por alta tasa de errores" \
  --metric-name "ErrorCount" \
  --namespace "AgentISA" \
  --statistic "Sum" \
  --period 300 \
  --threshold 10 \
  --comparison-operator "GreaterThanThreshold" \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:us-east-1:123456789012:AlertTopic"
```

### Monitoreo Local

Además del monitoreo en CloudWatch, puede realizar monitoreo local en la instancia EC2:

#### Logs Locales

Los logs de la aplicación se encuentran en:

- Logs de la aplicación: `/var/log/agent-isa/`
- Logs de Supervisor: `/var/log/supervisor/`
- Logs de Nginx: `/var/log/nginx/`
- Logs de systemd: `journalctl -u agent-isa.service`

Para ver los logs en tiempo real:

```bash
# Logs de la aplicación con Supervisor
sudo supervisorctl tail -f agent-isa

# Logs de la aplicación con systemd
sudo journalctl -f -u agent-isa.service

# Logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

#### Estado de los Servicios

Para verificar el estado de los servicios:

```bash
# Estado de Supervisor
sudo supervisorctl status

# Estado de systemd
sudo systemctl status agent-isa.service

# Estado de Nginx
sudo systemctl status nginx
```

#### Uso de Recursos

Para monitorear el uso de recursos:

```bash
# Uso de CPU y memoria
top

# Uso de disco
df -h

# Procesos de la aplicación
ps aux | grep agent-isa
```

## Mantenimiento

### Actualizaciones

#### Actualización de la Aplicación

Para actualizar la aplicación:

```bash
# Detener la aplicación
sudo supervisorctl stop agent-isa  # o sudo systemctl stop agent-isa.service

# Hacer backup
sudo tar -czf /tmp/agent-isa-backup-$(date +%Y%m%d).tar.gz -C /opt/agent-isa/data .

# Actualizar código
cd /opt/agent-isa/app
sudo git pull

# Actualizar dependencias
sudo /opt/agent-isa/venv/bin/pip install -r requirements.txt

# Iniciar la aplicación
sudo supervisorctl start agent-isa  # o sudo systemctl start agent-isa.service
```

#### Actualización del Sistema

Para actualizar el sistema operativo:

```bash
# En Amazon Linux
sudo yum update -y

# En Ubuntu
sudo apt update
sudo apt upgrade -y
```

### Respaldo y Recuperación

#### Respaldo Manual

Para realizar un respaldo manual:

```bash
# Respaldo de datos
sudo tar -czf /tmp/agent-isa-data-$(date +%Y%m%d).tar.gz -C /opt/agent-isa/data .

# Respaldo de configuración
sudo tar -czf /tmp/agent-isa-config-$(date +%Y%m%d).tar.gz -C /etc/agent-isa .

# Transferir a S3
aws s3 cp /tmp/agent-isa-data-$(date +%Y%m%d).tar.gz s3://su-bucket/backups/
aws s3 cp /tmp/agent-isa-config-$(date +%Y%m%d).tar.gz s3://su-bucket/backups/
```

#### Respaldo Automatizado

El script de respaldo automatizado se ejecuta diariamente a las 2 AM mediante cron. Puede verificar la configuración con:

```bash
sudo crontab -l
```

Los respaldos se almacenan en:
- Local: `/opt/agent-isa/backups/`
- S3: `s3://su-bucket/backups/`

#### Recuperación

Para recuperar desde un respaldo:

```bash
# Detener servicios
sudo supervisorctl stop agent-isa  # o sudo systemctl stop agent-isa.service

# Restaurar datos
sudo rm -rf /opt/agent-isa/data/*
sudo tar -xzf /tmp/agent-isa-data-YYYYMMDD.tar.gz -C /opt/agent-isa/data

# Restaurar configuración
sudo tar -xzf /tmp/agent-isa-config-YYYYMMDD.tar.gz -C /etc/agent-isa

# Configurar permisos
sudo chown -R agent-isa:agent-isa /opt/agent-isa/data

# Iniciar servicios
sudo supervisorctl start agent-isa  # o sudo systemctl start agent-isa.service
```

### Mantenimiento de Base de Datos

Agent-ISA utiliza SQLite por defecto. Para realizar mantenimiento:

```bash
# Hacer backup de la base de datos
sudo cp /opt/agent-isa/data/production.db /tmp/production-backup-$(date +%Y%m%d).db

# Verificar integridad
sudo sqlite3 /opt/agent-isa/data/production.db "PRAGMA integrity_check;"

# Optimizar
sudo sqlite3 /opt/agent-isa/data/production.db "VACUUM;"
```

### Rotación de Logs

Los logs se rotan automáticamente mediante logrotate. La configuración se encuentra en:

```
/etc/logrotate.d/agent-isa
```

Para forzar la rotación de logs:

```bash
sudo logrotate -f /etc/logrotate.d/agent-isa
```

## Solución de Problemas

### Verificación de Salud

Para verificar la salud de la aplicación:

```bash
# Verificar endpoint de salud
curl -s http://localhost:8000/health

# Verificar dependencias
sudo /opt/agent-isa/venv/bin/python /opt/agent-isa/app/OpenManusWeb/scripts/check_dependencies.py
```

### Problemas Comunes

#### La Aplicación No Responde

1. Verificar si el proceso está en ejecución:
   ```bash
   sudo supervisorctl status agent-isa
   ```

2. Verificar logs:
   ```bash
   sudo supervisorctl tail agent-isa
   ```

3. Reiniciar la aplicación:
   ```bash
   sudo supervisorctl restart agent-isa
   ```

#### Error 502 Bad Gateway

1. Verificar que la aplicación esté en ejecución:
   ```bash
   sudo supervisorctl status agent-isa
   ```

2. Verificar la configuración de Nginx:
   ```bash
   sudo nginx -t
   ```

3. Verificar los logs de Nginx:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

#### Problemas de Permisos

1. Verificar los permisos de los directorios:
   ```bash
   ls -la /opt/agent-isa/
   ```

2. Corregir los permisos:
   ```bash
   sudo chown -R agent-isa:agent-isa /opt/agent-isa/
   ```

#### Problemas con AWS

1. Verificar el rol de IAM asignado a la instancia:
   ```bash
   curl -s http://169.254.169.254/latest/meta-data/iam/info
   ```

2. Verificar credenciales:
   ```bash
   aws sts get-caller-identity
   ```

3. Probar acceso a S3:
   ```bash
   aws s3 ls
   ```

### Herramientas de Diagnóstico

#### Diagnóstico de Red

```bash
# Verificar conectividad
ping -c 4 s3.amazonaws.com

# Verificar puertos
nc -zv s3.amazonaws.com 443

# Verificar DNS
dig s3.amazonaws.com
```

#### Diagnóstico de Sistema

```bash
# Verificar uso de CPU
mpstat

# Verificar uso de memoria
free -m

# Verificar uso de disco
df -h
```

#### Diagnóstico de Aplicación

```bash
# Verificar procesos Python
ps aux | grep python

# Verificar conexiones de red
netstat -tuln

# Verificar archivos abiertos
lsof -p $(pgrep -f "python.*app.py")
```

## Optimización

### Optimización de Rendimiento

Para optimizar el rendimiento de la aplicación:

1. Ajustar el número de workers en la configuración:
   ```bash
   sudo nano /etc/supervisor/conf.d/agent-isa.conf
   ```

2. Ajustar la configuración de Nginx:
   ```bash
   sudo nano /etc/nginx/sites-available/agent-isa
   ```

3. Ajustar los límites de recursos en systemd:
   ```bash
   sudo nano /etc/systemd/system/agent-isa.service
   ```

### Optimización de Costos

Para optimizar los costos de AWS:

1. Utilizar instancias reservadas para EC2
2. Configurar ciclo de vida para objetos en S3
3. Ajustar la retención de logs en CloudWatch
4. Utilizar Auto Scaling para ajustar la capacidad según la demanda

## Seguridad

### Actualizaciones de Seguridad

Para aplicar actualizaciones de seguridad:

```bash
# En Amazon Linux
sudo yum update-minimal --security -y

# En Ubuntu
sudo apt update
sudo apt upgrade -y
```

### Auditoría de Seguridad

Para realizar una auditoría de seguridad básica:

```bash
# Verificar puertos abiertos
sudo netstat -tuln

# Verificar usuarios y permisos
sudo cat /etc/passwd | grep -v nologin

# Verificar últimos accesos
sudo last

# Verificar intentos fallidos de acceso
sudo grep "Failed password" /var/log/auth.log
```

## Recursos Adicionales

- [Documentación de AWS CloudWatch](https://docs.aws.amazon.com/cloudwatch/)
- [Documentación de Supervisor](http://supervisord.org/)
- [Documentación de Nginx](https://nginx.org/en/docs/)
- [Documentación de systemd](https://www.freedesktop.org/wiki/Software/systemd/)
