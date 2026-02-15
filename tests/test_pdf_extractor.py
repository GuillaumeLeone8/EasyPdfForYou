"""Tests for PDF extractor module."""

import io
from pathlib import Path

import pytest
from PIL import Image
import fitz

from easypdfforyou.core.pdf_extractor import PdfExtractor, TextBlock, ExtractedPage


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF for testing."""
    pdf_path = tmp_path / "test.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    
    # Add some text
    text = "Hello, World!\nThis is a test PDF."
    page.insert_text((72, 72), text, fontsize=12)
    
    doc.save(pdf_path)
    doc.close()
    
    return pdf_path


class TestPdfExtractor:
    """Test cases for PdfExtractor."""
    
    def test_initialization(self):
        """Test extractor initialization."""
        extractor = PdfExtractor(dpi=200)
        assert extractor.dpi == 200
    
    def test_extract_text(self, sample_pdf):
        """Test text extraction."""
        extractor = PdfExtractor()
        pages = extractor.extract_text(sample_pdf)
        
        assert len(pages) == 1
        assert isinstance(pages[0], ExtractedPage)
        assert "Hello" in pages[0].text
        assert pages[0].page_num == 0
    
    def test_extract_nonexistent_file(self):
        """Test extraction from non-existent file."""
        extractor = PdfExtractor()
        
        with pytest.raises(FileNotFoundError):
            extractor.extract_text("/nonexistent/file.pdf")
    
    def test_get_document_info(self, sample_pdf):
        """Test document info extraction."""
        extractor = PdfExtractor()
        info = extractor.get_document_info(sample_pdf)
        
        assert info["page_count"] == 1
        assert "file_size" in info
    
    def test_is_scanned_pdf(self, sample_pdf):
        """Test scanned PDF detection."""
        extractor = PdfExtractor()
        is_scanned = extractor.is_scanned_pdf(sample_pdf)
        
        # Sample has text, so should not be scanned
        assert is_scanned is False