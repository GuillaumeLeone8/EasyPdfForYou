"""Tests for OCR engine module."""

import pytest
from unittest.mock import Mock, patch
from PIL import Image
import numpy as np

from easypdfforyou.core.ocr_engine import OcrEngine


class TestOcrEngine:
    """Test cases for OcrEngine."""
    
    @patch('easypdfforyou.core.ocr_engine.pytesseract')
    def test_initialization(self, mock_pytesseract):
        """Test OCR engine initialization."""
        mock_pytesseract.get_tesseract_version.return_value = "4.1.1"
        
        engine = OcrEngine()
        assert engine is not None
    
    @patch('easypdfforyou.core.ocr_engine.pytesseract')
    def test_recognize(self, mock_pytesseract):
        """Test text recognition."""
        mock_pytesseract.image_to_string.return_value = "Hello World"
        mock_pytesseract.get_tesseract_version.return_value = "4.1.1"
        
        engine = OcrEngine()
        
        # Create a simple test image
        img = Image.new('RGB', (100, 30), color='white')
        
        result = engine.recognize(img, lang="eng", preprocess=False)
        
        assert result == "Hello World"
    
    @patch('easypdfforyou.core.ocr_engine.pytesseract')
    def test_recognize_with_numpy_array(self, mock_pytesseract):
        """Test recognition from numpy array."""
        mock_pytesseract.image_to_string.return_value = "Test"
        mock_pytesseract.get_tesseract_version.return_value = "4.1.1"
        
        engine = OcrEngine()
        
        # Create numpy array image
        arr = np.ones((30, 100, 3), dtype=np.uint8) * 255
        
        result = engine.recognize(arr, lang="eng", preprocess=False)
        
        assert result == "Test"
    
    @patch('easypdfforyou.core.ocr_engine.pytesseract')
    def test_recognize_with_boxes(self, mock_pytesseract):
        """Test recognition with bounding boxes."""
        mock_pytesseract.image_to_data.return_value = {
            "text": ["Hello", "World"],
            "conf": [95, 90],
            "left": [10, 50],
            "top": [10, 10],
            "width": [30, 40],
            "height": [20, 20],
        }
        mock_pytesseract.get_tesseract_version.return_value = "4.1.1"
        
        engine = OcrEngine()
        img = Image.new('RGB', (100, 30), color='white')
        
        result = engine.recognize_with_boxes(img, lang="eng", preprocess=False)
        
        assert len(result) == 2
        assert result[0]["text"] == "Hello"
    
    @patch('easypdfforyou.core.ocr_engine.pytesseract')
    def test_is_available(self, mock_pytesseract):
        """Test availability check."""
        mock_pytesseract.get_tesseract_version.return_value = "4.1.1"
        
        engine = OcrEngine()
        assert engine.is_available() is True
    
    @patch('easypdfforyou.core.ocr_engine.pytesseract')
    def test_is_available_when_not_configured(self, mock_pytesseract):
        """Test availability when tesseract is not configured."""
        mock_pytesseract.get_tesseract_version.side_effect = Exception("Not found")
        
        engine = OcrEngine()
        assert engine.is_available() is False
    
    def test_language_mapping(self):
        """Test language code mapping."""
        engine = OcrEngine()
        
        assert engine._map_language("zh-CN") == "chi_sim"
        assert engine._map_language("zh-TW") == "chi_tra"
        assert engine._map_language("en") == "eng"
        assert engine._map_language("unknown") == "unknown"