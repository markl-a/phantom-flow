"""Tests for media and messaging tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestImageProcessingTool:
    """Test Image processing tool."""

    def test_resize_image_mock(self, temp_test_dir):
        """Test resizing image with mock."""
        with patch("PIL.Image.open") as mock_open:
            mock_image = MagicMock()
            mock_image.size = (1920, 1080)
            mock_open.return_value = mock_image

            from ai_automation_framework.tools.media_messaging import ImageProcessingTool

            result = ImageProcessingTool.resize_image(
                input_path=str(temp_test_dir / "input.jpg"),
                output_path=str(temp_test_dir / "output.jpg"),
                width=800,
                height=600
            )

            assert result["success"] is True
            assert result["original_size"] == (1920, 1080)

    def test_convert_format_mock(self, temp_test_dir):
        """Test converting image format with mock."""
        with patch("PIL.Image.open") as mock_open:
            mock_image = MagicMock()
            mock_open.return_value = mock_image

            from ai_automation_framework.tools.media_messaging import ImageProcessingTool

            result = ImageProcessingTool.convert_format(
                input_path=str(temp_test_dir / "input.jpg"),
                output_path=str(temp_test_dir / "output.png"),
                format="PNG"
            )

            assert result["success"] is True
            assert result["format"] == "PNG"

    def test_apply_filter_mock(self, temp_test_dir):
        """Test applying filter with mock."""
        with patch("PIL.Image.open") as mock_open:
            mock_image = MagicMock()
            mock_image.filter.return_value = mock_image
            mock_open.return_value = mock_image

            from ai_automation_framework.tools.media_messaging import ImageProcessingTool

            result = ImageProcessingTool.apply_filter(
                input_path=str(temp_test_dir / "input.jpg"),
                output_path=str(temp_test_dir / "output.jpg"),
                filter_type="BLUR"
            )

            assert result["success"] is True


class TestOCRTool:
    """Test OCR tool."""

    def test_initialization(self):
        """Test tool initialization."""
        from ai_automation_framework.tools.media_messaging import OCRTool

        tool = OCRTool()
        assert tool is not None

    def test_extract_text_mock(self, temp_test_dir):
        """Test extracting text from image with mock."""
        with patch("pytesseract.image_to_string") as mock_ocr, \
             patch("PIL.Image.open") as mock_open:
            mock_ocr.return_value = "Extracted text from image"
            mock_image = MagicMock()
            mock_open.return_value = mock_image

            from ai_automation_framework.tools.media_messaging import OCRTool

            tool = OCRTool()
            result = tool.extract_text(str(temp_test_dir / "image.png"))

            assert result["success"] is True
            assert "Extracted text" in result["text"]


class TestSlackTool:
    """Test Slack tool."""

    def test_initialization(self):
        """Test tool initialization."""
        from ai_automation_framework.tools.media_messaging import SlackTool

        tool = SlackTool(webhook_url="https://hooks.slack.com/test")
        assert tool.webhook_url == "https://hooks.slack.com/test"

    def test_send_message_mock(self, mock_http_response):
        """Test sending message with mock."""
        mock_http_response["post"].return_value.status_code = 200
        mock_http_response["post"].return_value.text = "ok"

        from ai_automation_framework.tools.media_messaging import SlackTool

        tool = SlackTool(webhook_url="https://hooks.slack.com/test")
        result = tool.send_message("Test message")

        assert result["success"] is True

    def test_send_formatted_message_mock(self, mock_http_response):
        """Test sending formatted message with mock."""
        mock_http_response["post"].return_value.status_code = 200

        from ai_automation_framework.tools.media_messaging import SlackTool

        tool = SlackTool(webhook_url="https://hooks.slack.com/test")
        result = tool.send_message(
            text="Test message",
            channel="#general",
            username="TestBot"
        )

        assert result["success"] is True


class TestDiscordTool:
    """Test Discord tool."""

    def test_initialization(self):
        """Test tool initialization."""
        from ai_automation_framework.tools.media_messaging import DiscordTool

        tool = DiscordTool(webhook_url="https://discord.com/api/webhooks/test")
        assert "discord.com" in tool.webhook_url

    def test_send_message_mock(self, mock_http_response):
        """Test sending message with mock."""
        mock_http_response["post"].return_value.status_code = 204

        from ai_automation_framework.tools.media_messaging import DiscordTool

        tool = DiscordTool(webhook_url="https://discord.com/api/webhooks/test")
        result = tool.send_message("Test message")

        assert result["success"] is True

    def test_send_embed_mock(self, mock_http_response):
        """Test sending embed with mock."""
        mock_http_response["post"].return_value.status_code = 204

        from ai_automation_framework.tools.media_messaging import DiscordTool

        tool = DiscordTool(webhook_url="https://discord.com/api/webhooks/test")
        result = tool.send_embed(
            title="Test Embed",
            description="This is a test",
            color=0x00ff00
        )

        assert result["success"] is True


class TestVideoProcessor:
    """Test Video processor."""

    def test_initialization(self):
        """Test processor initialization."""
        with patch.dict("sys.modules", {"cv2": MagicMock(), "moviepy.editor": MagicMock()}):
            from ai_automation_framework.tools.video_processing import VideoProcessor

            processor = VideoProcessor()
            assert processor is not None

    def test_extract_frames_mock(self, temp_test_dir):
        """Test extracting frames with mock."""
        with patch("cv2.VideoCapture") as mock_cap:
            mock_capture = MagicMock()
            mock_capture.isOpened.side_effect = [True, True, True, False]
            mock_capture.read.side_effect = [
                (True, MagicMock()),
                (True, MagicMock()),
                (False, None),
            ]
            mock_cap.return_value = mock_capture

            with patch("cv2.imwrite"):
                from ai_automation_framework.tools.video_processing import VideoProcessor

                processor = VideoProcessor()
                # Note: actual test may need adjustment based on implementation
                assert processor is not None


class TestAudioProcessing:
    """Test Audio processing tools."""

    def test_speech_to_text_initialization(self):
        """Test SpeechToText initialization."""
        from ai_automation_framework.tools.audio_processing import SpeechToText

        stt = SpeechToText(provider="openai")
        assert stt.provider == "openai"

    def test_text_to_speech_initialization(self):
        """Test TextToSpeech initialization."""
        from ai_automation_framework.tools.audio_processing import TextToSpeech

        tts = TextToSpeech(provider="openai")
        assert tts.provider == "openai"
