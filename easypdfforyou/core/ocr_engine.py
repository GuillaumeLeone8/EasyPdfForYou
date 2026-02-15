"""OCR functionality using Tesseract."""

import io
from pathlib import Path
from typing import List, Optional, Union, Tuple
import logging

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

from easypdfforyou.core.config import get_config

logger = logging.getLogger(__name__)


class OcrEngine:
    """Optical Character Recognition engine using Tesseract."""
    
    # Language code mappings
    LANG_MAP = {
        "zh-CN": "chi_sim",  # Simplified Chinese
        "zh-TW": "chi_tra",  # Traditional Chinese
        "en": "eng",         # English
        "ja": "jpn",         # Japanese
        "ko": "kor",         # Korean
        "fr": "fra",         # French
        "de": "deu",         # German
        "es": "spa",         # Spanish
        "it": "ita",         # Italian
        "ru": "rus",         # Russian
        "pt": "por",         # Portuguese
    }
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        """Initialize the OCR engine.
        
        Args:
            tesseract_cmd: Path to tesseract executable.
        """
        config = get_config()
        
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        elif config.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = config.tesseract_cmd
        
        # Test tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            logger.warning(f"Tesseract not properly configured: {e}")
    
    def recognize(
        self,
        image: Union[Image.Image, np.ndarray, Path, str],
        lang: str = "eng",
        preprocess: bool = True
    ) -> str:
        """Recognize text from an image.
        
        Args:
            image: Input image (PIL Image, numpy array, or file path).
            lang: Language code for OCR.
            preprocess: Whether to apply image preprocessing.
            
        Returns:
            Recognized text.
        """
        # Convert to PIL Image
        pil_image = self._to_pil_image(image)
        
        # Preprocess if enabled
        if preprocess:
            pil_image = self._preprocess_image(pil_image)
        
        # Map language code
        tesseract_lang = self._map_language(lang)
        
        try:
            text = pytesseract.image_to_string(pil_image, lang=tesseract_lang)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    
    def recognize_with_boxes(
        self,
        image: Union[Image.Image, np.ndarray, Path, str],
        lang: str = "eng",
        preprocess: bool = True
    ) -> List[dict]:
        """Recognize text with bounding boxes.
        
        Args:
            image: Input image.
            lang: Language code.
            preprocess: Whether to apply preprocessing.
            
        Returns:
            List of dictionaries with text and bounding boxes.
        """
        pil_image = self._to_pil_image(image)
        
        if preprocess:
            pil_image = self._preprocess_image(pil_image)
        
        tesseract_lang = self._map_language(lang)
        
        try:
            data = pytesseract.image_to_data(
                pil_image,
                lang=tesseract_lang,
                output_type=pytesseract.Output.DICT
            )
            
            results = []
            n_boxes = len(data["text"])
            
            for i in range(n_boxes):
                if int(data["conf"][i]) > 30:  # Confidence threshold
                    results.append({
                        "text": data["text"][i],
                        "conf": data["conf"][i],
                        "left": data["left"][i],
                        "top": data["top"][i],
                        "width": data["width"][i],
                        "height": data["height"][i],
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"OCR with boxes failed: {e}")
            return []
    
    def _to_pil_image(self, image: Union[Image.Image, np.ndarray, Path, str]) -> Image.Image:
        """Convert various image formats to PIL Image."""
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        elif isinstance(image, np.ndarray):
            return Image.fromarray(image).convert("RGB")
        elif isinstance(image, (str, Path)):
            return Image.open(image).convert("RGB")
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Apply preprocessing to improve OCR accuracy."""
        # Convert to grayscale
        if image.mode != "L":
            image = image.convert("L")
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Apply mild denoising
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # Binarization (adaptive threshold would be better but this is simpler)
        image = image.point(lambda x: 0 if x < 128 else 255, "1")
        image = image.convert("L")
        
        return image
    
    def _map_language(self, lang: str) -> str:
        """Map language code to Tesseract language code."""
        return self.LANG_MAP.get(lang, lang)
    
    def is_available(self) -> bool:
        """Check if Tesseract is properly configured."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported Tesseract languages."""
        try:
            langs = pytesseract.get_languages()
            return langs
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return ["eng"]