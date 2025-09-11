
import json
import logging
import logging.handlers
import os
import threading
from pathlib import Path
from typing import Any

from langfuse import Langfuse, get_client
from langfuse.langchain import CallbackHandler

class ConfigManager:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking pattern
                if cls._instance is None:
                    cls._instance = super(ConfigManager, cls).__new__(cls)
                    cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(self, config_path: str = "config.json"):
        """Private initialization method called only once."""
        if not self._initialized:
            self.config_path = config_path
            self.config = self._load_config()
            self._setup_logging()
            self._setup_langfuse()
            self._initialized = True

    def _load_config(self) -> dict[str, Any]:
        """Loads the configuration from the JSON file."""
        try:
            with Path(self.config_path).open() as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Configuration file not found at {self.config_path}")
            raise
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from {self.config_path}")
            raise

    def _setup_logging(self):
        """Sets up the logging for the application."""
        logging_config = self.config.get("logging", {})
        log_level = logging_config.get("log_level", "INFO").upper()
        console_logging = logging_config.get("console_logging", True)

        system_config = self.config.get("system", {})
        logs_path = system_config.get("logs_path", "../logs")

        if not Path(logs_path).exists():
            Path(logs_path).mkdir(parents=True)

        log_file = logging_config.get("log_file", "app.log")
        log_file = Path(log_file) 

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)

        # Clear existing handlers
        if root_logger.hasHandlers():
            root_logger.handlers.clear()

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # File handler
        max_bytes = logging_config.get("max_bytes", 10485760)
        backup_count = logging_config.get("backup_count", 5)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Console handler
        if console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        logging.info("Logging configured.")
        
    def _setup_langfuse(self):
        """Sets up the langfuse for the application."""
        langfuse_config = self.config.get("instrumentation", {}).get("langfuse", {})
        Langfuse(
            secret_key=langfuse_config.get("secret_key", ""),
            public_key=langfuse_config.get("public_key", ""),
            host=langfuse_config.get("host", "http://127.0.0.1:3000")
        )   
        self._langfuse = get_client()
        self._langfuse_handler = CallbackHandler()
        logging.info("Langfuse configured.")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value."""
        return self.config.get(key, default)

    @property
    def llm_provider(self) -> str:
        return self.get("llm_provider", "default_provider")

    @property
    def llm_config(self) -> dict[str, Any]:
        return self.get("llm_config", {})

    @property
    def system(self) -> dict[str, Any]:
        return self.get("system", {})

    @property
    def logging_config(self) -> dict[str, Any]:
        return self.get("logging", {})

    @property
    def runtime(self) -> dict[str, Any]:
        return self.get("runtime", {})

    @property
    def server(self) -> dict[str, Any]:
        return self.get("server", {})
    
    @property
    def instrumentation(self) -> dict[str, Any]:
        return self.get("instrumentation", {})
    
    @property
    def langfuse_handler(self) -> CallbackHandler:
        return self._langfuse_handler


# Factory function - this is the only way to access ConfigManager
def get_config() -> ConfigManager:
    """Get the global ConfigManager instance. This is the only way to access ConfigManager."""
    config_path = Path(__file__).parent.parent / "config.json"
    return ConfigManager(config_path=config_path)

# Make ConfigManager constructor private by not exporting it
__all__ = ["get_config"]
