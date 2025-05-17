#!/usr/bin/env python3
"""
Interfaz web de chat simple para OpenManusWeb.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from typing import List, Dict, Any, Optional
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio actual al path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar módulos necesarios
from app.llm import LLM
from app.config import config

# Crear la aplicación FastAPI
app = FastAPI(title="ISA-Agent Chat")

# Crear directorio para templates si no existe
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

# Crear directorio para archivos estáticos si no existe
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# Configurar templates
templates = Jinja2Templates(directory=str(templates_dir))

# Configurar archivos estáticos
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Almacenar las conexiones WebSocket activas
active_connections: Dict[str, WebSocket] = {}

# Almacenar las conversaciones
conversations: Dict[str, List[Dict[str, str]]] = {}

# Modelo para el mensaje
class Message(BaseModel):
    content: str

# Crear el archivo HTML para la interfaz de chat
chat_html = """
<!DOCTYPE html>
<html lang="es" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ISA-Agent</title>
    
    <!-- Fuentes -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
    
    <!-- Iconos -->
    <link href="https://cdn.jsdelivr.net/npm/remixicon@3.5.0/fonts/remixicon.css" rel="stylesheet">
    
    <!-- Highlight.js para resaltado de código -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-light.min.css" id="code-theme-light">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/styles/atom-one-dark.min.css" id="code-theme-dark" disabled>
    
    <!-- CSS personalizado -->
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div class="app-container">
        <!-- Barra lateral (para futura expansión) -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <h2>ISA-Agent</h2>
            </div>
            <div class="sidebar-content">
                <!-- Contenido futuro -->
                <p class="sidebar-note">Próximamente: historial y configuración</p>
            </div>
        </aside>
        
        <!-- Contenido principal -->
        <main class="main-content">
            <header class="main-header">
                <div class="new-chat-btn">
                    <button>
                        <i class="ri-add-line"></i>
                        <span>Nueva conversación</span>
                    </button>
                </div>
                <div class="theme-toggle">
                    <button id="theme-toggle-btn">
                        <i class="ri-sun-line" id="light-icon"></i>
                        <i class="ri-moon-line" id="dark-icon"></i>
                    </button>
                </div>
            </header>
            
            <div class="chat-container">
                <div class="chat-messages" id="chat-messages">
                    <!-- Los mensajes se agregarán dinámicamente aquí -->
                </div>
                
                <div class="status-container">
                    <div class="status" id="status"></div>
                    <div class="typing-indicator" id="typing-indicator">
                        <span></span><span></span><span></span>
                    </div>
                </div>
                
                <form class="message-form" id="message-form">
                    <div class="message-input-container">
                        <textarea 
                            class="message-input" 
                            id="message-input" 
                            placeholder="Escribe tu mensaje aquí..." 
                            rows="1"
                            autofocus
                        ></textarea>
                    </div>
                    <button type="submit" class="send-button" id="send-button">
                        <i class="ri-send-plane-fill"></i>
                    </button>
                </form>
            </div>
        </main>
    </div>

    <!-- Scripts para Markdown y resaltado de código -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.8.0/highlight.min.js"></script>
    
    <!-- Script principal -->
    <script src="/static/js/main.js"></script>
