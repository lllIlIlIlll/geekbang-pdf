"""JavaScript script management for externalized scripts."""

from pathlib import Path
from typing import Dict


class ScriptManager:
    """Manages externalized JavaScript scripts."""

    SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
    _cache: Dict[str, str] = {}

    @classmethod
    def get_script(cls, name: str) -> str:
        """Get a JavaScript script by name.

        Args:
            name: Script name without .js extension

        Returns:
            str: JavaScript code content

        Raises:
            FileNotFoundError: If script doesn't exist
        """
        if name not in cls._cache:
            path = cls.SCRIPTS_DIR / f"{name}.js"
            if not path.exists():
                raise FileNotFoundError(f"Script '{name}' not found at {path}")
            cls._cache[name] = path.read_text(encoding="utf-8")
        return cls._cache[name]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the script cache to force reload."""
        cls._cache.clear()

    @classmethod
    def list_scripts(cls) -> list:
        """List all available scripts.

        Returns:
            list: List of script names (without .js extension)
        """
        return [p.stem for p in cls.SCRIPTS_DIR.glob("*.js")]
