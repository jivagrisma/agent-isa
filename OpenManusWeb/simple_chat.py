#!/usr/bin/env python3
"""
Interfaz web de chat simple para OpenManusWeb.
"""

import asyncio
import json
import logging
import math
import os
import sys
import uuid
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Verificar soporte para diferentes tipos de documentos
PDF_SUPPORT = True  # Ahora manejado por el DocumentProcessor

import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional

# Cargar variables de entorno
load_dotenv()

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

# Importar módulos personalizados
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from modules.search.tavily_search import TavilySearchEngine
from modules.document import DocumentAnalyzer, DocumentProcessor
from modules.document.document_context import DocumentContext

# Crear la aplicación FastAPI
app = FastAPI(title="ISA-Agent Chat")

# Inicializar el motor de búsqueda Tavily
tavily_search_engine = TavilySearchEngine()

# Inicializar el analizador de documentos
document_analyzer = DocumentAnalyzer()

# Inicializar el procesador de documentos
document_processor = DocumentProcessor()

# Inicializar el gestor de contexto de documentos
document_context_manager = DocumentContext()

# Crear directorio para archivos subidos si no existe
uploads_dir = Path(__file__).parent / "uploads"
uploads_dir.mkdir(exist_ok=True)

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

# Almacenar información de archivos cargados por sesión
session_files: Dict[str, List[Dict[str, Any]]] = {}

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
    Página principal de chat - Redirige a la versión mejorada.
    """
    # Redirigir a la versión mejorada
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/enhanced")

@app.get("/enhanced", response_class=HTMLResponse)
async def get_enhanced_chat_page(request: Request):
    """
    Página de chat mejorada con capacidades extendidas.
    """
    return templates.TemplateResponse("enhanced_chat_new.html", {"request": request})

# Modelo para la solicitud de búsqueda web
class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 5
    search_depth: str = "basic"

@app.post("/api/web-search")
async def web_search(request: WebSearchRequest):
    """
    Endpoint para realizar búsquedas web utilizando Tavily.
    """
    try:
        # Realizar búsqueda
        results = tavily_search_engine.search(
            query=request.query,
            max_results=request.max_results,
            search_depth=request.search_depth
        )

        # Formatear resultados
        formatted_results = tavily_search_engine.format_results(results)

        return {"success": True, "results": formatted_results}
    except Exception as e:
        logger.error(f"Error en búsqueda web: {e}")
        return {"success": False, "error": str(e)}

# Modelo para la respuesta de carga de archivos
class FileUploadResponse(BaseModel):
    success: bool
    filename: Optional[str] = None
    content_type: Optional[str] = None
    size: Optional[int] = None
    analysis: Optional[str] = None
    error: Optional[str] = None

@app.post("/api/upload-file", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...), session_id: str = Form(None)):
    """
    Endpoint para cargar archivos y analizarlos.

    Args:
        file: Archivo a cargar
        session_id: ID de sesión para asociar el archivo con una conversación
    """
    try:
        # Verificar si el archivo es válido
        if not file or not file.filename:
            return FileUploadResponse(success=False, error="No se proporcionó ningún archivo")

        # Obtener extensión del archivo
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''

        # Verificar tipo de archivo permitido
        allowed_extensions = ['txt', 'pdf', 'docx', 'xlsx', 'jpg', 'jpeg', 'png', 'md']
        if file_ext not in allowed_extensions:
            return FileUploadResponse(
                success=False,
                error=f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(allowed_extensions)}"
            )

        # Generar nombre de archivo único
        unique_filename = f"{int(time.time())}_{file.filename}"
        file_path = uploads_dir / unique_filename

        # Guardar archivo
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Obtener información del archivo
        file_size = os.path.getsize(file_path)
        content_type = file.content_type

        # Determinar si el archivo es grande (más de 5MB)
        is_large_file = file_size > 5 * 1024 * 1024

        # Procesar el archivo utilizando el procesador de documentos
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''

        # Procesar el archivo para extraer su contenido
        document_result = document_processor.process_document(str(file_path))

        # Verificar si hubo error en el procesamiento
        if "error" in document_result:
            logger.error(f"Error al procesar archivo: {document_result['error']}")
            analysis = f"Error al procesar el archivo: {document_result['error']}"
            file_text_content = None
        else:
            # Extraer contenido de texto si está disponible
            file_text_content = document_result.get("text_content")

            # Registrar información sobre el procesamiento
            if file_text_content:
                logger.info(f"Texto extraído del archivo {file_ext}: {len(file_text_content)} caracteres")

            # Para archivos grandes, iniciar análisis asíncrono
            if is_large_file:
                # Función para formatear tamaño de archivo
                def format_file_size(size_bytes):
                    if size_bytes == 0:
                        return "0 Bytes"
                    size_names = ["Bytes", "KB", "MB", "GB", "TB"]
                    i = int(math.log(size_bytes, 1024))
                    p = math.pow(1024, i)
                    s = round(size_bytes / p, 2)
                    return f"{s} {size_names[i]}"

                analysis = f"Archivo {file.filename} cargado correctamente. El análisis está en proceso y puede tardar unos minutos debido al tamaño del archivo ({format_file_size(file_size)}). Los resultados se actualizarán automáticamente cuando estén disponibles."

                # Crear información del archivo para la tarea asíncrona
                file_info = {
                    "filename": file.filename,
                    "path": str(file_path),
                    "content_type": content_type,
                    "size": file_size,
                    "analysis": analysis,
                    "text_content": file_text_content,
                    "metadata": document_result.get("metadata", {}),
                    "timestamp": int(time.time())
                }

                # Iniciar tarea en segundo plano para análisis
                asyncio.create_task(analyze_file_async(file_path, file_ext, file_info, session_id))
            else:
                # Análisis síncrono para archivos pequeños
                if file_text_content:
                    # Analizar con AWS Bedrock si hay texto extraído
                    result = document_analyzer.analyze_text(file_text_content)
                    if "error" in result:
                        analysis = f"Error al analizar el archivo: {result['error']}"
                    else:
                        analysis = result["analysis"]
                elif file_ext in ['jpg', 'jpeg', 'png']:
                    # Analizar imagen
                    result = document_analyzer.analyze_image(str(file_path))
                    if "error" in result:
                        analysis = f"Error al analizar la imagen: {result['error']}"
                    else:
                        analysis = result["analysis"]
                else:
                    # Tipos de archivo no soportados para análisis
                    analysis = f"Archivo {file.filename} cargado correctamente. El contenido ha sido extraído pero no se pudo generar un análisis automático."

        # Guardar información del archivo en la sesión si se proporciona un ID de sesión
        if not 'file_info' in locals():
            # Si no se creó file_info en el procesamiento asíncrono
            file_info = {
                "filename": file.filename,
                "path": str(file_path),
                "content_type": content_type,
                "size": file_size,
                "analysis": analysis,
                "text_content": file_text_content,
                "metadata": document_result.get("metadata", {}) if 'document_result' in locals() else {},
                "timestamp": int(time.time())
            }

        if session_id:
            if session_id not in session_files:
                session_files[session_id] = []

            # Añadir archivo a la sesión
            session_files[session_id].append(file_info)

            # Crear contexto de documento para mantener el contexto entre mensajes
            context_id = document_context_manager.create_document_context(session_id, file_info)
            logger.info(f"Contexto de documento creado: {context_id} para archivo {file.filename}")

            # Si hay una conversación activa, añadir un mensaje del sistema sobre el archivo
            if session_id in conversations:
                # Mensaje más detallado sobre el archivo cargado
                system_message = f"""[Sistema: El usuario ha cargado un archivo '{file.filename}'.

El archivo ha sido procesado y su contenido está disponible para análisis.
Si el usuario pregunta sobre el archivo o solicita un resumen, análisis o cualquier información relacionada,
utiliza el contenido del archivo para responder de manera completa y precisa.
El contexto del documento se mantendrá activo para futuras consultas.]"""

                conversations[session_id].append({"role": "system", "content": system_message})

        return FileUploadResponse(
            success=True,
            filename=file.filename,
            content_type=content_type,
            size=file_size,
            analysis=analysis
        )

    except Exception as e:
        logger.error(f"Error al cargar archivo: {e}")
        return FileUploadResponse(success=False, error=str(e))

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

        # Enviar mensaje de bienvenida con un tipo especial para que el cliente lo maneje correctamente
        await websocket.send_json({
            "type": "welcome",
            "content": "¡Hola! Soy el asistente ISA. ¿En qué puedo ayudarte hoy?"
        })

        while True:
            # Recibir mensaje del cliente
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_content = message_data.get("content", "")

            # Obtener configuración adicional si está disponible
            config_data = message_data.get("config", {})
            model = config_data.get("model")
            temperature = config_data.get("temperature", 0.7)

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

                # Utilizar el gestor de contexto para enriquecer el mensaje con el contenido del documento
                if len(messages) > 0 and messages[-1]["role"] == "user":
                    # Obtener el mensaje original del usuario
                    original_message = messages[-1]["content"]

                    # Verificar si hay archivos en la sesión
                    has_files = session_id in session_files and len(session_files[session_id]) > 0

                    # Verificar si el mensaje contiene palabras clave relacionadas con documentos
                    document_keywords = [
                        "documento", "archivo", "pdf", "adjunto", "anexo",
                        "resumen", "resumir", "resume", "contenido",
                        "analiza", "analizar", "análisis", "extraer",
                        "texto", "información", "datos", "leer",
                        "interpretar", "explicar", "describir", "elabora"
                    ]

                    message_lower = original_message.lower()
                    contains_document_reference = any(keyword in message_lower for keyword in document_keywords)

                    # Si hay archivos en la sesión, siempre forzar el enriquecimiento para mensajes que hacen referencia a documentos
                    if has_files and contains_document_reference:
                        logger.info(f"Forzando enriquecimiento para mensaje con referencia a documento en sesión: {session_id}")
                        # Enriquecer el mensaje con el contexto del documento activo, forzando el enriquecimiento
                        enriched_message = document_context_manager.enrich_message(session_id, original_message, force_enrich=True)

                        # Reemplazar el mensaje original con el mensaje enriquecido
                        messages[-1]["content"] = enriched_message

                        # Registrar la modificación
                        logger.info(f"Mensaje del usuario enriquecido con contexto de documento para sesión: {session_id}")
                    else:
                        # Intentar enriquecer el mensaje normalmente
                        enriched_message = document_context_manager.enrich_message(session_id, original_message)

                        # Si el mensaje fue enriquecido (es diferente al original), reemplazarlo
                        if enriched_message != original_message:
                            # Reemplazar el mensaje original con el mensaje enriquecido
                            messages[-1]["content"] = enriched_message

                            # Registrar la modificación
                            logger.info(f"Mensaje del usuario enriquecido con contexto de documento para sesión: {session_id}")

                # Intentar enviar mensaje al LLM con timeout
                try:
                    import asyncio
                    response = await asyncio.wait_for(
                        llm.ask_bedrock(
                            messages=messages,
                            stream=False,
                            temperature=temperature
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

@app.get("/api/models")
async def get_models():
    """
    Endpoint para obtener la lista de modelos disponibles.
    """
    # Lista de modelos disponibles
    models = [
        {
            "id": "anthropic.claude-3-sonnet-20240229-v1:0",
            "name": "Claude 3.7 Sonnet",
            "provider": "Anthropic",
            "capabilities": ["chat", "tools", "vision"],
            "max_tokens": 4096
        },
        {
            "id": "amazon.nova-lite-v1",
            "name": "Amazon Nova Lite",
            "provider": "Amazon",
            "capabilities": ["chat"],
            "max_tokens": 4096
        },
        {
            "id": "amazon.nova-pro-v1",
            "name": "Amazon Nova Pro",
            "provider": "Amazon",
            "capabilities": ["chat", "tools"],
            "max_tokens": 4096
        }
    ]

    return {"models": models}

@app.get("/api/files/{session_id}")
async def get_session_files(session_id: str):
    """
    Endpoint para obtener la lista de archivos cargados en una sesión.
    """
    if session_id not in session_files:
        return {"files": []}

    # Devolver información básica de los archivos (sin incluir el análisis completo)
    files_info = []
    for file in session_files[session_id]:
        files_info.append({
            "filename": file["filename"],
            "content_type": file["content_type"],
            "size": file["size"],
            "timestamp": file["timestamp"]
        })

    return {"files": files_info}

# Endpoint de compartir análisis eliminado

async def analyze_file_async(file_path, file_ext, file_info, session_id):
    """
    Analiza un archivo de forma asíncrona.

    Args:
        file_path: Ruta al archivo
        file_ext: Extensión del archivo
        file_info: Información del archivo
        session_id: ID de sesión
    """
    try:
        analysis = ""
        text_content = file_info.get("text_content")

        # Si no hay contenido de texto, intentar procesarlo de nuevo
        if not text_content:
            # Procesar el archivo para extraer su contenido
            document_result = document_processor.process_document(str(file_path))

            # Verificar si hubo error en el procesamiento
            if "error" in document_result:
                logger.error(f"Error al procesar archivo asíncrono: {document_result['error']}")
                analysis = f"Error al procesar el archivo: {document_result['error']}"
            else:
                # Extraer contenido de texto si está disponible
                text_content = document_result.get("text_content")

                # Actualizar la información del archivo con el contenido extraído
                file_info["text_content"] = text_content
                file_info["metadata"] = document_result.get("metadata", {})

                # Registrar información sobre el procesamiento
                if text_content:
                    logger.info(f"Texto extraído del archivo {file_ext} (asíncrono): {len(text_content)} caracteres")

        # Analizar el contenido si está disponible
        if text_content:
            # Analizar con AWS Bedrock
            result = document_analyzer.analyze_text(text_content)
            if "error" in result:
                analysis = f"Error al analizar el archivo: {result['error']}"
            else:
                analysis = result["analysis"]
        elif file_ext in ['jpg', 'jpeg', 'png']:
            # Analizar imagen
            result = document_analyzer.analyze_image(str(file_path))
            if "error" in result:
                analysis = f"Error al analizar la imagen: {result['error']}"
            else:
                analysis = result["analysis"]
        else:
            # No se pudo extraer contenido para análisis
            analysis = f"No se pudo extraer contenido del archivo para su análisis. El tipo de archivo {file_ext} puede no ser compatible o el archivo puede estar dañado."

        # Actualizar análisis en la información del archivo
        if session_id in session_files:
            for file in session_files[session_id]:
                if file["path"] == str(file_path):
                    file["analysis"] = analysis

                    # Notificar al cliente si hay una conexión activa
                    if session_id in active_connections:
                        websocket = active_connections[session_id]
                        await websocket.send_json({
                            "type": "file_update",
                            "content": f"El análisis del archivo '{file_info['filename']}' ha sido completado.",
                            "file_info": {
                                "filename": file_info["filename"],
                                "analysis": analysis,
                                "timestamp": file_info["timestamp"]
                            }
                        })

    except Exception as e:
        logger.error(f"Error en análisis asíncrono: {e}")

        # Actualizar con mensaje de error
        if session_id in session_files:
            for file in session_files[session_id]:
                if file["path"] == str(file_path):
                    file["analysis"] = f"Error durante el análisis: {str(e)}"



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
