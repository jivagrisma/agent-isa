"""
Generador de imágenes para agent-isa.
Proporciona capacidades de generación y edición de imágenes.
"""

import logging
import os
import json
import base64
import time
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, BinaryIO
import boto3
import requests
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import io

from ..core import PluginInterface, ConfigManager

# Configurar logging
logger = logging.getLogger(__name__)

class ImageGenerator(PluginInterface):
    """
    Generador de imágenes con soporte para diferentes servicios y estilos.
    
    Características:
    1. Generación de imágenes a partir de descripciones textuales
    2. Edición básica de imágenes
    3. Soporte para diferentes estilos y formatos
    4. Almacenamiento y gestión de imágenes generadas
    """
    
    VERSION = "0.1.0"
    DEPENDENCIES = ["core.ConfigManager"]
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        Inicializa el generador de imágenes.
        
        Args:
            config_manager: Gestor de configuración
        """
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.get_config("image")
        
        # Inicializar clientes
        self.bedrock_client = None
        self.s3_client = None
        
        # Directorio para almacenar imágenes
        self.images_dir = Path(self.config.get("storage.directory", "images"))
        os.makedirs(self.images_dir, exist_ok=True)
        
        logger.info("Generador de imágenes inicializado")
    
    def initialize_aws_clients(self):
        """
        Inicializa los clientes de AWS.
        """
        try:
            # Inicializar cliente de Bedrock
            region = self.config.get("aws.region", "us-east-1")
            
            # Crear cliente de Bedrock
            self.bedrock_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=region
            )
            
            # Inicializar cliente de S3 si está configurado
            if self.config.get("storage.use_s3", False):
                self.s3_client = boto3.client(
                    service_name="s3",
                    region_name=region
                )
            
            logger.info("Clientes AWS inicializados")
            return True
            
        except Exception as e:
            logger.error(f"Error al inicializar clientes AWS: {e}")
            return False
    
    async def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
        style: Optional[str] = None,
        size: Optional[str] = None,
        format: Optional[str] = None,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Genera una imagen a partir de una descripción textual.
        
        Args:
            prompt: Descripción textual de la imagen
            model: Modelo a utilizar (titan, stable-diffusion, etc.)
            style: Estilo de la imagen
            size: Tamaño de la imagen (ej. "1024x1024")
            format: Formato de la imagen (png, jpeg)
            save: Si debe guardar la imagen generada
            
        Returns:
            Diccionario con información de la imagen generada
        """
        # Verificar cliente de Bedrock
        if not self.bedrock_client:
            success = self.initialize_aws_clients()
            if not success:
                return {"error": "No se pudo inicializar el cliente de AWS Bedrock"}
        
        # Determinar modelo a utilizar
        if not model:
            model = self.config.get("generation.default_model", "amazon.titan-image-generator-v1")
        
        # Determinar tamaño
        if not size:
            size = self.config.get("generation.default_size", "1024x1024")
        width, height = map(int, size.split("x"))
        
        # Determinar formato
        if not format:
            format = self.config.get("generation.default_format", "png")
        
        # Construir prompt con estilo si se especifica
        full_prompt = prompt
        if style:
            style_prompt = self._get_style_prompt(style)
            full_prompt = f"{prompt}, {style_prompt}"
        
        try:
            # Generar imagen según el modelo
            if "titan" in model:
                image_data = self._generate_with_titan(full_prompt, width, height, format)
            elif "stable-diffusion" in model:
                image_data = self._generate_with_stable_diffusion(full_prompt, width, height, format)
            else:
                return {"error": f"Modelo no soportado: {model}"}
            
            # Guardar imagen si se solicita
            image_path = None
            if save:
                image_path = self._save_image(image_data, format)
            
            # Construir resultado
            result = {
                "success": True,
                "prompt": prompt,
                "model": model,
                "style": style,
                "size": size,
                "format": format,
                "image_data": base64.b64encode(image_data).decode("utf-8"),
                "image_path": str(image_path) if image_path else None,
                "timestamp": time.time()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error al generar imagen: {e}")
            return {"error": str(e)}
    
    def edit_image(
        self,
        image_data: Union[bytes, str, Path],
        operations: List[Dict[str, Any]],
        format: Optional[str] = None,
        save: bool = True
    ) -> Dict[str, Any]:
        """
        Edita una imagen aplicando operaciones básicas.
        
        Args:
            image_data: Datos de la imagen (bytes, ruta o base64)
            operations: Lista de operaciones a aplicar
            format: Formato de salida
            save: Si debe guardar la imagen editada
            
        Returns:
            Diccionario con información de la imagen editada
        """
        try:
            # Cargar imagen
            if isinstance(image_data, (str, Path)) and os.path.exists(image_data):
                # Cargar desde archivo
                img = Image.open(image_data)
            elif isinstance(image_data, bytes):
                # Cargar desde bytes
                img = Image.open(io.BytesIO(image_data))
            elif isinstance(image_data, str) and image_data.startswith("data:image"):
                # Cargar desde data URL
                image_data = image_data.split(",")[1]
                img = Image.open(io.BytesIO(base64.b64decode(image_data)))
            elif isinstance(image_data, str):
                # Intentar decodificar base64
                img = Image.open(io.BytesIO(base64.b64decode(image_data)))
            else:
                return {"error": "Formato de imagen no soportado"}
            
            # Aplicar operaciones
            for operation in operations:
                op_type = operation.get("type")
                
                if op_type == "resize":
                    width = operation.get("width", img.width)
                    height = operation.get("height", img.height)
                    img = img.resize((width, height))
                
                elif op_type == "crop":
                    left = operation.get("left", 0)
                    top = operation.get("top", 0)
                    right = operation.get("right", img.width)
                    bottom = operation.get("bottom", img.height)
                    img = img.crop((left, top, right, bottom))
                
                elif op_type == "rotate":
                    angle = operation.get("angle", 0)
                    img = img.rotate(angle)
                
                elif op_type == "flip":
                    direction = operation.get("direction", "horizontal")
                    if direction == "horizontal":
                        img = ImageOps.mirror(img)
                    elif direction == "vertical":
                        img = ImageOps.flip(img)
                
                elif op_type == "adjust":
                    # Ajustar brillo
                    if "brightness" in operation:
                        factor = operation["brightness"]
                        enhancer = ImageEnhance.Brightness(img)
                        img = enhancer.enhance(factor)
                    
                    # Ajustar contraste
                    if "contrast" in operation:
                        factor = operation["contrast"]
                        enhancer = ImageEnhance.Contrast(img)
                        img = enhancer.enhance(factor)
                    
                    # Ajustar color
                    if "color" in operation:
                        factor = operation["color"]
                        enhancer = ImageEnhance.Color(img)
                        img = enhancer.enhance(factor)
                
                elif op_type == "filter":
                    filter_name = operation.get("name", "")
                    
                    if filter_name == "blur":
                        radius = operation.get("radius", 2)
                        img = img.filter(ImageFilter.GaussianBlur(radius=radius))
                    elif filter_name == "sharpen":
                        img = img.filter(ImageFilter.SHARPEN)
                    elif filter_name == "edge_enhance":
                        img = img.filter(ImageFilter.EDGE_ENHANCE)
                    elif filter_name == "emboss":
                        img = img.filter(ImageFilter.EMBOSS)
                    elif filter_name == "contour":
                        img = img.filter(ImageFilter.CONTOUR)
            
            # Determinar formato de salida
            if not format:
                format = img.format or "PNG"
            
            # Convertir imagen a bytes
            buffer = io.BytesIO()
            img.save(buffer, format=format)
            output_data = buffer.getvalue()
            
            # Guardar imagen si se solicita
            image_path = None
            if save:
                image_path = self._save_image(output_data, format.lower())
            
            # Construir resultado
            result = {
                "success": True,
                "format": format.lower(),
                "width": img.width,
                "height": img.height,
                "image_data": base64.b64encode(output_data).decode("utf-8"),
                "image_path": str(image_path) if image_path else None,
                "operations": operations,
                "timestamp": time.time()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error al editar imagen: {e}")
            return {"error": str(e)}
    
    def analyze_image(
        self,
        image_data: Union[bytes, str, Path]
    ) -> Dict[str, Any]:
        """
        Analiza una imagen para extraer información.
        
        Args:
            image_data: Datos de la imagen (bytes, ruta o base64)
            
        Returns:
            Diccionario con información de la imagen
        """
        try:
            # Cargar imagen
            if isinstance(image_data, (str, Path)) and os.path.exists(image_data):
                # Cargar desde archivo
                img = Image.open(image_data)
                image_path = str(image_data)
            elif isinstance(image_data, bytes):
                # Cargar desde bytes
                img = Image.open(io.BytesIO(image_data))
                image_path = None
            elif isinstance(image_data, str) and image_data.startswith("data:image"):
                # Cargar desde data URL
                image_data = image_data.split(",")[1]
                img = Image.open(io.BytesIO(base64.b64decode(image_data)))
                image_path = None
            elif isinstance(image_data, str):
                # Intentar decodificar base64
                img = Image.open(io.BytesIO(base64.b64decode(image_data)))
                image_path = None
            else:
                return {"error": "Formato de imagen no soportado"}
            
            # Extraer información básica
            info = {
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height,
                "path": image_path,
                "size_bytes": os.path.getsize(image_path) if image_path else len(image_data) if isinstance(image_data, bytes) else None,
                "timestamp": time.time()
            }
            
            # Extraer información EXIF si está disponible
            if hasattr(img, "_getexif") and img._getexif():
                exif = {}
                for tag, value in img._getexif().items():
                    if tag in EXIF_TAGS:
                        exif[EXIF_TAGS[tag]] = value
                info["exif"] = exif
            
            return info
            
        except Exception as e:
            logger.error(f"Error al analizar imagen: {e}")
            return {"error": str(e)}
    
    def _generate_with_titan(
        self,
        prompt: str,
        width: int,
        height: int,
        format: str
    ) -> bytes:
        """
        Genera una imagen con Amazon Titan.
        
        Args:
            prompt: Descripción textual
            width: Ancho de la imagen
            height: Alto de la imagen
            format: Formato de la imagen
            
        Returns:
            Datos de la imagen generada
        """
        try:
            # Configurar parámetros
            request_body = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt,
                    "negativeText": self.config.get("generation.negative_prompt", ""),
                    "width": width,
                    "height": height
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "quality": self.config.get("generation.quality", "standard"),
                    "cfgScale": self.config.get("generation.cfg_scale", 8.0),
                    "seed": int(time.time()) % 1000000
                }
            }
            
            # Invocar modelo
            response = self.bedrock_client.invoke_model(
                modelId="amazon.titan-image-generator-v1",
                body=json.dumps(request_body)
            )
            
            # Procesar respuesta
            response_body = json.loads(response.get("body").read())
            
            if "images" in response_body and response_body["images"]:
                # Decodificar imagen base64
                image_b64 = response_body["images"][0]
                image_data = base64.b64decode(image_b64)
                
                # Convertir formato si es necesario
                if format.lower() != "png":
                    img = Image.open(io.BytesIO(image_data))
                    buffer = io.BytesIO()
                    img.save(buffer, format=format.upper())
                    image_data = buffer.getvalue()
                
                return image_data
            else:
                raise Exception("No se generó ninguna imagen")
                
        except Exception as e:
            logger.error(f"Error al generar imagen con Titan: {e}")
            raise
    
    def _generate_with_stable_diffusion(
        self,
        prompt: str,
        width: int,
        height: int,
        format: str
    ) -> bytes:
        """
        Genera una imagen con Stable Diffusion.
        
        Args:
            prompt: Descripción textual
            width: Ancho de la imagen
            height: Alto de la imagen
            format: Formato de la imagen
            
        Returns:
            Datos de la imagen generada
        """
        try:
            # Configurar parámetros
            request_body = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1.0
                    }
                ],
                "cfg_scale": self.config.get("generation.cfg_scale", 7.0),
                "height": height,
                "width": width,
                "samples": 1,
                "steps": self.config.get("generation.steps", 50)
            }
            
            # Añadir prompt negativo si está configurado
            negative_prompt = self.config.get("generation.negative_prompt", "")
            if negative_prompt:
                request_body["text_prompts"].append({
                    "text": negative_prompt,
                    "weight": -1.0
                })
            
            # Invocar modelo
            response = self.bedrock_client.invoke_model(
                modelId="stability.stable-diffusion-xl-v1",
                body=json.dumps(request_body)
            )
            
            # Procesar respuesta
            response_body = json.loads(response.get("body").read())
            
            if "artifacts" in response_body and response_body["artifacts"]:
                # Decodificar imagen base64
                image_b64 = response_body["artifacts"][0]["base64"]
                image_data = base64.b64decode(image_b64)
                
                # Convertir formato si es necesario
                if format.lower() != "png":
                    img = Image.open(io.BytesIO(image_data))
                    buffer = io.BytesIO()
                    img.save(buffer, format=format.upper())
                    image_data = buffer.getvalue()
                
                return image_data
            else:
                raise Exception("No se generó ninguna imagen")
                
        except Exception as e:
            logger.error(f"Error al generar imagen con Stable Diffusion: {e}")
            raise
    
    def _save_image(self, image_data: bytes, format: str) -> Path:
        """
        Guarda una imagen en disco o S3.
        
        Args:
            image_data: Datos de la imagen
            format: Formato de la imagen
            
        Returns:
            Ruta de la imagen guardada
        """
        # Generar nombre de archivo único
        filename = f"{uuid.uuid4()}.{format.lower()}"
        
        # Determinar ruta de guardado
        if self.config.get("storage.use_s3", False) and self.s3_client:
            # Guardar en S3
            bucket = self.config.get("storage.s3_bucket")
            key = f"{self.config.get('storage.s3_prefix', 'images')}/{filename}"
            
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=image_data,
                ContentType=f"image/{format.lower()}"
            )
            
            return Path(f"s3://{bucket}/{key}")
        else:
            # Guardar en disco local
            file_path = self.images_dir / filename
            
            with open(file_path, "wb") as f:
                f.write(image_data)
            
            return file_path
    
    def _get_style_prompt(self, style: str) -> str:
        """
        Obtiene el prompt para un estilo específico.
        
        Args:
            style: Estilo de imagen
            
        Returns:
            Prompt de estilo
        """
        style_prompts = {
            "realista": "realistic, detailed, photorealistic, high resolution",
            "anime": "anime style, vibrant colors, clean lines, 2D illustration",
            "acuarela": "watercolor painting, soft colors, flowing, artistic",
            "pixel_art": "pixel art, 8-bit style, retro gaming aesthetic",
            "3d": "3D render, detailed textures, volumetric lighting, ray tracing",
            "boceto": "pencil sketch, hand-drawn, detailed linework",
            "abstracto": "abstract art, non-representational, geometric shapes, bold colors",
            "vintage": "vintage style, retro, old-fashioned, nostalgic",
            "minimalista": "minimalist style, simple, clean, uncluttered",
            "comic": "comic book style, bold outlines, flat colors, action lines"
        }
        
        return style_prompts.get(style.lower(), style)


# Diccionario de etiquetas EXIF comunes
EXIF_TAGS = {
    0x010F: "Make",
    0x0110: "Model",
    0x0112: "Orientation",
    0x0132: "DateTime",
    0x829A: "ExposureTime",
    0x829D: "FNumber",
    0x8827: "ISOSpeedRatings",
    0x9003: "DateTimeOriginal",
    0x9004: "DateTimeDigitized",
    0x9286: "UserComment",
    0xA002: "PixelXDimension",
    0xA003: "PixelYDimension",
}
