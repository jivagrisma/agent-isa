"""
Módulo para gestionar el contexto de documentos en conversaciones.
"""

import json
import logging
import hashlib
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

# Configurar logging
logger = logging.getLogger(__name__)

class DocumentContext:
    """
    Gestor de contexto de documentos para mantener el contexto entre mensajes.
    """

    def __init__(self):
        """
        Inicializa el gestor de contexto de documentos.
        """
        # Crear directorio de caché si no existe
        self.cache_dir = Path(__file__).parent / "context_cache"
        self.cache_dir.mkdir(exist_ok=True)

        # Inicializar caché en memoria
        self.active_contexts = {}
        self.context_ttl = 3600 * 24  # 24 horas en segundos

        logger.info("Gestor de contexto de documentos inicializado")

    def create_document_context(self, session_id: str, file_info: Dict[str, Any]) -> str:
        """
        Crea un contexto de documento para una sesión.

        Args:
            session_id: ID de la sesión
            file_info: Información del archivo

        Returns:
            ID del contexto creado
        """
        # Generar ID único para el contexto
        context_id = self._generate_context_id(session_id, file_info)

        # Crear estructura de contexto
        context = {
            "context_id": context_id,
            "session_id": session_id,
            "file_info": file_info,
            "created_at": int(time.time()),
            "last_accessed": int(time.time()),
            "access_count": 0,
            "chunks": self._create_chunks(file_info),
            "metadata": {
                "filename": file_info.get("filename", ""),
                "content_type": file_info.get("content_type", ""),
                "size": file_info.get("size", 0),
                "active": True
            }
        }

        # Guardar en memoria
        self.active_contexts[context_id] = context

        # Guardar en disco
        self._save_context_to_disk(context_id, context)

        logger.info(f"Contexto de documento creado: {context_id} para sesión {session_id}")
        return context_id

    def get_document_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un contexto de documento.

        Args:
            context_id: ID del contexto

        Returns:
            Contexto del documento o None si no existe
        """
        # Verificar si existe en memoria
        if context_id in self.active_contexts:
            context = self.active_contexts[context_id]
            # Actualizar último acceso
            context["last_accessed"] = int(time.time())
            context["access_count"] += 1
            return context

        # Verificar si existe en disco
        context_path = self.cache_dir / f"{context_id}.json"
        if context_path.exists():
            try:
                with open(context_path, "r", encoding="utf-8") as f:
                    context = json.load(f)

                # Verificar si ha expirado
                if int(time.time()) - context["last_accessed"] > self.context_ttl:
                    logger.info(f"Contexto expirado: {context_id}")
                    return None

                # Actualizar último acceso
                context["last_accessed"] = int(time.time())
                context["access_count"] += 1

                # Guardar en memoria
                self.active_contexts[context_id] = context

                # Actualizar en disco
                self._save_context_to_disk(context_id, context)

                return context
            except Exception as e:
                logger.error(f"Error al cargar contexto desde disco: {e}")
                return None

        return None

    def get_active_context_for_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el contexto activo para una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            Contexto activo o None si no hay ninguno
        """
        # Buscar en memoria primero
        for context_id, context in self.active_contexts.items():
            if context["session_id"] == session_id and context["metadata"]["active"]:
                return context

        # Buscar en disco si no está en memoria
        try:
            for file_path in self.cache_dir.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        context = json.load(f)

                    if context["session_id"] == session_id and context["metadata"]["active"]:
                        # Actualizar último acceso
                        context["last_accessed"] = int(time.time())
                        context["access_count"] += 1

                        # Guardar en memoria
                        self.active_contexts[context["context_id"]] = context

                        # Actualizar en disco
                        self._save_context_to_disk(context["context_id"], context)

                        return context
                except Exception as e:
                    logger.error(f"Error al leer archivo de contexto {file_path}: {e}")
                    continue
        except Exception as e:
            logger.error(f"Error al buscar contextos en disco: {e}")

        return None

    def enrich_message(self, session_id: str, message: str, force_enrich: bool = False) -> str:
        """
        Enriquece un mensaje con el contexto del documento activo.

        Args:
            session_id: ID de la sesión
            message: Mensaje original
            force_enrich: Si es True, fuerza el enriquecimiento independientemente de otras condiciones

        Returns:
            Mensaje enriquecido
        """
        # Obtener contexto activo
        context = self.get_active_context_for_session(session_id)
        if not context:
            logger.warning(f"No se encontró contexto activo para la sesión {session_id}")
            return message

        # Obtener información del archivo
        file_info = context["file_info"]

        # Si se fuerza el enriquecimiento, no verificar otras condiciones
        if not force_enrich:
            # Verificar si el mensaje hace referencia a documentos o archivos
            # Lista de palabras clave que indican referencia a documentos
            document_keywords = [
                "documento", "archivo", "pdf", "adjunto", "anexo",
                "resumen", "resumir", "resume", "contenido",
                "analiza", "analizar", "análisis", "extraer",
                "texto", "información", "datos", "leer",
                "interpretar", "explicar", "describir", "elabora"
            ]

            # Verificar si el mensaje contiene alguna de las palabras clave
            message_lower = message.lower()
            contains_document_reference = any(keyword in message_lower for keyword in document_keywords)

            # Si el mensaje no hace referencia explícita a documentos, verificar si es reciente después de cargar un archivo
            is_recent_upload = int(time.time()) - file_info.get("timestamp", 0) < 600  # 10 minutos

            # Enriquecer el mensaje si hace referencia a documentos o si es reciente después de cargar un archivo
            should_enrich = contains_document_reference or is_recent_upload

            # Si no se debe enriquecer, devolver el mensaje original
            if not should_enrich:
                logger.info(f"No se enriquece el mensaje para la sesión {session_id} (no contiene referencias a documentos y no es reciente)")
                return message
        else:
            logger.info(f"Forzando enriquecimiento del mensaje para la sesión {session_id}")

        # Preparar información básica del archivo
        file_metadata = f"Nombre del archivo: {file_info.get('filename', '')}\nTipo: {file_info.get('content_type', '')}\n"

        # Incluir el contenido del texto si está disponible
        if "text_content" in file_info and file_info["text_content"]:
            # Limitar el contenido para no exceder los límites de tokens
            text_content = file_info["text_content"]
            if len(text_content) > 12000:
                text_content = text_content[:12000] + "...\n[Contenido truncado por ser demasiado largo]"

            # Crear un nuevo mensaje que incluya tanto la consulta del usuario como el contenido del archivo
            enriched_message = f"""
{message}

A continuación está el contenido del archivo adjunto '{file_info.get('filename', '')}':

{file_metadata}
----- CONTENIDO DEL ARCHIVO -----
{text_content}
----- FIN DEL CONTENIDO -----

Por favor, utiliza este contenido para responder a mi consulta. Recuerda que el usuario ha adjuntado este documento y está haciendo preguntas sobre él.
"""
        else:
            # Si no hay contenido de texto, usar el análisis
            enriched_message = f"""
{message}

A continuación está el análisis del archivo adjunto '{file_info.get('filename', '')}':

{file_metadata}
----- ANÁLISIS DEL ARCHIVO -----
{file_info.get('analysis', 'No hay análisis disponible')}
----- FIN DEL ANÁLISIS -----

Por favor, utiliza este análisis para responder a mi consulta. Recuerda que el usuario ha adjuntado este documento y está haciendo preguntas sobre él.
"""

        # Registrar que se ha enriquecido el mensaje
        logger.info(f"Mensaje enriquecido con contexto de documento para sesión {session_id}")

        return enriched_message

    def _generate_context_id(self, session_id: str, file_info: Dict[str, Any]) -> str:
        """
        Genera un ID único para el contexto.

        Args:
            session_id: ID de la sesión
            file_info: Información del archivo

        Returns:
            ID único del contexto
        """
        # Crear hash basado en la sesión, nombre del archivo y timestamp
        content = f"{session_id}_{file_info.get('filename', '')}_{file_info.get('timestamp', int(time.time()))}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _create_chunks(self, file_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Divide el contenido del archivo en chunks para mejor manejo.

        Args:
            file_info: Información del archivo

        Returns:
            Lista de chunks
        """
        chunks = []

        # Verificar si hay contenido de texto
        if "text_content" in file_info and file_info["text_content"]:
            text_content = file_info["text_content"]

            # Dividir en chunks de aproximadamente 4000 caracteres
            chunk_size = 4000

            # Si el contenido es pequeño, usar un solo chunk
            if len(text_content) <= chunk_size:
                chunks.append({
                    "id": "chunk_1",
                    "text": text_content,
                    "start_char": 0,
                    "end_char": len(text_content)
                })
            else:
                # Dividir por párrafos primero
                paragraphs = text_content.split("\n\n")

                current_chunk = ""
                chunk_id = 1
                start_char = 0

                for paragraph in paragraphs:
                    # Si añadir el párrafo excede el tamaño del chunk, guardar el chunk actual y empezar uno nuevo
                    if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                        chunks.append({
                            "id": f"chunk_{chunk_id}",
                            "text": current_chunk,
                            "start_char": start_char,
                            "end_char": start_char + len(current_chunk)
                        })

                        chunk_id += 1
                        start_char += len(current_chunk)
                        current_chunk = paragraph + "\n\n"
                    else:
                        current_chunk += paragraph + "\n\n"

                # Añadir el último chunk si queda algo
                if current_chunk:
                    chunks.append({
                        "id": f"chunk_{chunk_id}",
                        "text": current_chunk,
                        "start_char": start_char,
                        "end_char": start_char + len(current_chunk)
                    })

        return chunks

    def _save_context_to_disk(self, context_id: str, context: Dict[str, Any]) -> None:
        """
        Guarda un contexto en disco.

        Args:
            context_id: ID del contexto
            context: Datos del contexto
        """
        try:
            context_path = self.cache_dir / f"{context_id}.json"
            with open(context_path, "w", encoding="utf-8") as f:
                json.dump(context, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error al guardar contexto en disco: {e}")
