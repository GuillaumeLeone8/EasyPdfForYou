"""Translation functionality using Google Translate and OpenRouter APIs."""

import re
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Union, Dict, Any
import logging

import requests
from googletrans import Translator as GoogleTransTranslator, LANGUAGES

from easypdfforyou.core.config import get_config

logger = logging.getLogger(__name__)


class Translator(ABC):
    """Abstract base class for translators."""
    
    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Translate text from source language to target language.
        
        Args:
            text: Text to translate.
            source_lang: Source language code (e.g., 'en', 'zh-CN').
            target_lang: Target language code.
            
        Returns:
            Translated text.
        """
        pass
    
    @abstractmethod
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """Translate multiple texts.
        
        Args:
            texts: List of texts to translate.
            source_lang: Source language code.
            target_lang: Target language code.
            
        Returns:
            List of translated texts.
        """
        pass
    
    def _split_text(self, text: str, max_length: int = 5000) -> List[str]:
        """Split long text into chunks."""
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by paragraphs first
        paragraphs = text.split("\n")
        
        for para in paragraphs:
            if len(current_chunk) + len(para) + 1 <= max_length:
                current_chunk += para + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


class GoogleTranslator(Translator):
    """Google Translate implementation."""
    
    def __init__(self):
        """Initialize Google Translator."""
        self.translator = GoogleTransTranslator()
        logger.info("Google Translator initialized")
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Translate text using Google Translate."""
        if not text.strip():
            return text
        
        # Handle 'auto' source language
        if source_lang == "auto":
            source_lang = "auto"
        
        try:
            # Split long text
            chunks = self._split_text(text, max_length=4000)
            translated_chunks = []
            
            for chunk in chunks:
                result = self.translator.translate(
                    chunk,
                    src=source_lang if source_lang != "auto" else None,
                    dest=target_lang
                )
                translated_chunks.append(result.text)
                time.sleep(0.5)  # Rate limiting
            
            return "\n".join(translated_chunks)
            
        except Exception as e:
            logger.error(f"Google translation failed: {e}")
            return text  # Return original on failure
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """Translate multiple texts using Google Translate."""
        results = []
        for text in texts:
            translated = self.translate(text, source_lang, target_lang)
            results.append(translated)
            time.sleep(0.5)  # Rate limiting
        return results
    
    def detect_language(self, text: str) -> str:
        """Detect the language of a text."""
        try:
            result = self.translator.detect(text)
            return result.lang
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            return "en"


class OpenRouterTranslator(Translator):
    """OpenRouter API translator using LLM models."""
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    
    # Language names for better prompts
    LANG_NAMES = {
        "zh-CN": "Simplified Chinese",
        "zh-TW": "Traditional Chinese",
        "en": "English",
        "ja": "Japanese",
        "ko": "Korean",
        "fr": "French",
        "de": "German",
        "es": "Spanish",
        "it": "Italian",
        "ru": "Russian",
    }
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize OpenRouter Translator.
        
        Args:
            api_key: OpenRouter API key.
            model: Model to use (default: google/gemini-2.0-flash-001).
        """
        config = get_config()
        
        self.api_key = api_key or config.openrouter_api_key
        self.model = model or config.openrouter_model
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        logger.info(f"OpenRouter Translator initialized with model: {self.model}")
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Translate text using OpenRouter API."""
        if not text.strip():
            return text
        
        source_name = self.LANG_NAMES.get(source_lang, source_lang)
        target_name = self.LANG_NAMES.get(target_lang, target_lang)
        
        prompt = f"""Translate the following text from {source_name} to {target_name}.
Preserve the original formatting and structure. Do not add explanations.

Text to translate:
{text}

Translation:"""
        
        try:
            response = self._call_api(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"OpenRouter translation failed: {e}")
            return text  # Return original on failure
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """Translate multiple texts using OpenRouter API."""
        results = []
        for text in texts:
            translated = self.translate(text, source_lang, target_lang)
            results.append(translated)
            time.sleep(1)  # Rate limiting
        return results
    
    def _call_api(self, prompt: str) -> str:
        """Call OpenRouter API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }
        
        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]


class TranslationService:
    """High-level translation service with fallback support."""
    
    def __init__(
        self,
        primary_translator: Optional[Translator] = None,
        fallback_translator: Optional[Translator] = None
    ):
        """Initialize translation service.
        
        Args:
            primary_translator: Primary translator to use.
            fallback_translator: Fallback translator if primary fails.
        """
        config = get_config()
        
        # Initialize translators
        if primary_translator:
            self.primary = primary_translator
        elif config.openrouter_api_key:
            self.primary = OpenRouterTranslator()
        else:
            self.primary = GoogleTranslator()
        
        self.fallback = fallback_translator or GoogleTranslator()
        
        logger.info(f"Translation service initialized (primary: {type(self.primary).__name__})")
    
    def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "zh-CN"
    ) -> str:
        """Translate text with fallback support."""
        try:
            return self.primary.translate(text, source_lang, target_lang)
        except Exception as e:
            logger.warning(f"Primary translation failed, using fallback: {e}")
            return self.fallback.translate(text, source_lang, target_lang)
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str = "auto",
        target_lang: str = "zh-CN"
    ) -> List[str]:
        """Translate multiple texts with fallback support."""
        try:
            return self.primary.translate_batch(texts, source_lang, target_lang)
        except Exception as e:
            logger.warning(f"Primary batch translation failed, using fallback: {e}")
            return self.fallback.translate_batch(texts, source_lang, target_lang)


# Convenience factory function
def create_translator(provider: str = "auto", **kwargs) -> Translator:
    """Create a translator instance.
    
    Args:
        provider: Translator provider ('google', 'openrouter', or 'auto').
        **kwargs: Additional arguments for the translator.
        
    Returns:
        Translator instance.
    """
    config = get_config()
    
    if provider == "auto":
        if config.openrouter_api_key:
            return OpenRouterTranslator(**kwargs)
        return GoogleTranslator()
    elif provider == "google":
        return GoogleTranslator()
    elif provider == "openrouter":
        return OpenRouterTranslator(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")