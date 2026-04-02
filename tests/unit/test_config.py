"""Tests for config module."""

import json
import tempfile
from pathlib import Path

import pytest

import config.config as config_module
from config.config import (
    _is_encrypted,
    ensure_config_dir,
    get_cookie,
    get_default_output_dir,
    load_config,
    save_config,
    set_cookie,
    set_default_output_dir,
    safe_resolve_path,
)
from src.exceptions import ConfigError


class TestIsEncrypted:
    """Tests for _is_encrypted function."""

    def test_plain_text_not_encrypted(self):
        """Plain text cookie should not be detected as encrypted."""
        assert _is_encrypted("GCESS=abc123") is False

    def test_fernet_token_is_encrypted(self):
        """Fernet token should be detected as encrypted."""
        # Fernet tokens always start with 'gAAAAA'
        assert _is_encrypted("gAAAAAabcdef123456") is True


class TestCookieEncryption:
    """Tests for cookie encryption functionality."""

    def test_encrypt_decrypt_roundtrip(self, temp_config_dir, sample_cookie):
        """Cookie should be encrypted and decrypted correctly."""
        set_cookie(sample_cookie)

        # Verify cookie is stored encrypted
        config = load_config()
        stored = config.get("cookie")
        assert stored is not None
        assert stored != sample_cookie
        assert _is_encrypted(stored)

        # Verify cookie is decrypted correctly when retrieved
        retrieved = get_cookie()
        assert retrieved == sample_cookie

    def test_plain_text_backward_compatibility(self, temp_config_dir):
        """Old plain text cookies should still be readable."""
        # Simulate old config with plain text cookie
        config_data = {"cookie": "plain_text_cookie=abc123", "default_output_dir": "/tmp"}
        with open(config_module.CONFIG_FILE, "w") as f:
            json.dump(config_data, f)

        # Should return plain text cookie without error
        retrieved = get_cookie()
        assert retrieved == "plain_text_cookie=abc123"


class TestSafeResolvePath:
    """Tests for path traversal protection."""

    def test_path_traversal_blocked(self):
        """Paths with '..' should be blocked."""
        with pytest.raises(ConfigError, match="parent directory reference"):
            safe_resolve_path("../../../etc/passwd")

    def test_valid_absolute_path(self, tmp_path):
        """Valid absolute paths should work."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        result = safe_resolve_path(str(test_file))
        assert result == test_file.resolve()

    def test_valid_home_path(self):
        """Paths with ~ should work."""
        result = safe_resolve_path("~/Documents")
        assert result == Path.home() / "Documents"

    def test_path_outside_base_dir_blocked(self, tmp_path):
        """Paths outside base_dir should be blocked."""
        base = tmp_path / "base"
        base.mkdir()

        outside = tmp_path / "outside"
        outside.mkdir()

        with pytest.raises(ConfigError, match="outside allowed directory"):
            safe_resolve_path(str(outside), base_dir=base)


class TestConfigOperations:
    """Tests for configuration read/write operations."""

    def test_save_and_load_config(self, temp_config_dir):
        """Config should be saved and loaded correctly."""
        test_config = {
            "cookie": "test_cookie",
            "default_output_dir": "/test/path"
        }
        save_config(test_config)
        loaded = load_config()

        assert loaded["cookie"] == "test_cookie"
        assert loaded["default_output_dir"] == "/test/path"

    def test_get_default_output_dir_default(self, temp_config_dir):
        """Should return cwd if no default output dir set."""
        # With empty config
        result = get_default_output_dir()
        assert result == str(Path.cwd())

    def test_set_and_get_default_output_dir(self, temp_config_dir):
        """Should save and retrieve default output dir."""
        set_default_output_dir("/custom/path")
        assert get_default_output_dir() == "/custom/path"
