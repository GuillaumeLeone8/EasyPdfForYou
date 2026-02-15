"""Translation functionality supporting multiple providers."""

import re
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    """Result from translation."""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float = 0.0
    provider: str = ""
    
    def __repr__(self) -> str:
        return f"TranslationResult({self.source_lang} -> {self.target_lang}, provider={self.provider})"


class Translator(ABC):
    """Abstract base class for translators."""
    
    # Language code mappings to standardize across providers
    LANG_MAPPINGS = {
        "zh-CN": ["zh-CN", "zh", "zh-Hans", "zh_Hans", "chi_sim"],
        "zh-TW": ["zh-TW", "zh-Hant", "zh_Hant", "zh-HK", "chi_tra"],
        "en": ["en", "eng", "english"],
        "ja": ["ja", "jpn", "japanese"],
        "ko": ["ko", "kor", "korean"],
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize translator.
        
        Args:
            api_key: API key for the translation service.
        """
        self.api_key = api_key
    
    @abstractmethod
    def translate(
        self, 
        text: str, 
        target_lang: str, 
        source_lang: str = "auto"
    ) -> TranslationResult:
        """Translate text.
        
        Args:
            text: Text to translate.
            target_lang: Target language code.
            source_lang: Source language code ("auto" for auto-detect).
            
        Returns:
            TranslationResult object.
        """
        pass
    
    @abstractmethod
    def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: str = "auto"
    ) -> List[TranslationResult]:
        """Translate multiple texts.
        
        Args:
            texts: List of texts to translate.
            target_lang: Target language code.
            source_lang: Source language code.
            
        Returns:
            List of TranslationResult objects.
        """
        pass
    
    def _normalize_lang_code(self, lang_code: str) -> str:
        """Normalize language code to standard format.
        
        Args:
            lang_code: Language code to normalize.
            
        Returns:
            Normalized language code.
        """
        lang_code = lang_code.lower().strip()
        
        for standard, variants in self.LANG_MAPPINGS.items():
            if lang_code in [v.lower() for v in variants]:
                return standard
        
        return lang_code
    
    def _split_text(self, text: str, max_length: int = 5000) -> List[str]:
        """Split text into chunks for translation.
        
        Args:
            text: Text to split.
            max_length: Maximum chunk length.
            
        Returns:
            List of text chunks.
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?。！？])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks


class GoogleTranslator(Translator):
    """Google Translate API implementation.
    
    Note: This uses the free googletrans library, not the official paid API.
    For production use with high volume, consider using the official Google Cloud Translation API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Google Translator.
        
        Args:
            api_key: Google Cloud API key (optional for free version).
        """
        super().__init__(api_key)
        self._translator = None
        self._init_translator()
    
    def _init_translator(self) -> None:
        """Initialize the googletrans translator."""
        try:
            from googletrans import Translator as GoogleTrans
            self._translator = GoogleTrans()
            logger.info("Google Translator initialized")
        except ImportError:
            logger.warning("googletrans not installed, trying alternative")
            self._translator = None
    
    def translate(
        self, 
        text: str, 
        target_lang: str, 
        source_lang: str = "auto"
    ) -> TranslationResult:
        """Translate text using Google Translate.
        
        Args:
            text: Text to translate.
            target_lang: Target language code.
            source_lang: Source language code.
            
        Returns:
            TranslationResult object.
        """
        if not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                provider="google"
            )
        
        target_lang = self._normalize_lang_code(target_lang)
        src_lang = None if source_lang == "auto" else self._normalize_lang_code(source_lang)
        
        try:
            if self._translator:
                result = self._translator.translate(
                    text,
                    dest=target_lang,
                    src=src_lang
                )
                
                return TranslationResult(
                    original_text=text,
                    translated_text=result.text,
                    source_lang=result.src if result.src else source_lang,
                    target_lang=target_lang,
                    confidence=getattr(result, 'confidence', 0.0),
                    provider="google"
                )
            else:
                # Fallback: return original with warning
                logger.warning("Google Translator not available")
                return TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    provider="google_fallback"
                )
                
        except Exception as e:
            logger.error(f"Google Translate error: {e}")
            raise
    
    def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: str = "auto"
    ) -> List[TranslationResult]:
        """Translate multiple texts.
        
        Args:
            texts: List of texts to translate.
            target_lang: Target language code.
            source_lang: Source language code.
            
        Returns:
            List of TranslationResult objects.
        """
        results = []
        for text in texts:
            try:
                result = self.translate(text, target_lang, source_lang)
                results.append(result)
                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                logger.error(f"Batch translation error: {e}")
                results.append(TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    provider="google_error"
                ))
        
        return results


