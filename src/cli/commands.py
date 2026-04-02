"""Click command definitions for GeekBang PDF Saver."""

import click

from ..models.pdf_options import PDFOptions


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """GeekBang PDF Saver - Save geekbang.org course pages as PDF."""
    pass


@cli.command()
@click.argument("url")
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--name", "-n", type=str, help="Output filename (single URL mode)")
@click.option("--cookie", type=str, help="Session cookie")
@click.option("--use-config", is_flag=True, help="Use cookie from config")
@click.option("--use-chrome", is_flag=True, help="Get cookie from Chrome browser")
@click.option("--page-size", type=click.Choice(["A4", "Letter", "Legal"]), default="A4")
@click.option("--landscape", is_flag=True, help="Use landscape orientation")
def save(url, output, name, cookie, use_config, use_chrome, page_size, landscape):
    """Save a URL as PDF."""
    options = PDFOptions(
        page_size=page_size,
        landscape=landscape,
    )
    click.echo(f"Saving {url} as PDF with options: {options.to_dict()}")


@cli.command()
@click.option("--browser-login", is_flag=True, help="Login via browser")
def login(browser_login):
    """Login to GeekBang."""
    if browser_login:
        click.echo("Opening browser for login...")
    else:
        click.echo("Please use --browser-login option")


if __name__ == "__main__":
    cli()
