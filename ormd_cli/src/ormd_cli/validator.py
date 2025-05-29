# src/ormd_cli/validator.py
import re
import yaml
import markdown
from pathlib import Path
from typing import List, Dict, Any

class ORMDValidator:
    def __init__(self):
        self.errors = []
    
    def validate_file(self, file_path: str) -> bool:
        """Main validation entry point"""
        try:
            content = Path(file_path).read_text(encoding='utf-8')
            
            # Check version tag
            if not self._check_version_tag(content):
                return False
                
            # Parse document components
            front_matter, body, metadata = self._parse_document(content) # Expects 3 values
            
            # Validate front-matter structure
            if not self._validate_front_matter(front_matter):
                return False
                
            # Check link references
            if not self._validate_link_references(front_matter, body):
                return False
                
            return len(self.errors) == 0
            
        except Exception as e:
            self.errors.append(f"Failed to read file: {e}")
            return False
    
    def _check_version_tag(self, content: str) -> bool:
        """Check for <!-- ormd:0.1 --> at start. Does not remove the tag."""
        if not content.strip().startswith('<!-- ormd:0.1 -->'):
            self.errors.append("Missing or invalid version tag")
            return False
        return True
    
    def _parse_document(self, content: str) -> tuple: # Expected to receive full content
        """Split into version, front-matter, body, and metadata using a state machine"""
        lines = content.splitlines(keepends=True)
        
        state = "EXPECT_VERSION"
        version_tag_content = None # Stores the actual version tag line
        front_matter_lines = []
        body_lines = []
        metadata_blocks = {} # Stores metadata, keyed by meta_id. Values are lists of lines.
        
        front_matter_delim = None
        current_meta_id = None # ID of the metadata block currently being parsed

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped_line = line.strip()

            if state == "EXPECT_VERSION":
                if stripped_line.startswith('<!-- ormd:0.1 -->'):
                    version_tag_content = line 
                    state = "EXPECT_FRONT_MATTER_START"
                    i += 1
                else:
                    # No version tag found at the beginning.
                    # The _check_version_tag method should have already caught this if it's called first.
                    # If _parse_document is the sole source of truth for parsing order, this is the error point.
                    self.errors.append("Missing or invalid version tag (expected at the beginning of the document)")
                    return None, None, None # Critical error, cannot proceed
                continue

            elif state == "EXPECT_FRONT_MATTER_START":
                if stripped_line == "---":
                    front_matter_delim = "---"
                    state = "IN_FRONT_MATTER"
                elif stripped_line == "+++":
                    front_matter_delim = "+++"
                    state = "IN_FRONT_MATTER"
                elif stripped_line.startswith("+++meta"):
                    # No front-matter, directly into metadata
                    state = "IN_META_HEADER"
                    continue # Re-process this line in IN_META_HEADER state
                else:
                    # No front-matter, and not starting with metadata, so it's body content
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
                    # Do not increment i here, re-process the current line in the new state
                    continue 
                else:
                    # Not metadata, so it's body content
                    body_lines.append(line)
                    state = "IN_BODY" 
                i += 1
                continue

            elif state == "IN_BODY":
                if stripped_line.startswith("+++meta"):
                    state = "IN_META_HEADER"
                    # Do not increment i here, re-process the current line in the new state
                    continue
                else:
                    body_lines.append(line)
                i += 1
                continue
            
            elif state == "IN_META_HEADER":
                # Expecting a line like "+++meta" or "+++meta optional_id"
                match = re.match(r'\+\+\+meta\s*(\w*)\s*$', stripped_line, re.IGNORECASE)
                if match:
                    current_meta_id = match.group(1) if match.group(1) else "default"
                    if current_meta_id in metadata_blocks:
                        self.errors.append(f"Duplicate metadata block ID: {current_meta_id}. Content will be overwritten.")
                        # Overwriting existing content for the same ID.
                    metadata_blocks[current_meta_id] = [] # Initialize/reset list for lines
                    state = "IN_META_CONTENT"
                else:
                    # This line looked like a meta header but wasn't valid.
                    # Treat as a body line instead of erroring, to be more robust.
                    self.errors.append(f"Invalid or malformed metadata header: '{stripped_line}'. Treating as body content.")
                    body_lines.append(line) 
                    state = "IN_BODY"
                i += 1
                continue

            elif state == "IN_META_CONTENT":
                if stripped_line == "+++end-meta":
                    state = "EXPECT_BODY_OR_META_START" # Expect more body or another meta block
                    current_meta_id = None # Reset, as we've finished this block
                else:
                    if current_meta_id: # This should be true if state machine is correct
                        metadata_blocks[current_meta_id].append(line)
                    else:
                        # This case should ideally not be reached.
                        # If it is, it implies an error in state transition.
                        self.errors.append(f"Internal parser error: Attempted to add content to metadata without ID. Line: '{stripped_line}'")
                        body_lines.append(line) # Fallback: treat as body
                        state = "IN_BODY" # Try to recover by going to body state
                i += 1
                continue
            
            # Fallback for unhandled states or lines (e.g., if a state is missed in logic)
            # This should ideally not be reached.
            self.errors.append(f"Unhandled line in parsing state machine: '{stripped_line}' (State: {state})")
            body_lines.append(line) # Treat as body content as a fallback
            i += 1


        # --- Post-loop parsing ---

        # Parse front-matter (YAML)
        front_matter_str = "".join(front_matter_lines)
        if not front_matter_str.strip(): # Covers empty lines between delims, or no lines at all
            front_matter = {}
        else:
            try:
                front_matter = yaml.safe_load(front_matter_str)
                if front_matter is None: # YAML content that parses to None (e.g. just a comment)
                    front_matter = {} 
            except yaml.YAMLError as e:
                self.errors.append(f"Invalid YAML in front-matter: {e}")
                front_matter = None # Error case, _validate_front_matter will catch this None
        
        # Consolidate metadata blocks from lists of lines to single strings
        parsed_metadata = {}
        if metadata_blocks:
            for meta_id, lines_list in metadata_blocks.items():
                parsed_metadata[meta_id] = "".join(lines_list)
        
        final_body = "".join(body_lines)

        # Note: version_tag_content is captured but not explicitly returned with the other parts.
        # The _check_version_tag method already validates its presence.
        # If it needs to be returned, the tuple signature and call sites must be updated.
        return front_matter, final_body, parsed_metadata if parsed_metadata else None
    
    def _validate_front_matter(self, front_matter: Dict[str, Any]) -> bool:
        """Validate required fields and structure"""
        if front_matter is None: # Caused by YAML error or other parsing failure
            # The error for this (e.g., Invalid YAML) should have been added by the parser.
            return False 
            
        # If front_matter is an empty dictionary (e.g. "+++\n+++" was parsed)
        # it's not None, but it is empty. Check for required fields.
        required = ['title', 'authors', 'links']
        all_fields_present = True
        for field in required:
            if field not in front_matter:
                self.errors.append(f"Missing required field: {field}")
                all_fields_present = False
        
        if not all_fields_present:
            return False

        # Validate links structure (only if all required fields were present)
        links = front_matter.get('links', []) # 'links' is guaranteed now by checks above
        if not isinstance(links, list):
            self.errors.append("'links' must be a list")
            return False
            
        for i, link in enumerate(links):
            if not isinstance(link, dict):
                self.errors.append(f"Link {i} must be an object")
                continue
            if 'id' not in link:
                self.errors.append(f"Link {i} missing 'id' field")
            if 'rel' not in link:
                self.errors.append(f"Link {i} missing 'rel' field")
            if 'to' not in link:
                self.errors.append(f"Link {i} missing 'to' field")
        
        return True
    
    def _validate_link_references(self, front_matter: Dict[str, Any], body: str) -> bool:
        """Check that all [[link-id]] references exist in links"""
        if not front_matter:
            return False
            
        # Extract all [[id]] references from body
        link_refs = re.findall(r'\[\[([^\]]+)\]\]', body)
        
        # Get all defined link IDs
        defined_ids = set()
        for link in front_matter.get('links', []):
            if isinstance(link, dict) and 'id' in link:
                defined_ids.add(link['id'])
        
        # Check for undefined references
        for ref in link_refs:
            if ref not in defined_ids:
                self.errors.append(f"Undefined link reference: [[{ref}]]")
        
        return len([e for e in self.errors if 'Undefined link' in e]) == 0