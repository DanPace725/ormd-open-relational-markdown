"""Parsing utilities for ORMD documents."""
import re
import yaml
from typing import Tuple, Dict, Optional, List


def parse_document(content: str) -> Tuple[Optional[Dict], str, Optional[Dict[str, str]], List[str]]:
    """Parse full ORMD document content.

    Returns a tuple ``(front_matter, body, metadata, errors)``.
    ``front_matter`` will be ``None`` if YAML parsing fails.
    ``metadata`` is ``None`` if no metadata blocks were found.
    ``errors`` contains any parsing related warnings or errors.
    """
    errors: List[str] = []

    lines = content.splitlines(keepends=True)

    state = "EXPECT_VERSION"
    front_matter_lines: List[str] = []
    body_lines: List[str] = []
    metadata_blocks: Dict[str, List[str]] = {}

    front_matter_delim = None
    current_meta_id = None

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped_line = line.strip()

        if state == "EXPECT_VERSION":
            if stripped_line.startswith("<!-- ormd:0.1 -->"):
                state = "EXPECT_FRONT_MATTER_START"
                i += 1
            else:
                errors.append(
                    "Missing or invalid version tag (expected at the beginning of the document)"
                )
                return None, None, None, errors
            continue

        elif state == "EXPECT_FRONT_MATTER_START":
            if stripped_line == "---":
                front_matter_delim = "---"
                state = "IN_FRONT_MATTER"
            elif stripped_line == "+++":
                front_matter_delim = "+++"
                state = "IN_FRONT_MATTER"
            elif stripped_line.startswith("+++meta"):
                state = "IN_META_HEADER"
                continue
            else:
                body_lines.append(line)
                state = "IN_BODY"
            i += 1
            continue

        elif state == "IN_FRONT_MATTER":
            if stripped_line == front_matter_delim:
                state = "EXPECT_BODY_OR_META_START"
            else:
                front_matter_lines.append(line)
            i += 1
            continue

        elif state == "EXPECT_BODY_OR_META_START":
            if stripped_line.startswith("+++meta"):
                state = "IN_META_HEADER"
                continue
            else:
                body_lines.append(line)
                state = "IN_BODY"
            i += 1
            continue

        elif state == "IN_BODY":
            if stripped_line.startswith("+++meta"):
                state = "IN_META_HEADER"
                continue
            else:
                body_lines.append(line)
            i += 1
            continue

        elif state == "IN_META_HEADER":
            match = re.match(r"\+\+\+meta\s*(\w*)\s*$", stripped_line, re.IGNORECASE)
            if match:
                current_meta_id = match.group(1) if match.group(1) else "default"
                if current_meta_id in metadata_blocks:
                    errors.append(
                        f"Duplicate metadata block ID: {current_meta_id}. Content will be overwritten."
                    )
                metadata_blocks[current_meta_id] = []
                state = "IN_META_CONTENT"
            else:
                errors.append(
                    f"Invalid or malformed metadata header: '{stripped_line}'. Treating as body content."
                )
                body_lines.append(line)
                state = "IN_BODY"
            i += 1
            continue

        elif state == "IN_META_CONTENT":
            if stripped_line == "+++end-meta":
                state = "EXPECT_BODY_OR_META_START"
                current_meta_id = None
            else:
                if current_meta_id:
                    metadata_blocks[current_meta_id].append(line)
                else:
                    errors.append(
                        f"Internal parser error: Attempted to add content to metadata without ID. Line: '{stripped_line}'"
                    )
                    body_lines.append(line)
                    state = "IN_BODY"
            i += 1
            continue

        errors.append(
            f"Unhandled line in parsing state machine: '{stripped_line}' (State: {state})"
        )
        body_lines.append(line)
        i += 1

    # --- Post-loop parsing ---
    front_matter_str = "".join(front_matter_lines)
    if not front_matter_str.strip():
        front_matter = {}
    else:
        try:
            front_matter = yaml.safe_load(front_matter_str)
            if front_matter is None:
                front_matter = {}
        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML in front-matter: {e}")
            front_matter = None

    parsed_metadata: Dict[str, str] = {}
    if metadata_blocks:
        for meta_id, lines_list in metadata_blocks.items():
            parsed_metadata[meta_id] = "".join(lines_list)

    final_body = "".join(body_lines)

    return front_matter, final_body, parsed_metadata if parsed_metadata else None, errors 