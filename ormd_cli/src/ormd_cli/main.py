# src/ormd_cli/main.py
import click
from .validator import ORMDValidator
from .packager import ORMDPackager
from .updater import ORMDUpdater
from typing import Optional
import io # Changed from 'from io import StringIO' to just 'import io'
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfparser import PDFParser, PDFSyntaxError # Added PDFParser
from pdfminer.pdfdocument import PDFDocument # Added PDFDocument
from pdfminer.psparser import PSKeyword, PSLiteral # Added for decoding
from pdfminer.utils import decode_text # Added for decoding
import yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta # Added timedelta
from .utils import get_view_template, SYMBOLS
from .parser import parse_document, serialize_front_matter, _parse_front_matter_and_body
import zipfile
import json # Used by render, open, edit
# re is no longer used directly in main.py
# webbrowser, threading, http.server, socketserver, tempfile, socket, os were moved
from .server import _serve_and_open
from .html_generator import _generate_viewable_html, _generate_editable_html, generate_render_html
# get_edit_template, _generate_viewable_html, _generate_editable_html, markdown and re imports removed as logic moved.

@click.group()
def cli():
    """ORMD CLI - Tools for Open Relational Markdown"""
    pass

@cli.command()
@click.argument('file_path')
def create(file_path: str):
    """Create a new ORMD file with minimal front-matter."""
    try:
        p = Path(file_path)
        filename = p.stem

        # Convert filename to title (e.g., "my-doc-name" -> "My Doc Name")
        title = filename.replace('-', ' ').replace('_', ' ').title()

        now_utc_iso = datetime.now(timezone.utc).isoformat()

        front_matter_data = {
            "title": title,
            "authors": [],
            "dates": { # Using 'dates' namespace as per serialize_front_matter logic
                "created": now_utc_iso,
                "modified": now_utc_iso,
            },
            # Consider adding other useful defaults if any, e.g.
            # "version": "1.0.0",
            # "status": "draft",
            # "permissions": {"editable": True, "mode": "private"}
        }

        front_matter_string = serialize_front_matter(front_matter_data)

        # Ensure there's a blank line after front-matter for the body
        # serialize_front_matter already adds a newline at the end of the block.
        # We add one more for an empty body.
        content = f"<!-- ormd:0.1 -->\n{front_matter_string}\n"

        with click.open_file(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        click.echo(f"{SYMBOLS['success']} Created ORMD file: {file_path}")

    except Exception as e:
        click.echo(f"{SYMBOLS['error']} Failed to create file: {str(e)}")
        # exit(1) removed for click consistency, though it was present in the original create
@cli.command()
@click.argument('file_path')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation info')
def validate(file_path, verbose):
    """Validate an ORMD file against the 0.1 specification with comprehensive Phase 1 checks"""
    validator = ORMDValidator()
    
    is_valid = validator.validate_file(file_path)
    
    if verbose or not is_valid:
        # Show detailed validation summary
        click.echo(validator.get_validation_summary())
    else:
        # Show simple success message
        if is_valid and not validator.warnings:
            click.echo(f"{SYMBOLS['success']} {file_path} is valid ORMD 0.1")
        elif is_valid and validator.warnings:
            click.echo(f"{SYMBOLS['success']} {file_path} is valid ORMD 0.1 (with {len(validator.warnings)} warning(s))")
            if not verbose:
                click.echo("Use --verbose to see warnings")
    
    # Always show warnings even in non-verbose mode if validation passes
    if is_valid and validator.warnings and not verbose:
        click.echo(f"{SYMBOLS['warning']}  {len(validator.warnings)} warning(s) - use --verbose for details")
    
    if not is_valid:
        exit(1)

@cli.command()
@click.argument('content_file')
@click.argument('meta_file')
@click.option('--out', '-o', default='package.ormd', help='Output package file')
@click.option('--validate/--no-validate', default=True, help='Validate content before packing')
def pack(content_file, meta_file, out, validate):
    """Pack content.ormd and meta.json into a single .ormd package"""
    
    # Optional validation step
    if validate:
        validator = ORMDValidator()
        if not validator.validate_file(content_file):
            click.echo(f"{SYMBOLS['error']} Content file failed validation:")
            for error in validator.errors:
                click.echo(f"  {SYMBOLS['bullet']} {error}")
            click.echo("Use --no-validate to skip validation")
            exit(1)
    
    packager = ORMDPackager()
    if packager.pack(content_file, meta_file, out):
        click.echo(f"{SYMBOLS['success']} Created package: {out}")
    else:
        click.echo(f"{SYMBOLS['error']} Failed to create package")
        exit(1)

@cli.command()
@click.argument('package_file')
@click.option('--out-dir', '-d', default='./unpacked', help='Output directory')
@click.option('--overwrite', is_flag=True, help='Overwrite existing files')
def unpack(package_file, out_dir, overwrite):
    """Unpack a .ormd package for editing"""
    from pathlib import Path
    
    # Check if output directory exists and has files
    out_path = Path(out_dir)
    if out_path.exists() and any(out_path.iterdir()) and not overwrite:
        click.echo(f"{SYMBOLS['error']} Directory {out_dir} is not empty. Use --overwrite to force.")
        exit(1)
    
    packager = ORMDPackager()
    if packager.unpack(package_file, out_dir):
        click.echo(f"{SYMBOLS['success']} Unpacked to: {out_dir}")
        
        # Show what was extracted
        if out_path.exists():
            files = list(out_path.iterdir())
            click.echo("Files extracted:")
            for file in sorted(files):
                click.echo(f"  {SYMBOLS['bullet']} {file.name}")
    else:
        click.echo(f"{SYMBOLS['error']} Failed to unpack {package_file}")
        exit(1)

@cli.command()
@click.argument('file_path')
@click.option('--dry-run', '-n', is_flag=True, help='Show what would be updated without making changes')
@click.option('--force-update', '-f', is_flag=True, help='Update locked fields (ignore locked: true)')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed update information')
def update(file_path, dry_run, force_update, verbose):
    """Update and sync front-matter fields (date_modified, word_count, link_ids, asset_ids)"""
    updater = ORMDUpdater()
    
    try:
        result = updater.update_file(
            file_path, 
            dry_run=dry_run, 
            force_update=force_update, 
            verbose=verbose
        )
        
        if dry_run:
            if result['changes']:
                click.echo(f"{SYMBOLS['info']} Would update {file_path}:")
                for field, change in result['changes'].items():
                    old_val = change.get('old', 'None')
                    new_val = change.get('new')
                    click.echo(f"  {SYMBOLS['bullet']} {field}: {old_val} → {new_val}")
            else:
                click.echo(f"{SYMBOLS['success']} {file_path} is already up to date")
        else:
            if result['updated']:
                click.echo(f"{SYMBOLS['success']} Updated {file_path}")
                if verbose and result['changes']:
                    click.echo("Changes made:")
                    for field, change in result['changes'].items():
                        old_val = change.get('old', 'None')
                        new_val = change.get('new')
                        click.echo(f"  {SYMBOLS['bullet']} {field}: {old_val} → {new_val}")
            else:
                click.echo(f"{SYMBOLS['success']} {file_path} is already up to date")
                
    except Exception as e:
        click.echo(f"{SYMBOLS['error']} Failed to update {file_path}: {str(e)}")
        exit(1)

@cli.command()
@click.argument('input_file')
@click.option('--out', '-o', default=None, help='Output HTML file')
def render(input_file, out):
    """Render an ORMD file or package to HTML with sidebar features."""
    input_path = Path(input_file)
    is_zip = input_path.suffix == '.ormd' and zipfile.is_zipfile(input_file)
    raw_ormd = ''
    meta = {}
    title = 'ORMD Document'
    history = ''
    main_html = ''
    links = []
    front_matter = {}
    body = ''
    metadata = None

    if is_zip:
        with zipfile.ZipFile(input_file, 'r') as zf:
            if 'content.ormd' in zf.namelist():
                raw_ormd = zf.read('content.ormd').decode('utf-8')
            if 'meta.json' in zf.namelist():
                meta = json.loads(zf.read('meta.json').decode('utf-8'))
    else:
        raw_ormd = Path(input_file).read_text(encoding='utf-8')

    # Unified parsing for both file and package using the shared parser
    front_matter, body, metadata, parse_errors = parse_document(raw_ormd)
    title = front_matter.get('title', title) if front_matter else title
    links = front_matter.get('links', []) if front_matter else []

    # The main HTML generation logic is now in html_generator.py
    # However, the render command itself still handles initial parsing and file I/O.
    # The 'body' passed to generate_render_html is the raw body from parse_document.
    # Link replacement and markdown conversion are now inside generate_render_html.
    html_content = generate_render_html(raw_ormd, front_matter, body, links, meta)

    # Determine output path
    if out is None:
        out = str(input_path.with_suffix('.html'))
    Path(out).write_text(html, encoding='utf-8')
    click.echo(f"✅ Rendered HTML written to: {out}")

@cli.command()
@click.argument('file_path')
@click.option('--port', '-p', default=0, help='Local server port (0 for random)')
@click.option('--no-browser', is_flag=True, help='Don\'t automatically open browser')
@click.option('--show-url', is_flag=True, help='Just show URL that would be opened (for testing)')
def open(file_path, port, no_browser, show_url):
    """Open ORMD document in browser for viewing"""
    
    # Validate file exists
    if not Path(file_path).exists():
        click.echo(f"{SYMBOLS['error']} File not found: {file_path}")
        exit(1)
    
    try:
        # Parse the document (similar to render command)
        input_path = Path(file_path)
        is_zip = input_path.suffix == '.ormd' and zipfile.is_zipfile(file_path)
        raw_ormd = ''
        meta = {}
        
        if is_zip:
            with zipfile.ZipFile(file_path, 'r') as zf:
                if 'content.ormd' in zf.namelist():
                    raw_ormd = zf.read('content.ormd').decode('utf-8')
                if 'meta.json' in zf.namelist():
                    meta = json.loads(zf.read('meta.json').decode('utf-8'))
        else:
            raw_ormd = Path(file_path).read_text(encoding='utf-8')

        # Parse document
        front_matter, body, metadata, parse_errors = parse_document(raw_ormd)
        
        if parse_errors:
            click.echo(f"{SYMBOLS['warning']} Document has parsing errors:")
            for error in parse_errors:
                click.echo(f"  {SYMBOLS['bullet']} {error}")
        
        title = front_matter.get('title', 'ORMD Document') if front_matter else 'ORMD Document'
        links = front_matter.get('links', []) if front_matter else []
        permissions = front_matter.get('permissions', {}) if front_matter else {}
        
        # Generate HTML for viewing
        html_content = _generate_viewable_html(file_path, raw_ormd, front_matter, body, links, meta)
        
        if show_url:
            # Just show what would happen without starting server
            if port == 0:
                port = 8000  # Default for display
            click.echo(f"{SYMBOLS['success']} Would open '{title}' at http://localhost:{port}/")
            click.echo(f"{SYMBOLS['info']} HTML generated successfully ({len(html_content)} characters)")
            return
        
        # Start server and open browser
        _serve_and_open(html_content, port, no_browser, file_path, title)
        
    except Exception as e:
        click.echo(f"{SYMBOLS['error']} Failed to open {file_path}: {str(e)}")
        exit(1)

@cli.command()
@click.argument('file_path')
@click.option('--port', '-p', default=0, help='Local server port (0 for random)')
@click.option('--no-browser', is_flag=True, help='Don\'t automatically open browser')
@click.option('--force', '-f', is_flag=True, help='Force edit even if permissions deny it')
@click.option('--show-url', is_flag=True, help='Just show URL that would be opened (for testing)')
def edit(file_path, port, no_browser, force, show_url):
    """Open ORMD document in browser for editing"""
    
    # Validate file exists
    if not Path(file_path).exists():
        click.echo(f"{SYMBOLS['error']} File not found: {file_path}")
        exit(1)
    
    try:
        # Parse the document
        input_path = Path(file_path)
        is_zip = input_path.suffix == '.ormd' and zipfile.is_zipfile(file_path)
        raw_ormd = ''
        meta = {}
        
        if is_zip:
            with zipfile.ZipFile(file_path, 'r') as zf:
                if 'content.ormd' in zf.namelist():
                    raw_ormd = zf.read('content.ormd').decode('utf-8')
                if 'meta.json' in zf.namelist():
                    meta = json.loads(zf.read('meta.json').decode('utf-8'))
        else:
            raw_ormd = Path(file_path).read_text(encoding='utf-8')

        # Parse document
        front_matter, body, metadata, parse_errors = parse_document(raw_ormd)
        
        if parse_errors:
            click.echo(f"{SYMBOLS['warning']} Document has parsing errors:")
            for error in parse_errors:
                click.echo(f"  {SYMBOLS['bullet']} {error}")
        
        title = front_matter.get('title', 'ORMD Document') if front_matter else 'ORMD Document'
        links = front_matter.get('links', []) if front_matter else []
        permissions = front_matter.get('permissions', {}) if front_matter else {}
        
        # Check permissions before proceeding
        can_edit = permissions.get('editable', True)  # Default to editable
        is_signed = permissions.get('signed', False)
        perm_mode = permissions.get('mode', 'draft')
        
        if is_signed and not force:
            click.echo(f"{SYMBOLS['error']} Document is cryptographically signed and cannot be edited")
            click.echo("Use --force to edit anyway (will break signature)")
            exit(1)
        
        if not can_edit and not force:
            click.echo(f"{SYMBOLS['error']} Document permissions deny editing (editable: false)")
            click.echo("Use --force to edit anyway")
            exit(1)
        
        if perm_mode == 'private' and not force:
            click.echo(f"{SYMBOLS['warning']} Document is marked as private")
            click.echo("Continuing with edit (use --force to suppress this warning)")
        
        # Show warnings for forced edits
        if force:
            if is_signed:
                click.echo(f"{SYMBOLS['warning']} Editing signed document - signature will be invalidated")
            if not can_edit:
                click.echo(f"{SYMBOLS['warning']} Editing document marked as non-editable")
        
        # Generate HTML for editing
        html_content = _generate_editable_html(file_path, raw_ormd, front_matter, body, links, meta)
        
        if show_url:
            # Just show what would happen without starting server
            if port == 0:
                port = 8000  # Default for display
            click.echo(f"{SYMBOLS['success']} Would edit '{title}' at http://localhost:{port}/")
            click.echo(f"{SYMBOLS['info']} Editable HTML generated successfully ({len(html_content)} characters)")
            return
        
        # Start server and open browser
        _serve_and_open(html_content, port, no_browser, file_path, f"{title} [EDIT]")
        
    except Exception as e:
        click.echo(f"{SYMBOLS['error']} Failed to edit {file_path}: {str(e)}")
        exit(1)

# _generate_viewable_html, _generate_editable_html, and the old get_edit_template (if it was here) are removed.
# _serve_and_open was already moved to server.py.

from .converter import convert_cmd
cli.add_command(convert_cmd)

if __name__ == '__main__':
    cli()
    
    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_html_path = f.name
    
    # Find available port if not specified
    if port == 0:
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
    
    # Custom HTTP handler to serve our temporary file
    class ORMDHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=Path(temp_html_path).parent, **kwargs)
        
        def log_message(self, format, *args):
            # Suppress HTTP logs for cleaner output
            return
    
    try:
        # Use a simpler approach with better interrupt handling
        httpd = http.server.HTTPServer(("", port), ORMDHandler)
        httpd.timeout = 0.5  # Short timeout for responsiveness
        
        url = f"http://localhost:{port}/{Path(temp_html_path).name}"
        
        click.echo(f"{SYMBOLS['success']} Opening '{title}' in browser")
        click.echo(f"{SYMBOLS['info']} Server running at {url}")
        click.echo(f"{SYMBOLS['info']} Press Ctrl+C to stop")
        
        if not no_browser:
            # Open browser after short delay to ensure server is ready
            threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        
        # Simple serving loop that's easier to interrupt
        try:
            while True:
                httpd.handle_request()
        except KeyboardInterrupt:
            click.echo(f"\n{SYMBOLS['info']} Stopping server...")
        finally:
            httpd.server_close()
            
    except OSError as e:
        if "Address already in use" in str(e):
            click.echo(f"{SYMBOLS['error']} Port {port} is already in use. Try a different port with --port")
        else:
            click.echo(f"{SYMBOLS['error']} Failed to start server: {str(e)}")
        exit(1)
    finally:
        # Cleanup temporary file
        try:
            os.unlink(temp_html_path)
        except:
            pass

from .converter import convert_cmd
cli.add_command(convert_cmd)

if __name__ == '__main__':
    cli()