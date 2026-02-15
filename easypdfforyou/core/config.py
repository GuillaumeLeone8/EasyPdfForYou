"""Configuration management for EasyPdfForYou."""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Config:
    """Application configuration."""
    
    # Translation API settings
    openrouter_api_key: Optional[str] = None
    openrouter_model: str = "google/gemini-2.0-flash-001"
    
    # Tesseract OCR settings
    tesseract_cmd: Optional[str] = None
    
    # PDF processing settings
    dpi: int = 300
    max_pages: int = 0  # 0 means no limit
    
    # Output settings
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    
    # Language settings
    default_source_lang: str = "auto"
    default_target_lang: str = "zh-CN"
    
    # Web UI settings
    web_host: str = "127.0.0.1"
    web_port: int = 5000
    web_debug: bool = False
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        config = cls()
        
        # Translation API
        config.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        config.openrouter_model = os.getenv("OPENROUTER_MODEL", config.openrouter_model)
        
        # Tesseract
        config.tesseract_cmd = os.getenv("TESSERACT_CMD")
        
        # PDF settings
        if dpi := os.getenv("PDF_DPI"):
            config.dpi = int(dpi)
        if max_pages := os.getenv("PDF_MAX_PAGES"):
            config.max_pages = int(max_pages)
        
        # Output
        if output_dir := os.getenv("OUTPUT_DIR"):
            config.output_dir = Path(output_dir)
        
        # Language
        config.default_source_lang = os.getenv("DEFAULT_SOURCE_LANG", config.default_source_lang)
        config.default_target_lang = os.getenv("DEFAULT_TARGET_LANG", config.default_target_lang)
        
        # Web UI
        config.web_host = os.getenv("WEB_HOST", config.web_host)
        if web_port := os.getenv("WEB_PORT"):
            config.web_port = int(web_port)
        config.web_debug = os.getenv("WEB_DEBUG", "false").lower() == "true"
        
        return config
    
    @classmethod
    def from_file(cls, path: Path) -> "Config":
        """Load configuration from a file.
        
        Supports JSON and YAML formats.
        """
        import json
        
        config = cls()
        
        if not path.exists():
            return config
        
        with open(path, "r", encoding="utf-8") as f:
            if path.suffix in (".yaml", ".yml"):
                try:
                    import yaml
                    data = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("PyYAML is required for YAML config files")
            else:
                data = json.load(f)
        
        # Update config from file data
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    
    def save(self, path: Path) -> None:
        """Save configuration to a JSON file."""
        import json
        
        data = {
            "openrouter_api_key": self.openrouter_api_key,
            "openrouter_model": self.openrouter_model,
            "tesseract_cmd": self.tesseract_cmd,
            "dpi": self.dpi,
            "max_pages": self.max_pages,
            "output_dir": str(self.output_dir),
            "default_source_lang": self.default_source_lang,
            "default_target_lang": self.default_target_lang,
            "web_host": self.web_host,
            "web_port": self.web_port,
            "web_debug": self.web_debug,
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config