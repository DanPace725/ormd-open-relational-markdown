# src/ormd_cli/validator.py
import re
import yaml
import markdown
from pathlib import Path
from typing import List, Dict, Any
from .parser import parse_document
from .schema import validate_front_matter_schema

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
            
            # Validate front-matter structure using schema
            if not self._validate_front_matter_schema(front_matter):
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
    
    def _validate_front_matter_schema(self, front_matter: Dict[str, Any]) -> bool:
        """Validate front-matter against the official ORMD schema"""
        if front_matter is None:
            # The error for this (e.g., Invalid YAML) should have been added by the parser.
            return False 
        
        # Use the schema validator
        is_valid, schema_errors = validate_front_matter_schema(front_matter)
        
        # Add schema validation errors to our error list
        self.errors.extend(schema_errors)
        
        return is_valid
    
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