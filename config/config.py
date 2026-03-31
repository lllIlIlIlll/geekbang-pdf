"""Configuration management for GeekBang PDF Saver."""

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".geekbang-pdf"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    """Load configuration from file.

    Returns:
        dict: Configuration dictionary with keys:
            - cookie: Session cookie for authentication
            - default_output_dir: Default output directory for PDFs
    """
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        return {"cookie": None, "default_output_dir": str(Path.cwd())}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"cookie": None, "default_output_dir": str(Path.cwd())}


def save_config(config):
    """Save configuration to file.

    Args:
        config: Configuration dictionary to save
    """
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_cookie():
    """Get the saved session cookie.

    Returns:
        str or None: The cookie string or None if not set
    """
    config = load_config()
    return config.get("cookie")


def set_cookie(cookie):
    """Save the session cookie.

    Args:
        cookie: Cookie string to save
    """
    config = load_config()
    config["cookie"] = cookie
    save_config(config)


def get_default_output_dir():
    """Get the default output directory.

    Returns:
        str: Default output directory path
    """
    config = load_config()
    return config.get("default_output_dir", str(Path.cwd()))


def set_default_output_dir(output_dir):
    """Set the default output directory.

    Args:
        output_dir: Directory path to set as default
    """
    config = load_config()
    config["default_output_dir"] = output_dir
    save_config(config)
