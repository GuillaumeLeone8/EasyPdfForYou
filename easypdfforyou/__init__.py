"""EasyPdfForYou - A lightweight PDF document processing and translation tool.

This package provides functionality for:
- PDF text extraction
- OCR for scanned PDFs
- Document translation (Google Translate + OpenRouter API)
- Bilingual PDF generation
- CLI and Web interfaces
"""

__version__ = "0.1.0"
__author__ = "Guillaume Leone"
__email__ = "GuillaumeLeone8@gmail.com"

from easypdfforyou.core.pdf_extractor import PdfExtractor
from easypdfforyou.core.ocr_engine import OcrEngine
from easypdfforyou.core.translator import Translator, GoogleTranslator, OpenRouterTranslator
from easypdfforyou.core.bilingual_generator import BilingualGenerator

__all__ = [
    "PdfExtractor",
    "OcrEngine", 
    "Translator",
    "GoogleTranslator",
    "OpenRouterTranslator",
    "BilingualGenerator",
]