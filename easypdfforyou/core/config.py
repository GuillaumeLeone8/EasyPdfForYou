"""Configuration management for EasyPdfForYou."""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for EasyPdfForYou.
    
    Loads configuration from environment variables and config files.
    Priority: Environment variables > Config file > Defaults
    """
    
    DEFAULT_CONFIG_PATHS = [
        Path.home() / ".easypdfforyou" / "config.json",
        Path.home() / ".config" / "easypdfforyou" / "config.json",
        Path("/etc/easypdfforyou/config.json"),
        Path("config.json"),
    ]
    
    DEFAULTS = {
        "google_translate_api_key": None,
        "openrouter_api_key": None,
        "openrouter_model": "google/gemini-2.0-flash-001",
        "tesseract_cmd": None,
        "tesseract_lang": "eng+chi_sim+chi_tra+jpn+kor",
        "default_source_lang": "auto",
        "default_target_lang": "zh-CN",
        "pdf_dpi": 300,
        "output_format": "side_by_side",
        "font_path": None,
        "log_level": "INFO",
        "max_workers": 4,
        "chunk_size": 5000,
        "web_host": "0.0.0.0",
        "web_port": 5000,
        "web_debug": False,
    }
    
    SUPPORTED_LANGUAGES = {
        "zh-CN": "Simplified Chinese",
        "zh-TW": "Traditional Chinese",
        "en": "English",
        "ja": "Japanese",
        "ko": "Korean",
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Optional path to config file to load.
        """
        self._config: Dict[str, Any] = self.DEFAULTS.copy()
        self._load_from_file(config_path)
        self._load_from_env()
        
    def _load_from_file(self, config_path: Optional[str] = None) -> None:
        """Load configuration from file.
        
        Args:
            config_path: Optional path to config file.
        """
        paths_to_check = []
        
        if config_path:
            paths_to_check.append(Path(config_path))
        else:
            paths_to_check.extend(self.DEFAULT_CONFIG_PATHS)
        
        for path in paths_to_check:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        file_config = json.load(f)
                    self._config.update(file_config)
                    logger.info(f"Loaded configuration from {path}")
                    break
                except (json.JSONDecodeError, IOError) as e:
                    logger.warning(f"Failed to load config from {path}: {e}")
    
    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "EASYPDF_GOOGLE_API_KEY": "google_translate_api_key",
            "EASYPDF_OPENROUTER_API_KEY": "openrouter_api_key",
            "EASYPDF_OPENROUTER_MODEL": "openrouter_model",
            "EASYPDF_TESSERACT_CMD": "tesseract_cmd",
            "EASYPDF_TESSERACT_LANG": "tesseract_lang",
            "EASYPDF_DEFAULT_SOURCE_LANG": "default_source_lang",
            "EASYPDF_DEFAULT_TARGET_LANG": "default_target_lang",
            "EASYPDF_PDF_DPI": "pdf_dpi",
            "EASYPDF_OUTPUT_FORMAT": "output_format",
            "EASYPDF_FONT_PATH": "font_path",
            "EASYPDF_LOG_LEVEL": "log_level",
            "EASYPDF_MAX_WORKERS": "max_workers",
            "EASYPDF_CHUNK_SIZE": "chunk_size",
            "EASYPDF_WEB_HOST": "web_host",
            "EASYPDF_WEB_PORT": "web_port",
            "EASYPDF_WEB_DEBUG": "web_debug",
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in ["pdf_dpi", "max_workers", "chunk_size", "web_port"]:
                    try:
                        value = int(value)
                    except ValueError:
                        continue
                elif config_key in ["web_debug"]:
                    value = value.lower() in ("true", "1", "yes", "on")
                self._config[config_key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key.
            default: Default value if key not found.
            
        Returns:
            Configuration value or default.
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key.
            value: Value to set.
        """
        self._config[key] = value
    
    def save(self, path: Optional[str] = None) -> None:
        """Save configuration to file.
        
        Args:
            path: Path to save config file. If None, uses default location.
        """
        if path is None:
            config_dir = Path.home() / ".easypdfforyou"
            config_dir.mkdir(parents=True, exist_ok=True)
            path = config_dir / "config.json"
        else:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved configuration to {path}")
    
    @property
    def google_api_key(self) -> Optional[str]:
        """Get Google Translate API key."""
        return self._config.get("google_translate_api_key")
    
    @property
    def openrouter_api_key(self) -> Optional[str]:
        """Get OpenRouter API key."""
        return self._config.get("openrouter_api_key")
    
    @property
    def tesseract_cmd(self) -> Optional[str]:
        """Get Tesseract OCR command path."""
        return self._config.get("tesseract_cmd")
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self._config.get("log_level", "INFO")
    
    def is_language_supported(self, lang_code: str) -> bool:
        """Check if language code is supported.
        
        Args:
            lang_code: ISO language code.
            
        Returns:
            True if supported, False otherwise.
        """
        return lang_code in self.SUPPORTED_LANGUAGES or lang_code == "auto"
    
    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name.
        
        Args:
            lang_code: ISO language code.
            
        Returns:
            Language name or code if not found.
        """
        return self.SUPPORTED_LANGUAGES.get(lang_code, lang_code)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary.
        
        Returns:
            Configuration dictionary.
        """
        return self._config.copy()
