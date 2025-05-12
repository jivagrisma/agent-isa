#!/usr/bin/env python3
"""
Esquemas para la aplicación.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Message(BaseModel):
    """Modelo para los mensajes."""
    role: str
    content: str

class ChatRequest(BaseModel):
    """Modelo para las solicitudes de chat."""
    messages: List[Message]
    stream: bool = False
    temperature: float = 0.7

class ChatResponse(BaseModel):
    """Modelo para las respuestas de chat."""
    message: Message
