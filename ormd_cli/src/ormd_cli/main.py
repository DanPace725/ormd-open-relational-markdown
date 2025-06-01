# src/ormd_cli/main.py
import click
from .validator import ORMDValidator
from .packager import ORMDPackager
from .updater import ORMDUpdater
import markdown
import yaml
from pathlib import Path
from datetime import datetime, timezone
from .utils import HTML_TEMPLATE, SYMBOLS
from .parser import parse_document, serialize_front_matter
import zipfile
import json
import re
import webbrowser
import threading
import http.server
import socketserver
import tempfile
import socket
import os

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
        exit(1)

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

    # --- Semantic link rendering ---
    def replace_link(match):
        link_id = match.group(1)
        link = next((l for l in links if l.get('id') == link_id), None)
        if link:
            rel = link.get('rel', 'related')
            to = link.get('to', f'#{link_id}')
            label = link_id
            return f'<a href="{to}" class="ormd-link ormd-link-{rel}">{label}</a>'
        else:
            return f'<span class="ormd-link ormd-link-undefined">{link_id}</span>'
    body = re.sub(r'\[\[([^\]]+)\]\]', replace_link, body)
    # --- End semantic link rendering ---

    # Render Markdown to HTML
    main_html = markdown.markdown(body, extensions=['extra', 'toc', 'sane_lists'])

    # Prepare history info from meta.json if available
    if meta:
        created = meta.get('created', '')
        modified = meta.get('modified', '')
        provenance = meta.get('provenance', {})
        history = f"<b>Created:</b> {created}<br><b>Modified:</b> {modified}<br>"
        if provenance:
            history += f"<b>Hash:</b> {provenance.get('hash', '')}<br>"
            history += f"<b>Signature Ref:</b> {provenance.get('sigRef', '')}<br>"
            history += f"<b>Timestamp:</b> {provenance.get('timestamp', '')}<br>"

    # Fill the HTML template
    html = HTML_TEMPLATE.format(
        title=title,
        raw_ormd=raw_ormd.replace('<', '&lt;').replace('>', '&gt;'),
        main_html=main_html,
        history=history
    )
    


    # Insert links data for D3.js graph (as a JS variable)
    links_json = json.dumps(links)
    # Replace any '// renderGraph(...);' line with the actual call
    new_html, n = re.subn(r'// renderGraph\(.*\);', f'renderGraph({links_json});', html)
    if n == 0:
        # If no placeholder was found, append the call at the end of the script
        new_html = html.replace('</script>', f'renderGraph({links_json});\n</script>')
    html = new_html

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

def _generate_viewable_html(file_path, raw_ormd, front_matter, body, links, meta):
    """Generate HTML for viewing ORMD document"""
    
    title = front_matter.get('title', 'ORMD Document') if front_matter else 'ORMD Document'
    permissions = front_matter.get('permissions', {}) if front_matter else {}
    
    # --- Semantic link rendering (same as render command) ---
    def replace_link(match):
        link_id = match.group(1)
        link = next((l for l in links if l.get('id') == link_id), None)
        if link:
            rel = link.get('rel', 'related')
            to = link.get('to', f'#{link_id}')
            label = link_id
            return f'<a href="{to}" class="ormd-link ormd-link-{rel}">{label}</a>'
        else:
            return f'<span class="ormd-link ormd-link-undefined">{link_id}</span>'
    
    processed_body = re.sub(r'\[\[([^\]]+)\]\]', replace_link, body)
    
    # Render Markdown to HTML
    main_html = markdown.markdown(processed_body, extensions=['extra', 'toc', 'sane_lists'])
    
    # Prepare history info from meta.json if available
    history = ''
    if meta:
        created = meta.get('created', '')
        modified = meta.get('modified', '')
        provenance = meta.get('provenance', {})
        history = f"<b>Created:</b> {created}<br><b>Modified:</b> {modified}<br>"
        if provenance:
            history += f"<b>Hash:</b> {provenance.get('hash', '')}<br>"
            history += f"<b>Signature Ref:</b> {provenance.get('sigRef', '')}<br>"
            history += f"<b>Timestamp:</b> {provenance.get('timestamp', '')}<br>"
    
    # Add permissions info to history
    if permissions:
        history += "<br><b>Permissions:</b><br>"
        history += f"Mode: {permissions.get('mode', 'draft')}<br>"
        history += f"Editable: {permissions.get('editable', True)}<br>"
        history += f"Signed: {permissions.get('signed', False)}<br>"
    
    # Fill the HTML template (reuse existing template)
    html = HTML_TEMPLATE.format(
        title=f"{title} - ORMD Viewer",
        raw_ormd=raw_ormd.replace('<', '&lt;').replace('>', '&gt;'),
        main_html=main_html,
        history=history
    )
    
    # Insert links data for D3.js graph
    links_json = json.dumps(links)
    new_html, n = re.subn(r'// renderGraph\(.*\);', f'renderGraph({links_json});', html)
    if n == 0:
        new_html = html.replace('</script>', f'renderGraph({links_json});\n</script>')
    
    return new_html

