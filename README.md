# Agent-ISA con Integración AWS Bedrock

Este repositorio contiene una implementación de Agent-ISA, un proyecto basado en la bifurcación de OpenManusWeb, con integración a AWS Bedrock, permitiendo utilizar modelos de lenguaje avanzados como Amazon Nova Pro, Amazon Nova Lite y Claude 3.7 Sonnet.

## Características

- Integración robusta con AWS Bedrock
- Interfaz de chat web moderna y responsive
- Soporte para diferentes modelos de AWS Bedrock
- Manejo de errores mejorado
- Scripts de prueba para verificar la integración

## Estructura del Repositorio

```
OpenManusWeb/
├── app/                    # Código principal de la aplicación
│   ├── config.py           # Configuración de la aplicación
│   └── llm.py              # Integración con AWS Bedrock
├── config/                 # Archivos de configuración
│   └── config.toml         # Configuración de AWS Bedrock
├── docs/                   # Documentación
│   └── aws_bedrock_integration.md  # Documentación de la integración con AWS Bedrock
├── static/                 # Archivos estáticos para la interfaz web
├── templates/              # Plantillas HTML para la interfaz web
├── simple_chat.py          # Interfaz web de chat
├── test_bedrock.py         # Script de prueba para AWS Bedrock
└── test_cli.py             # Interfaz de línea de comandos para AWS Bedrock
```

## Requisitos

- Python 3.12 o superior
- Cuenta de AWS con acceso a AWS Bedrock
- Credenciales de AWS (Access Key ID y Secret Access Key)
- Acceso a los modelos de AWS Bedrock (Amazon Nova Pro, Claude 3 Sonnet, etc.)

## Instalación

1. Clona este repositorio:
   ```bash
   git clone https://github.com/jivagrisma/agent-isa.git
   cd agent-isa
   ```

2. Crea un entorno virtual y actívalo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### Interfaz Web de Chat

Para iniciar la interfaz web de chat:

```bash
python simple_chat.py
```

Luego, abre tu navegador y navega a `http://localhost:8005`.

### Pruebas de AWS Bedrock

Para probar la integración con AWS Bedrock:

```bash
python test_bedrock.py
```

### Interfaz de Línea de Comandos

Para utilizar la interfaz de línea de comandos:

```bash
python test_cli.py
```

## Documentación

Para más información sobre la integración con AWS Bedrock, consulta la [documentación detallada](docs/aws_bedrock_integration.md).

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Jorge Grisales - jivagrisma@gmail.com

Enlace del proyecto: [https://github.com/jivagrisma/agent-isa](https://github.com/jivagrisma/agent-isa)
