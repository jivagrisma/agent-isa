# Guía de Despliegue en AWS EC2

Esta guía proporciona instrucciones detalladas para desplegar Agent-ISA en una instancia EC2 de Amazon Web Services.

## Requisitos Previos

### Instancia EC2
- Amazon Linux 2 o Ubuntu Server 20.04/22.04 LTS
- Tipo de instancia recomendada: t3.medium (mínimo)
- Almacenamiento: 20 GB (mínimo)
- Grupo de seguridad con los siguientes puertos abiertos:
  - SSH (22)
  - HTTP (80)
  - HTTPS (443)

### Permisos de AWS
- Rol de IAM con los siguientes permisos:
  - AmazonS3ReadOnlyAccess
  - CloudWatchAgentServerPolicy
  - AmazonBedrockFullAccess (o permisos específicos para los modelos utilizados)

## Métodos de Despliegue

Existen dos métodos principales para desplegar Agent-ISA en EC2:

1. **Despliegue Automatizado**: Utilizando el script de despliegue incluido en el repositorio.
2. **Despliegue Manual**: Siguiendo los pasos detallados en esta guía.

## Despliegue Automatizado

El despliegue automatizado es la forma más sencilla de instalar Agent-ISA en una instancia EC2.

### Requisitos
- Acceso SSH a la instancia EC2
- Clave SSH configurada
- Git instalado en la máquina local

### Pasos

1. Clone el repositorio en su máquina local:
   ```bash
   git clone https://github.com/jivagrisma/agent-isa.git
   cd agent-isa
   ```

2. Ejecute el script de despliegue:
   ```bash
   ./OpenManusWeb/scripts/deploy.sh <IP-INSTANCIA> <USUARIO> <RUTA-CLAVE-SSH>
   ```
   
   Ejemplo:
   ```bash
   ./OpenManusWeb/scripts/deploy.sh 12.34.56.78 ec2-user ~/.ssh/mi-clave.pem
   ```

3. El script realizará automáticamente las siguientes acciones:
   - Transferir los archivos necesarios a la instancia EC2
   - Instalar dependencias
   - Configurar servicios
   - Iniciar la aplicación

4. Una vez completado, podrá acceder a la aplicación en:
   ```
   http://<IP-INSTANCIA>
   ```

## Despliegue Manual

Si prefiere realizar el despliegue manualmente o necesita personalizar la instalación, siga estos pasos:

### 1. Preparar la Instancia EC2

Conéctese a su instancia EC2:

```bash
ssh -i <CLAVE-SSH> <USUARIO>@<IP-INSTANCIA>
```

Actualice el sistema e instale las dependencias necesarias:

```bash
# En Amazon Linux
sudo yum update -y
sudo yum install -y python3 python3-pip python3-devel git nginx supervisor

# En Ubuntu
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git nginx supervisor
```

### 2. Crear Usuario de Servicio

```bash
sudo useradd -r -s /bin/false -d /opt/agent-isa agent-isa
```

### 3. Crear Estructura de Directorios

```bash
sudo mkdir -p /opt/agent-isa
sudo mkdir -p /opt/agent-isa/data
sudo mkdir -p /opt/agent-isa/data/storage
sudo mkdir -p /opt/agent-isa/data/cache
sudo mkdir -p /var/log/agent-isa
sudo mkdir -p /etc/agent-isa
```

### 4. Clonar Repositorio

```bash
sudo git clone https://github.com/jivagrisma/agent-isa.git /opt/agent-isa/app
```

### 5. Crear Entorno Virtual

```bash
cd /opt/agent-isa
sudo python3 -m venv venv
sudo /opt/agent-isa/venv/bin/pip install --upgrade pip
sudo /opt/agent-isa/venv/bin/pip install -r /opt/agent-isa/app/requirements.txt
```

### 6. Configurar Variables de Entorno

Cree un archivo de variables de entorno:

```bash
sudo tee /etc/agent-isa/agent-isa.env > /dev/null << EOF
AGENT_ISA_ENV=production
PYTHONPATH=/opt/agent-isa/app
JWT_SECRET=$(openssl rand -hex 32)
EOF
```

### 7. Configurar Supervisor

Cree un archivo de configuración para Supervisor:

```bash
sudo tee /etc/supervisor/conf.d/agent-isa.conf > /dev/null << EOF
[program:agent-isa]
command=/opt/agent-isa/venv/bin/python /opt/agent-isa/app/OpenManusWeb/app.py
directory=/opt/agent-isa/app
user=agent-isa
environment=AGENT_ISA_ENV="production",PYTHONPATH="/opt/agent-isa/app"
autostart=true
autorestart=true
startretries=3
stderr_logfile=/var/log/agent-isa/supervisor-error.log
stdout_logfile=/var/log/agent-isa/supervisor-output.log
EOF
```

### 8. Configurar Nginx

Cree un archivo de configuración para Nginx:

```bash
sudo tee /etc/nginx/sites-available/agent-isa > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias /opt/agent-isa/app/OpenManusWeb/static;
        expires 30d;
    }
}
EOF
```

Habilite el sitio en Nginx:

```bash
# En sistemas con sites-enabled
sudo ln -sf /etc/nginx/sites-available/agent-isa /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# En Amazon Linux
sudo cp /etc/nginx/sites-available/agent-isa /etc/nginx/conf.d/
```

### 9. Configurar Permisos

```bash
sudo chown -R agent-isa:agent-isa /opt/agent-isa
sudo chown -R agent-isa:agent-isa /var/log/agent-isa
sudo chmod -R 755 /opt/agent-isa
sudo chmod -R 755 /var/log/agent-isa
```

### 10. Iniciar Servicios

```bash
sudo systemctl restart supervisor
sudo systemctl restart nginx
```

### 11. Verificar Instalación

```bash
sudo supervisorctl status agent-isa
curl -s http://localhost:8000/health
```

## Configuración de Systemd (Alternativa a Supervisor)

Si prefiere utilizar systemd en lugar de Supervisor, siga estos pasos:

1. Copie el archivo de servicio:
   ```bash
   sudo cp /opt/agent-isa/app/OpenManusWeb/scripts/systemd/agent-isa.service /etc/systemd/system/
   ```

2. Recargue systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Habilite e inicie el servicio:
   ```bash
   sudo systemctl enable agent-isa.service
   sudo systemctl start agent-isa.service
   ```

4. Verifique el estado:
   ```bash
   sudo systemctl status agent-isa.service
   ```

## Configuración de HTTPS con Let's Encrypt

Para configurar HTTPS con Let's Encrypt, siga estos pasos:

1. Instale Certbot:
   ```bash
   # En Amazon Linux
   sudo amazon-linux-extras install epel -y
   sudo yum install -y certbot python-certbot-nginx
   
   # En Ubuntu
   sudo apt install -y certbot python3-certbot-nginx
   ```

2. Obtenga un certificado:
   ```bash
   sudo certbot --nginx -d su-dominio.com
   ```

3. Siga las instrucciones en pantalla para completar la configuración.

4. Certbot actualizará automáticamente la configuración de Nginx.

## Monitoreo y Mantenimiento

### Logs

Los logs de la aplicación se encuentran en:

- Logs de la aplicación: `/var/log/agent-isa/`
- Logs de Supervisor: `/var/log/supervisor/`
- Logs de Nginx: `/var/log/nginx/`
- Logs de systemd: `journalctl -u agent-isa.service`

### Reinicio de Servicios

Para reiniciar la aplicación:

```bash
# Con Supervisor
sudo supervisorctl restart agent-isa

# Con systemd
sudo systemctl restart agent-isa.service
```

Para reiniciar Nginx:

```bash
sudo systemctl restart nginx
```

### Actualización de la Aplicación

Para actualizar la aplicación:

