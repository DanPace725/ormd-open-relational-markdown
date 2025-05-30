"""Parsing utilities for ORMD documents."""
import re
import yaml
from typing import Tuple, Dict, Optional, List


def parse_document(content: str) -> Tuple[Optional[Dict], str, Optional[Dict[str, str]], List[str]]:
    """Parse full ORMD document content.

    Returns a tuple ``(front_matter, body, metadata, errors)``.
    ``front_matter`` will be ``None`` if YAML parsing fails.
    ``metadata`` is always ``None`` in the new schema (no more +++meta blocks).
    ``errors`` contains any parsing related warnings or errors.
    
    Note: The metadata parameter is kept for backward compatibility but will always be None
    since all metadata now goes in the front-matter YAML block.
    """
    errors: List[str] = []
    
    # Check for version tag at the beginning
    if not content.strip().startswith('<!-- ormd:0.1 -->'):
        errors.append("Missing or invalid version tag (expected at the beginning of the document)")
        return None, "", None, errors
    
    # Remove the version tag
    content_without_version = re.sub(r'^<!-- ormd:0\.1 -->\s*\n?', '', content, flags=re.MULTILINE)
    
    # Parse front-matter and body
    front_matter, body = _parse_front_matter_and_body(content_without_version)
    
    # Validate YAML if present
    if front_matter is None and content_without_version.strip().startswith(('---', '+++')):
        errors.append("Invalid YAML in front-matter")
        return None, body, None, errors
    
    # Convert empty front-matter to empty dict
    if front_matter is None:
        front_matter = {}
    
    # Note: metadata blocks (+++meta) are no longer supported
    # All metadata should be in the front-matter YAML block
    # Only warn if we find actual +++meta block patterns, not just the text "+++meta"
    if re.search(r'^[ ]*\+\+\+meta\b', body, re.MULTILINE):
        errors.append("Warning: +++meta blocks are deprecated. Please move all metadata to the front-matter YAML block.")
    
    return front_matter, body, None, errors


def _parse_front_matter_and_body(content: str) -> Tuple[Optional[Dict], str]:
    """Parse YAML front-matter and document body.
    
    Supports both --- and +++ delimiters for front-matter.
    Returns (front_matter_dict, body_content)
    """
    content = content.strip()
    
    # Check if content starts with front-matter delimiters
    if content.startswith('---\n'):
        return _extract_yaml_block(content, '---')
    elif content.startswith('+++\n'):
        return _extract_yaml_block(content, '+++')
    else:
        # No front-matter, entire content is body
        return None, content


def _extract_yaml_block(content: str, delimiter: str) -> Tuple[Optional[Dict], str]:
    """Extract YAML front-matter block with given delimiter."""
    lines = content.split('\n')
    
    if lines[0] != delimiter:
        return None, content
    
    # Find closing delimiter
    closing_line = None
    for i in range(1, len(lines)):
        if lines[i].strip() == delimiter:
            closing_line = i
            break
    
    if closing_line is None:
        # No closing delimiter found, treat as body content
        return None, content
    
    # Extract YAML content
    yaml_lines = lines[1:closing_line]
    yaml_content = '\n'.join(yaml_lines)
    
    # Extract body content (everything after closing delimiter)
    body_lines = lines[closing_line + 1:]
    body_content = '\n'.join(body_lines).strip()
    
    # Parse YAML
    try:
        if yaml_content.strip():
            front_matter = yaml.safe_load(yaml_content)
            if front_matter is None:
                front_matter = {}
        else:
            front_matter = {}
    except yaml.YAMLError:
        return None, body_content
    
    return front_matter, body_content


