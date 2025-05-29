# src/ormd_cli/main.py
import click
from .validator import ORMDValidator
from .packager import ORMDPackager
import markdown
import yaml
from pathlib import Path
from .utils import HTML_TEMPLATE
import zipfile
import json

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
            click.echo(f"❌ Content file failed validation:")
            for error in validator.errors:
                click.echo(f"  • {error}")
            click.echo("Use --no-validate to skip validation")
            exit(1)
    
    packager = ORMDPackager()
    if packager.pack(content_file, meta_file, out):
        click.echo(f"✅ Created package: {out}")
    else:
        click.echo(f"❌ Failed to create package")
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
        click.echo(f"❌ Directory {out_dir} is not empty. Use --overwrite to force.")
        exit(1)
    
    packager = ORMDPackager()
    if packager.unpack(package_file, out_dir):
        click.echo(f"✅ Unpacked to: {out_dir}")
        
        # Show what was extracted
        if out_path.exists():
            files = list(out_path.iterdir())
            click.echo("Files extracted:")
            for file in sorted(files):
                click.echo(f"  • {file.name}")
    else:
        click.echo(f"❌ Failed to unpack {package_file}")
        exit(1)

def parse_ormd_content(content: str):
    """Parse ORMD content string into (front_matter, body)."""
    import yaml
    import re
    # Remove version tag if present
    content = content.strip()
    if content.startswith('<!-- ormd:0.1 -->'):
        content = content.split('-->', 1)[-1].lstrip()
    # Look for YAML front-matter
    if content.startswith('---\n'):
        parts = content.split('---\n', 2)
        if len(parts) >= 3:
            try:
                front_matter = yaml.safe_load(parts[1])
                body = parts[2]
                return front_matter, body
            except Exception:
                pass  # fall through to error
    # If parsing fails, return empty front_matter and all content as body
    return {"links": []}, content

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

    if is_zip:
        with zipfile.ZipFile(input_file, 'r') as zf:
            if 'content.ormd' in zf.namelist():
                raw_ormd = zf.read('content.ormd').decode('utf-8')
            if 'meta.json' in zf.namelist():
                meta = json.loads(zf.read('meta.json').decode('utf-8'))
    else:
        raw_ormd = Path(input_file).read_text(encoding='utf-8')

    # Unified parsing for both file and package
    front_matter, body = parse_ormd_content(raw_ormd)
    title = front_matter.get('title', title)
    links = front_matter.get('links', [])

    # --- Semantic link rendering ---
    import re
    def replace_link(match):
        link_id = match.group(1)
        link = next((l for l in links if l.get('id') == link_id), None)
        if link:
            rel = link.get('rel', 'related')
            to = link.get('to', f'#{link_id}')
            label = link_id
            return f'<a href="{to}" class="ormd-link ormd-link-{rel}">[[{label}]]</a>'
        else:
            return f'<span class="ormd-link ormd-link-undefined">[[{link_id}]]</span>'
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
    html = html.replace('</style>', '''
.ormd-link { padding: 2px 6px; border-radius: 4px; text-decoration: none; font-weight: 500; }
.ormd-link-supports { background: #e3f6e3; color: #217a21; border: 1px solid #b6e6b6; }
.ormd-link-refutes { background: #ffeaea; color: #b80000; border: 1px solid #ffb3b3; }
.ormd-link-related { background: #eaf4ff; color: #1a4d80; border: 1px solid #b3d1ff; }
.ormd-link-undefined { background: #f9e6e6; color: #a94442; border: 1px solid #e4b9b9; }
</style>''')

    # Insert links data for D3.js graph (as a JS variable)
    links_json = json.dumps(links)
    html = re.sub(r'(// renderGraph\(\[\{id: \'g1\', rel: \'supports\', to: \'#goal\'\}\]\);)', f'renderGraph({links_json});', html)

    # Determine output path
    if out is None:
        out = str(input_path.with_suffix('.html'))
    Path(out).write_text(html, encoding='utf-8')
    click.echo(f"✅ Rendered HTML written to: {out}")

if __name__ == '__main__':
    cli()