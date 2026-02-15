# EasyPdfForYou Usage Guide

## Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Advanced Examples](#advanced-examples)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)

## Installation

### System Requirements

- Python 3.8 or higher
- Tesseract OCR (optional, for scanned PDFs)

### Install Package

```bash
pip install git+https://github.com/GuillaumeLeone8/EasyPdfForYou.git
```

### Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    tesseract-ocr-jpn \
    tesseract-ocr-kor
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Windows:**
1. Download installer from https://github.com/UB-Mannheim/tesseract/wiki
2. Add to PATH or set `TESSERACT_CMD` environment variable

## Basic Usage

### 1. Extract Text from PDF

```bash
# Extract all text
epdf extract document.pdf

# Extract to file
epdf extract document.pdf -o output.txt

# Extract first 5 pages only
epdf extract document.pdf -o output.txt -p 5

# Extract with block-level detail
epdf extract document.pdf --format blocks
```

### 2. Translate PDF

```bash
# Basic translation to Chinese
epdf translate document.pdf --target zh-CN

# Specify output file
epdf translate document.pdf --target zh-CN -o translated.pdf

# Translate from Japanese to English
epdf translate japanese.pdf --source ja --target en
```

### 3. OCR for Scanned PDFs

```bash
# Force OCR mode
epdf translate scanned.pdf --target zh-CN --ocr

# OCR single page
epdf ocr scanned.pdf --page 0 --lang chi_sim
```

### 4. Web Interface

```bash
# Start web server
epdf web

# Custom host and port
epdf web --host 0.0.0.0 --port 8080
```

Then open http://localhost:5000 in your browser.

## Advanced Examples

### Bilingual PDF Layouts

#### Side-by-Side Layout
Original text and translation appear on the same page:

```bash
epdf translate document.pdf --target zh-CN --layout side_by_side
```

**Output format:**
```
Page 1
--------
Original:
Hello World

Translation:
你好世界
```

#### Line-by-Line Layout
Original and translation alternate line by line:

```bash
epdf translate document.pdf --target zh-CN --layout line_by_line
```

**Output format:**
```
Page 1
--------
Hello World
你好世界
How are you?
你好吗？
```

#### Overlay Layout
Translation overlays the original PDF:

```bash
epdf translate document.pdf --target zh-CN --layout overlay
```

### Python API Examples

#### Extract and Process Text

```python
from easypdfforyou import PdfExtractor

extractor = PdfExtractor(dpi=300)
pages = extractor.extract_text("document.pdf")

for page in pages:
    print(f"Page {page.page_num + 1}:")
    print(f"  Text length: {len(page.text)}")
    print(f"  Dimensions: {page.width} x {page.height}")
    print(f"  Text blocks: {len(page.text_blocks)}")
```

#### Custom Translation Pipeline

```python
from easypdfforyou import PdfExtractor, TranslationService, BilingualGenerator
from easypdfforyou.core.translator import OpenRouterTranslator

# Extract
extractor = PdfExtractor()
pages = extractor.extract_text("document.pdf")
texts = [page.text for page in pages]

# Translate with OpenRouter
translator = TranslationService(
    primary_translator=OpenRouterTranslator(
        api_key="your-api-key",
        model="google/gemini-2.0-flash-001"
    )
)
translated = translator.translate_batch(texts, "en", "zh-CN")

# Generate bilingual PDF
generator = BilingualGenerator()
generator.generate(
    texts,
    translated,
    "bilingual.pdf",
    layout="side_by_side"
)
```

#### OCR Pipeline

```python
from easypdfforyou import PdfExtractor, OcrEngine, TranslationService

extractor = PdfExtractor()
ocr_engine = OcrEngine()
translator = TranslationService()

# Process each page
results = []
for i, page in enumerate(extractor.extract_text("scanned.pdf")):
    # Render to image
    img = extractor.render_page_to_image("scanned.pdf", page_num=i)
    
    # OCR
    text = ocr_engine.recognize(img, lang="chi_sim")
    
    # Translate
    translated = translator.translate(text, "zh-CN", "en")
    
    results.append({
        "page": i + 1,
        "original": text,
        "translated": translated
    })
```

### Batch Processing

```python
import os
from pathlib import Path
from easypdfforyou import PdfExtractor, TranslationService, BilingualGenerator

extractor = PdfExtractor()
translator = TranslationService()
generator = BilingualGenerator()

input_dir = Path("./input_pdfs")
output_dir = Path("./output_pdfs")
output_dir.mkdir(exist_ok=True)

for pdf_file in input_dir.glob("*.pdf"):
    print(f"Processing {pdf_file.name}...")
    
    try:
        # Extract
        pages = extractor.extract_text(pdf_file)
        texts = [page.text for page in pages]
        
        # Translate
        translated = translator.translate_batch(texts, "auto", "zh-CN")
        
        # Generate
        output_file = output_dir / f"{pdf_file.stem}_zh.pdf"
        generator.generate(texts, translated, output_file)
        
        print(f"  ✓ Saved to {output_file}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
```