</body>
</html>
"""

# Guardar el archivo HTML
with open(templates_dir / "chat.html", "w") as f:
    f.write(chat_html)

@app.get("/", response_class=HTMLResponse)
async def get_chat_page(request: Request):
    """
    Página principal de chat.
    """
    return templates.TemplateResponse("chat.html", {"request": request})

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Endpoint WebSocket para la comunicación en tiempo real.
    """
    await websocket.accept()
    active_connections[session_id] = websocket

    # Inicializar la conversación si no existe
    if session_id not in conversations:
        conversations[session_id] = []

    try:
        # Inicializar el cliente LLM
        llm = LLM(config_name="default")

        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "message",
            "content": "¡Hola! Soy el asistente ISA. ¿En qué puedo ayudarte hoy?"
        })

        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_content = message_data.get("content", "")

            # Guardar mensaje del usuario
            conversations[session_id].append({"role": "user", "content": message_content})

            # Enviar estado de "escribiendo"
            await websocket.send_json({
                "type": "status",
                "content": "Escribiendo...",
                "status": "typing"
            })

            try:
                # Procesar mensaje con el LLM
                messages = conversations[session_id]

                # Intentar enviar mensaje al LLM con timeout
                try:
                    import asyncio
                    response = await asyncio.wait_for(
                        llm.ask_bedrock(
                            messages=messages,
                            stream=False,
                            temperature=0.7
                        ),
                        timeout=30  # 30 segundos de timeout
                    )

                    # Guardar respuesta del bot
                    conversations[session_id].append({"role": "assistant", "content": response})

                    # Enviar respuesta al cliente
                    await websocket.send_json({
                        "type": "message",
                        "content": response
                    })

                    # Actualizar estado
                    await websocket.send_json({
                        "type": "status",
                        "content": "Conectado",
                        "status": "success"
                    })

                except asyncio.TimeoutError:
                    logger.error("La solicitud a AWS Bedrock excedió el tiempo límite (30 segundos)")

                    # Enviar mensaje de error al cliente
                    await websocket.send_json({
                        "type": "message",
                        "content": "Lo siento, la solicitud ha tardado demasiado tiempo. Por favor, intenta con una solicitud más simple o inténtalo de nuevo más tarde."
                    })

                    # Actualizar estado
                    await websocket.send_json({
                        "type": "status",
                        "content": "Timeout",
                        "status": "error"
                    })

                except Exception as e:
                    logger.error(f"Error al enviar mensaje a AWS Bedrock: {e}")

                    # Determinar el tipo de error
                    error_message = str(e)
                    if "ValidationException" in error_message:
                        if "throughput isn't supported" in error_message:
                            # Error de modelo no soportado
                            await websocket.send_json({
                                "type": "message",
                                "content": "Lo siento, el modelo actual no está disponible. Por favor, contacta al administrador para cambiar a un modelo compatible."
                            })
                        else:
                            # Otro error de validación
                            await websocket.send_json({
                                "type": "message",
                                "content": "Lo siento, hay un problema con la configuración del modelo. Por favor, contacta al administrador."
                            })
                    elif "AccessDeniedException" in error_message:
                        # Error de acceso denegado
                        await websocket.send_json({
                            "type": "message",
                            "content": "Lo siento, no tengo acceso al modelo solicitado. Por favor, contacta al administrador para verificar las credenciales."
                        })
                    elif "ServiceUnavailableException" in error_message or "ThrottlingException" in error_message:
                        # Error de servicio no disponible o throttling
                        await websocket.send_json({
                            "type": "message",
                            "content": "Lo siento, el servicio está temporalmente no disponible o ha alcanzado el límite de solicitudes. Por favor, inténtalo de nuevo más tarde."
                        })
                    else:
                        # Otro tipo de error
                        await websocket.send_json({
                            "type": "message",
                            "content": f"Lo siento, ocurrió un error al procesar tu mensaje. Por favor, inténtalo de nuevo más tarde."
                        })

                    # Actualizar estado
                    await websocket.send_json({
                        "type": "status",
                        "content": "Error",
                        "status": "error"
                    })

            except Exception as e:
                logger.error(f"Error general al procesar mensaje: {e}")

                # Enviar mensaje de error al cliente
                await websocket.send_json({
                    "type": "message",
                    "content": "Lo siento, ocurrió un error inesperado. Por favor, inténtalo de nuevo más tarde."
                })

                # Actualizar estado
                await websocket.send_json({
                    "type": "status",
                    "content": "Error",
                    "status": "error"
                })

    except WebSocketDisconnect:
        # Manejar desconexión
        if session_id in active_connections:
            del active_connections[session_id]
        logger.info(f"Cliente desconectado: {session_id}")

    except Exception as e:
        # Manejar otros errores
        logger.error(f"Error en WebSocket: {e}")
        if session_id in active_connections:
            del active_connections[session_id]

@app.get("/api/health")
async def health_check():
    """
    Endpoint para verificar el estado de la aplicación.
    """
    return {"status": "ok"}

def main():
    """
    Función principal para iniciar la aplicación.
    """
    # Obtener puerto de los argumentos de línea de comandos
    import argparse
    parser = argparse.ArgumentParser(description="ISA-Agent Chat")
    parser.add_argument("--port", type=int, default=8005, help="Puerto para la aplicación web")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host para la aplicación web")
    args = parser.parse_args()

    # Iniciar la aplicación
    print(f"🚀 ISA-Agent Chat iniciando en http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
