"""Configuration module for GeekBang PDF Saver."""

from .config import (
    load_config,
    save_config,
    get_cookie,
    set_cookie,
    get_default_output_dir,
    set_default_output_dir,
    ensure_config_dir,
)

__all__ = [
    "load_config",
    "save_config",
    "get_cookie",
    "set_cookie",
    "get_default_output_dir",
    "set_default_output_dir",
    "ensure_config_dir",
]
