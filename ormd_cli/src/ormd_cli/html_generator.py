import markdown
import json
import re
from pathlib import Path
from .utils import get_view_template, SYMBOLS

def get_edit_template() -> str:
    """Reads and returns the content of the edit_template.html file."""
    template_path = Path(__file__).parent / "templates" / "edit_template.html"
    try:
        return template_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return "<html><body><h1>Error: Edit template not found.</h1><p>Searched at: {}</p></body></html>".format(template_path.resolve())
    except Exception as e:
        return f"<html><body><h1>Error loading edit template: {e}</h1></body></html>"

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
    html_template_content = get_view_template() # Call the function from utils
    html = html_template_content.format(
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
    editable_template_str = get_edit_template() # Call the function now in this module

    # Prepare template variables
    file_name = Path(file_path).name
    file_path_safe = file_path.replace('\\', '/').replace(' ', '_')  # Safe for localStorage key
    raw_ormd_escaped = raw_ormd.replace('<', '&lt;').replace('>', '&gt;')

    return editable_template_str.format(
        title=f"{title}",
        raw_ormd_escaped=raw_ormd_escaped,
        main_html=main_html,
        history=history,
        file_name=file_name,
        file_path_safe=file_path_safe
    )

def generate_render_html(raw_ormd: str, front_matter: dict, body: str, links: list, meta: dict) -> str:
    """Generates HTML for the 'render' command."""
    title = front_matter.get('title', 'ORMD Document') if front_matter else 'ORMD Document'

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

    processed_body = re.sub(r'\[\[([^\]]+)\]\]', replace_link, body)
    # --- End semantic link rendering ---

    # Render Markdown to HTML with syntax highlighting
    main_html_content = markdown.markdown(
        processed_body,  # Use the link-processed body
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
    history_content = ''
    if meta:
        created = meta.get('created', '')
        modified = meta.get('modified', '')
        provenance = meta.get('provenance', {})
        history_content = f"<b>Created:</b> {created}<br><b>Modified:</b> {modified}<br>"
        if provenance:
            history_content += f"<b>Hash:</b> {provenance.get('hash', '')}<br>"
            history_content += f"<b>Signature Ref:</b> {provenance.get('sigRef', '')}<br>"
            history_content += f"<b>Timestamp:</b> {provenance.get('timestamp', '')}<br>"

    # Fill the HTML template
    template_str = get_view_template()
    html_output = template_str.format(
        title=title,
        raw_ormd=raw_ormd.replace('<', '&lt;').replace('>', '&gt;'),
        main_html=main_html_content,
        history=history_content
    )

    # Insert links data for D3.js graph (as a JS variable)
    links_json_str = json.dumps(links)
    # Replace any '// renderGraph(...);' line with the actual call
    final_html, n = re.subn(r'// renderGraph\(.*\);', f'renderGraph({links_json_str});', html_output)
    if n == 0:
        # If no placeholder was found, append the call at the end of the script
        final_html = html_output.replace('</script>', f'renderGraph({links_json_str});\n</script>')

    return final_html
