# src/ormd_cli/packager.py
import zipfile
import json
from pathlib import Path
from typing import Optional

class ORMDPackager:
    def pack(self, content_file: str, meta_file: str, output: str) -> bool:
        """Pack content.ormd and meta.json into a .ormd zip"""
        try:
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Add main content file
                zf.write(content_file, 'content.ormd')
                
                # Add metadata
                zf.write(meta_file, 'meta.json')
                
                # TODO: Add optional files (render.css, ops/, etc.)
                
            return True
        except Exception as e:
            print(f"Packing failed: {e}")
            return False
    
    def unpack(self, package_file: str, output_dir: str) -> bool:
        """Unpack a .ormd zip into directory"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(package_file, 'r') as zf:
                zf.extractall(output_path)
            
            return True
        except Exception as e:
            print(f"Unpacking failed: {e}")
            return False