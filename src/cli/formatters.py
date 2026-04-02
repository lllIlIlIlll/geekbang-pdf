"""Rich console formatters for GeekBang PDF Saver."""

from typing import Optional

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ConsoleFormatter:
    """Console output formatter using rich library.

    Falls back to plain print if rich is not available.
    """

    def __init__(self, use_rich: bool = True):
        """Initialize formatter.

        Args:
            use_rich: Whether to use rich formatting (default: True)
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        self.console = Console() if self.use_rich else None

    def print(self, message: str, style: Optional[str] = None):
        """Print a message.

        Args:
            message: Message to print
            style: Rich style string (e.g., 'bold red')
        """
        if self.use_rich and self.console:
            self.console.print(message, style=style)
        else:
            print(message)

    def print_header(self, text: str):
        """Print a header.

        Args:
            text: Header text
        """
        self.print(f"\n{'='*50}", style="bold blue")
        self.print(text, style="bold blue")
        self.print(f"{'='*50}\n", style="bold blue")

    def print_success(self, message: str):
        """Print a success message.

        Args:
            message: Success message
        """
        self.print(f"✓ {message}", style="green")

    def print_error(self, message: str):
        """Print an error message.

        Args:
            message: Error message
        """
        self.print(f"✗ {message}", style="bold red")

    def print_warning(self, message: str):
        """Print a warning message.

        Args:
            message: Warning message
        """
        self.print(f"⚠ {message}", style="yellow")

    def create_progress(self) -> Optional["Progress"]:
        """Create a progress bar.

        Returns:
            Progress instance or None if rich not available
        """
        if self.use_rich:
            return Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
            )
        return None

    def create_table(self, title: str, columns: list) -> Optional["Table"]:
        """Create a table.

        Args:
            title: Table title
            columns: List of column names

        Returns:
            Table instance or None if rich not available
        """
        if not self.use_rich:
            return None

        table = Table(title=title)
        for col in columns:
            table.add_column(col)
        return table
