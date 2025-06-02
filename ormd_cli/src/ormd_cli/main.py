# src/ormd_cli/main.py
import click
from .validator import ORMDValidator
from .packager import ORMDPackager
from .updater import ORMDUpdater
from typing import Optional
import io # Changed from 'from io import StringIO' to just 'import io'
from .updater import ORMDUpdater
from typing import Optional
import io
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextBoxHorizontal
from pdfminer.pdfparser import PDFParser, PDFSyntaxError # Added PDFParser
from pdfminer.pdfdocument import PDFDocument # Added PDFDocument
from pdfminer.psparser import PSKeyword, PSLiteral # Added for decoding
from pdfminer.utils import decode_text # Added for decoding
import markdown
import yaml
from pathlib import Path
from datetime import datetime, timezone, timedelta # Added timedelta
from .utils import HTML_TEMPLATE, SYMBOLS
from .parser import parse_document, serialize_front_matter, _parse_front_matter_and_body
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
@click.argument('input_file_path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('output_ormd_path', type=click.Path(dir_okay=False, resolve_path=True))
@click.option('--input-format', '-f', type=click.Choice(['txt', 'md', 'pdf'], case_sensitive=False), help='Specify the input file format.') # Added 'pdf'
def convert(input_file_path: str, output_ormd_path: str, input_format: Optional[str]):
    """Convert a file (e.g. TXT, MD, PDF) to an ORMD file."""
    try:
        input_p = Path(input_file_path)
        output_p = Path(output_ormd_path)

        # Determine format
        effective_input_format = input_format
        if not effective_input_format:
            effective_input_format = input_p.suffix.lower().lstrip('.')

        click.echo(f"{SYMBOLS['info']} Starting conversion...")
        click.echo(f"  Input file: {input_file_path}")
        click.echo(f"  Output ORMD file: {output_ormd_path}")
        click.echo(f"  Detected input format: {effective_input_format if effective_input_format else 'unknown (will attempt .txt)'}")

        if effective_input_format == 'txt':
            click.echo(f"  Converting from TXT to ORMD...")

            # Read TXT content
            with click.open_file(input_p, 'r', encoding='utf-8') as f:
                txt_content = f.read()

            # Derive title
            title = input_p.stem.replace('-', ' ').replace('_', ' ').title()
            now_utc_iso = datetime.now(timezone.utc).isoformat()

            front_matter_data = {
                "title": title,
                "authors": [],
                "dates": {
                    "created": now_utc_iso,
                    "modified": now_utc_iso,
                },
                "source_file": str(input_p.resolve()), # Absolute path
                "conversion_details": {
                    "from_format": "txt",
                    "conversion_date": now_utc_iso
                }
            }

            front_matter_string = serialize_front_matter(front_matter_data)
            ormd_content = f"<!-- ormd:0.1 -->\n{front_matter_string}\n{txt_content}"

            with click.open_file(output_p, 'w', encoding='utf-8') as f:
                f.write(ormd_content)

            click.echo(f"{SYMBOLS['success']} Successfully converted '{input_p.name}' to '{output_p.name}'")

        elif effective_input_format == 'md':
            click.echo(f"  Converting from MD to ORMD...")

            with click.open_file(input_p, 'r', encoding='utf-8') as f:
                md_content_full = f.read()

            body_content = "" # Initialize body_content
            existing_fm = {}  # Initialize existing_fm

            if md_content_full.strip().startswith("<!-- ormd:0.1 -->"):
                # File is likely already an ORMD file, parse it fully
                parsed_fm, parsed_body, _, parse_errors = parse_document(md_content_full)
                if parse_errors: # Still try to proceed if only minor errors
                    click.echo(f"{SYMBOLS['warning']} Input ORMD-like file has parsing issues:")
                    for error in parse_errors: click.echo(f"    {SYMBOLS['bullet']} {error}")
                if parsed_fm is not None: # if major parsing error, parsed_fm might be None
                    existing_fm = parsed_fm
                body_content = parsed_body # Use body from full parse
            else:
                # Plain MD file, try to get its front-matter and body
                raw_fm, plain_body = _parse_front_matter_and_body(md_content_full)
                existing_fm = raw_fm if raw_fm is not None else {}
                body_content = plain_body

            now_utc_iso = datetime.now(timezone.utc).isoformat()
            default_title = input_p.stem.replace('-', ' ').replace('_', ' ').title()

            # Initialize new front-matter with defaults
            new_fm = {
                "title": default_title,
                "authors": [],
                "dates": { # Default 'created' and 'modified' to now
                    "created": now_utc_iso,
                    "modified": now_utc_iso,
                },
                "source_file": str(input_p.resolve()),
                "conversion_details": {
                    "from_format": "md",
                    "conversion_date": now_utc_iso
                }
            }

            # Merge existing_fm into new_fm
            # Existing fields take precedence, except for special handling for 'dates'
            # and ensuring 'source_file' & 'conversion_details' are from the conversion process.
            if existing_fm:
                for key, value in existing_fm.items():
                    if key == "dates":
                        if isinstance(value, dict):
                            new_fm["dates"]["created"] = value.get("created", new_fm["dates"]["created"])
                            # new_fm["dates"]["modified"] is already set to now_utc_iso
                    elif key not in ["source_file", "conversion_details"]:
                        new_fm[key] = value

                # If 'dates' object was not in existing_fm, check for root 'date' or 'created'
                if "dates" not in existing_fm:
                    if "date" in existing_fm:
                        new_fm["dates"]["created"] = existing_fm["date"] # Override default 'created'
                    elif "created" in existing_fm: # A root 'created' field
                        new_fm["dates"]["created"] = existing_fm["created"] # Override default 'created'

            # Ensure 'authors' is a list. If overridden by a non-list, reset.
            if not isinstance(new_fm.get("authors"), list):
                click.echo(f"{SYMBOLS['warning']} Existing 'authors' field was not a list. Resetting to empty list.")
                new_fm["authors"] = []

            # Ensure title is present, if existing_fm didn't have one, default_title is used.
            # If existing_fm had a title, it would have overwritten the default.
            if not new_fm.get("title"): # Should not happen if default_title is always set.
                 new_fm["title"] = default_title


            final_fm_string = serialize_front_matter(new_fm)
            # Ensure body_content doesn't start with newlines if it was empty after FM.
            ormd_content = f"<!-- ormd:0.1 -->\n{final_fm_string}\n{body_content.lstrip()}"


            with click.open_file(output_p, 'w', encoding='utf-8') as f:
                f.write(ormd_content)

            click.echo(f"{SYMBOLS['success']} Successfully converted '{input_p.name}' to '{output_p.name}'")

        elif effective_input_format == 'pdf':
            click.echo(f"  PDF conversion selected for '{input_p.name}'.")

            # --- Metadata Extraction ---
            pdf_meta = {}
            try:
                # Using click.open_file for consistency, as PDFParser needs a binary file object.
                with click.open_file(input_file_path, 'rb') as fp:
                    parser = PDFParser(fp)
                    doc = PDFDocument(parser)
                    if doc.info and isinstance(doc.info, list) and len(doc.info) > 0:
                        raw_info = doc.info[0]
                        for k, v_obj in raw_info.items():
                            key_str = decode_text(k) if isinstance(k, bytes) else str(k)
                            if isinstance(v_obj, (PSLiteral, PSKeyword)):
                                value_str = decode_text(v_obj.name)
                            elif isinstance(v_obj, bytes):
                                value_str = decode_text(v_obj)
                            else:
                                value_str = str(v_obj)
                            pdf_meta[key_str] = value_str
                        click.echo(f"    {SYMBOLS['info']} Extracted PDF metadata keys: {list(pdf_meta.keys())}")
            except PDFSyntaxError as e:
                 click.echo(f"{SYMBOLS['error']} Failed to parse PDF for metadata (PDFSyntaxError): {e}. Ensure it's a valid PDF.")
                 exit(1)
            except Exception as e:
                click.echo(f"{SYMBOLS['warning']} Could not extract metadata from PDF (general error): {e}")

            # --- Text Extraction (Layout Analysis) ---
            extracted_text_blocks = []
            pdf_body_content = ""
            try:
                laparams = LAParams()
                for page_layout in extract_pages(input_file_path, laparams=laparams):
                    for element in page_layout:
                        if isinstance(element, LTTextBoxHorizontal):
                            extracted_text_blocks.append(element.get_text())
                pdf_body_content = "\n\n".join(extracted_text_blocks).strip()
                click.echo(f"    {SYMBOLS['success']} Successfully processed PDF text using layout analysis.")
            except PDFSyntaxError as e:
                click.echo(f"{SYMBOLS['error']} Failed to process PDF for text extraction (PDFSyntaxError): {e}. Ensure it's a valid PDF.")
                exit(1)
            except Exception as e:
                click.echo(f"{SYMBOLS['error']} Failed to process PDF file '{input_p.name}' for text extraction: {e}")
                exit(1)

            # --- Front-matter Population ---
            now_utc_iso = datetime.now(timezone.utc).isoformat()
            default_title = input_p.stem.replace('-', ' ').replace('_', ' ').title()

            title = pdf_meta.get('Title', default_title)
            if not title or not isinstance(title, str) or title.isspace():
                title = default_title

            authors = []
            pdf_author_str = pdf_meta.get('Author')
            if pdf_author_str and isinstance(pdf_author_str, str) and not pdf_author_str.isspace():
                if any(delim in pdf_author_str for delim in [',', ';', '&']):
                    authors = [a.strip() for a in re.split(r'[,;&]+', pdf_author_str) if a.strip()]
                else:
                    authors.append(pdf_author_str)

            keywords = []
            pdf_keywords_str = pdf_meta.get('Keywords')
            if pdf_keywords_str and isinstance(pdf_keywords_str, str) and not pdf_keywords_str.isspace():
                keywords = [kw.strip() for kw in re.split(r'[,;\s]+', pdf_keywords_str) if kw.strip()]

            created_date_iso = _parse_pdf_date_string(pdf_meta.get('CreationDate')) or now_utc_iso
            modified_date_iso = _parse_pdf_date_string(pdf_meta.get('ModDate')) or now_utc_iso

            front_matter_data = {
                "title": title,
                "authors": authors,
                "keywords": keywords if keywords else [],
                "dates": {
                    "created": created_date_iso,
                    "modified": modified_date_iso,
                },
                "source_file": str(input_p.resolve()),
                "conversion_details": {
                    "from_format": "pdf",
                    "conversion_date": now_utc_iso,
                    "extraction_method": "pdfminer.six layout analysis (paragraphs)",
                    "source_metadata_fields": list(pdf_meta.keys())
                }
            }
            if pdf_meta.get('ModDate') and modified_date_iso != now_utc_iso:
                 front_matter_data["conversion_details"]["source_modified_date"] = modified_date_iso

            front_matter_string = serialize_front_matter(front_matter_data)
            ormd_content = f"<!-- ormd:0.1 -->\n{front_matter_string}\n{pdf_body_content}"

            with click.open_file(output_p, 'w', encoding='utf-8') as f:
                f.write(ormd_content)

            click.echo(f"{SYMBOLS['success']} Successfully converted PDF '{input_p.name}' to ORMD file '{output_p.name}'")

        else:
            click.echo(f"{SYMBOLS['error']} Unsupported input format: '{effective_input_format}'. Only 'txt', 'md', and 'pdf' are supported.")
            click.echo(f"Please specify format with --input-format (e.g., txt, md, pdf).")
            exit(1)

    except Exception as e:
        click.echo(f"{SYMBOLS['error']} Failed during conversion: {str(e)}")
        exit(1)

# Helper function to parse PDF date strings
def _parse_pdf_date_string(pdf_date_str: str) -> Optional[str]:
    if not pdf_date_str or not isinstance(pdf_date_str, (str, bytes)):
        return None

    if isinstance(pdf_date_str, bytes):
        try:
            pdf_date_str = pdf_date_str.decode('utf-8', 'surrogateescape')
        except UnicodeDecodeError:
            return None # Cannot decode

    if pdf_date_str.startswith("D:"):
        pdf_date_str = pdf_date_str[2:]

    # Regex to capture YYYYMMDDHHMMSS and optional timezone offset
    # D:YYYYMMDDHHMMSSOHH'mm' (O is +, -, or Z)
    match = re.match(
        r"(\d{4})(\d{2})?(\d{2})?(\d{2})?(\d{2})?(\d{2})?" # Year, Month, Day, Hour, Minute, Second
        r"([Zz])?" # Z for UTC
        r"([+\-])?(\d{2})?'?(\d{2})?'?", # Timezone offset like +02'00' or -0500
        pdf_date_str
    )

    if not match:
        return None

    parts = match.groups()

    year = int(parts[0])
    month = int(parts[1] or 1)
    day = int(parts[2] or 1)
    hour = int(parts[3] or 0)
    minute = int(parts[4] or 0)
    second = int(parts[5] or 0)

    dt = datetime(year, month, day, hour, minute, second)

    utc_char = parts[6]
    offset_sign_char = parts[7]
    offset_hour_str = parts[8]
    offset_min_str = parts[9]

    if utc_char: # 'Z' means UTC
        dt = dt.replace(tzinfo=timezone.utc)
    elif offset_sign_char and offset_hour_str:
        offset_hours = int(offset_hour_str)
        offset_minutes = int(offset_min_str or 0)
        offset_delta = timedelta(hours=offset_hours, minutes=offset_minutes)
        if offset_sign_char == '-':
            offset_delta = -offset_delta

        dt = dt.replace(tzinfo=timezone(offset_delta))
        dt = dt.astimezone(timezone.utc) # Convert to UTC
    else:
        # No timezone info, assume UTC as a fallback, or local (pdfminer might imply local)
        # For consistency, let's assume UTC if no offset, though PDF spec implies local.
        # This might need refinement based on how source PDFs typically store dates.
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.isoformat().replace("+00:00", "Z")


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

    # Render Markdown to HTML with syntax highlighting
    main_html = markdown.markdown(
        body, 
        extensions=['extra', 'toc', 'sane_lists', 'codehilite'], 
        extension_configs={
            'codehilite': {
                'css_class': 'codehilite',
                'guess_lang': True,
                'use_pygments': True
            },
            'toc': {
                'permalink': True
            }
        }
    )

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
    
    # Render Markdown to HTML with syntax highlighting
    main_html = markdown.markdown(
        processed_body, 
        extensions=['extra', 'toc', 'sane_lists', 'codehilite'], 
        extension_configs={
            'codehilite': {
                'css_class': 'codehilite',
                'guess_lang': True,
                'use_pygments': True
            },
            'toc': {
                'permalink': True
            }
        }
    )
    
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
    
    # Render Markdown to HTML with syntax highlighting
    main_html = markdown.markdown(
        processed_body, 
        extensions=['extra', 'toc', 'sane_lists', 'codehilite'], 
        extension_configs={
            'codehilite': {
                'css_class': 'codehilite',
                'guess_lang': True,
                'use_pygments': True
            },
            'toc': {
                'permalink': True
            }
        }
    )
    
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
      scroll-behavior: smooth;
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
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      background: #0d1117;
      color: #c9d1d9;
      border: 1px solid #30363d;
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
    
    #editor-split {{
      width: 100%;
      height: 100%;
      min-height: 400px;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      background: #0d1117;
      color: #c9d1d9;
      border: 1px solid #30363d;
      border-radius: 6px;
      padding: 16px;
      font-size: 14px;
      line-height: 1.6;
      resize: none;
      tab-size: 2;
      outline: none;
    }}
    
    #editor-split:focus {{
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
    
    /* Enhanced Code Block Styles - Same as main template */
    pre {{
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 6px;
      padding: 16px;
      font-size: 14px;
      line-height: 1.45;
      overflow-x: auto;
      color: #c9d1d9;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      margin: 16px 0;
    }}
    
    code {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 3px;
      padding: 2px 6px;
      font-size: 0.9em;
      color: #f85149;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    }}
    
    pre code {{
      background: transparent;
      border: none;
      padding: 0;
      color: inherit;
      border-radius: 0;
    }}
    
    /* Syntax highlighting for common languages */
    .codehilite .k {{ color: #ff7b72; }} /* keyword */
    .codehilite .s {{ color: #a5d6ff; }} /* string */
    .codehilite .nb {{ color: #79c0ff; }} /* builtin */
    .codehilite .nf {{ color: #d2a8ff; }} /* function */
    .codehilite .c {{ color: #8b949e; }} /* comment */
    .codehilite .mi {{ color: #79c0ff; }} /* number */
    .codehilite .o {{ color: #ff7b72; }} /* operator */
    
    /* YAML/ORMD specific highlighting */
    .language-yaml .na {{ color: #79c0ff; }} /* attribute name */
    .language-yaml .s {{ color: #a5d6ff; }} /* string */
    .language-ormd .nc {{ color: #f85149; }} /* comment tag */
    
    /* ORMD Link Styles - Enhanced for dark theme */
    .ormd-link {{ 
      padding: 3px 8px; 
      border-radius: 4px; 
      text-decoration: none; 
      font-weight: 500; 
      transition: all 0.2s ease;
      border: 1px solid transparent;
    }}
    .ormd-link:hover {{
      transform: translateY(-1px);
      box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }}
    .ormd-link-supports {{ 
      background: #1a4d1a; 
      color: #7dd87d; 
      border-color: #4d7c4d; 
    }}
    .ormd-link-supports:hover {{
      background: #2e6b2e;
      color: #a3e8a3;
    }}
    .ormd-link-refutes {{ 
      background: #4d1a1a; 
      color: #ff7d7d; 
      border-color: #7c4d4d; 
    }}
    .ormd-link-refutes:hover {{
      background: #6b2e2e;
      color: #ffa3a3;
    }}
    .ormd-link-related {{ 
      background: #1a3d4d; 
      color: #7dc7ff; 
      border-color: #4d6d7c; 
    }}
    .ormd-link-related:hover {{
      background: #2e576b;
      color: #a3d8ff;
    }}
    .ormd-link-undefined {{ 
      background: #4d3d1a; 
      color: #ffb366; 
      border-color: #7c6d4d; 
    }}
    .ormd-link-undefined:hover {{
      background: #6b562e;
      color: #ffc999;
    }}

    /* Main content typography improvements */
    #preview-area h1, #preview-area h2, #preview-area h3, #preview-area h4, #preview-area h5, #preview-area h6,
    #split-preview h1, #split-preview h2, #split-preview h3, #split-preview h4, #split-preview h5, #split-preview h6 {{
      color: #ffffff;
      margin-top: 24px;
      margin-bottom: 16px;
      line-height: 1.25;
    }}
    
    #preview-area h1, #split-preview h1 {{ border-bottom: 1px solid #30363d; padding-bottom: 10px; }}
    #preview-area h2, #split-preview h2 {{ border-bottom: 1px solid #30363d; padding-bottom: 8px; }}
    
    #preview-area p, #split-preview p {{
      line-height: 1.6;
      margin-bottom: 16px;
    }}
    
    #preview-area ul, #preview-area ol, #split-preview ul, #split-preview ol {{
      padding-left: 2em;
      margin-bottom: 16px;
    }}
    
    #preview-area li, #split-preview li {{
      margin-bottom: 4px;
    }}
    
    #preview-area blockquote, #split-preview blockquote {{
      border-left: 4px solid #30363d;
      padding-left: 16px;
      margin: 16px 0;
      color: #8b949e;
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
      
      // Add smooth scrolling for anchor links in preview
      addSmoothScrolling(previewElement);
    }}
    
    function addSmoothScrolling(container) {{
      container.addEventListener('click', function(e) {{
        if (e.target.tagName === 'A' && e.target.getAttribute('href') && e.target.getAttribute('href').startsWith('#')) {{
          e.preventDefault();
          const targetId = e.target.getAttribute('href').substring(1);
          const targetElement = container.querySelector('#' + targetId);
          if (targetElement) {{
            targetElement.scrollIntoView({{ behavior: 'smooth' }});
            // Highlight the target briefly
            const originalBg = targetElement.style.backgroundColor;
            targetElement.style.backgroundColor = '#004080';
            setTimeout(() => {{
              targetElement.style.backgroundColor = originalBg;
            }}, 1000);
          }}
        }}
      }});
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
      
      // Add smooth scrolling to initial preview content
      const previewArea = document.getElementById('preview-content');
      const splitPreviewArea = document.getElementById('split-preview-content');
      addSmoothScrolling(previewArea);
      addSmoothScrolling(splitPreviewArea);
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