```bash
cd /opt/agent-isa/app
sudo git pull
sudo /opt/agent-isa/venv/bin/pip install -r requirements.txt
sudo supervisorctl restart agent-isa  # o sudo systemctl restart agent-isa.service
```

## Respaldo y Recuperación

### Respaldo Manual

Para realizar un respaldo manual:

```bash
# Respaldo de datos
sudo tar -czf /tmp/agent-isa-data-$(date +%Y%m%d).tar.gz -C /opt/agent-isa/data .

# Respaldo de configuración
sudo tar -czf /tmp/agent-isa-config-$(date +%Y%m%d).tar.gz -C /etc/agent-isa .

# Transferir a S3 (opcional)
aws s3 cp /tmp/agent-isa-data-$(date +%Y%m%d).tar.gz s3://su-bucket/backups/
aws s3 cp /tmp/agent-isa-config-$(date +%Y%m%d).tar.gz s3://su-bucket/backups/
```

### Respaldo Automatizado

Para configurar respaldos automatizados, cree un script de respaldo:

```bash
sudo tee /opt/agent-isa/scripts/backup.sh > /dev/null << 'EOF'
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/opt/agent-isa/backups"
S3_BUCKET="su-bucket"

# Crear directorio de respaldo
mkdir -p $BACKUP_DIR

# Respaldar datos
tar -czf $BACKUP_DIR/agent-isa-data-$TIMESTAMP.tar.gz -C /opt/agent-isa/data .

# Respaldar configuración
tar -czf $BACKUP_DIR/agent-isa-config-$TIMESTAMP.tar.gz -C /etc/agent-isa .

# Subir a S3
aws s3 cp $BACKUP_DIR/agent-isa-data-$TIMESTAMP.tar.gz s3://$S3_BUCKET/backups/
aws s3 cp $BACKUP_DIR/agent-isa-config-$TIMESTAMP.tar.gz s3://$S3_BUCKET/backups/

# Eliminar respaldos antiguos (más de 30 días)
find $BACKUP_DIR -name "agent-isa-*.tar.gz" -type f -mtime +30 -delete
EOF
```

Haga el script ejecutable y configúrelo como tarea cron:

```bash
sudo chmod +x /opt/agent-isa/scripts/backup.sh
sudo crontab -e
```

Añada la siguiente línea para ejecutar el respaldo diariamente a las 2 AM:

```
0 2 * * * /opt/agent-isa/scripts/backup.sh
```

### Recuperación

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

## Solución de Problemas

### Verificación de Dependencias

Ejecute el script de verificación de dependencias:

```bash
sudo /opt/agent-isa/venv/bin/python /opt/agent-isa/app/OpenManusWeb/scripts/check_dependencies.py
```

### Problemas Comunes

1. **La aplicación no inicia**:
   - Verifique los logs: `sudo supervisorctl tail agent-isa`
   - Verifique permisos: `ls -la /opt/agent-isa/`
   - Verifique variables de entorno: `cat /etc/agent-isa/agent-isa.env`

2. **Error 502 Bad Gateway**:
   - Verifique que la aplicación esté en ejecución: `sudo supervisorctl status agent-isa`
   - Verifique la configuración de Nginx: `sudo nginx -t`
   - Verifique los logs de Nginx: `sudo tail -f /var/log/nginx/error.log`

3. **Problemas de permisos**:
   - Verifique los permisos de los directorios: `ls -la /opt/agent-isa/`
   - Corrija los permisos: `sudo chown -R agent-isa:agent-isa /opt/agent-isa/`

4. **Problemas con AWS**:
   - Verifique el rol de IAM asignado a la instancia
   - Verifique los logs de la aplicación para errores de AWS
   - Pruebe las credenciales: `aws s3 ls`

## Recursos Adicionales

- [Documentación de AWS EC2](https://docs.aws.amazon.com/ec2/)
- [Documentación de Nginx](https://nginx.org/en/docs/)
- [Documentación de Supervisor](http://supervisord.org/)
