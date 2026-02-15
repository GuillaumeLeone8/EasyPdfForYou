"""Command-line interface for EasyPdfForYou."""

import sys
from pathlib import Path
from typing import Optional

import click

from easypdfforyou import __version__
from easypdfforyou.core.config import get_config, set_config, Config
from easypdfforyou.core.pdf_extractor import PdfExtractor
from easypdfforyou.core.ocr_engine import OcrEngine
from easypdfforyou.core.translator import create_translator, TranslationService
from easypdfforyou.core.bilingual_generator import BilingualGenerator


@click.group()
@click.version_option(version=__version__, prog_name="epdf")
@click.option("--config", type=click.Path(), help="Path to configuration file.")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool) -> None:
    """EasyPdfForYou - PDF translation tool.
    
    A lightweight tool for extracting, translating, and processing PDF documents.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    
    if config:
        cfg = Config.from_file(Path(config))
        set_config(cfg)
    
    if verbose:
        click.echo("Verbose mode enabled.")


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output file path.")
@click.option("--max-pages", "-p", type=int, default=0, help="Maximum pages to extract (0 for all).")
@click.option("--format", "fmt", type=click.Choice(["text", "json", "blocks"]), default="text", help="Output format.")
@click.pass_context
def extract(ctx: click.Context, pdf_path: str, output: Optional[str], max_pages: int, fmt: str) -> None:
    """Extract text from a PDF file."""
    if ctx.obj.get("verbose"):
        click.echo(f"Extracting from: {pdf_path}")
    
    extractor = PdfExtractor()
    pages = extractor.extract_text(pdf_path, max_pages=max_pages)
    
    results = []
    for page in pages:
        if fmt == "text":
            results.append(f"=== Page {page.page_num + 1} ===\n{page.text}")
        elif fmt == "json":
            import json
            results.append(json.dumps({
                "page_num": page.page_num,
                "text": page.text,
                "width": page.width,
                "height": page.height,
            }))
        elif fmt == "blocks":
            for block in page.text_blocks:
                results.append(f"[{block.bbox}] {block.text}")
    
    output_text = "\n\n".join(results)
    
    if output:
        Path(output).write_text(output_text, encoding="utf-8")
        click.echo(f"Extracted text saved to: {output}")
    else:
        click.echo(output_text)


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--source", "-s", default="auto", help="Source language code (e.g., en, zh-CN).")
@click.option("--target", "-t", default="zh-CN", help="Target language code.")
@click.option("--output", "-o", type=click.Path(), help="Output PDF path.")
@click.option("--provider", type=click.Choice(["google", "openrouter", "auto"]), default="auto", help="Translation provider.")
@click.option("--layout", type=click.Choice(["side_by_side", "line_by_line", "overlay"]), default="side_by_side", help="Bilingual layout.")
@click.option("--ocr", is_flag=True, help="Use OCR for scanned PDFs.")
@click.pass_context
def translate(
    ctx: click.Context,
    pdf_path: str,
    source: str,
    target: str,
    output: Optional[str],
    provider: str,
    layout: str,
    ocr: bool
) -> None:
    """Translate a PDF file."""
    if ctx.obj.get("verbose"):
        click.echo(f"Translating {pdf_path} from {source} to {target}")
    
    pdf_path = Path(pdf_path)
    
    # Set default output path
    if not output:
        output = pdf_path.parent / f"{pdf_path.stem}_{target}{pdf_path.suffix}"
    
    # Extract text
    extractor = PdfExtractor()
    
    if ocr or extractor.is_scanned_pdf(pdf_path):
        click.echo("Using OCR for scanned PDF...")
        ocr_engine = OcrEngine()
        
        pages_text = []
        for i, page in enumerate(extractor.extract_text(pdf_path)):
            img = extractor.render_page_to_image(pdf_path, page_num=i)
            text = ocr_engine.recognize(img, lang=source)
            pages_text.append(text)
    else:
        pages_text = [page.text for page in extractor.extract_text(pdf_path)]
    
    # Translate
    click.echo(f"Translating using {provider}...")
    translator = TranslationService()
    translated_pages = translator.translate_batch(pages_text, source, target)
    
    # Generate bilingual PDF
    click.echo("Generating bilingual PDF...")
    generator = BilingualGenerator()
    generator.generate(
        pages_text,
        translated_pages,
        output,
        layout=layout,
        original_pdf_path=pdf_path
    )
    
    click.echo(f"Bilingual PDF saved to: {output}")


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--page", "-p", type=int, default=0, help="Page number to OCR (0-indexed).")
@click.option("--lang", "-l", default="eng", help="Language code for OCR.")
@click.option("--output", "-o", type=click.Path(), help="Output text file.")
@click.pass_context
def ocr(ctx: click.Context, pdf_path: str, page: int, lang: str, output: Optional[str]) -> None:
    """Perform OCR on a PDF page."""
    if ctx.obj.get("verbose"):
        click.echo(f"Performing OCR on page {page} of {pdf_path}")
    
    extractor = PdfExtractor()
    img = extractor.render_page_to_image(pdf_path, page_num=page)
    
    ocr_engine = OcrEngine()
    text = ocr_engine.recognize(img, lang=lang)
    
    if output:
        Path(output).write_text(text, encoding="utf-8")
        click.echo(f"OCR result saved to: {output}")
    else:
        click.echo(text)


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to.")
@click.option("--port", "-p", type=int, default=5000, help="Port to listen on.")
@click.option("--debug", is_flag=True, help="Enable debug mode.")
def web(host: str, port: int, debug: bool) -> None:
    """Start the web UI server."""
    click.echo(f"Starting web server on http://{host}:{port}")
    
    from easypdfforyou.web.app import create_app
    app = create_app()
    app.run(host=host, port=port, debug=debug)


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
def info(pdf_path: str) -> None:
    """Show PDF document information."""
    extractor = PdfExtractor()
    info = extractor.get_document_info(pdf_path)
    
    click.echo(f"File: {pdf_path}")
    click.echo(f"Pages: {info['page_count']}")
    click.echo(f"Title: {info['title'] or 'N/A'}")
    click.echo(f"Author: {info['author'] or 'N/A'}")
    click.echo(f"Creator: {info['creator'] or 'N/A'}")
    click.echo(f"Producer: {info['producer'] or 'N/A'}")
    click.echo(f"File Size: {info['file_size']:,} bytes")


if __name__ == "__main__":
    cli()