def _generate_editable_html(file_path, raw_ormd, front_matter, body, links, meta):
    """Generate HTML for editing ORMD document"""
    
    title = front_matter.get('title', 'ORMD Document') if front_matter else 'ORMD Document'
    permissions = front_matter.get('permissions', {}) if front_matter else {}
    
    # --- Semantic link rendering (same as render command) ---
    def replace_link(match):
        link_id = match.group(1)
        link = next((l for l in links if l.get('id') == link_id), None)
        if link:
            rel = link.get('rel', 'related')
            to = link.get('to', f'#{link_id}')
            label = link_id
            return f'<a href="{to}" class="ormd-link ormd-link-{rel}">{label}</a>'
        else:
            return f'<span class="ormd-link ormd-link-undefined">{link_id}</span>'
    
    processed_body = re.sub(r'\[\[([^\]]+)\]\]', replace_link, body)
    
    # Render Markdown to HTML
    main_html = markdown.markdown(processed_body, extensions=['extra', 'toc', 'sane_lists'])
    
    # Prepare history info from meta.json if available
    history = ''
    if meta:
        created = meta.get('created', '')
        modified = meta.get('modified', '')
        provenance = meta.get('provenance', {})
        history = f"<b>Created:</b> {created}<br><b>Modified:</b> {modified}<br>"
        if provenance:
            history += f"<b>Hash:</b> {provenance.get('hash', '')}<br>"
            history += f"<b>Signature Ref:</b> {provenance.get('sigRef', '')}<br>"
            history += f"<b>Timestamp:</b> {provenance.get('timestamp', '')}<br>"
    
    # Add permissions info to history
    if permissions:
        history += "<br><b>Permissions:</b><br>"
        history += f"Mode: {permissions.get('mode', 'draft')}<br>"
        history += f"Editable: {permissions.get('editable', True)}<br>"
        history += f"Signed: {permissions.get('signed', False)}<br>"
    
    # Create the editable HTML template with main area editing
    editable_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    /* Base styles */
    body {{
      margin: 0;
      font-family: system-ui, sans-serif;
      background: #121212;
      color: #e0e0e0;
    }}
    
    /* Top toolbar */
    #toolbar {{
      background: #1c1c1c;
      border-bottom: 1px solid #373e47;
      padding: 12px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    
    #toolbar h1 {{
      margin: 0;
      font-size: 1.2em;
      color: #e0e0e0;
      flex-grow: 1;
    }}
    
    .btn {{
      border: none;
      padding: 8px 16px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      transition: background 0.2s;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    
    .btn-primary {{ background: #217a21; color: white; }}
    .btn-primary:hover {{ background: #2e8b2e; }}
    
    .btn-secondary {{ background: #004080; color: white; }}
    .btn-secondary:hover {{ background: #0066cc; }}
    
    .btn-tertiary {{ background: #666; color: white; }}
    .btn-tertiary:hover {{ background: #888; }}
    
    .btn-toggle {{
      background: #333;
      color: white;
      border: 1px solid #555;
    }}
    .btn-toggle:hover {{ background: #444; }}
    .btn-toggle.active {{
      background: #004080;
      border-color: #0066cc;
    }}
    
    /* Main container */
    #container {{
      display: flex;
      min-height: calc(100vh - 60px);
    }}
    
    /* Sidebar */
    #sidebar {{
      width: 300px;
      background: #1c1c1c;
      border-right: 1px solid #373e47;
      transition: width 0.2s;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      color: #e0e0e0;
    }}
    
    #sidebar.collapsed {{
      width: 0;
      border-right: none;
    }}
    
    #sidebar nav {{
      display: flex;
      flex-direction: column;
      border-bottom: 1px solid #373e47;
      padding: 8px;
    }}
    
    #sidebar nav button {{
      background: none;
      border: none;
      padding: 12px;
      font-size: 1em;
      cursor: pointer;
      text-align: left;
      transition: background 0.1s;
      color: #e0e0e0;
      border-radius: 4px;
      margin: 2px 0;
    }}
    
    #sidebar nav button:hover {{
      background: #333333;
    }}
    
    #sidebar nav button.active {{
      background: #004080;
      font-weight: bold;
      color: #ffffff;
    }}
    
    .panel {{
      display: none;
      padding: 16px;
      overflow-y: auto;
      flex: 1;
      background: #1c1c1c;
      color: #e0e0e0;
    }}
    
    .panel.active {{
      display: block;
    }}
    
    /* Main content area */
    #main-content {{
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }}
    
    /* Editor and preview areas */
    #edit-area {{
      flex: 1;
      padding: 20px;
      background: #121212;
      display: none;
    }}
    
    #edit-area.active {{
      display: block;
    }}
    
    #preview-area {{
      flex: 1;
      padding: 40px 5vw;
      background: #121212;
      color: #e0e0e0;
      overflow-y: auto;
      display: none;
    }}
    
    #preview-area.active {{
      display: block;
    }}
    
    /* Split view */
    #split-view {{
      display: none;
      flex: 1;
    }}
    
    #split-view.active {{
      display: flex;
    }}
    
    #split-edit {{
      flex: 1;
      padding: 20px;
      background: #121212;
      border-right: 1px solid #373e47;
    }}
    
    #split-preview {{
      flex: 1;
      padding: 20px;
      background: #141414;
      overflow-y: auto;
    }}
    
    /* Editor styles */
    #editor {{
      width: 100%;
      height: 100%;
      min-height: 500px;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      background: #22272e;
      color: #c9d1d9;
      border: 1px solid #373e47;
      border-radius: 6px;
      padding: 16px;
      font-size: 14px;
      line-height: 1.6;
      resize: none;
      tab-size: 2;
      outline: none;
    }}
    
    #editor:focus {{
      border-color: #0066cc;
      box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.2);
    }}
    
    /* Status bar */
    #status-bar {{
      background: #1c1c1c;
      border-top: 1px solid #373e47;
      padding: 8px 20px;
      font-size: 12px;
      color: #666;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    
    #validation-feedback {{
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
    }}
    
    .feedback-success {{ background: #1e3a1e; color: #4caf50; }}
    .feedback-warning {{ background: #3a2e1e; color: #ff9800; }}
    .feedback-error {{ background: #3a1e1e; color: #f44336; }}
    
    /* ORMD Link Styles */
    .ormd-link {{ 
      padding: 2px 6px; 
      border-radius: 4px; 
      text-decoration: underline; 
      font-weight: 500; 
    }}
    .ormd-link-supports {{ 
      background: #e3f6e3; 
      color: #217a21; 
      border: 1px solid #b6e6b6; 
    }}
    .ormd-link-refutes {{ 
      background: #ffeaea; 
      color: #b80000; 
      border: 1px solid #ffb3b3; 
    }}
    .ormd-link-related {{ 
      background: #eaf4ff; 
      color: #1a4d80; 
      border: 1px solid #b3d1ff; 
    }}
    .ormd-link-undefined {{ 
      background: #f9e6e6; 
      color: #a94442; 
      border: 1px solid #e4b9b9; 
    }}
    
    pre, code {{
      background: #22272e;
      border: 1px solid #373e47;
      border-radius: 4px;
      padding: 8px;
      font-size: 0.95em;
      overflow-x: auto;
      color: #c9d1d9;
    }}
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {{
      #toolbar {{
        padding: 8px 12px;
        flex-direction: column;
        align-items: stretch;
      }}
      
      #toolbar h1 {{
        font-size: 1.1em;
        margin-bottom: 8px;
      }}
      
      #sidebar {{
        position: absolute;
        z-index: 10;
        height: 100%;
        left: 0;
        top: 0;
      }}
      
      #split-view.active {{
        flex-direction: column;
      }}
      
      #split-edit {{
        border-right: none;
        border-bottom: 1px solid #373e47;
      }}
    }}
  </style>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/js-yaml@4.1.0/dist/js-yaml.min.js"></script>
