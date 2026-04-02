"""Configuration data models for GeekBang PDF Saver."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class PDFConfig:
    """Configuration for the PDF saver application.

    Attributes:
        cookie: Session cookie for authentication
        default_output_dir: Default directory for PDF output
        page_size: Default PDF page size (A4, Letter, Legal)
        landscape: Whether to use landscape orientation by default
    """

    cookie: Optional[str] = None
    default_output_dir: Path = field(default_factory=lambda: Path.home() / ".geekbang-pdf")
    page_size: str = "A4"
    landscape: bool = False

    def __post_init__(self):
        """Ensure default_output_dir is a Path object."""
        if isinstance(self.default_output_dir, str):
            self.default_output_dir = Path(self.default_output_dir)
