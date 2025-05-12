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
app = FastAPI(title="OpenManusWeb Simple Chat")

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
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OpenManusWeb Chat</title>
    <style>
        :root {
            --primary-color: #4a6fa5;
            --secondary-color: #6b8cae;
            --background-color: #f5f7fa;
            --text-color: #333;
            --light-color: #fff;
            --border-color: #e1e4e8;
            --success-color: #28a745;
            --error-color: #dc3545;
            --font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: var(--font-family);
            background-color: var(--background-color);
            color: var(--text-color);
            line-height: 1.6;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem;
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        header {
            background-color: var(--primary-color);
            color: var(--light-color);
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }

        h1 {
            font-size: 1.5rem;
            margin: 0;
        }

        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: var(--light-color);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            margin-top: 1rem;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
        }

        .message {
            margin-bottom: 1rem;
            padding: 0.75rem;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
        }

        .user-message {
            background-color: var(--primary-color);
            color: var(--light-color);
            align-self: flex-end;
            margin-left: auto;
        }

        .bot-message {
            background-color: var(--secondary-color);
            color: var(--light-color);
            align-self: flex-start;
        }

        .message-form {
            display: flex;
            padding: 1rem;
            border-top: 1px solid var(--border-color);
            background-color: var(--light-color);
        }

        .message-input {
            flex: 1;
            padding: 0.75rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            font-family: var(--font-family);
            font-size: 1rem;
            resize: none;
        }

        .send-button {
            background-color: var(--primary-color);
            color: var(--light-color);
            border: none;
            border-radius: 4px;
            padding: 0.75rem 1.5rem;
            margin-left: 0.5rem;
            cursor: pointer;
            font-family: var(--font-family);
            font-size: 1rem;
            transition: background-color 0.2s;
        }

        .send-button:hover {
            background-color: var(--secondary-color);
        }

        .send-button:disabled {
            background-color: var(--border-color);
            cursor: not-allowed;
        }

        .status {
            text-align: center;
            padding: 0.5rem;
            font-size: 0.875rem;
            color: var(--text-color);
        }

        .typing {
            color: var(--primary-color);
            font-style: italic;
        }

        .error {
            color: var(--error-color);
        }

        .success {
            color: var(--success-color);
        }

        @media (max-width: 768px) {
            .container {
                padding: 0.5rem;
            }

            .message {
                max-width: 90%;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>OpenManusWeb Chat</h1>
    </header>
    <div class="container">
        <div class="chat-container">
            <div class="chat-messages" id="chat-messages"></div>
            <div class="status" id="status"></div>
            <form class="message-form" id="message-form">
                <textarea class="message-input" id="message-input" placeholder="Escribe tu mensaje aquí..." rows="2"></textarea>
                <button type="submit" class="send-button" id="send-button">Enviar</button>
            </form>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const chatMessages = document.getElementById('chat-messages');
            const messageForm = document.getElementById('message-form');
            const messageInput = document.getElementById('message-input');
            const sendButton = document.getElementById('send-button');
            const statusElement = document.getElementById('status');

            // Generar un ID de sesión único
            const sessionId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

            // Conectar al WebSocket
            const ws = new WebSocket(`ws://${window.location.host}/ws/${sessionId}`);

            // Manejar eventos del WebSocket
            ws.onopen = () => {
                console.log('Conexión WebSocket establecida');
                statusElement.textContent = 'Conectado';
                statusElement.className = 'status success';
                sendButton.disabled = false;
            };

            ws.onclose = () => {
                console.log('Conexión WebSocket cerrada');
                statusElement.textContent = 'Desconectado';
                statusElement.className = 'status error';
                sendButton.disabled = true;
            };

            ws.onerror = (error) => {
                console.error('Error en la conexión WebSocket:', error);
                statusElement.textContent = 'Error de conexión';
                statusElement.className = 'status error';
                sendButton.disabled = true;
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);

                if (data.type === 'message') {
                    // Añadir mensaje del bot
                    addMessage(data.content, 'bot');
                } else if (data.type === 'status') {
                    // Actualizar estado
                    statusElement.textContent = data.content;
                    statusElement.className = `status ${data.status}`;
                }
            };

            // Manejar envío de mensajes
            messageForm.addEventListener('submit', (e) => {
                e.preventDefault();

                const message = messageInput.value.trim();
                if (message) {
                    // Enviar mensaje al servidor
                    ws.send(JSON.stringify({ content: message }));

                    // Añadir mensaje del usuario
                    addMessage(message, 'user');

                    // Limpiar input
                    messageInput.value = '';

                    // Actualizar estado
                    statusElement.textContent = 'Escribiendo...';
                    statusElement.className = 'status typing';
                }
            });

            // Función para añadir mensajes al chat
            function addMessage(content, sender) {
                const messageElement = document.createElement('div');
                messageElement.className = `message ${sender}-message`;
                messageElement.textContent = content;

                chatMessages.appendChild(messageElement);

                // Scroll al final
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            // Ajustar altura del textarea
            messageInput.addEventListener('input', () => {
                messageInput.style.height = 'auto';
                messageInput.style.height = (messageInput.scrollHeight) + 'px';
            });
        });
    </script>
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
            "content": "¡Hola! Soy el asistente de OpenManusWeb. ¿En qué puedo ayudarte hoy?"
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
    parser = argparse.ArgumentParser(description="OpenManusWeb Simple Chat")
    parser.add_argument("--port", type=int, default=8005, help="Puerto para la aplicación web")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host para la aplicación web")
    args = parser.parse_args()

    # Iniciar la aplicación
    print(f"🚀 OpenManusWeb Simple Chat iniciando en http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