</head>
<body>
  <div id="toolbar">
    <h1>{title} <span style="color: #666; font-weight: normal;">[EDIT]</span></h1>
    
    <button onclick="saveToOriginal()" class="btn btn-primary" title="Save changes to original file">
      💾 Save
    </button>
    
    <button onclick="downloadCopy()" class="btn btn-secondary" title="Download a copy">
      ⬇️ Download
    </button>
    
    <div style="border-left: 1px solid #555; height: 24px; margin: 0 8px;"></div>
    
    <button id="edit-btn" onclick="showEdit()" class="btn btn-toggle active">
      ✏️ Edit
    </button>
    
    <button id="preview-btn" onclick="showPreview()" class="btn btn-toggle">
      👁️ Preview
    </button>
    
    <button id="split-btn" onclick="showSplit()" class="btn btn-toggle">
      ⚡ Split
    </button>
    
    <div style="border-left: 1px solid #555; height: 24px; margin: 0 8px;"></div>
    
    <button onclick="toggleSidebar()" class="btn btn-tertiary" id="sidebar-toggle">
      📋 Info
    </button>
  </div>

  <div id="container">
    <div id="sidebar" class="collapsed">
      <nav>
        <button id="toggle-raw" class="active">📄 Raw</button>
        <button id="toggle-history">📝 Info</button>
        <button id="toggle-help">❓ Help</button>
      </nav>
      
      <div id="panel-raw" class="panel active">
        <h3>📄 Raw ORMD</h3>
        <pre id="raw-content" style="font-size: 11px; max-height: 300px; overflow-y: auto;">{raw_ormd_escaped}</pre>
      </div>
      
      <div id="panel-history" class="panel">
        <h3>📝 Document Info</h3>
        <div id="history-content">{history}</div>
      </div>
      
      <div id="panel-help" class="panel">
        <h3>❓ Keyboard Shortcuts</h3>
        <div style="font-size: 12px; line-height: 1.6;">
          <div><kbd>Ctrl+S</kbd> Save to file</div>
          <div><kbd>Ctrl+D</kbd> Download copy</div>
          <div><kbd>Ctrl+P</kbd> Toggle preview</div>
          <div><kbd>Ctrl+\</kbd> Split view</div>
          <div><kbd>Tab</kbd> Insert 2 spaces</div>
        </div>
      </div>
    </div>
    
    <div id="main-content">
      <!-- Edit Mode -->
      <div id="edit-area" class="active">
        <textarea id="editor" placeholder="Enter your ORMD content here...">{raw_ormd_escaped}</textarea>
      </div>
      
      <!-- Preview Mode -->
      <div id="preview-area">
        <div id="preview-content">{main_html}</div>
      </div>
      
      <!-- Split Mode -->
      <div id="split-view">
        <div id="split-edit">
          <textarea id="editor-split" placeholder="Enter your ORMD content here...">{raw_ormd_escaped}</textarea>
        </div>
        <div id="split-preview">
          <div id="split-preview-content">{main_html}</div>
        </div>
      </div>
    </div>
  </div>
  
  <div id="status-bar">
    <div>
      <span id="char-count">0 characters</span>
      <span style="margin-left: 16px;" id="auto-save-status"></span>
    </div>
    <div id="validation-feedback"></div>
  </div>
  
  <script>
    let originalContent = document.getElementById('editor').value;
    let isModified = false;
    let autoSaveTimer = null;
    let currentMode = 'edit'; // 'edit', 'preview', 'split'
    
    // Get the active editor (depends on current mode)
    function getActiveEditor() {{
      return currentMode === 'split' ? document.getElementById('editor-split') : document.getElementById('editor');
    }}
    
    // Panel switching logic for sidebar
    const panels = ['raw', 'history', 'help'];
    panels.forEach(name => {{
      document.getElementById('toggle-' + name).onclick = () => {{
        panels.forEach(n => {{
          document.getElementById('toggle-' + n).classList.remove('active');
          document.getElementById('panel-' + n).classList.remove('active');
        }});
        document.getElementById('toggle-' + name).classList.add('active');
        document.getElementById('panel-' + name).classList.add('active');
      }};
    }});
    
    // View mode switching
    function showEdit() {{
      currentMode = 'edit';
      updateViewMode();
      syncEditorContent();
      getActiveEditor().focus();
    }}
    
    function showPreview() {{
      currentMode = 'preview';
      updateViewMode();
      updatePreview();
    }}
    
    function showSplit() {{
      currentMode = 'split';
      updateViewMode();
      syncEditorContent();
      updatePreview();
      document.getElementById('editor-split').focus();
    }}
    
    function updateViewMode() {{
      // Hide all modes
      document.getElementById('edit-area').classList.remove('active');
      document.getElementById('preview-area').classList.remove('active');
      document.getElementById('split-view').classList.remove('active');
      
      // Remove active from all buttons
      document.getElementById('edit-btn').classList.remove('active');
      document.getElementById('preview-btn').classList.remove('active');
      document.getElementById('split-btn').classList.remove('active');
      
      // Show current mode
      if (currentMode === 'edit') {{
        document.getElementById('edit-area').classList.add('active');
        document.getElementById('edit-btn').classList.add('active');
      }} else if (currentMode === 'preview') {{
        document.getElementById('preview-area').classList.add('active');
        document.getElementById('preview-btn').classList.add('active');
      }} else if (currentMode === 'split') {{
        document.getElementById('split-view').classList.add('active');
        document.getElementById('split-btn').classList.add('active');
      }}
    }}
    
    function syncEditorContent() {{
      const mainEditor = document.getElementById('editor');
      const splitEditor = document.getElementById('editor-split');
      
      if (currentMode === 'split') {{
        splitEditor.value = mainEditor.value;
      }} else {{
        mainEditor.value = splitEditor.value;
      }}
    }}
    
    function toggleSidebar() {{
      const sidebar = document.getElementById('sidebar');
      sidebar.classList.toggle('collapsed');
      
      const btn = document.getElementById('sidebar-toggle');
      btn.textContent = sidebar.classList.contains('collapsed') ? '📋 Info' : '✖️ Close';
    }}
    
    // Editor event handlers
    function setupEditor(editor) {{
      editor.addEventListener('input', function() {{
        isModified = true;
        document.title = '● ' + document.title.replace('● ', '');
        
        clearTimeout(autoSaveTimer);
        autoSaveTimer = setTimeout(autoSave, 2000);
        
        updateCharCount();
        validateContent();
        
        if (currentMode === 'split') {{
          updatePreview();
        }}
      }});
      
      // Tab key handling
      editor.addEventListener('keydown', function(e) {{
        if (e.key === 'Tab') {{
          e.preventDefault();
          const start = editor.selectionStart;
          const end = editor.selectionEnd;
          editor.value = editor.value.substring(0, start) + '  ' + editor.value.substring(end);
          editor.selectionStart = editor.selectionEnd = start + 2;
        }}
      }});
    }}
    
    setupEditor(document.getElementById('editor'));
    setupEditor(document.getElementById('editor-split'));
    
    function autoSave() {{
      const content = getActiveEditor().value;
      localStorage.setItem('ormd-autosave-{file_path_safe}', content);
      document.getElementById('auto-save-status').textContent = 
        '📁 Auto-saved at ' + new Date().toLocaleTimeString();
    }}
    
    function updateCharCount() {{
      const content = getActiveEditor().value;
      document.getElementById('char-count').textContent = 
        content.length + ' characters, ' + content.split('\\n').length + ' lines';
    }}
    
    function saveToOriginal() {{
      const content = getActiveEditor().value;
      
      // Use modern File System Access API if available
      if ('showSaveFilePicker' in window) {{
        saveWithFilePicker(content, '{file_name}');
      }} else {{
        // Fallback - show instructions
        showFeedback('warning', '💾 Copy the content and save manually to: {file_name}');
        // Also trigger download as backup
        downloadCopy();
      }}
    }}
    
    function downloadCopy() {{
      const content = getActiveEditor().value;
      const timestamp = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '-');
      const fileName = '{file_name}'.replace('.ormd', `_${{timestamp}}.ormd`);
      
      const blob = new Blob([content], {{ type: 'text/plain' }});
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      a.click();
      
      URL.revokeObjectURL(url);
      showFeedback('success', '⬇️ Downloaded copy as ' + fileName);
    }}
    
    async function saveWithFilePicker(content, suggestedName) {{
      try {{
        const fileHandle = await window.showSaveFilePicker({{
          suggestedName: suggestedName,
          types: [
            {{
              description: 'ORMD files',
              accept: {{ 'text/plain': ['.ormd'] }}
            }}
          ]
        }});
        
        const writable = await fileHandle.createWritable();
        await writable.write(content);
        await writable.close();
        
        isModified = false;
        document.title = document.title.replace('● ', '');
        showFeedback('success', '💾 Saved successfully');
        
      }} catch (err) {{
        if (err.name !== 'AbortError') {{
          showFeedback('error', '❌ Save failed: ' + err.message);
        }}
      }}
    }}
    
    function updatePreview() {{
      const content = getActiveEditor().value;
      
      // Update raw content panel
      document.getElementById('raw-content').textContent = content;
      
      // Parse ORMD content
      const parsed = parseORMD(content);
      
      // Render markdown with ORMD features
      const renderedHTML = renderORMDContent(parsed);
      
      // Update preview element
      const previewElement = currentMode === 'split' ? 
        document.getElementById('split-preview-content') : 
        document.getElementById('preview-content');
      
      previewElement.innerHTML = renderedHTML;
    }}
    
    function parseORMD(content) {{
      // Parse ORMD document
      const result = {{
        frontMatter: {{}},
        body: '',
        links: [],
        isValid: false,
        errors: []
      }};
      
      if (!content.trim()) {{
        result.errors.push('Document is empty');
        return result;
      }}
      
      // Check for ORMD version tag
      if (!content.startsWith('<!-- ormd:0.1 -->')) {{
        result.errors.push('Missing ORMD version tag');
        return result;
      }}
      
      const lines = content.split('\\n');
      let frontMatterStart = -1;
      let frontMatterEnd = -1;
      let delimiter = '';
      
      // Find front-matter block
      for (let i = 1; i < lines.length; i++) {{
        const line = lines[i].trim();
        if (line === '+++' || line === '---') {{
          if (frontMatterStart === -1) {{
            frontMatterStart = i;
            delimiter = line;
          }} else if (line === delimiter) {{
            frontMatterEnd = i;
            break;
          }}
        }}
      }}
      
      if (frontMatterStart === -1 || frontMatterEnd === -1) {{
        result.errors.push('Invalid or missing front-matter block');
        return result;
      }}
      
      // Extract front-matter YAML
      const frontMatterYaml = lines.slice(frontMatterStart + 1, frontMatterEnd).join('\\n');
      try {{
        if (typeof jsyaml !== 'undefined') {{
          result.frontMatter = jsyaml.load(frontMatterYaml) || {{}};
        }} else {{
          // Fallback simple YAML parser for basic cases
          result.frontMatter = parseSimpleYaml(frontMatterYaml);
        }}
        result.links = result.frontMatter.links || [];
      }} catch (e) {{
        result.errors.push('Invalid YAML in front-matter: ' + e.message);
        return result;
      }}
      
      // Extract body
      result.body = lines.slice(frontMatterEnd + 1).join('\\n').trim();
      result.isValid = true;
      
      return result;
    }}
    
    function renderORMDContent(parsed) {{
      if (!parsed.isValid) {{
        return '<div style="padding: 20px; background: #3a1e1e; color: #f44336; border-radius: 6px; margin-bottom: 20px;">' +
          '<h3>❌ Parsing Errors</h3>' +
          '<ul>' + parsed.errors.map(error => '<li>' + escapeHtml(error) + '</li>').join('') + '</ul>' +
          '</div>';
      }}
      
      // Process semantic links in body
      let processedBody = parsed.body;
      
      // Replace [[link-id]] with actual links
      processedBody = processedBody.replace(/\\[\\[([^\\]]+)\\]\\]/g, (match, linkId) => {{
        const link = parsed.links.find(l => l.id === linkId);
        if (link) {{
          const rel = link.rel || 'related';
          const to = link.to || '#' + linkId;
          return `<a href="${{escapeHtml(to)}}" class="ormd-link ormd-link-${{escapeHtml(rel)}}">${{escapeHtml(linkId)}}</a>`;
        }} else {{
          return `<span class="ormd-link ormd-link-undefined">${{escapeHtml(linkId)}}</span>`;
        }}
      }});
      
      // Render markdown
      let htmlContent = '';
      try {{
        htmlContent = marked.parse(processedBody);
      }} catch (e) {{
        return '<div style="padding: 20px; background: #3a1e1e; color: #f44336; border-radius: 6px;">' +
          '<h3>❌ Markdown Rendering Error</h3>' +
          '<p>' + escapeHtml(e.message) + '</p>' +
          '</div>';
      }}
      
      // Add front-matter info at the top
      let frontMatterHTML = '';
      if (parsed.frontMatter.title) {{
        frontMatterHTML += '<div style="padding: 16px; background: #1a1a1a; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #004080;">';
        frontMatterHTML += '<h2 style="margin: 0 0 8px 0; color: #0066cc;">📄 ' + escapeHtml(parsed.frontMatter.title) + '</h2>';
        
        if (parsed.frontMatter.authors && parsed.frontMatter.authors.length > 0) {{
          frontMatterHTML += '<p style="margin: 4px 0; color: #ccc;">👤 ' + 
            parsed.frontMatter.authors.map(author => 
              typeof author === 'string' ? author : (author.display || author.id)
            ).join(', ') + '</p>';
        }}
        
        if (parsed.links.length > 0) {{
          frontMatterHTML += '<p style="margin: 4px 0; color: #ccc;">🔗 ' + parsed.links.length + ' semantic link(s)</p>';
        }}
        
        if (parsed.frontMatter.permissions) {{
          const perms = parsed.frontMatter.permissions;
          frontMatterHTML += '<p style="margin: 4px 0; color: #ccc;">🔒 Mode: ' + (perms.mode || 'draft') + 
            ', Editable: ' + (perms.editable !== false) + 
            ', Signed: ' + (perms.signed === true) + '</p>';
        }}
        
        frontMatterHTML += '</div>';
      }}
      
      return frontMatterHTML + htmlContent;
    }}
    
    function escapeHtml(text) {{
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }}
    
    function parseSimpleYaml(yamlText) {{
      // Very basic YAML parser for simple front-matter
      // This handles basic key-value pairs and simple lists
      const result = {{}};
      const lines = yamlText.split('\\n');
      let currentKey = null;
      let currentList = null;
      
      for (const line of lines) {{
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        
        if (line.startsWith('  - ') && currentList) {{
          // List item
          const value = line.substring(4).trim();
          if (value.includes(':')) {{
            // Object in list
            const obj = {{}};
            const parts = value.split(':');
            obj[parts[0].trim()] = parts[1].trim();
            currentList.push(obj);
          }} else {{
            currentList.push(value);
          }}
        }} else if (line.includes(':')) {{
          // Key-value pair
          const colonIndex = line.indexOf(':');
          const key = line.substring(0, colonIndex).trim();
          const value = line.substring(colonIndex + 1).trim();
          
          if (value === '' || value === '[]') {{
            // Empty value or empty list
            result[key] = [];
            currentList = result[key];
            currentKey = key;
          }} else {{
            result[key] = value;
            currentList = null;
            currentKey = null;
          }}
        }}
      }}
      
      return result;
    }}
    
    function validateContent() {{
      const content = getActiveEditor().value;
      
      if (!content.trim()) {{
        showFeedback('warning', '⚠️ Document is empty');
        return false;
      }}
      
      if (!content.startsWith('<!-- ormd:0.1 -->')) {{
        showFeedback('error', '❌ Missing ORMD version tag');
        return false;
      }}
      
      if (!content.includes('+++') && !content.includes('---')) {{
        showFeedback('error', '❌ Missing front-matter block');
        return false;
      }}
      
      showFeedback('success', '✅ Valid ORMD format');
      return true;
    }}
    
    function showFeedback(type, message) {{
      const feedback = document.getElementById('validation-feedback');
      feedback.className = 'feedback-' + type;
      feedback.textContent = message;
    }}
    
    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {{
      if (e.ctrlKey) {{
        switch(e.key) {{
          case 's':
            e.preventDefault();
            saveToOriginal();
            break;
          case 'd':
            e.preventDefault();
            downloadCopy();
            break;
          case 'p':
            e.preventDefault();
            showPreview();
            break;
          case '\\\\':
            e.preventDefault();
            showSplit();
            break;
        }}
      }}
    }});
    
    // Prevent accidental navigation
    window.addEventListener('beforeunload', function(e) {{
      if (isModified) {{
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
      }}
    }});
    
    // Initialize
    window.addEventListener('load', function() {{
      // Load auto-saved content if available
      const autoSaved = localStorage.getItem('ormd-autosave-{file_path_safe}');
      if (autoSaved && autoSaved !== originalContent) {{
        if (confirm('Found auto-saved changes. Would you like to restore them?')) {{
          getActiveEditor().value = autoSaved;
          isModified = true;
          document.title = '● ' + document.title;
        }}
      }}
      
      updateCharCount();
      validateContent();
      updatePreview(); // Show initial preview
    }});
  </script>
</body>
</html>
    '''
    
    # Prepare template variables
    file_name = Path(file_path).name
    file_path_safe = file_path.replace('\\', '/').replace(' ', '_')  # Safe for localStorage key
    raw_ormd_escaped = raw_ormd.replace('<', '&lt;').replace('>', '&gt;')
    
    return editable_template.format(
        title=f"{title}",
        raw_ormd_escaped=raw_ormd_escaped,
        main_html=main_html,
        history=history,
        file_name=file_name,
        file_path_safe=file_path_safe
    )

def _serve_and_open(html_content, port, no_browser, file_path, title):
    """Start local server and optionally open browser"""
    
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

if __name__ == '__main__':
    cli()