## Configuration

### Environment Variables

Create a `.env` file or export in your shell:

```bash
# OpenRouter for LLM translation
export OPENROUTER_API_KEY="sk-or-v1-..."
export OPENROUTER_MODEL="google/gemini-2.0-flash-001"

# Tesseract (if not in PATH)
export TESSERACT_CMD="/usr/local/bin/tesseract"

# Default settings
export DEFAULT_SOURCE_LANG="auto"
export DEFAULT_TARGET_LANG="zh-CN"
export PDF_DPI="300"
export OUTPUT_DIR="./translated"

# Web UI settings
export WEB_HOST="127.0.0.1"
export WEB_PORT="5000"
```

### Config File

Create `config.json`:

```json
{
  "openrouter_api_key": "sk-or-v1-...",
  "openrouter_model": "google/gemini-2.0-flash-001",
  "tesseract_cmd": "/usr/bin/tesseract",
  "dpi": 300,
  "max_pages": 0,
  "default_source_lang": "auto",
  "default_target_lang": "zh-CN",
  "web_host": "127.0.0.1",
  "web_port": 5000
}
```

Use with CLI:
```bash
epdf --config config.json translate document.pdf
```

### Python Configuration

```python
from easypdfforyou.core.config import Config, set_config

config = Config.from_env()
config.openrouter_api_key = "sk-or-v1-..."
config.default_target_lang = "zh-CN"
config.dpi = 300

set_config(config)
```

## Troubleshooting

### OCR Not Working

**Problem:** OCR returns empty text

**Solutions:**
1. Check Tesseract is installed:
   ```bash
   tesseract --version
   ```
2. Install language packs:
   ```bash
   # List installed languages
   tesseract --list-langs
   
   # Install Chinese
   sudo apt-get install tesseract-ocr-chi-sim
   ```
3. Set Tesseract path:
   ```bash
   export TESSERACT_CMD="/usr/bin/tesseract"
   ```

### Translation Fails

**Problem:** Google Translate rate limited

**Solution:** 
- Wait a few minutes between requests
- Use OpenRouter with API key
- Add delays in batch processing

```python
import time

for text in texts:
    result = translator.translate(text, "en", "zh-CN")
    time.sleep(1)  # Rate limiting
```

### PDF Won't Extract

**Problem:** Encrypted or corrupted PDF

**Solution:**
```python
import fitz  # PyMuPDF

# Check if PDF is encrypted
doc = fitz.open("document.pdf")
if doc.is_encrypted:
    # Try to decrypt with empty password
    if not doc.authenticate(""):
        print("PDF is password protected")
    else:
        print("PDF decrypted")
doc.close()
```

### Chinese Characters Not Displaying

**Problem:** Missing CJK fonts in generated PDF

**Solution:**
```python
from easypdfforyou.core.bilingual_generator import BilingualGenerator

# Use a font with CJK support
generator = BilingualGenerator(
    font_path="/path/to/NotoSansCJK-Regular.ttc"
)
```

Common CJK fonts:
- Noto Sans CJK (Google)
- Source Han Sans
- WenQuanYi Micro Hei

### Memory Issues with Large PDFs

**Solution:**
```python
# Process in chunks
extractor = PdfExtractor()

chunk_size = 10
total_pages = 100

for start in range(0, total_pages, chunk_size):
    end = min(start + chunk_size, total_pages)
    pages = extractor.extract_text(
        "large.pdf",
        max_pages=end
    )[start:end]
    # Process chunk...
```

## Tips and Best Practices

1. **Always check if PDF is scanned before OCR:**
   ```python
   if extractor.is_scanned_pdf("document.pdf"):
       # Use OCR
   else:
       # Direct text extraction
   ```

2. **Cache translation results:**
   ```python
   import hashlib
   import json
   
   cache_file = "translation_cache.json"
   cache = json.loads(Path(cache_file).read_text()) if Path(cache_file).exists() else {}
   
   text_hash = hashlib.md5(text.encode()).hexdigest()
   if text_hash in cache:
       return cache[text_hash]
   else:
       translated = translator.translate(text, "en", "zh-CN")
       cache[text_hash] = translated
       Path(cache_file).write_text(json.dumps(cache))
   ```

3. **Handle errors gracefully:**
   ```python
   from easypdfforyou.core.translator import TranslationService
   
   service = TranslationService()
   
   try:
       result = service.translate(text, "en", "zh-CN")
   except Exception as e:
       # Fallback to original text
       result = text
       print(f"Translation failed: {e}")
   ```

4. **Use appropriate DPI:**
   - 150 DPI: Fast, good for text
   - 300 DPI: Balanced (recommended)
   - 600 DPI: High quality, slower