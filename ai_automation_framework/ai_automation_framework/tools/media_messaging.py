"""Image processing, OCR, and messaging platform tools."""

from typing import Dict, Any, List, Optional
import requests
import json
from pathlib import Path
import base64
import io
import os
from urllib.parse import urlparse

# Lazy load PIL - only import when needed
_PIL_LOADED = False
Image = None
ImageEnhance = None
ImageFilter = None


def _ensure_pil():
    """Lazy load PIL modules."""
    global _PIL_LOADED, Image, ImageEnhance, ImageFilter
    if not _PIL_LOADED:
        try:
            from PIL import Image as _Image, ImageEnhance as _ImageEnhance, ImageFilter as _ImageFilter
            Image = _Image
            ImageEnhance = _ImageEnhance
            ImageFilter = _ImageFilter
            _PIL_LOADED = True
        except ImportError:
            raise ImportError("PIL (Pillow) is required for image processing. Install with: pip install Pillow")


class ImageProcessingTool:
    """Tool for image processing and manipulation."""

    @staticmethod
    def _validate_image_path(image_path: str) -> Optional[str]:
        """
        Validate that image file exists.

        Args:
            image_path: Path to image file

        Returns:
            Error message if invalid, None if valid
        """
        if not image_path:
            return "Image path cannot be empty"
        if not os.path.exists(image_path):
            return f"Image file not found: {image_path}"
        if not os.path.isfile(image_path):
            return f"Path is not a file: {image_path}"
        return None

    @staticmethod
    def resize_image(
        input_path: str,
        output_path: str,
        width: int,
        height: int,
        maintain_aspect: bool = True
    ) -> Dict[str, Any]:
        """
        Resize an image.

        Args:
            input_path: Input image path
            output_path: Output image path
            width: Target width
            height: Target height
            maintain_aspect: Maintain aspect ratio

        Returns:
            Result dictionary
        """
        # Validate input file exists
        validation_error = ImageProcessingTool._validate_image_path(input_path)
        if validation_error:
            return {"success": False, "error": validation_error}

        try:
            _ensure_pil()
            img = Image.open(input_path)
            original_size = img.size

            if maintain_aspect:
                img.thumbnail((width, height), Image.Resampling.LANCZOS)
            else:
                img = img.resize((width, height), Image.Resampling.LANCZOS)

            img.save(output_path)

            return {
                "success": True,
                "original_size": original_size,
                "new_size": img.size,
                "output": output_path
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied: {str(e)}"}
        except OSError as e:
            return {"success": False, "error": f"Invalid image file or format: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Image processing error: {str(e)}"}

    @staticmethod
    def convert_format(
        input_path: str,
        output_path: str,
        format: str = "PNG"
    ) -> Dict[str, Any]:
        """Convert image to different format."""
        # Validate input file exists
        validation_error = ImageProcessingTool._validate_image_path(input_path)
        if validation_error:
            return {"success": False, "error": validation_error}

        try:
            _ensure_pil()
            img = Image.open(input_path)
            img.save(output_path, format=format.upper())

            return {
                "success": True,
                "input": input_path,
                "output": output_path,
                "format": format
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied: {str(e)}"}
        except OSError as e:
            return {"success": False, "error": f"Invalid image file or format: {str(e)}"}
        except ValueError as e:
            return {"success": False, "error": f"Invalid format specified: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Image processing error: {str(e)}"}

    @staticmethod
    def apply_filter(
        input_path: str,
        output_path: str,
        filter_type: str = "BLUR"
    ) -> Dict[str, Any]:
        """
        Apply filter to image.

        Args:
            input_path: Input image
            output_path: Output image
            filter_type: Filter type (BLUR, SHARPEN, EDGE_ENHANCE, etc.)

        Returns:
            Result
        """
        # Validate input file exists
        validation_error = ImageProcessingTool._validate_image_path(input_path)
        if validation_error:
            return {"success": False, "error": validation_error}

        try:
            _ensure_pil()
            img = Image.open(input_path)

            filters = {
                "BLUR": ImageFilter.BLUR,
                "SHARPEN": ImageFilter.SHARPEN,
                "EDGE_ENHANCE": ImageFilter.EDGE_ENHANCE,
                "SMOOTH": ImageFilter.SMOOTH,
                "DETAIL": ImageFilter.DETAIL
            }

            if filter_type.upper() in filters:
                filtered = img.filter(filters[filter_type.upper()])
                filtered.save(output_path)

                return {
                    "success": True,
                    "filter": filter_type,
                    "output": output_path
                }
            else:
                return {"success": False, "error": f"Unknown filter: {filter_type}"}

        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied: {str(e)}"}
        except OSError as e:
            return {"success": False, "error": f"Invalid image file or format: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Image processing error: {str(e)}"}

    @staticmethod
    def adjust_brightness(
        input_path: str,
        output_path: str,
        factor: float = 1.5
    ) -> Dict[str, Any]:
        """Adjust image brightness (factor: 0.0 to 2.0)."""
        # Validate input file exists
        validation_error = ImageProcessingTool._validate_image_path(input_path)
        if validation_error:
            return {"success": False, "error": validation_error}

        try:
            _ensure_pil()
            img = Image.open(input_path)
            enhancer = ImageEnhance.Brightness(img)
            enhanced = enhancer.enhance(factor)
            enhanced.save(output_path)

            return {
                "success": True,
                "brightness_factor": factor,
                "output": output_path
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied: {str(e)}"}
        except OSError as e:
            return {"success": False, "error": f"Invalid image file or format: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Image processing error: {str(e)}"}

    @staticmethod
    def create_thumbnail(
        input_path: str,
        output_path: str,
        size: tuple = (128, 128)
    ) -> Dict[str, Any]:
        """Create image thumbnail."""
        # Validate input file exists
        validation_error = ImageProcessingTool._validate_image_path(input_path)
        if validation_error:
            return {"success": False, "error": validation_error}

        try:
            _ensure_pil()
            img = Image.open(input_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path)

            return {
                "success": True,
                "thumbnail_size": img.size,
                "output": output_path
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied: {str(e)}"}
        except OSError as e:
            return {"success": False, "error": f"Invalid image file or format: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Image processing error: {str(e)}"}

    @staticmethod
    def get_image_info(image_path: str) -> Dict[str, Any]:
        """Get image metadata."""
        # Validate input file exists
        validation_error = ImageProcessingTool._validate_image_path(image_path)
        if validation_error:
            return {"success": False, "error": validation_error}

        try:
            _ensure_pil()
            img = Image.open(image_path)

            return {
                "success": True,
                "size": img.size,
                "format": img.format,
                "mode": img.mode,
                "width": img.width,
                "height": img.height
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied: {str(e)}"}
        except OSError as e:
            return {"success": False, "error": f"Invalid image file or format: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Image processing error: {str(e)}"}


class OCRTool:
    """OCR (Optical Character Recognition) tool."""

    @staticmethod
    def extract_text_from_image(image_path: str) -> Dict[str, Any]:
        """
        Extract text from image using OCR.

        Args:
            image_path: Path to image file

        Returns:
            Extracted text
        """
        # Validate input file exists
        if not image_path:
            return {"success": False, "error": "Image path cannot be empty"}
        if not os.path.exists(image_path):
            return {"success": False, "error": f"Image file not found: {image_path}"}
        if not os.path.isfile(image_path):
            return {"success": False, "error": f"Path is not a file: {image_path}"}

        try:
            import pytesseract
            _ensure_pil()

            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)

            return {
                "success": True,
                "text": text.strip(),
                "char_count": len(text),
                "line_count": len(text.splitlines())
            }
        except ImportError:
            return {
                "success": False,
                "error": "pytesseract not installed. Install with: pip install pytesseract"
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied: {str(e)}"}
        except OSError as e:
            return {"success": False, "error": f"Invalid image file or format: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"OCR processing error: {str(e)}"}

    @staticmethod
    def extract_text_from_pdf(pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        """Extract text from PDF page."""
        try:
            from pdf2image import convert_from_path
            import pytesseract

            images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1)

            if images:
                text = pytesseract.image_to_string(images[0])
                return {
                    "success": True,
                    "page": page_num,
                    "text": text.strip()
                }
            else:
                return {"success": False, "error": "Could not convert PDF page"}

        except Exception as e:
            return {"success": False, "error": str(e)}


class SlackTool:
    """Slack integration tool."""

    @staticmethod
    def _validate_webhook_url(url: str) -> Optional[str]:
        """
        Validate webhook URL format.

        Args:
            url: URL to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not url:
            return "Webhook URL cannot be empty"

        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return f"Invalid URL format: {url}"
            if result.scheme not in ['http', 'https']:
                return f"URL must use http or https scheme: {url}"
            return None
        except Exception as e:
            return f"Invalid URL: {str(e)}"

    def __init__(self, webhook_url: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize Slack tool.

        Args:
            webhook_url: Slack webhook URL
            token: Slack bot token
        """
        # Validate webhook URL if provided
        if webhook_url:
            validation_error = self._validate_webhook_url(webhook_url)
            if validation_error:
                raise ValueError(f"Invalid webhook URL: {validation_error}")

        self.webhook_url = webhook_url
        self.token = token

    def send_message(
        self,
        message: str,
        channel: Optional[str] = None,
        username: str = "Bot"
    ) -> Dict[str, Any]:
        """
        Send message to Slack.

        Args:
            message: Message text
            channel: Channel name (if using token)
            username: Bot username

        Returns:
            Result
        """
        try:
            if self.webhook_url:
                payload = {
                    "text": message,
                    "username": username
                }
                response = requests.post(self.webhook_url, json=payload)
                response.raise_for_status()

                return {
                    "success": True,
                    "message": "Message sent via webhook",
                    "status_code": response.status_code
                }
            elif self.token and channel:
                headers = {"Authorization": f"Bearer {self.token}"}
                data = {
                    "channel": channel,
                    "text": message
                }
                response = requests.post(
                    "https://slack.com/api/chat.postMessage",
                    headers=headers,
                    json=data
                )
                response.raise_for_status()

                return {
                    "success": True,
                    "message": "Message sent via API",
                    "response": response.json()
                }
            else:
                return {"success": False, "error": "No webhook URL or token provided"}

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP request failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Slack messaging error: {str(e)}"}

    def upload_file(
        self,
        file_path: str,
        channel: str,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload file to Slack channel."""
        try:
            if not self.token:
                return {"success": False, "error": "Token required for file upload"}

            # Validate file exists
            if not file_path:
                return {"success": False, "error": "File path cannot be empty"}
            if not os.path.exists(file_path):
                return {"success": False, "error": f"File not found: {file_path}"}
            if not os.path.isfile(file_path):
                return {"success": False, "error": f"Path is not a file: {file_path}"}

            headers = {"Authorization": f"Bearer {self.token}"}

            with open(file_path, 'rb') as f:
                files = {'file': f}
                data = {
                    'channels': channel,
                    'title': title or Path(file_path).name
                }

                response = requests.post(
                    "https://slack.com/api/files.upload",
                    headers=headers,
                    files=files,
                    data=data
                )
                response.raise_for_status()

                return {
                    "success": True,
                    "response": response.json()
                }

        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except PermissionError as e:
            return {"success": False, "error": f"Permission denied: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP request failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"File upload error: {str(e)}"}


class DiscordTool:
    """Discord integration tool."""

    @staticmethod
    def _validate_webhook_url(url: str) -> Optional[str]:
        """
        Validate webhook URL format.

        Args:
            url: URL to validate

        Returns:
            Error message if invalid, None if valid
        """
        if not url:
            return "Webhook URL cannot be empty"

        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return f"Invalid URL format: {url}"
            if result.scheme not in ['http', 'https']:
                return f"URL must use http or https scheme: {url}"
            return None
        except Exception as e:
            return f"Invalid URL: {str(e)}"

    def __init__(self, webhook_url: str = None):
        """
        Initialize Discord tool.

        Args:
            webhook_url: Discord webhook URL
        """
        # Validate webhook URL if provided
        if webhook_url:
            validation_error = self._validate_webhook_url(webhook_url)
            if validation_error:
                raise ValueError(f"Invalid webhook URL: {validation_error}")

        self.webhook_url = webhook_url

    def send_message(
        self,
        content: str,
        username: str = "Bot",
        avatar_url: str = None
    ) -> Dict[str, Any]:
        """
        Send message to Discord.

        Args:
            content: Message content
            username: Bot username
            avatar_url: Avatar URL

        Returns:
            Result
        """
        # Validate webhook URL is set
        if not self.webhook_url:
            return {"success": False, "error": "Webhook URL not configured"}

        try:
            payload = {
                "content": content,
                "username": username
            }

            if avatar_url:
                payload["avatar_url"] = avatar_url

            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()

            return {
                "success": True,
                "message": "Message sent to Discord",
                "status_code": response.status_code
            }

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP request failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Discord messaging error: {str(e)}"}

    def send_embed(
        self,
        title: str,
        description: str,
        color: int = 0x00ff00,
        fields: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send embed message to Discord."""
        # Validate webhook URL is set
        if not self.webhook_url:
            return {"success": False, "error": "Webhook URL not configured"}

        try:
            embed = {
                "title": title,
                "description": description,
                "color": color
            }

            if fields:
                embed["fields"] = fields

            payload = {"embeds": [embed]}

            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()

            return {
                "success": True,
                "message": "Embed sent to Discord"
            }

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP request failed: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Discord messaging error: {str(e)}"}


# Tool schemas
MEDIA_MESSAGING_SCHEMAS = {
    "resize_image": {
        "type": "function",
        "function": {
            "name": "resize_image",
            "description": "Resize an image",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {"type": "string"},
                    "output_path": {"type": "string"},
                    "width": {"type": "integer"},
                    "height": {"type": "integer"}
                },
                "required": ["input_path", "output_path", "width", "height"]
            }
        }
    },
    "send_slack_message": {
        "type": "function",
        "function": {
            "name": "send_slack_message",
            "description": "Send message to Slack",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        }
    }
}
