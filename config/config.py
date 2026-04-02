"""Configuration management for GeekBang PDF Saver."""

import json
from pathlib import Path
from typing import Optional

from src.exceptions import ConfigError

CONFIG_DIR = Path.home() / ".geekbang-pdf"
CONFIG_FILE = CONFIG_DIR / "config.json"
KEY_FILE = CONFIG_DIR / "key.key"

# Try to import cryptography, fall back to no encryption if not available
_cryptography_available = False
_fernet = None
try:
    from cryptography.fernet import Fernet
    _cryptography_available = True
except ImportError:
    pass


def _load_or_create_key():
    """Load existing encryption key or create a new one.

    Returns:
        Fernet instance or None if cryptography is not available
    """
    if not _cryptography_available:
        return None

    KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        key = KEY_FILE.read_bytes()
    else:
        key = Fernet.generate_key()
        KEY_FILE.write_bytes(key)
        KEY_FILE.chmod(0o600)
    return Fernet(key)


# Initialize Fernet instance
_fernet = _load_or_create_key()


def _is_encrypted(cookie: str) -> bool:
    """Check if a cookie string is encrypted (Fernet token).

    Fernet tokens start with 'gAAAAA' prefix.

    Args:
        cookie: Cookie string to check

    Returns:
        bool: True if the cookie appears to be encrypted
    """
    return cookie.startswith('gAAAAA')


def _encrypt_cookie(cookie: str) -> str:
    """Encrypt a cookie string.

    Args:
        cookie: Plain text cookie string

    Returns:
        str: Encrypted cookie string

    Raises:
        ConfigError: If encryption fails
    """
    if not _fernet:
        raise ConfigError("Cryptography library not available for encryption")
    try:
        return _fernet.encrypt(cookie.encode()).decode()
    except Exception as e:
        raise ConfigError(f"Failed to encrypt cookie: {e}")


def _decrypt_cookie(encrypted_cookie: str) -> str:
    """Decrypt an encrypted cookie string.

    Args:
        encrypted_cookie: Encrypted cookie string

    Returns:
        str: Decrypted cookie string

    Raises:
        ConfigError: If decryption fails
    """
    if not _fernet:
        raise ConfigError("Cryptography library not available for decryption")
    try:
        return _fernet.decrypt(encrypted_cookie.encode()).decode()
    except Exception as e:
        raise ConfigError(f"Failed to decrypt cookie: {e}")


def ensure_config_dir():
    """Ensure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _get_project_out_dir():
    """Get the project's out directory for PDF output.

    Returns:
        Path: Path to the project's out directory
    """
    # Project root is two levels up from config/config.py
    project_root = Path(__file__).parent.parent
    out_dir = project_root / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def load_config():
    """Load configuration from file.

    Returns:
        dict: Configuration dictionary with keys:
            - cookie: Session cookie for authentication
            - default_output_dir: Default output directory for PDFs
    """
    ensure_config_dir()
    if not CONFIG_FILE.exists():
        return {"cookie": None, "default_output_dir": str(_get_project_out_dir())}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"cookie": None, "default_output_dir": str(_get_project_out_dir())}


def save_config(config):
    """Save configuration to file.

    Args:
        config: Configuration dictionary to save
    """
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_cookie() -> Optional[str]:
    """Get the saved session cookie.

    Returns:
        str or None: The cookie string or None if not set

    Note:
        Returns plain text cookie for backward compatibility with
        unencrypted cookies stored by older versions.
    """
    config = load_config()
    cookie = config.get("cookie")
    if not cookie:
        return None

    # Backward compatibility: if not encrypted, return as-is
    if not _is_encrypted(cookie):
        return cookie

    # Decrypt encrypted cookie
    return _decrypt_cookie(cookie)


def set_cookie(cookie: str) -> None:
    """Save the session cookie with encryption.

    Args:
        cookie: Cookie string to save

    Note:
        Cookie is encrypted before storage for security.
        Old unencrypted cookies are preserved until overwritten.
    """
    config = load_config()

    # Encrypt cookie before storage
    encrypted_cookie = _encrypt_cookie(cookie)
    config["cookie"] = encrypted_cookie
    save_config(config)


def get_default_output_dir() -> str:
    """Get the default output directory.

    Returns:
        str: Default output directory path (project's out directory)
    """
    # Always use project's out directory as default
    return str(_get_project_out_dir())


def set_default_output_dir(output_dir: str) -> None:
    """Set the default output directory.

    Args:
        output_dir: Directory path to set as default
    """
    config = load_config()
    config["default_output_dir"] = output_dir
    save_config(config)


def safe_resolve_path(user_path: str, base_dir: Path = None) -> Path:
    """Safely resolve a user-provided path, preventing directory traversal.

    Args:
        user_path: Path string provided by user
        base_dir: Optional base directory to restrict path within

    Returns:
        Path: Resolved absolute path

    Raises:
        ConfigError: If path contains traversal attempts or is outside base_dir
    """
    # Check for parent directory traversal in original path
    # This must be checked before resolve() since resolve() can mask ".."
    # by resolving relative to CWD instead of preserving traversal intent
    if ".." in user_path:
        raise ConfigError("Path contains invalid parent directory reference")

    # Now safe to expand user and resolve
    path = Path(user_path).expanduser().resolve()

    # If base_dir is specified, ensure path is within it
    if base_dir:
        try:
            path.relative_to(base_dir.resolve())
        except ValueError:
            raise ConfigError("Path is outside allowed directory")

    return path
