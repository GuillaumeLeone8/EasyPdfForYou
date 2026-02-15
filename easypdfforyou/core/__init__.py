"""Core modules for EasyPdfForYou."""

from easypdfforyou.core.config import Config, get_config, set_config
from easypdfforyou.core.pdf_extractor import PdfExtractor, ExtractedPage, TextBlock
from easypdfforyou.core.ocr_engine import OcrEngine
from easypdfforyou.core.translator import (
    Translator,
    GoogleTranslator,
    OpenRouterTranslator,
    TranslationService,
    create_translator
)
from easypdfforyou.core.bilingual_generator import BilingualGenerator, BilingualPage

__all__ = [
    "Config",
    "get_config",
    "set_config",
    "PdfExtractor",
    "ExtractedPage",
    "TextBlock",
    "OcrEngine",
    "Translator",
    "GoogleTranslator",
    "OpenRouterTranslator",
    "TranslationService",
    "create_translator",
    "BilingualGenerator",
    "BilingualPage",
]