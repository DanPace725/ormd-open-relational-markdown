# src/ormd_cli/main.py
import click
from .validator import ORMDValidator

@click.group()
def cli():
    """ORMD CLI - Tools for Open Relational Markdown"""
    pass

@cli.command()
@click.argument('file_path')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation info')
def validate(file_path, verbose):
    """Validate an ORMD file against the 0.1 specification"""
    validator = ORMDValidator()
    
    if validator.validate_file(file_path):
        click.echo(f"✅ {file_path} is valid ORMD 0.1")
        return
    
    click.echo(f"❌ {file_path} failed validation:")
    for error in validator.errors:
        click.echo(f"  • {error}")
    
    exit(1)

if __name__ == '__main__':
    cli()