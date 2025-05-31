#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from pathlib import Path

# Create a simple test file
content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
---

# Test Document

Simple test content.
'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
    f.write(content)
    temp_path = f.name

try:
    # Test the validate command
    cmd = [sys.executable, '-m', 'src.ormd_cli.main', 'validate', temp_path]
    print(f"Running command: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    
    print(f"Return code: {result.returncode}")
    print(f"STDOUT: {repr(result.stdout)}")
    print(f"STDERR: {repr(result.stderr)}")
    
finally:
    Path(temp_path).unlink() 