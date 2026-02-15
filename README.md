# EasyPdfForYou

[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/GuillaumeLeone8/EasyPdfForYou/releases/tag/v0.1.0)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

A lightweight PDF document processing and translation tool supporting Google Translate and OpenRouter APIs.

## Features

- 📄 **PDF Text Extraction** - Extract text while preserving layout structure
- 🔍 **OCR Support** - Recognize text from scanned PDFs using Tesseract
- 🌐 **Multi-language Translation** - Support for 9+ languages (English, Chinese, Japanese, Korean, etc.)
- 📝 **Bilingual PDF Generation** - Create side-by-side, line-by-line, or overlay bilingual documents
- 💻 **CLI Interface** - Command-line tool for batch processing
- 🌐 **Web UI** - Easy-to-use web interface
- 🔧 **Multiple Translation Providers** - Google Translate (free) and OpenRouter (LLM-based)

## Supported Languages

| Language | Code | OCR Support |
|----------|------|-------------|
| English | `en` | ✅ |
| Simplified Chinese | `zh-CN` | ✅ |
| Traditional Chinese | `zh-TW` | ✅ |
| Japanese | `ja` | ✅ |
| Korean | `ko` | ✅ |
| French | `fr` | ✅ |
| German | `de` | ✅ |
| Spanish | `es` | ✅ |
| Italian | `it` | ✅ |
| Portuguese | `pt` | ✅ |
| Russian | `ru` | ✅ |

## Installation

### From Source

```bash
git clone https://github.com/GuillaumeLeone8/EasyPdfForYou.git
cd EasyPdfForYou
pip install -e .
```

### System Dependencies

For OCR functionality, install Tesseract:

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
Download from https://github.com/UB-Mannheim/tesseract/wiki

## Quick Start

### CLI Usage

```bash
# Extract text from PDF
epdf extract document.pdf -o output.txt

# Translate PDF
e pdf translate document.pdf --target zh-CN -o translated.pdf

# Use OCR for scanned PDFs
epdf translate scanned.pdf --target zh-CN --ocr -o translated.pdf

# Different layout styles
epdf translate document.pdf --target zh-CN --layout side_by_side
e pdf translate document.pdf --target zh-CN --layout line_by_line
e pdf translate document.pdf --target zh-CN --layout overlay

# OCR a specific page
epdf ocr document.pdf --page 0 --lang eng

# Show PDF info
epdf info document.pdf
```

### Web UI

```bash
# Start the web server
epdf web --host 0.0.0.0 --port 5000

# Then open http://localhost:5000 in your browser
```

### Python API

```python
from easypdfforyou import PdfExtractor, TranslationService, BilingualGenerator

# Extract text
extractor = PdfExtractor()
pages = extractor.extract_text("document.pdf")

# Translate
pages_text = [page.text for page in pages]
translator = TranslationService()
translated = translator.translate_batch(pages_text, "en", "zh-CN")

# Generate bilingual PDF
generator = BilingualGenerator()
generator.generate(
    pages_text,
    translated,
    "output.pdf",
    layout="side_by_side"
)
```

## Configuration

### Environment Variables

```bash
# OpenRouter API (for LLM-based translation)
export OPENROUTER_API_KEY="your-api-key"
export OPENROUTER_MODEL="google/gemini-2.0-flash-001"

# Tesseract path (if not in PATH)
export TESSERACT_CMD="/usr/bin/tesseract"

# Default settings
export DEFAULT_TARGET_LANG="zh-CN"
export PDF_DPI="300"
export OUTPUT_DIR="./output"
```

### Config File

Create `config.json`:

```json
{
  "openrouter_api_key": "your-api-key",
  "openrouter_model": "google/gemini-2.0-flash-001",
  "default_target_lang": "zh-CN",
  "dpi": 300
}
```

Then use with CLI:
```bash
epdf --config config.json translate document.pdf
```

## Translation Providers

### Google Translate (Default)
- Free, no API key required
- Supports all major languages
- Rate limited by Google

### OpenRouter (Optional)
- Higher quality LLM-based translation
- Supports models like Gemini, GPT, etc.
- Requires API key from https://openrouter.ai

## Development

### Setup Development Environment

```bash
git clone https://github.com/GuillaumeLeone8/EasyPdfForYou.git
cd EasyPdfForYou
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=easypdfforyou
```

### Code Formatting

```bash
black easypdfforyou tests
flake8 easypdfforyou tests
```

## Project Structure

```
easypdfforyou/
├── easypdfforyou/
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── pdf_extractor.py    # PDF text extraction
│   │   ├── ocr_engine.py       # Tesseract OCR
│   │   ├── translator.py       # Translation APIs
│   │   └── bilingual_generator.py  # PDF generation
│   ├── cli/
│   │   └── main.py             # CLI interface
│   ├── web/
│   │   ├── app.py              # Flask web app
│   │   └── templates/
│   │       └── index.html      # Web UI
│   └── utils/
│       └── __init__.py         # Utility functions
├── tests/                      # Test suite
├── docs/                       # Documentation
├── examples/                   # Example files
├── setup.py                    # Package setup
└── README.md                   # This file
```

## API Documentation

See [docs/API.md](docs/API.md) for detailed API documentation.

## Usage Examples

See [docs/USAGE.md](docs/USAGE.md) for more usage examples.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) - PDF processing
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR engine
- [Googletrans](https://github.com/ssut/py-googletrans) - Google Translate
- [OpenRouter](https://openrouter.ai) - LLM API
- [ReportLab](https://www.reportlab.com) - PDF generation
- [Flask](https://flask.palletsprojects.com) - Web framework

## Changelog

### v0.1.0 (2026-02-15)
- Initial release
- PDF text extraction with layout preservation
- OCR support for scanned documents
- Multi-language translation (Google + OpenRouter)
- Bilingual PDF generation (3 layouts)
- CLI interface
- Web UI
- Full test coverage