class OpenRouterTranslator(Translator):
    """OpenRouter API implementation for translation using LLMs."""
    
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_MODEL = "google/gemini-2.0-flash-001"
    
    # Model-specific rate limits
    RATE_LIMIT_DELAY = 1.0
    
    def __init__(
        self, 
        api_key: str,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        max_tokens: int = 4096
    ):
        """Initialize OpenRouter Translator.
        
        Args:
            api_key: OpenRouter API key.
            model: Model to use for translation.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens per request.
        """
        super().__init__(api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        })
    
    def _create_prompt(
        self, 
        text: str, 
        target_lang: str, 
        source_lang: str = "auto"
    ) -> str:
        """Create translation prompt.
        
        Args:
            text: Text to translate.
            target_lang: Target language.
            source_lang: Source language.
            
        Returns:
            Formatted prompt string.
        """
        lang_names = {
            "zh-CN": "Simplified Chinese",
            "zh-TW": "Traditional Chinese",
            "en": "English",
            "ja": "Japanese",
            "ko": "Korean",
        }
        
        target_name = lang_names.get(target_lang, target_lang)
        
        if source_lang == "auto":
            prompt = f"""Translate the following text to {target_name}. 
Preserve formatting, special characters, and structure.
Only return the translation, no explanations:

{text}"""
        else:
            source_name = lang_names.get(source_lang, source_lang)
            prompt = f"""Translate the following text from {source_name} to {target_name}.
Preserve formatting, special characters, and structure.
Only return the translation, no explanations:

{text}"""
        
        return prompt
    
    def translate(
        self, 
        text: str, 
        target_lang: str, 
        source_lang: str = "auto"
    ) -> TranslationResult:
        """Translate text using OpenRouter.
        
        Args:
            text: Text to translate.
            target_lang: Target language code.
            source_lang: Source language code.
            
        Returns:
            TranslationResult object.
        """
        if not text.strip():
            return TranslationResult(
                original_text=text,
                translated_text="",
                source_lang=source_lang,
                target_lang=target_lang,
                provider="openrouter"
            )
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        target_lang = self._normalize_lang_code(target_lang)
        
        # Split long texts
        chunks = self._split_text(text, max_length=3000)
        translated_chunks = []
        
        for chunk in chunks:
            prompt = self._create_prompt(chunk, target_lang, source_lang)
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional translator. Provide accurate, natural translations while preserving formatting and structure."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            try:
                response = self._session.post(
                    self.API_URL,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                
                data = response.json()
                translated_text = data["choices"][0]["message"]["content"].strip()
                translated_chunks.append(translated_text)
                
                # Rate limiting
                time.sleep(self.RATE_LIMIT_DELAY)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"OpenRouter API error: {e}")
                raise
            except (KeyError, IndexError) as e:
                logger.error(f"Invalid response format: {e}")
                raise
        
        full_translation = " ".join(translated_chunks)
        
        return TranslationResult(
            original_text=text,
            translated_text=full_translation,
            source_lang=source_lang,
            target_lang=target_lang,
            confidence=0.9,  # LLMs don't provide confidence scores
            provider=f"openrouter:{self.model}"
        )
    
    def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: str = "auto"
    ) -> List[TranslationResult]:
        """Translate multiple texts.
        
        Args:
            texts: List of texts to translate.
            target_lang: Target language code.
            source_lang: Source language code.
            
        Returns:
            List of TranslationResult objects.
        """
        results = []
        for text in texts:
            try:
                result = self.translate(text, target_lang, source_lang)
                results.append(result)
            except Exception as e:
                logger.error(f"Batch translation error: {e}")
                results.append(TranslationResult(
                    original_text=text,
                    translated_text=text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    provider=f"openrouter:{self.model}_error"
                ))
        
        return results
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models from OpenRouter.
        
        Returns:
            List of model information dictionaries.
        """
        try:
            response = self._session.get(
                "https://openrouter.ai/api/v1/models",
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to get models: {e}")
            return []


def create_translator(
    provider: str = "google",
    api_key: Optional[str] = None,
    **kwargs
) -> Translator:
    """Factory function to create translator instances.
    
    Args:
        provider: Translator provider ('google' or 'openrouter').
        api_key: API key for the provider.
        **kwargs: Additional arguments for the translator.
        
    Returns:
        Translator instance.
        
    Raises:
        ValueError: If provider is not supported.
    """
    if provider.lower() == "google":
        return GoogleTranslator(api_key)
    elif provider.lower() == "openrouter":
        if not api_key:
            raise ValueError("OpenRouter requires an API key")
        return OpenRouterTranslator(api_key, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")
