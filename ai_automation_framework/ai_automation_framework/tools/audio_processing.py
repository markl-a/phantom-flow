"""
語音處理工具
Audio Processing Tools

提供語音轉文字 (STT)、文字轉語音 (TTS) 等功能。
"""

import os
from typing import Optional, List
from pathlib import Path

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from google.cloud import speech_v1, texttospeech
    HAS_GOOGLE_CLOUD = True
except ImportError:
    HAS_GOOGLE_CLOUD = False

try:
    import azure.cognitiveservices.speech as speechsdk
    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False


class SpeechToText:
    """語音轉文字"""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        初始化語音轉文字服務

        Args:
            provider: 服務提供商 (openai, google, azure)
            api_key: API 密鑰
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")

        if provider == "openai" and HAS_OPENAI:
            if self.api_key is None:
                raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
            self.client = OpenAI(api_key=self.api_key)
        elif provider == "azure" and HAS_AZURE:
            # Azure Speech 初始化
            speech_key = os.getenv("AZURE_SPEECH_KEY")
            if speech_key is None:
                raise ValueError("Azure Speech key is required. Set AZURE_SPEECH_KEY environment variable.")
            service_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
            self.speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=service_region
            )

    def transcribe(
        self,
        audio_file: str,
        language: str = "zh-TW",
        **kwargs
    ) -> str:
        """
        將音頻文件轉換為文字

        Args:
            audio_file: 音頻文件路徑
            language: 語言代碼
            **kwargs: 其他參數

        Returns:
            轉錄的文字
        """
        if self.provider == "openai" and HAS_OPENAI:
            return self._transcribe_openai(audio_file, language, **kwargs)
        elif self.provider == "google" and HAS_GOOGLE_CLOUD:
            return self._transcribe_google(audio_file, language, **kwargs)
        elif self.provider == "azure" and HAS_AZURE:
            return self._transcribe_azure(audio_file, language, **kwargs)
        else:
            raise ValueError(f"不支持的提供商或未安裝依賴: {self.provider}")

    def _transcribe_openai(self, audio_file: str, language: str, **kwargs) -> str:
        """使用 OpenAI Whisper 轉錄"""
        with open(audio_file, "rb") as f:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language=language,
                **kwargs
            )
        return transcript.text

    def _transcribe_google(self, audio_file: str, language: str, **kwargs) -> str:
        """使用 Google Cloud Speech-to-Text 轉錄"""
        client = speech_v1.SpeechClient()

        with open(audio_file, "rb") as f:
            content = f.read()

        audio = speech_v1.RecognitionAudio(content=content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code=language,
            **kwargs
        )

        response = client.recognize(config=config, audio=audio)

        transcripts = [result.alternatives[0].transcript for result in response.results]
        return " ".join(transcripts)

    def _transcribe_azure(self, audio_file: str, language: str, **kwargs) -> str:
        """使用 Azure Speech Services 轉錄"""
        audio_config = speechsdk.audio.AudioConfig(filename=audio_file)
        self.speech_config.speech_recognition_language = language

        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        else:
            raise Exception(f"語音識別失敗: {result.reason}")


class TextToSpeech:
    """文字轉語音"""

    def __init__(self, provider: str = "openai", api_key: Optional[str] = None):
        """
        初始化文字轉語音服務

        Args:
            provider: 服務提供商 (openai, google, azure)
            api_key: API 密鑰
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")

        if provider == "openai" and HAS_OPENAI:
            if self.api_key is None:
                raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
            self.client = OpenAI(api_key=self.api_key)
        elif provider == "azure" and HAS_AZURE:
            speech_key = os.getenv("AZURE_SPEECH_KEY")
            if speech_key is None:
                raise ValueError("Azure Speech key is required. Set AZURE_SPEECH_KEY environment variable.")
            service_region = os.getenv("AZURE_SPEECH_REGION", "eastus")
            self.speech_config = speechsdk.SpeechConfig(
                subscription=speech_key,
                region=service_region
            )

    def synthesize(
        self,
        text: str,
        output_file: str,
        voice: str = "alloy",
        language: str = "zh-TW",
        **kwargs
    ) -> str:
        """
        將文字轉換為語音

        Args:
            text: 要轉換的文字
            output_file: 輸出音頻文件路徑
            voice: 語音類型
            language: 語言代碼
            **kwargs: 其他參數

        Returns:
            輸出文件路徑
        """
        if self.provider == "openai" and HAS_OPENAI:
            return self._synthesize_openai(text, output_file, voice, **kwargs)
        elif self.provider == "google" and HAS_GOOGLE_CLOUD:
            return self._synthesize_google(text, output_file, voice, language, **kwargs)
        elif self.provider == "azure" and HAS_AZURE:
            return self._synthesize_azure(text, output_file, voice, language, **kwargs)
        else:
            raise ValueError(f"不支持的提供商或未安裝依賴: {self.provider}")

    def _synthesize_openai(self, text: str, output_file: str, voice: str, **kwargs) -> str:
        """使用 OpenAI TTS"""
        response = self.client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            **kwargs
        )

        with open(output_file, "wb") as f:
            f.write(response.content)

        return output_file

    def _synthesize_google(
        self,
        text: str,
        output_file: str,
        voice: str,
        language: str,
        **kwargs
    ) -> str:
        """使用 Google Cloud Text-to-Speech"""
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice_params = texttospeech.VoiceSelectionParams(
            language_code=language,
            name=voice if voice else None,
            **kwargs
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config
        )

        with open(output_file, "wb") as f:
            f.write(response.audio_content)

        return output_file

    def _synthesize_azure(
        self,
        text: str,
        output_file: str,
        voice: str,
        language: str,
        **kwargs
    ) -> str:
        """使用 Azure Speech Services"""
        self.speech_config.speech_synthesis_voice_name = voice
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_file)

        speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )

        result = speech_synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return output_file
        else:
            raise Exception(f"語音合成失敗: {result.reason}")


__all__ = ['SpeechToText', 'TextToSpeech']
