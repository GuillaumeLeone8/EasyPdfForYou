"""PDF text extraction functionality."""

import io
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import logging

import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """Represents a block of text with position information."""
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_num: int
    font_size: float = 12.0
    font_name: str = ""
    is_bold: bool = False
    
    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        """Return bounding box as tuple."""
        return (self.x0, self.y0, self.x1, self.y1)
    
    @property
    def center_x(self) -> float:
        """Return center x coordinate."""
        return (self.x0 + self.x1) / 2
    
    @property
    def center_y(self) -> float:
        """Return center y coordinate."""
        return (self.y0 + self.y1) / 2
    
    @property
    def width(self) -> float:
        """Return block width."""
        return self.x1 - self.x0
    
    @property
    def height(self) -> float:
        """Return block height."""
        return self.y1 - self.y0


@dataclass
class PageContent:
    """Represents content extracted from a single page."""
    page_num: int
    width: float
    height: float
    text_blocks: List[TextBlock]
    images: List[Dict[str, Any]]
    rotation: int = 0
    
    @property
    def full_text(self) -> str:
        """Get all text from page as single string."""
        return "\n".join(block.text for block in self.text_blocks)
    
    @property
    def has_text(self) -> bool:
        """Check if page has any text."""
        return len(self.text_blocks) > 0


