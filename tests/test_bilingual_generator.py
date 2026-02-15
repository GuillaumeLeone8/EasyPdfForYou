"""Tests for bilingual generator module."""

import pytest
from pathlib import Path
import fitz

from easypdfforyou.core.bilingual_generator import BilingualGenerator


@pytest.fixture
def sample_pages():
    """Sample pages for testing."""
    return [
        "Hello World\nThis is page 1",
        "Second page\nMore content here"
    ]


@pytest.fixture
def translated_pages():
    """Translated sample pages."""
    return [
        "你好世界\n这是第1页",
        "第二页\n更多内容在这里"
    ]


class TestBilingualGenerator:
    """Test cases for BilingualGenerator."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = BilingualGenerator(dpi=200)
        assert generator.dpi == 200
    
    def test_generate_side_by_side(self, tmp_path, sample_pages, translated_pages):
        """Test side-by-side generation."""
        generator = BilingualGenerator()
        output_path = tmp_path / "output.pdf"
        
        result = generator.generate_side_by_side(
            sample_pages,
            translated_pages,
            output_path
        )
        
        assert result.exists()
        assert result.stat().st_size > 0
    
    def test_generate_line_by_line(self, tmp_path, sample_pages, translated_pages):
        """Test line-by-line generation."""
        generator = BilingualGenerator()
        output_path = tmp_path / "output.pdf"
        
        result = generator.generate_line_by_line(
            sample_pages,
            translated_pages,
            output_path
        )
        
        assert result.exists()
    
    def test_generate_with_invalid_layout(self, tmp_path, sample_pages, translated_pages):
        """Test generation with invalid layout."""
        generator = BilingualGenerator()
        output_path = tmp_path / "output.pdf"
        
        with pytest.raises(ValueError):
            generator.generate(
                sample_pages,
                translated_pages,
                output_path,
                layout="invalid"
            )
    
    def test_generate_overlay_without_original(self, tmp_path, translated_pages):
        """Test overlay generation without original PDF."""
        generator = BilingualGenerator()
        output_path = tmp_path / "output.pdf"
        
        with pytest.raises(ValueError):
            generator.generate(
                [],
                translated_pages,
                output_path,
                layout="overlay"
            )
    
    def test_generate_overlay(self, tmp_path, sample_pages, translated_pages):
        """Test overlay generation."""
        # Create a sample PDF
        original_pdf = tmp_path / "original.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Original text", fontsize=12)
        doc.save(original_pdf)
        doc.close()
        
        generator = BilingualGenerator()
        output_path = tmp_path / "output.pdf"
        
        result = generator.generate_overlay_pdf(
            original_pdf,
            translated_pages,
            output_path
        )
        
        assert result.exists()