def migrate_legacy_metadata(front_matter: Dict, legacy_metadata: Optional[Dict[str, str]]) -> Dict:
    """Migrate legacy +++meta blocks to front-matter structure.
    
    This function helps migrate old documents that still have +++meta blocks
    by moving their content into the appropriate front-matter fields.
    """
    if not legacy_metadata:
        return front_matter
    
    migrated = front_matter.copy()
    
    # Process each metadata block
    for meta_id, meta_content in legacy_metadata.items():
        try:
            # Try to parse as YAML first
            parsed_meta = yaml.safe_load(meta_content)
            if isinstance(parsed_meta, dict):
                # Migrate known fields to appropriate namespaces
                _migrate_metadata_fields(migrated, parsed_meta)
            else:
                # Store as simple key-value if not a dict
                migrated[f'legacy_{meta_id}'] = meta_content
        except yaml.YAMLError:
            # Store as plain text if YAML parsing fails
            migrated[f'legacy_{meta_id}'] = meta_content
    
    return migrated


def _migrate_metadata_fields(front_matter: Dict, metadata: Dict) -> None:
    """Migrate specific metadata fields to appropriate front-matter namespaces."""
    
    # Migrate date fields to dates namespace
    date_fields = ['created', 'modified', 'date_created', 'date_modified']
    dates = front_matter.setdefault('dates', {})
    for field in date_fields:
        if field in metadata:
            if field.startswith('date_'):
                # Convert date_created -> created
                new_field = field[5:]
            else:
                new_field = field
            dates[new_field] = metadata[field]
    
    # Migrate metrics fields to metrics namespace  
    metrics_fields = ['word_count', 'wordCount', 'reading_time', 'readingTime']
    metrics = front_matter.setdefault('metrics', {})
    for field in metrics_fields:
        if field in metadata:
            if field in ['wordCount', 'readingTime']:
                # Convert camelCase to snake_case
                new_field = 'word_count' if field == 'wordCount' else 'reading_time'
            else:
                new_field = field
            metrics[new_field] = metadata[field]
    
    # Migrate permissions fields to permissions namespace
    permission_fields = ['mode', 'editable', 'signed']
    permissions = front_matter.setdefault('permissions', {})
    for field in permission_fields:
        if field in metadata:
            permissions[field] = metadata[field]
    
    # Migrate simple fields directly
    simple_fields = ['version', 'status', 'description', 'language', 'license']
    for field in simple_fields:
        if field in metadata:
            front_matter[field] = metadata[field]
    
    # Migrate keywords/tags
    if 'keywords' in metadata:
        front_matter['keywords'] = metadata['keywords']
    elif 'tags' in metadata:
        front_matter['keywords'] = metadata['tags']


def serialize_front_matter(front_matter: Dict) -> str:
    """Serialize front-matter dictionary to YAML with stable ordering.
    
    Orders fields by logical grouping for better readability:
    1. Core required fields (title, authors, links)
    2. Organized metadata namespaces (dates, metrics, permissions)  
    3. Optional simple fields (version, status, etc.)
    """
    if not front_matter:
        return "---\n---\n"
    
    # Create ordered dictionary with stable field ordering
    ordered_fm = {}
    
    # 1. Required core fields first
    for field in ['title', 'authors', 'links']:
        if field in front_matter:
            ordered_fm[field] = front_matter[field]
    
    # 2. Organized metadata namespaces
    for namespace in ['dates', 'metrics', 'permissions']:
        if namespace in front_matter:
            ordered_fm[namespace] = front_matter[namespace]
    
    # 3. Optional simple fields in logical order
    optional_fields = ['version', 'status', 'description', 'language', 'license', 'keywords']
    for field in optional_fields:
        if field in front_matter:
            ordered_fm[field] = front_matter[field]
    
    # 4. Any remaining fields (to handle extensions)
    for field, value in front_matter.items():
        if field not in ordered_fm:
            ordered_fm[field] = value
    
    # Serialize to YAML with clean formatting
    yaml_content = yaml.dump(
        ordered_fm, 
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,  # Preserve our custom ordering
        indent=2
    )
    
    return f"---\n{yaml_content}---\n" 