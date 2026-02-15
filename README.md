# EasyPdfForYou

A lightweight PDF document processing and translation tool inspired by BabelDOC. Extract text from PDFs, translate content, and create bilingual documents.

## Features

- 📄 **PDF Text Extraction**: Extract text from PDF documents with layout preservation
- 🌐 **Translation Support**: Integrate with multiple translation APIs
- 📖 **Bilingual Comparison**: Side-by-side original and translated text
- 🚀 **Command Line Interface**: Easy-to-use CLI for quick processing
- 🧪 **Well Tested**: Comprehensive test suite with high coverage

## Installation

```bash
pip install easypdfforyou
```

## Quick Start

```python
from easypdfforyou import PdfProcessor

# Extract text from PDF
processor = PdfProcessor()
text = processor.extract_text("document.pdf")

# Translate content
translated = processor.translate(text, target_lang="zh", translator="google")

# Create bilingual PDF
processor.create_bilingual_pdf("document.pdf", "output.pdf", translated)
```

## CLI Usage

```bash
# Extract text
epdf extract document.pdf -o output.txt

# Translate PDF
epdf translate document.pdf --target zh --translator google -o translated.pdf

# Bilingual comparison
epdf bilingual document.pdf --target zh -o bilingual.pdf
```

## Supported Translators

- Google Translate (default)
- OpenAI GPT
- Custom API endpoints

## License

MIT License - See LICENSE file for details
