"""Pytest configuration and fixtures for GeekBang PDF Saver tests."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temporary config directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".geekbang-pdf"
        config_dir.mkdir()

        # Need to patch the actual module variables, not dict keys
        from config import config as config_module
        original_dir = config_module.CONFIG_DIR
        original_file = config_module.CONFIG_FILE
        original_key = config_module.KEY_FILE

        config_module.CONFIG_DIR = config_dir
        config_module.CONFIG_FILE = config_dir / "config.json"
        config_module.KEY_FILE = config_dir / "key.key"

        yield config_dir

        # Restore original values
        config_module.CONFIG_DIR = original_dir
        config_module.CONFIG_FILE = original_file
        config_module.KEY_FILE = original_key


@pytest.fixture
def sample_cookie():
    """Sample cookie string for testing."""
    return "GCESS=abc123xyz; another_cookie=test_value"
