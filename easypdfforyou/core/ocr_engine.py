"""OCR engine for scanned PDFs using Tesseract."""

import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import logging

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract

logger = logging.getLogger(__name__)


@dataclass
class OcrResult:
    """Result from OCR processing."""
    text: str
    confidence: float
    bounding_box: Optional[Tuple[int, int, int, int]] = None
    page_num: int = 0
    
    def __repr__(self) -> str:
        return f"OcrResult(text='{self.text[:50]}...', confidence={self.confidence:.1f}%)"


class OcrEngine:
    """OCR engine using Tesseract for text recognition in images."""
    
    # Language code mappings
    LANG_CODES = {
        "zh-CN": "chi_sim",
        "zh-TW": "chi_tra",
        "en": "eng",
        "ja": "jpn",
        "ko": "kor",
        "auto": "eng+chi_sim+chi_tra+jpn+kor",
    }
    
    def __init__(
        self, 
        tesseract_cmd: Optional[str] = None,
        lang: str = "eng+chi_sim+chi_tra+jpn+kor"
    ):
        """Initialize OCR engine.
        
        Args:
            tesseract_cmd: Path to tesseract executable.
            lang: Default language(s) for OCR.
        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        self.lang = lang
        self._check_tesseract()
    
    def _check_tesseract(self) -> None:
        """Check if Tesseract is installed and accessible."""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract version: {version}")
        except Exception as e:
            logger.error(f"Tesseract not found: {e}")
            raise RuntimeError(
                "Tesseract OCR is not installed or not in PATH. "
                "Please install Tesseract: https://github.com/tesseract-ocr/tesseract"
            )
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results.
        
        Args:
            image: PIL Image to preprocess.
            
        Returns:
            Preprocessed image.
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(2.0)
        
        # Apply mild denoising
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        return image
    
    def recognize(
        self, 
        image: Union[Image.Image, np.ndarray, str, Path],
        lang: Optional[str] = None,
        preprocess: bool = True
    ) -> OcrResult:
        """Recognize text in an image.
        
        Args:
            image: Image to process (PIL Image, numpy array, or path).
            lang: Language code for OCR.
            preprocess: Whether to apply image preprocessing.
            
        Returns:
            OcrResult with recognized text and confidence.
        """
        # Load image
        if isinstance(image, (str, Path)):
            image = Image.open(image)
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Preprocess if requested
        if preprocess:
            image = self._preprocess_image(image)
        
        # Determine language
        ocr_lang = self._map_language(lang) if lang else self.lang
        
        # Perform OCR
        try:
            # Get detailed data including confidence
            data = pytesseract.image_to_data(
                image, 
                lang=ocr_lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and calculate average confidence
            texts = []
            confidences = []
            
            for i, text in enumerate(data['text']):
                if text.strip():
                    texts.append(text)
                    confidences.append(float(data['conf'][i]))
            
            full_text = ' '.join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return OcrResult(
                text=full_text,
                confidence=avg_confidence,
                page_num=0
            )
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return OcrResult(text="", confidence=0.0)
    
    def recognize_with_boxes(
        self,
        image: Union[Image.Image, np.ndarray, str, Path],
        lang: Optional[str] = None,
        preprocess: bool = True
    ) -> List[OcrResult]:
        """Recognize text with bounding box information.
        
        Args:
            image: Image to process.
            lang: Language code.
            preprocess: Whether to preprocess image.
            
        Returns:
            List of OcrResult objects with bounding boxes.
        """
        # Load image
        if isinstance(image, (str, Path)):
            image = Image.open(image)
        elif isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Preprocess if requested
        if preprocess:
            image = self._preprocess_image(image)
        
        # Determine language
        ocr_lang = self._map_language(lang) if lang else self.lang
        
        results = []
        
        try:
            data = pytesseract.image_to_data(
                image,
                lang=ocr_lang,
                output_type=pytesseract.Output.DICT
            )
            
            for i, text in enumerate(data['text']):
                if text.strip() and int(data['conf'][i]) > 0:
                    results.append(OcrResult(
                        text=text,
                        confidence=float(data['conf'][i]),
                        bounding_box=(
                            data['left'][i],
                            data['top'][i],
                            data['left'][i] + data['width'][i],
                            data['top'][i] + data['height'][i]
                        ),
                        page_num=0
                    ))
            
        except Exception as e:
            logger.error(f"OCR with boxes failed: {e}")
        
        return results
    
    def recognize_pdf_page(
        self,
        pdf_image: Image.Image,
        page_num: int = 0,
        lang: Optional[str] = None
    ) -> str:
        """Recognize text from a PDF page image.
        
        Args:
            pdf_image: Rendered PDF page as PIL Image.
            page_num: Page number for reference.
            lang: Language code.
            
        Returns:
            Recognized text.
        """
        result = self.recognize(pdf_image, lang=lang, preprocess=True)
        result.page_num = page_num
        return result.text
    
    def _map_language(self, lang_code: str) -> str:
        """Map language code to Tesseract language code.
        
        Args:
            lang_code: ISO or internal language code.
            
        Returns:
            Tesseract language code.
        """
        return self.LANG_CODES.get(lang_code, lang_code)
    
    def get_supported_languages(self) -> List[str]:
        """Get list of installed Tesseract languages.
        
        Returns:
            List of language codes.
        """
        try:
            langs = pytesseract.get_languages()
            return langs
        except Exception as e:
            logger.error(f"Failed to get languages: {e}")
            return []
    
    def is_language_installed(self, lang_code: str) -> bool:
        """Check if a language is installed.
        
        Args:
            lang_code: Language code to check.
            
        Returns:
            True if language is installed.
        """
        tesseract_lang = self._map_language(lang_code)
        installed = self.get_supported_languages()
        return tesseract_lang in installed
    
    def process_scanned_pdf(
        self,
        page_images: List[Image.Image],
        lang: Optional[str] = None
    ) -> List[str]:
        """Process a scanned PDF (list of page images).
        
        Args:
            page_images: List of PIL Images, one per page.
            lang: Language code.
            
        Returns:
            List of recognized text for each page.
        """
        results = []
        
        for page_num, image in enumerate(page_images):
            logger.info(f"Processing page {page_num + 1}/{len(page_images)}")
            text = self.recognize_pdf_page(image, page_num, lang)
            results.append(text)
        
        return results
