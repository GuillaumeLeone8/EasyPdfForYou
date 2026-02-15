"""Web interface for EasyPdfForYou."""

import os
import tempfile
from pathlib import Path
from typing import Any

from flask import Flask, render_template, request, send_file, jsonify

from easypdfforyou.core.pdf_extractor import PdfExtractor
from easypdfforyou.core.ocr_engine import OcrEngine
from easypdfforyou.core.translator import TranslationService
from easypdfforyou.core.bilingual_generator import BilingualGenerator


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50MB max file size
    app.config["UPLOAD_FOLDER"] = tempfile.gettempdir()
    
    @app.route("/")
    def index() -> str:
        """Render the main page."""
        return render_template("index.html")
    
    @app.route("/api/extract", methods=["POST"])
    def api_extract() -> Any:
        """API endpoint for text extraction."""
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        try:
            # Save uploaded file
            filepath = Path(app.config["UPLOAD_FOLDER"]) / file.filename
            file.save(filepath)
            
            # Extract text
            extractor = PdfExtractor()
            pages = extractor.extract_text(filepath)
            
            result = {
                "pages": [
                    {
                        "page_num": page.page_num + 1,
                        "text": page.text,
                        "width": page.width,
                        "height": page.height,
                    }
                    for page in pages
                ]
            }
            
            # Clean up
            filepath.unlink(missing_ok=True)
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/translate", methods=["POST"])
    def api_translate() -> Any:
        """API endpoint for PDF translation."""
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400
        
        # Get parameters
        source_lang = request.form.get("source_lang", "auto")
        target_lang = request.form.get("target_lang", "zh-CN")
        layout = request.form.get("layout", "side_by_side")
        use_ocr = request.form.get("use_ocr", "false").lower() == "true"
        
        try:
            # Save uploaded file
            input_path = Path(app.config["UPLOAD_FOLDER"]) / file.filename
            file.save(input_path)
            
            output_filename = f"{input_path.stem}_{target_lang}.pdf"
            output_path = Path(app.config["UPLOAD_FOLDER"]) / output_filename
            
            # Extract text
            extractor = PdfExtractor()
            
            if use_ocr or extractor.is_scanned_pdf(input_path):
                pages_text = []
                ocr_engine = OcrEngine()
                for i in range(len(extractor.extract_text(input_path, max_pages=1))):
                    img = extractor.render_page_to_image(input_path, page_num=i)
                    text = ocr_engine.recognize(img, lang=source_lang if source_lang != "auto" else "eng")
                    pages_text.append(text)
            else:
                pages = extractor.extract_text(input_path)
                pages_text = [page.text for page in pages]
            
            # Translate
            translator = TranslationService()
            translated_pages = translator.translate_batch(pages_text, source_lang, target_lang)
            
            # Generate bilingual PDF
            generator = BilingualGenerator()
            generator.generate(
                pages_text,
                translated_pages,
                output_path,
                layout=layout,
                original_pdf_path=input_path
            )
            
            # Clean up input file
            input_path.unlink(missing_ok=True)
            
            return send_file(
                output_path,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=output_filename
            )
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route("/api/ocr", methods=["POST"])
    def api_ocr() -> Any:
        """API endpoint for OCR."""
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files["file"]
        lang = request.form.get("lang", "eng")
        page_num = int(request.form.get("page", 0))
        
        try:
            # Save uploaded file
            filepath = Path(app.config["UPLOAD_FOLDER"]) / file.filename
            file.save(filepath)
            
            # Perform OCR
            extractor = PdfExtractor()
            img = extractor.render_page_to_image(filepath, page_num=page_num)
            
            ocr_engine = OcrEngine()
            text = ocr_engine.recognize(img, lang=lang)
            
            # Clean up
            filepath.unlink(missing_ok=True)
            
            return jsonify({
                "page": page_num + 1,
                "language": lang,
                "text": text
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app