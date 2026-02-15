"""Bilingual PDF generation functionality."""

import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import logging

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER

logger = logging.getLogger(__name__)


@dataclass
class BilingualPage:
    """Represents a bilingual page with original and translated content."""
    page_num: int
    original_text: str
    translated_text: str
    original_image: Optional[Image.Image] = None
    layout: str = "side_by_side"  # side_by_side, line_by_line, overlay


class BilingualGenerator:
    """Generate bilingual PDF documents."""
    
    LAYOUTS = ["side_by_side", "line_by_line", "overlay"]
    
    def __init__(
        self,
        font_path: Optional[str] = None,
        dpi: int = 300
    ):
        """Initialize bilingual generator.
        
        Args:
            font_path: Path to font file for non-Latin characters.
            dpi: DPI for image rendering.
        """
        self.font_path = font_path
        self.dpi = dpi
        self._register_fonts()
    
    def _register_fonts(self) -> None:
        """Register fonts for PDF generation."""
        try:
            # Try to register a font that supports CJK characters
            if self.font_path and Path(self.font_path).exists():
                pdfmetrics.registerFont(TTFont('CustomFont', self.font_path))
                self.default_font = 'CustomFont'
            else:
                # Use standard Helvetica as fallback
                self.default_font = 'Helvetica'
        except Exception as e:
            logger.warning(f"Font registration failed: {e}")
            self.default_font = 'Helvetica'
    
    def generate_side_by_side(
        self,
        original_pages: List[str],
        translated_pages: List[str],
        output_path: Union[str, Path],
        page_size: Tuple[float, float] = A4
    ) -> Path:
        """Generate side-by-side bilingual PDF.
        
        Args:
            original_pages: List of original text pages.
            translated_pages: List of translated text pages.
            output_path: Output PDF path.
            page_size: Page size tuple (width, height).
            
        Returns:
            Path to generated PDF.
        """
        output_path = Path(output_path)
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=page_size,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'BilingualTitle',
            parent=styles['Heading1'],
            fontName=self.default_font,
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        original_style = ParagraphStyle(
            'OriginalText',
            parent=styles['Normal'],
            fontName=self.default_font,
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=12
        )
        
        translated_style = ParagraphStyle(
            'TranslatedText',
            parent=styles['Normal'],
            fontName=self.default_font,
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=20,
            textColor='blue'
        )
        
        story = []
        
        for i, (orig, trans) in enumerate(zip(original_pages, translated_pages)):
            # Page title
            story.append(Paragraph(f"Page {i + 1}", title_style))
            story.append(Spacer(1, 20))
            
            # Original text
            story.append(Paragraph("<b>Original:</b>", original_style))
            story.append(Paragraph(orig.replace('\n', '<br/>'), original_style))
            story.append(Spacer(1, 12))
            
            # Translated text
            story.append(Paragraph("<b>Translation:</b>", translated_style))
            story.append(Paragraph(trans.replace('\n', '<br/>'), translated_style))
            
            # Page break except for last page
            if i < len(original_pages) - 1:
                story.append(PageBreak())
        
        doc.build(story)
        logger.info(f"Generated side-by-side PDF: {output_path}")
        
        return output_path
    
    def generate_line_by_line(
        self,
        original_pages: List[str],
        translated_pages: List[str],
        output_path: Union[str, Path],
        page_size: Tuple[float, float] = A4
    ) -> Path:
        """Generate line-by-line bilingual PDF (interleaved).
        
        Args:
            original_pages: List of original text pages.
            translated_pages: List of translated text pages.
            output_path: Output PDF path.
            page_size: Page size tuple.
            
        Returns:
            Path to generated PDF.
        """
        output_path = Path(output_path)
        
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=page_size,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        styles = getSampleStyleSheet()
        
        original_style = ParagraphStyle(
            'OriginalLine',
            parent=styles['Normal'],
            fontName=self.default_font,
            fontSize=10,
            spaceAfter=6
        )
        
        translated_style = ParagraphStyle(
            'TranslatedLine',
            parent=styles['Normal'],
            fontName=self.default_font,
            fontSize=10,
            spaceAfter=12,
            textColor='blue'
        )
        
        story = []
        
        for i, (orig, trans) in enumerate(zip(original_pages, translated_pages)):
            story.append(Paragraph(f"<b>Page {i + 1}</b>", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Split into lines and interleave
            orig_lines = orig.split('\n')
            trans_lines = trans.split('\n')
            
            for j in range(max(len(orig_lines), len(trans_lines))):
                if j < len(orig_lines) and orig_lines[j].strip():
                    story.append(Paragraph(orig_lines[j], original_style))
                if j < len(trans_lines) and trans_lines[j].strip():
                    story.append(Paragraph(trans_lines[j], translated_style))
            
            if i < len(original_pages) - 1:
                story.append(PageBreak())
        
        doc.build(story)
        logger.info(f"Generated line-by-line PDF: {output_path}")
        
        return output_path
    
    def generate_overlay_pdf(
        self,
        original_pdf_path: Union[str, Path],
        translated_pages: List[str],
        output_path: Union[str, Path]
    ) -> Path:
        """Generate overlay bilingual PDF (translation overlay on original).
        
        Args:
            original_pdf_path: Path to original PDF.
            translated_pages: List of translated text pages.
            output_path: Output PDF path.
            
        Returns:
            Path to generated PDF.
        """
        output_path = Path(output_path)
        original_pdf_path = Path(original_pdf_path)
        
        # Open original PDF
        doc = fitz.open(original_pdf_path)
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            if page_num < len(translated_pages):
                # Add translation as overlay text
                # Position at bottom of page
                rect = page.rect
                text = translated_pages[page_num]
                
                # Create a semi-transparent annotation or text box
                # This is a simplified version - overlay text at bottom
                text_rect = fitz.Rect(
                    50, rect.height - 150, rect.width - 50, rect.height - 50
                )
                
                page.insert_textbox(
                    text_rect,
                    text,
                    fontsize=8,
                    color=(0, 0, 1),  # Blue text
                    align=fitz.TEXT_ALIGN_LEFT
                )
        
        doc.save(output_path)
        doc.close()
        
        logger.info(f"Generated overlay PDF: {output_path}")
        return output_path
    
    def generate(
        self,
        original_pages: List[str],
        translated_pages: List[str],
        output_path: Union[str, Path],
        layout: str = "side_by_side",
        original_pdf_path: Optional[Union[str, Path]] = None
    ) -> Path:
        """Generate bilingual PDF with specified layout.
        
        Args:
            original_pages: List of original text pages.
            translated_pages: List of translated text pages.
            output_path: Output PDF path.
            layout: Layout type (side_by_side, line_by_line, overlay).
            original_pdf_path: Original PDF path (required for overlay layout).
            
        Returns:
            Path to generated PDF.
            
        Raises:
            ValueError: If layout is not supported.
        """
        if layout not in self.LAYOUTS:
            raise ValueError(f"Unsupported layout: {layout}. Use: {self.LAYOUTS}")
        
        if layout == "side_by_side":
            return self.generate_side_by_side(original_pages, translated_pages, output_path)
        elif layout == "line_by_line":
            return self.generate_line_by_line(original_pages, translated_pages, output_path)
        elif layout == "overlay":
            if not original_pdf_path:
                raise ValueError("original_pdf_path is required for overlay layout")
            return self.generate_overlay_pdf(original_pdf_path, translated_pages, output_path)
        
        return Path(output_path)