class PdfExtractor:
    """Extract text and images from PDF files while preserving layout."""
    
    def __init__(self, dpi: int = 300):
        """Initialize PDF extractor.
        
        Args:
            dpi: DPI for image extraction from PDF pages.
        """
        self.dpi = dpi
        self._doc: Optional[fitz.Document] = None
        self._file_path: Optional[Path] = None
    
    def open(self, file_path: Union[str, Path]) -> "PdfExtractor":
        """Open a PDF file.
        
        Args:
            file_path: Path to PDF file.
            
        Returns:
            Self for method chaining.
            
        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file is not a valid PDF.
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        try:
            self._doc = fitz.open(file_path)
            self._file_path = file_path
            logger.info(f"Opened PDF: {file_path} ({len(self._doc)} pages)")
        except Exception as e:
            raise ValueError(f"Failed to open PDF: {e}")
        
        return self
    
    def close(self) -> None:
        """Close the PDF document."""
        if self._doc:
            self._doc.close()
            self._doc = None
            self._file_path = None
            logger.info("Closed PDF document")
    
    def __enter__(self) -> "PdfExtractor":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
    
    @property
    def page_count(self) -> int:
        """Get number of pages in the PDF."""
        if self._doc is None:
            raise RuntimeError("No PDF document open")
        return len(self._doc)
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Get PDF metadata."""
        if self._doc is None:
            raise RuntimeError("No PDF document open")
        return dict(self._doc.metadata)
    
    def is_scanned(self, sample_pages: int = 3) -> bool:
        """Check if PDF appears to be scanned (image-based).
        
        Args:
            sample_pages: Number of pages to sample.
            
        Returns:
            True if PDF appears to be scanned.
        """
        if self._doc is None:
            raise RuntimeError("No PDF document open")
        
        pages_to_check = min(sample_pages, self.page_count)
        text_counts = []
        image_counts = []
        
        for page_num in range(pages_to_check):
            page = self._doc[page_num]
            text = page.get_text()
            text_counts.append(len(text.strip()))
            image_counts.append(len(page.get_images()))
        
        # If average text is very low but images exist, likely scanned
        avg_text = sum(text_counts) / len(text_counts)
        avg_images = sum(image_counts) / len(image_counts)
        
        return avg_text < 100 and avg_images > 0
    
    def extract_text(
        self, 
        page_numbers: Optional[List[int]] = None,
        preserve_layout: bool = True
    ) -> str:
        """Extract text from PDF.
        
        Args:
            page_numbers: Specific pages to extract (None = all pages).
            preserve_layout: Whether to preserve layout formatting.
            
        Returns:
            Extracted text.
        """
        if self._doc is None:
            raise RuntimeError("No PDF document open")
        
        if page_numbers is None:
            page_numbers = list(range(self.page_count))
        
        texts = []
        for page_num in page_numbers:
            if page_num < 0 or page_num >= self.page_count:
                logger.warning(f"Page {page_num} out of range, skipping")
                continue
            
            page = self._doc[page_num]
            
            if preserve_layout:
                text = page.get_text("blocks")
                # Sort by vertical position, then horizontal
                text = sorted(text, key=lambda b: (b[1], b[0]))
                page_text = "\n".join(block[4] for block in text if len(block) > 4)
            else:
                page_text = page.get_text()
            
            texts.append(page_text)
        
        return "\n\n".join(texts)
    
    def extract_page_content(self, page_number: int) -> PageContent:
        """Extract detailed content from a specific page.
        
        Args:
            page_number: Page number (0-indexed).
            
        Returns:
            PageContent object with text blocks and images.
        """
        if self._doc is None:
            raise RuntimeError("No PDF document open")
        
        if page_number < 0 or page_number >= self.page_count:
            raise ValueError(f"Page number {page_number} out of range")
        
        page = self._doc[page_number]
        
        # Extract text blocks
        text_blocks = []
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" not in block:
                continue
            
            block_text_parts = []
            font_size = 12.0
            font_name = ""
            is_bold = False
            
            for line in block["lines"]:
                for span in line.get("spans", []):
                    block_text_parts.append(span.get("text", ""))
                    font_size = max(font_size, span.get("size", 12.0))
                    font_name = span.get("font", font_name)
                    flags = span.get("flags", 0)
                    is_bold = is_bold or bool(flags & 2 ** 4)  # Check bold flag
            
            if block_text_parts:
                text_blocks.append(TextBlock(
                    text="".join(block_text_parts).strip(),
                    x0=block["bbox"][0],
                    y0=block["bbox"][1],
                    x1=block["bbox"][2],
                    y1=block["bbox"][3],
                    page_num=page_number,
                    font_size=font_size,
                    font_name=font_name,
                    is_bold=is_bold,
                ))
        
        # Sort by position (top to bottom, left to right)
        text_blocks.sort(key=lambda b: (b.y0, b.x0))
        
        # Extract image info
        images = []
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = self._doc.extract_image(xref)
            images.append({
                "index": img_index,
                "xref": xref,
                "ext": base_image["ext"],
                "width": base_image.get("width", 0),
                "height": base_image.get("height", 0),
            })
        
        return PageContent(
            page_num=page_number,
            width=page.rect.width,
            height=page.rect.height,
            text_blocks=text_blocks,
            images=images,
            rotation=page.rotation,
        )
    
    def extract_all_pages(self) -> List[PageContent]:
        """Extract content from all pages.
        
        Returns:
            List of PageContent objects.
        """
        return [self.extract_page_content(i) for i in range(self.page_count)]
    
    def extract_images(self, page_number: Optional[int] = None) -> List[Image.Image]:
        """Extract images from PDF.
        
        Args:
            page_number: Specific page (None = all pages).
            
        Returns:
            List of PIL Image objects.
        """
        if self._doc is None:
            raise RuntimeError("No PDF document open")
        
        images = []
        pages_to_check = [page_number] if page_number is not None else range(self.page_count)
        
        for page_num in pages_to_check:
            if page_num is None:
                continue
            page = self._doc[page_num]
            
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = self._doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                try:
                    image = Image.open(io.BytesIO(image_bytes))
                    images.append(image)
                except Exception as e:
                    logger.warning(f"Failed to extract image from page {page_num}: {e}")
        
        return images
    
    def render_page_to_image(
        self, 
        page_number: int, 
        dpi: Optional[int] = None
    ) -> Image.Image:
        """Render a PDF page to an image.
        
        Args:
            page_number: Page number to render.
            dpi: DPI for rendering (uses instance default if None).
            
        Returns:
            PIL Image object.
        """
        if self._doc is None:
            raise RuntimeError("No PDF document open")
        
        if page_number < 0 or page_number >= self.page_count:
            raise ValueError(f"Page number {page_number} out of range")
        
        page = self._doc[page_number]
        mat = fitz.Matrix((dpi or self.dpi) / 72, (dpi or self.dpi) / 72)
        pix = page.get_pixmap(matrix=mat)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img
    
    def render_all_pages(self, dpi: Optional[int] = None) -> List[Image.Image]:
        """Render all pages to images.
        
        Args:
            dpi: DPI for rendering.
            
        Returns:
            List of PIL Image objects.
        """
        return [
            self.render_page_to_image(i, dpi) 
            for i in range(self.page_count)
        ]
    
    def get_fonts(self) -> List[Dict[str, Any]]:
        """Get list of fonts used in the PDF.
        
        Returns:
            List of font information dictionaries.
        """
        if self._doc is None:
            raise RuntimeError("No PDF document open")
        
        fonts = []
        for page_num in range(self.page_count):
            page = self._doc[page_num]
            for font in page.get_fonts():
                fonts.append({
                    "page": page_num,
                    "xref": font[0],
                    "name": font[3],
                    "type": font[1],
                })
        
        return fonts
    
    def search_text(self, pattern: str, case_sensitive: bool = False) -> List[Dict[str, Any]]:
        """Search for text pattern in PDF.
        
        Args:
            pattern: Regular expression pattern to search.
            case_sensitive: Whether search is case sensitive.
            
        Returns:
            List of match dictionaries with page, text, and position.
        """
        if self._doc is None:
            raise RuntimeError("No PDF document open")
        
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        
        matches = []
        for page_num in range(self.page_count):
            page = self._doc[page_num]
            text = page.get_text()
            
            for match in regex.finditer(text):
                matches.append({
                    "page": page_num,
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                })
        
        return matches
