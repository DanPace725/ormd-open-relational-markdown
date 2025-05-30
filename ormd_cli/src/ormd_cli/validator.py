# src/ormd_cli/validator.py
import re
import yaml
import markdown
from pathlib import Path
from typing import List, Dict, Any
from .parser import parse_document

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
                
            # Parse document components using the shared parser
            front_matter, body, metadata, parse_errors = parse_document(content)
            self.errors.extend(parse_errors)
            
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