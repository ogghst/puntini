"""
Unit tests for the ConfigManager class.
"""

import json
import logging
import os
import sys
from typing import Any, Dict
from unittest.mock import patch

import pytest

# Add the 'apps' directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from apps.backend.config import ConfigManager


@pytest.fixture(autouse=True)
def reset_singleton():
    """
    Resets the ConfigManager singleton instance before each test to ensure test isolation.
    """
    ConfigManager._instance = None


@pytest.fixture
def mock_config_data() -> Dict[str, Any]:
    """
    Provides a dictionary with mock configuration data for testing.
    """
    return {
        "llm_provider": "test_provider",
        "llm_config": {"model": "test_model"},
        "system": {"logs_path": "test_logs"},
        "logging": {
            "log_level": "DEBUG",
            "console_logging": False,
            "max_bytes": 1000,
            "backup_count": 2,
        },
        "runtime": {"mode": "test"},
        "server": {"host": "localhost", "port": 8080},
    }


@pytest.fixture
def mock_config_file(tmp_path, mock_config_data: Dict[str, Any]) -> str:
    """
    Creates a temporary configuration file with mock data for testing.
    """
    config_file = tmp_path / "config.json"
    with open(config_file, 'w') as f:
        json.dump(mock_config_data, f)
    return str(config_file)


def test_config_manager_is_singleton(mock_config_file: str):
    """
    Tests that the ConfigManager class correctly implements the singleton pattern.
    """
    cm1 = ConfigManager(config_path=mock_config_file)
    cm2 = ConfigManager(config_path=mock_config_file)
    assert cm1 is cm2


def test_load_config_success(mock_config_file: str, mock_config_data: Dict[str, Any]):
    """
    Tests that the configuration is loaded successfully from a valid JSON file.
    """
    cm = ConfigManager(config_path=mock_config_file)
    assert cm.config == mock_config_data


def test_load_config_file_not_found():
    """
    Tests that a FileNotFoundError is raised if the configuration file does not exist.
    """
    with pytest.raises(FileNotFoundError):
        ConfigManager(config_path="non_existent_config.json")


def test_load_config_json_decode_error(tmp_path):
    """
    Tests that a json.JSONDecodeError is raised for a malformed configuration file.
    """
    invalid_json_file = tmp_path / "invalid.json"
    with open(invalid_json_file, 'w') as f:
        f.write("{'invalid': 'json'")
    with pytest.raises(json.JSONDecodeError):
        ConfigManager(config_path=str(invalid_json_file))


def test_get_method(mock_config_file: str):
    """
    Tests the get() method for retrieving configuration values.
    """
    cm = ConfigManager(config_path=mock_config_file)
    assert cm.get("llm_provider") == "test_provider"
    assert cm.get("non_existent_key", "default_value") == "default_value"


def test_properties(mock_config_file: str, mock_config_data: Dict[str, Any]):
    """
    Tests the property getters for accessing specific configuration sections.
    """
    cm = ConfigManager(config_path=mock_config_file)
    assert cm.llm_provider == mock_config_data["llm_provider"]
    assert cm.llm_config == mock_config_data["llm_config"]
    assert cm.system == mock_config_data["system"]
    assert cm.logging_config == mock_config_data["logging"]
    assert cm.runtime == mock_config_data["runtime"]
    assert cm.server == mock_config_data["server"]


@patch("os.makedirs")
@patch("os.path.exists", return_value=False)
def test_setup_logging_creates_log_dir(mock_exists, mock_makedirs, mock_config_file: str):
    """
    Tests that the logging setup creates the log directory if it does not exist.
    """
    with patch('logging.handlers.RotatingFileHandler') as mock_handler:
        mock_handler.return_value.level = logging.NOTSET
        ConfigManager(config_path=mock_config_file)
        # The log path is retrieved from the mock config data
        log_path = "test_logs"
        mock_exists.assert_called_with(log_path)
        mock_makedirs.assert_called_with(log_path)
