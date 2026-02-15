"""
EasyPdfForYou - A comprehensive PDF translation tool.

This package provides tools for extracting text from PDFs, translating content,
and generating bilingual PDF documents.
"""

__version__ = "0.1.0"
__author__ = "EasyPdfForYou Team"
__email__ = "support@easypdfforyou.com"

from .core.pdf_extractor import PdfExtractor
from .core.translator import Translator, GoogleTranslator, OpenRouterTranslator
from .core.ocr_engine import OcrEngine
from .core.bilingual_generator import BilingualGenerator
from .core.config import Config

__all__ = [
    "PdfExtractor",
    "Translator",
    "GoogleTranslator",
    "OpenRouterTranslator",
    "OcrEngine",
    "BilingualGenerator",
    "Config",
]
