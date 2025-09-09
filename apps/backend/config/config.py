
import json
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Any


class ConfigManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = "config.json"):
        if not hasattr(self, "initialized"):
            self.config_path = config_path
            self.config = self._load_config()
            self._setup_logging()
            self.initialized = True

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

        log_file = Path(logs_path) / "app.log"

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

# Global instance - will be created when needed
config_manager = None

def get_config() -> ConfigManager:
    global config_manager
    if config_manager is None:
        # Look for config.json in the parent directory (backend folder)
        config_path = Path(__file__).parent.parent / "config.json"
        config_manager = ConfigManager(config_path=config_path)
    return config_manager
