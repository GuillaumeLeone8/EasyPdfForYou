"""Web interface for EasyPdfForYou."""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime

from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename

from ..core.config import Config
from ..core.pdf_extractor import PdfExtractor
from ..core.ocr_engine import OcrEngine
from ..core.translator import create_translator
from ..core.bilingual_generator import BilingualGenerator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Configuration
config = Config()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename: str) -> bool:
    """Check if file has allowed extension.
    
    Args:
        filename: Name of file.
        
    Returns:
        True if allowed.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html',
                         languages=Config.SUPPORTED_LANGUAGES,
                         providers=['google', 'openrouter'])


@app.route('/api/extract', methods=['POST'])
def api_extract():
    """API endpoint to extract text from PDF."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF allowed.'}), 400
    
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        # Extract text
        extractor = PdfExtractor()
        extractor.open(tmp_path)
        
        page_contents = extractor.extract_all_pages()
        
        result = {
            'page_count': extractor.page_count,
            'metadata': extractor.metadata,
            'is_scanned': extractor.is_scanned(),
            'pages': []
        }
        
        for page in page_contents:
            result['pages'].append({
                'page_num': page.page_num + 1,
                'text': page.full_text,
                'has_text': page.has_text,
                'text_blocks_count': len(page.text_blocks),
                'images_count': len(page.images)
            })
        
        extractor.close()
        
        # Cleanup
        os.unlink(tmp_path)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/translate', methods=['POST'])
def api_translate():
    """API endpoint to translate PDF."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Get parameters
    source_lang = request.form.get('source_lang', 'auto')
    target_lang = request.form.get('target_lang', 'zh-CN')
    provider = request.form.get('provider', 'google')
    api_key = request.form.get('api_key', '')
    use_ocr = request.form.get('use_ocr', 'false').lower() == 'true'
    output_format = request.form.get('format', 'side_by_side')
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF allowed.'}), 400
    
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        # Extract text
        extractor = PdfExtractor()
        extractor.open(tmp_path)
        
        # Use OCR if requested or auto-detected
        if use_ocr or (not use_ocr and extractor.is_scanned()):
            ocr = OcrEngine(tesseract_cmd=config.get('tesseract_cmd'))
            page_images = extractor.render_all_pages()
            texts = ocr.process_scanned_pdf(page_images, source_lang)
        else:
            page_contents = extractor.extract_all_pages()
            texts = [page.full_text for page in page_contents]
        
        # Translate
        if api_key:
            translator = create_translator(provider, api_key)
        else:
            translator = create_translator(provider, config.get(f'{provider}_api_key'))
        
        translations = []
        for text in texts:
            result = translator.translate(text, target_lang, source_lang)
            translations.append(result.translated_text)
        
        extractor.close()
        
        # Generate output
        if output_format == 'text':
            # Return as text
            output_text = "\n\n---\n\n".join(translations)
            output_path = tempfile.mktemp(suffix='.txt')
            Path(output_path).write_text(output_text, encoding='utf-8')
            mime_type = 'text/plain'
        else:
            # Generate bilingual PDF
            generator = BilingualGenerator(font_path=config.get('font_path'))
            output_path = tempfile.mktemp(suffix='.pdf')
            generator.generate(
                original_texts=texts,
                translated_texts=translations,
                output_path=output_path,
                format_type=output_format,
                title=f"Translated Document ({source_lang} → {target_lang})"
            )
            mime_type = 'application/pdf'
        
        # Cleanup input file
        os.unlink(tmp_path)
        
        # Return file
        return send_file(
            output_path,
            mimetype=mime_type,
            as_attachment=True,
            download_name=f"translated_{file.filename}"
        )
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ocr', methods=['POST'])
def api_ocr():
    """API endpoint for OCR."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    lang = request.form.get('lang', config.get('tesseract_lang'))
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only PDF allowed.'}), 400
    
    try:
        # Save uploaded file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        # OCR
        extractor = PdfExtractor(dpi=300)
        extractor.open(tmp_path)
        
        ocr = OcrEngine(tesseract_cmd=config.get('tesseract_cmd'), lang=lang)
        
        texts = []
        for i in range(extractor.page_count):
            img = extractor.render_page_to_image(i)
            text = ocr.recognize_pdf_page(img, i)
            texts.append(text)
        
        extractor.close()
        os.unlink(tmp_path)
        
        return jsonify({
            'page_count': len(texts),
            'texts': texts,
            'full_text': "\n\n--- Page Break ---\n\n".join(texts)
        })
        
    except Exception as e:
        logger.error(f"OCR error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload and translation."""
    if 'file' not in request.files:
        flash('No file provided', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('Invalid file type. Only PDF allowed.', 'error')
        return redirect(url_for('index'))
    
    # Get form parameters
    source_lang = request.form.get('source_lang', 'auto')
    target_lang = request.form.get('target_lang', 'zh-CN')
    provider = request.form.get('provider', 'google')
    api_key = request.form.get('api_key', '')
    
    try:
        # Save file
        filename = secure_filename(file.filename)
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        # Extract and translate
        extractor = PdfExtractor()
        extractor.open(tmp_path)
        
        if extractor.is_scanned():
            flash('Detected scanned PDF, using OCR...', 'info')
            ocr = OcrEngine(tesseract_cmd=config.get('tesseract_cmd'))
            page_images = extractor.render_all_pages()
            texts = ocr.process_scanned_pdf(page_images, source_lang)
        else:
            page_contents = extractor.extract_all_pages()
            texts = [page.full_text for page in page_contents]
        
        # Translate
        translator = create_translator(
            provider,
            api_key or config.get(f'{provider}_api_key')
        )
        
        translations = []
        for text in texts:
            result = translator.translate(text, target_lang, source_lang)
            translations.append(result.translated_text)
        
        extractor.close()
        
        # Generate output
        generator = BilingualGenerator(font_path=config.get('font_path'))
        output_path = tempfile.mktemp(suffix='.pdf')
        generator.generate(
            original_texts=texts,
            translated_texts=translations,
            output_path=output_path,
            format_type='side_by_side',
            title=f"Translated: {filename}"
        )
        
        os.unlink(tmp_path)
        
        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"translated_{filename}"
        )
        
    except Exception as e:
        logger.error(f"Upload processing error: {e}")
        flash(f'Error processing file: {e}', 'error')
        return redirect(url_for('index'))


def run_app(host: Optional[str] = None, port: Optional[int] = None, debug: bool = False):
    """Run the Flask application.
    
    Args:
        host: Host to bind to.
        port: Port to bind to.
        debug: Enable debug mode.
    """
    host = host or config.get('web_host', '0.0.0.0')
    port = port or config.get('web_port', 5000)
    debug = debug or config.get('web_debug', False)
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_app()
