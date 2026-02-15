"""Tests for translator module."""

import pytest
from unittest.mock import Mock, patch

from easypdfforyou.core.translator import (
    GoogleTranslator,
    OpenRouterTranslator,
    TranslationService,
    create_translator
)


class TestGoogleTranslator:
    """Test cases for GoogleTranslator."""
    
    @patch('easypdfforyou.core.translator.GoogleTransTranslator')
    def test_translate(self, mock_translator_class):
        """Test basic translation."""
        mock_translator = Mock()
        mock_translator.translate.return_value = Mock(text="你好")
        mock_translator_class.return_value = mock_translator
        
        translator = GoogleTranslator()
        result = translator.translate("Hello", "en", "zh-CN")
        
        assert result == "你好"
    
    def test_translate_empty_text(self):
        """Test translation of empty text."""
        translator = GoogleTranslator()
        result = translator.translate("", "en", "zh-CN")
        
        assert result == ""
    
    @patch('easypdfforyou.core.translator.GoogleTransTranslator')
    def test_detect_language(self, mock_translator_class):
        """Test language detection."""
        mock_translator = Mock()
        mock_translator.detect.return_value = Mock(lang="en")
        mock_translator_class.return_value = mock_translator
        
        translator = GoogleTranslator()
        result = translator.detect_language("Hello")
        
        assert result == "en"


class TestOpenRouterTranslator:
    """Test cases for OpenRouterTranslator."""
    
    def test_initialization_without_api_key(self):
        """Test initialization without API key."""
        with pytest.raises(ValueError):
            OpenRouterTranslator(api_key=None)
    
    @patch('easypdfforyou.core.translator.requests.post')
    def test_translate(self, mock_post):
        """Test translation with API."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "你好"}}]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        translator = OpenRouterTranslator(api_key="test_key")
        result = translator.translate("Hello", "en", "zh-CN")
        
        assert result == "你好"


class TestTranslationService:
    """Test cases for TranslationService."""
    
    @patch('easypdfforyou.core.translator.GoogleTransTranslator')
    def test_translate_with_fallback(self, mock_translator_class):
        """Test translation with fallback."""
        mock_translator = Mock()
        mock_translator.translate.return_value = Mock(text="你好")
        mock_translator_class.return_value = mock_translator
        
        service = TranslationService()
        result = service.translate("Hello", "en", "zh-CN")
        
        assert result == "你好"


class TestCreateTranslator:
    """Test cases for create_translator factory function."""
    
    def test_create_google_translator(self):
        """Test creating Google translator."""
        translator = create_translator("google")
        assert isinstance(translator, GoogleTranslator)
    
    def test_create_unknown_provider(self):
        """Test creating translator with unknown provider."""
        with pytest.raises(ValueError):
            create_translator("unknown")