# EasyPdfForYou API Documentation

## Core Modules

### PdfExtractor

Extract text and images from PDF documents.

```python
from easypdfforyou.core.pdf_extractor import PdfExtractor

extractor = PdfExtractor(dpi=300)
pages = extractor.extract_text("document.pdf", max_pages=10)
```

#### Methods

##### `__init__(dpi=300)`
Initialize the extractor.

**Parameters:**
- `dpi` (int): DPI for image rendering. Default: 300

##### `extract_text(pdf_path, max_pages=0, preserve_layout=True) -> List[ExtractedPage]`
Extract text from PDF.

**Parameters:**
- `pdf_path` (str|Path): Path to PDF file
- `max_pages` (int): Maximum pages to extract (0 for all)
- `preserve_layout` (bool): Preserve text layout

**Returns:** List of ExtractedPage objects

##### `render_page_to_image(pdf_path, page_num=0, zoom=2.0) -> PIL.Image`
Render a PDF page to image.

**Parameters:**
- `pdf_path` (str|Path): Path to PDF file
- `page_num` (int): Page number (0-indexed)
- `zoom` (float): Zoom factor

**Returns:** PIL Image object

##### `get_document_info(pdf_path) -> dict`
Get PDF metadata.

**Returns:** Dictionary with page_count, title, author, etc.

##### `is_scanned_pdf(pdf_path, sample_pages=3) -> bool`
Check if PDF is likely scanned.

### OcrEngine

Optical Character Recognition using Tesseract.

```python
from easypdfforyou.core.ocr_engine import OcrEngine

engine = OcrEngine()
text = engine.recognize(image, lang="eng")
```

#### Methods

##### `__init__(tesseract_cmd=None)`
Initialize OCR engine.

**Parameters:**
- `tesseract_cmd` (str): Path to tesseract executable

##### `recognize(image, lang="eng", preprocess=True) -> str`
Recognize text from image.

**Parameters:**
- `image` (PIL.Image|ndarray|Path): Input image
- `lang` (str): Language code
- `preprocess` (bool): Apply image preprocessing

**Returns:** Recognized text

##### `recognize_with_boxes(image, lang="eng", preprocess=True) -> List[dict]`
Recognize text with bounding boxes.

**Returns:** List of dicts with text, conf, left, top, width, height

##### `is_available() -> bool`
Check if Tesseract is configured.

### Translator Classes

#### GoogleTranslator

```python
from easypdfforyou.core.translator import GoogleTranslator

translator = GoogleTranslator()
text = translator.translate("Hello", "en", "zh-CN")
```

#### OpenRouterTranslator

```python
from easypdfforyou.core.translator import OpenRouterTranslator

translator = OpenRouterTranslator(
    api_key="your-api-key",
    model="google/gemini-2.0-flash-001"
)
text = translator.translate("Hello", "en", "zh-CN")
```

#### TranslationService

High-level service with automatic fallback.

```python
from easypdfforyou.core.translator import TranslationService

service = TranslationService()
text = service.translate("Hello", "en", "zh-CN")
```

##### `translate(text, source_lang="auto", target_lang="zh-CN") -> str`
Translate with fallback support.

##### `translate_batch(texts, source_lang="auto", target_lang="zh-CN") -> List[str]`
Translate multiple texts.

### BilingualGenerator

Generate bilingual PDF documents.

```python
from easypdfforyou.core.bilingual_generator import BilingualGenerator

generator = BilingualGenerator()
generator.generate(
    original_pages=["Hello"],
    translated_pages=["你好"],
    output_path="output.pdf",
    layout="side_by_side"
)
```

#### Layouts

- `side_by_side`: Original and translation on same page
- `line_by_line`: Interleaved line-by-line
- `overlay`: Translation overlay on original PDF

#### Methods

##### `generate(original_pages, translated_pages, output_path, layout="side_by_side", original_pdf_path=None) -> Path`
Generate bilingual PDF.

**Parameters:**
- `original_pages` (List[str]): Original text pages
- `translated_pages` (List[str]): Translated text pages
- `output_path` (str|Path): Output PDF path
- `layout` (str): Layout style
- `original_pdf_path` (str|Path): Required for overlay layout

### Config

Configuration management.

```python
from easypdfforyou.core.config import Config, get_config, set_config

# Load from environment
config = Config.from_env()

# Load from file
config = Config.from_file(Path("config.json"))

# Get global config
config = get_config()
```

#### Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENROUTER_API_KEY` | OpenRouter API key |
| `OPENROUTER_MODEL` | Model name |
| `TESSERACT_CMD` | Tesseract path |
| `PDF_DPI` | Default DPI |
| `DEFAULT_TARGET_LANG` | Default target language |

## Data Classes

### ExtractedPage

```python
@dataclass
class ExtractedPage:
    page_num: int
    text: str
    text_blocks: List[TextBlock]
    images: List[PIL.Image]
    width: float
    height: float
```

### TextBlock

```python
@dataclass
class TextBlock:
    text: str
    bbox: Tuple[float, float, float, float]
    page_num: int
    block_num: int
```

## CLI Commands

### extract

```bash
epdf extract document.pdf -o output.txt --max-pages 10
```

### translate

```bash
epdf translate document.pdf \
    --source en \
    --target zh-CN \
    --output translated.pdf \
    --layout side_by_side \
    --ocr
```

### ocr

```bash
epdf ocr document.pdf --page 0 --lang chi_sim
```

### web

```bash
epdf web --host 0.0.0.0 --port 5000 --debug
```

## Web API Endpoints

### POST /api/extract

Extract text from PDF.

**Request:**
- Content-Type: multipart/form-data
- file: PDF file

**Response:**
```json
{
  "pages": [
    {
      "page_num": 1,
      "text": "Extracted text...",
      "width": 612,
      "height": 792
    }
  ]
}
```

### POST /api/translate

Translate PDF file.

**Request:**
- Content-Type: multipart/form-data
- file: PDF file
- source_lang: Source language code
- target_lang: Target language code
- layout: Layout style
- use_ocr: "true" or "false"

**Response:** PDF file download

### POST /api/ocr

Perform OCR on PDF page.

**Request:**
- Content-Type: multipart/form-data
- file: PDF file
- lang: Language code
- page: Page number (0-indexed)

**Response:**
```json
{
  "page": 1,
  "language": "eng",
  "text": "Recognized text..."
}
```