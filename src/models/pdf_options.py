"""PDF generation options data model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PDFOptions:
    """Options for PDF generation.

    Attributes:
        page_size: Page size (A4, Letter, Legal)
        landscape: Whether to use landscape orientation
        wait_time: Seconds to wait for dynamic content
        margin_top: Top margin in mm
        margin_bottom: Bottom margin in mm
        margin_left: Left margin in mm
        margin_right: Right margin in mm
    """

    page_size: str = "A4"
    landscape: bool = False
    wait_time: int = 5
    margin_top: str = "20mm"
    margin_bottom: str = "20mm"
    margin_left: str = "15mm"
    margin_right: str = "15mm"

    @classmethod
    def from_dict(cls, data: dict) -> "PDFOptions":
        """Create PDFOptions from a dictionary.

        Args:
            data: Dictionary with option keys

        Returns:
            PDFOptions instance
        """
        return cls(
            page_size=data.get("page_size", "A4"),
            landscape=data.get("landscape", False),
            wait_time=data.get("wait_time", 5),
            margin_top=data.get("margin_top", "20mm"),
            margin_bottom=data.get("margin_bottom", "20mm"),
            margin_left=data.get("margin_left", "15mm"),
            margin_right=data.get("margin_right", "15mm"),
        )

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "page_size": self.page_size,
            "landscape": self.landscape,
            "wait_time": self.wait_time,
            "margin_top": self.margin_top,
            "margin_bottom": self.margin_bottom,
            "margin_left": self.margin_left,
            "margin_right": self.margin_right,
        }
