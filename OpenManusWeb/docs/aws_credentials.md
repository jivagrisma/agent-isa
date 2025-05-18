# Configuración de Credenciales de AWS

Esta guía proporciona instrucciones detalladas para configurar y gestionar las credenciales de AWS en Agent-ISA, con especial énfasis en la seguridad.

## Introducción

Agent-ISA utiliza servicios de AWS como Bedrock, S3 y CloudWatch. Para acceder a estos servicios, se requieren credenciales de AWS que deben manejarse de manera segura.

## Mejores Prácticas de Seguridad

1. **Nunca incluya credenciales en el código fuente**
2. **Nunca comparta credenciales en mensajes, correos o chats**
3. **Utilice variables de entorno o archivos de configuración seguros**
4. **Aplique el principio de privilegio mínimo** (otorgue solo los permisos necesarios)
5. **Rote las credenciales periódicamente**
6. **Monitoree el uso de las credenciales**

## Configuración de Variables de Entorno

### Método 1: Archivo .env

1. Copie el archivo `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edite el archivo `.env` y configure sus credenciales:
   ```bash
   nano .env
   ```

3. Cargue las variables de entorno:
   ```bash
   source scripts/setup_env.sh
   ```

### Método 2: Variables de Entorno del Sistema

Configure las variables de entorno directamente en su shell:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
```

Para hacerlas persistentes, añádalas a su archivo `.bashrc` o `.zshrc`.

### Método 3: Perfil de Instancia EC2

En producción, se recomienda utilizar perfiles de instancia EC2 en lugar de credenciales estáticas:

1. Cree un rol IAM con los permisos necesarios
2. Asigne el rol a la instancia EC2
3. Configure `use_instance_profile = true` en el archivo de configuración de producción

## Configuración de Modelos de Bedrock

Agent-ISA utiliza varios modelos de AWS Bedrock:

1. **Nova Pro**: Para OCR y análisis de imágenes
2. **Nova Lite**: Para tareas de análisis de imágenes más ligeras
3. **Titan Multimodal Embeddings**: Para generación de embeddings de imágenes
4. **Claude 3.7 Sonnet**: Para generación de texto avanzada

Configure los IDs de los modelos en el archivo `.env`:

```
BEDROCK_MODEL_NOVA_PRO=amazon.nova-pro
BEDROCK_MODEL_NOVA_LITE=amazon.nova-lite
BEDROCK_MODEL_TITAN_EMBEDDINGS=amazon.titan-embed-image-v1
BEDROCK_MODEL_CLAUDE=anthropic.claude-3-sonnet-20240229-v1
```

## Verificación de Credenciales

Para verificar que sus credenciales están configuradas correctamente, ejecute:

```bash
python test_credentials.py --validate
```

Para verificar el acceso a los modelos de Bedrock:

```bash
python test_credentials.py --models
```

Para probar la invocación de un modelo:

```bash
python test_credentials.py --invoke claude --prompt "Hola, ¿cómo estás?"
```

## Permisos Requeridos

Para que Agent-ISA funcione correctamente, las credenciales de AWS deben tener los siguientes permisos:

### Permisos para Bedrock

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels"
            ],
            "Resource": "*"
        }
    ]
}
```

### Permisos para S3

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

### Permisos para CloudWatch

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "cloudwatch:PutMetricData"
            ],
            "Resource": "*"
        }
    ]
}
```

## Rotación de Credenciales

Se recomienda rotar las credenciales periódicamente:

1. Cree nuevas credenciales en la consola de AWS IAM
2. Actualice el archivo `.env` o las variables de entorno con las nuevas credenciales
3. Verifique que todo funcione correctamente
4. Elimine las credenciales antiguas

## Solución de Problemas

### Error: "No se pueden validar las credenciales"

- Verifique que las credenciales sean correctas
- Verifique que la región sea correcta
- Verifique que las credenciales tengan los permisos necesarios

### Error: "No se puede acceder a los modelos de Bedrock"

- Verifique que su cuenta tenga acceso a los modelos de Bedrock
- Verifique que los IDs de los modelos sean correctos
- Verifique que las credenciales tengan permisos para Bedrock

### Error: "No se puede invocar el modelo"

- Verifique que el modelo esté disponible en su región
- Verifique que tenga cuota suficiente para el modelo
- Verifique los logs para obtener más detalles del error

## Recursos Adicionales

- [Documentación de AWS IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html)
- [Mejores prácticas de seguridad para AWS](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Documentación de AWS Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html)
