import click
import logging

@click.group()
def cli():
    """Kimi Instruct CLI"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from .recursive_cli import recursive

cli.add_command(recursive)

if __name__ == "__main__":
    cli()