"""PDF extraction functionality using PyMuPDF."""

import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import logging

import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a block of text in a PDF."""
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page_num: int
    block_num: int
    font_size: float = 0.0
    font_name: str = ""
    is_bold: bool = False
    is_italic: bool = False


@dataclass
class ExtractedPage:
    """Represents an extracted page from a PDF."""
    page_num: int
    text: str
    text_blocks: List[TextBlock]
    images: List[Image.Image]
    width: float
    height: float


class PdfExtractor:
    """Extract text and images from PDF documents."""
    
    def __init__(self, dpi: int = 300):
        """Initialize the PDF extractor.
        
        Args:
            dpi: DPI for image rendering.
        """
        self.dpi = dpi
    
    def extract_text(
        self,
        pdf_path: Union[str, Path],
        max_pages: int = 0,
        preserve_layout: bool = True
    ) -> List[ExtractedPage]:
        """Extract text from a PDF document.
        
        Args:
            pdf_path: Path to the PDF file.
            max_pages: Maximum number of pages to extract (0 for all).
            preserve_layout: Whether to preserve text layout.
            
        Returns:
            List of extracted pages.
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Extracting text from {pdf_path}")
        
        pages = []
        
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)
            pages_to_extract = min(max_pages, total_pages) if max_pages > 0 else total_pages
            
            for page_num in range(pages_to_extract):
                page = doc[page_num]
                extracted_page = self._extract_page(page, page_num)
                pages.append(extracted_page)
                
                logger.debug(f"Extracted page {page_num + 1}/{pages_to_extract}")
        
        logger.info(f"Successfully extracted {len(pages)} pages")
        return pages
    
    def _extract_page(self, page: fitz.Page, page_num: int) -> ExtractedPage:
        """Extract content from a single page."""
        # Get page dimensions
        rect = page.rect
        width, height = rect.width, rect.height
        
        # Extract text with layout preservation
        text = page.get_text("text")
        
        # Extract text blocks with metadata
        text_blocks = []
        blocks = page.get_text("blocks")
        
        for block_num, block in enumerate(blocks):
            if len(block) >= 7:
                x0, y0, x1, y1, text_content, block_no, block_type = block[:7]
                if block_type == 0:  # Text block
                    text_blocks.append(TextBlock(
                        text=text_content,
                        bbox=(x0, y0, x1, y1),
                        page_num=page_num,
                        block_num=block_num
                    ))
        
        # Sort blocks by vertical position (top to bottom)
        text_blocks.sort(key=lambda b: b.bbox[1])
        
        # Extract images
        images = self._extract_images(page)
        
        return ExtractedPage(
            page_num=page_num,
            text=text,
            text_blocks=text_blocks,
            images=images,
            width=width,
            height=height
        )
    
    def _extract_images(self, page: fitz.Page) -> List[Image.Image]:
        """Extract images from a page."""
        images = []
        
        image_list = page.get_images()
        
        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]
            base_image = page.parent.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            try:
                image = Image.open(io.BytesIO(image_bytes))
                images.append(image)
            except Exception as e:
                logger.warning(f"Failed to extract image {img_index}: {e}")
        
        return images
    
    def render_page_to_image(
        self,
        pdf_path: Union[str, Path],
        page_num: int = 0,
        zoom: float = 2.0
    ) -> Image.Image:
        """Render a PDF page to an image.
        
        Args:
            pdf_path: Path to the PDF file.
            page_num: Page number to render (0-indexed).
            zoom: Zoom factor for rendering.
            
        Returns:
            Rendered image.
        """
        pdf_path = Path(pdf_path)
        
        with fitz.open(pdf_path) as doc:
            if page_num >= len(doc):
                raise ValueError(f"Page {page_num} does not exist (document has {len(doc)} pages)")
            
            page = doc[page_num]
            
            # Set zoom matrix
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, dpi=self.dpi)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            return image
    
    def get_document_info(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """Get information about a PDF document.
        
        Args:
            pdf_path: Path to the PDF file.
            
        Returns:
            Dictionary with document information.
        """
        pdf_path = Path(pdf_path)
        
        with fitz.open(pdf_path) as doc:
            metadata = doc.metadata
            
            return {
                "page_count": len(doc),
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", ""),
                "file_size": pdf_path.stat().st_size,
            }
    
    def is_scanned_pdf(self, pdf_path: Union[str, Path], sample_pages: int = 3) -> bool:
        """Check if a PDF is likely a scanned document.
        
        Args:
            pdf_path: Path to the PDF file.
            sample_pages: Number of pages to sample.
            
        Returns:
            True if the PDF appears to be scanned.
        """
        pdf_path = Path(pdf_path)
        
        with fitz.open(pdf_path) as doc:
            pages_to_check = min(sample_pages, len(doc))
            
            for page_num in range(pages_to_check):
                page = doc[page_num]
                text = page.get_text().strip()
                
                # If page has very little text but has images, likely scanned
                if len(text) < 50 and page.get_images():
                    return True
        
        return False