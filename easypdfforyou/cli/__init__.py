"""Command line interface for EasyPdfForYou."""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, List

from ..core.config import Config
from ..core.pdf_extractor import PdfExtractor
from ..core.ocr_engine import OcrEngine
from ..core.translator import create_translator
from ..core.bilingual_generator import BilingualGenerator


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration.
    
    Args:
        level: Logging level.
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def extract_command(args: argparse.Namespace) -> int:
    """Handle extract command.
    
    Args:
        args: Command arguments.
        
    Returns:
        Exit code.
    """
    extractor = PdfExtractor(dpi=args.dpi)
    
    try:
        extractor.open(args.input)
        
        if args.pages:
            page_numbers = [int(p) - 1 for p in args.pages.split(',')]
        else:
            page_numbers = None
        
        text = extractor.extract_text(
            page_numbers=page_numbers,
            preserve_layout=args.preserve_layout
        )
        
        if args.output:
            Path(args.output).write_text(text, encoding='utf-8')
            print(f"Text extracted to: {args.output}")
        else:
            print(text)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        extractor.close()


def translate_command(args: argparse.Namespace) -> int:
    """Handle translate command.
    
    Args:
        args: Command arguments.
        
    Returns:
        Exit code.
    """
    setup_logging(args.log_level)
    config = Config(args.config)
    
    # Initialize extractor
    extractor = PdfExtractor(dpi=config.get('pdf_dpi', 300))
    
    try:
        extractor.open(args.input)
        
        # Determine if OCR is needed
        use_ocr = args.ocr or (args.auto_ocr and extractor.is_scanned())
        
        if use_ocr:
            print("Using OCR for scanned document...")
            ocr = OcrEngine(
                tesseract_cmd=config.get('tesseract_cmd'),
                lang=config.get('tesseract_lang')
            )
            page_images = extractor.render_all_pages()
            texts = ocr.process_scanned_pdf(page_images, args.source_lang)
        else:
            print("Extracting text from PDF...")
            page_contents = extractor.extract_all_pages()
            texts = [page.full_text for page in page_contents]
        
        print(f"Extracted {len(texts)} pages of text")
        
        # Initialize translator
        api_key = args.api_key or config.get(f'{args.provider}_api_key')
        translator = create_translator(
            provider=args.provider,
            api_key=api_key
        )
        
        print(f"Translating from {args.source_lang} to {args.target_lang}...")
        translations = []
        
        for i, text in enumerate(texts, 1):
            print(f"  Translating page {i}/{len(texts)}...", end='\r')
            result = translator.translate(text, args.target_lang, args.source_lang)
            translations.append(result.translated_text)
        
        print(f"\nTranslation complete!")
        
        # Generate output
        generator = BilingualGenerator(font_path=config.get('font_path'))
        
        if args.format == 'text':
            # Output as text file
            output_text = "\n\n---\n\n".join(translations)
            Path(args.output).write_text(output_text, encoding='utf-8')
        else:
            # Generate bilingual PDF
            generator.generate(
                original_texts=texts,
                translated_texts=translations,
                output_path=args.output,
                format_type=args.format,
                title=args.title or f"Translated Document ({args.source_lang} → {args.target_lang})"
            )
        
        print(f"Output saved to: {args.output}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    finally:
        extractor.close()


def ocr_command(args: argparse.Namespace) -> int:
    """Handle OCR command.
    
    Args:
        args: Command arguments.
        
    Returns:
        Exit code.
    """
    config = Config(args.config)
    
    try:
        ocr = OcrEngine(
            tesseract_cmd=config.get('tesseract_cmd'),
            lang=args.lang or config.get('tesseract_lang')
        )
        
        extractor = PdfExtractor(dpi=args.dpi)
        extractor.open(args.input)
        
        texts = []
        for i in range(extractor.page_count):
            print(f"Processing page {i + 1}/{extractor.page_count}...", end='\r')
            img = extractor.render_page_to_image(i, dpi=args.dpi)
            text = ocr.recognize_pdf_page(img, i)
            texts.append(text)
        
        print(f"\nOCR complete!")
        
        full_text = "\n\n--- Page Break ---\n\n".join(texts)
        
        if args.output:
            Path(args.output).write_text(full_text, encoding='utf-8')
            print(f"Text saved to: {args.output}")
        else:
            print(full_text)
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def config_command(args: argparse.Namespace) -> int:
    """Handle config command.
    
    Args:
        args: Command arguments.
        
    Returns:
        Exit code.
    """
    config = Config()
    
    if args.set:
        for item in args.set:
            if '=' in item:
                key, value = item.split('=', 1)
                config.set(key.strip(), value.strip())
                print(f"Set {key} = {value}")
        
        if args.global_config:
            config.save()
        else:
            config.save('config.json')
        
        print("Configuration saved")
        return 0
    
    if args.get:
        value = config.get(args.get)
        print(f"{args.get} = {value}")
        return 0
    
    if args.list:
        print("Current configuration:")
        for key, value in config.to_dict().items():
            # Mask API keys
            if 'key' in key.lower() and value:
                value = value[:8] + "..." if len(str(value)) > 10 else "***"
            print(f"  {key} = {value}")
        return 0
    
    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser.
    
    Returns:
        Argument parser.
    """
    parser = argparse.ArgumentParser(
        prog='easypdfforyou',
        description='EasyPdfForYou - PDF translation tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract text from PDF
  easypdfforyou extract input.pdf -o output.txt

  # Translate PDF using Google Translate
  easypdfforyou translate input.pdf -o output.pdf --target zh-CN

  # Translate with OpenRouter
  easypdfforyou translate input.pdf -o output.pdf --provider openrouter --target zh-CN

  # OCR a scanned PDF
  easypdfforyou ocr scanned.pdf -o text.txt

  # Configure API keys
  easypdfforyou config --set openrouter_api_key=sk-xxx --global
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract text from PDF')
    extract_parser.add_argument('input', type=str, help='Input PDF file')
    extract_parser.add_argument('-o', '--output', type=str, help='Output text file')
    extract_parser.add_argument('-p', '--pages', type=str, help='Page numbers (e.g., 1,3,5-10)')
    extract_parser.add_argument('--no-preserve-layout', dest='preserve_layout',
                                action='store_false', default=True,
                                help='Do not preserve layout')
    extract_parser.add_argument('--dpi', type=int, default=300, help='DPI for image extraction')
    
    # Translate command
    translate_parser = subparsers.add_parser('translate', help='Translate PDF')
    translate_parser.add_argument('input', type=str, help='Input PDF file')
    translate_parser.add_argument('-o', '--output', type=str, required=True, help='Output file')
    translate_parser.add_argument('--source', dest='source_lang', default='auto',
                                  help='Source language (default: auto)')
    translate_parser.add_argument('--target', dest='target_lang', required=True,
                                  help='Target language (e.g., zh-CN, en, ja, ko)')
    translate_parser.add_argument('--provider', choices=['google', 'openrouter'],
                                  default='google', help='Translation provider')
    translate_parser.add_argument('--api-key', type=str, help='API key for provider')
    translate_parser.add_argument('--format', choices=['side_by_side', 'interleaved', 'text'],
                                  default='side_by_side', help='Output format')
    translate_parser.add_argument('--title', type=str, help='Document title')
    translate_parser.add_argument('--ocr', action='store_true', help='Force OCR')
    translate_parser.add_argument('--auto-ocr', action='store_true',
                                  help='Auto-detect and use OCR for scanned PDFs')
    
    # OCR command
    ocr_parser = subparsers.add_parser('ocr', help='OCR a scanned PDF')
    ocr_parser.add_argument('input', type=str, help='Input PDF file')
    ocr_parser.add_argument('-o', '--output', type=str, help='Output text file')
    ocr_parser.add_argument('--lang', type=str, help='OCR language')
    ocr_parser.add_argument('--dpi', type=int, default=300, help='DPI for rendering')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--set', action='append', metavar='KEY=VALUE',
                               help='Set configuration value')
    config_parser.add_argument('--get', type=str, metavar='KEY',
                               help='Get configuration value')
    config_parser.add_argument('--list', action='store_true',
                               help='List all configuration values')
    config_parser.add_argument('--global', dest='global_config', action='store_true',
                               help='Use global configuration file')
    
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point.
    
    Args:
        argv: Command line arguments.
        
    Returns:
        Exit code.
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if not args.command:
        parser.print_help()
        return 1
    
    setup_logging(args.log_level)
    
    commands = {
        'extract': extract_command,
        'translate': translate_command,
        'ocr': ocr_command,
        'config': config_command,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    
    return 1


if __name__ == '__main__':
    sys.exit(main())
