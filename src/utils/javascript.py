"""JavaScript script management for externalized scripts."""

import re
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
    def _extract_function_name(cls, script_content: str) -> str:
        """Extract the function name from script content.

        Args:
            script_content: JavaScript code content

        Returns:
            str: The function name defined in the script
        """
        # Match function declarations: function functionName(
        match = re.search(r'function\s+(\w+)\s*\(', script_content)
        if match:
            return match.group(1)
        raise ValueError(f"Could not extract function name from script: {script_content[:100]}")

    @classmethod
    def execute_script(cls, page, name: str, selectors_json: str) -> dict:
        """Execute a JavaScript function on the page.

        Args:
            page: Playwright page object
            name: Script name (without .js extension)
            selectors_json: JSON string of platform selectors

        Returns:
            dict: Result of JS function execution
        """
        script = cls.get_script(name)
        func_name = cls._extract_function_name(script)
        # Escape backslashes for JavaScript string literal
        # JSON has \" for escaped quotes, but in JS string literal \ is also escape
        escaped_json = selectors_json.replace('\\', '\\\\')
        result = page.evaluate(
            f"(function(){{ {script}; return {func_name}('{escaped_json}'); }})()"
        )
        return result

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
