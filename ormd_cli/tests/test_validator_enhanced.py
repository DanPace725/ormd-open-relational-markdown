"""Tests for enhanced ORMD validator functionality.

These tests cover the comprehensive Phase 1 validation checks:
- Required field enforcement with clear guidance
- Semantic link consistency
- Asset existence checks  
- Strict YAML schema compliance
"""

import pytest
import tempfile
import os
from pathlib import Path
from ormd_cli.validator import ORMDValidator


class TestEnhancedValidator:
    """Test the enhanced ORMD validator functionality."""

    def test_missing_version_tag_guidance(self):
        """Test clear guidance for missing version tag."""
        content = '''---
title: "Test Document"
authors: ["Test Author"]
links: []
---

# Test

Content here.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert not result
            assert any("Add '<!-- ormd:0.1 -->' at the top" in error for error in validator.errors)
            
        finally:
            os.unlink(temp_path)

    def test_missing_required_fields_guidance(self):
        """Test clear guidance for missing required fields."""
        content = '''<!-- ormd:0.1 -->
---
description: "Missing required fields"
---

# Test

Content here.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert not result
            assert any("title: Your Document Title" in error for error in validator.errors)
            assert any("authors: [Author Name]" in error for error in validator.errors)
            assert any("links: []" in error for error in validator.errors)
            
        finally:
            os.unlink(temp_path)

    def test_no_front_matter_guidance(self):
        """Test guidance when front-matter is completely missing."""
        content = '''<!-- ormd:0.1 -->

# Test Document

No front-matter at all.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert not result
            assert any("No front-matter found" in error for error in validator.errors)
            assert any("title: Your Document Title" in error for error in validator.errors)
            
        finally:
            os.unlink(temp_path)

    def test_strict_schema_unknown_fields(self):
        """Test that unknown fields are rejected in Phase 1."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
custom_field: "Not allowed"
another_unknown: 123
---

# Test

Content here.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert not result
            assert any("Unknown fields" in error for error in validator.errors)
            assert any("custom_field" in error for error in validator.errors)
            assert any("another_unknown" in error for error in validator.errors)
            assert any("Phase 1 only allows these fields" in error for error in validator.errors)
            
        finally:
            os.unlink(temp_path)

    def test_semantic_link_consistency_undefined_refs(self):
        """Test detection of undefined link references."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links:
  - id: "defined-link"
    rel: "supports"
    to: "#section"
---

# Test Document

This references [[defined-link]] which is good.
But this references [[undefined-link]] which is bad.
And this references [[another-undefined]] which is also bad.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert not result
            assert any("Undefined link reference [[undefined-link]]" in error for error in validator.errors)
            assert any("Undefined link reference [[another-undefined]]" in error for error in validator.errors)
            # Should not complain about defined-link
            assert not any("[[defined-link]]" in error for error in validator.errors)
            
        finally:
            os.unlink(temp_path)

    def test_semantic_link_consistency_unused_definitions(self):
        """Test warnings for unused link definitions."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links:
  - id: "used-link"
    rel: "supports"
    to: "#section"
  - id: "unused-link"
    rel: "supports"
    to: "#other"
---

# Test Document

This references [[used-link]] but not the other one.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert result  # Should pass validation
            assert any("unused-link" in warning for warning in validator.warnings)
            assert any("defined but not referenced" in warning for warning in validator.warnings)
            
        finally:
            os.unlink(temp_path)

    def test_link_ids_consistency_outdated(self):
        """Test detection of outdated link_ids field."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links:
  - id: "current-link"
    rel: "supports"
    to: "#section"
link_ids: ["old-link", "another-old"]
---

# Test Document

This references [[current-link]] which is different from link_ids.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert not result  # Should fail due to undefined current-link
            assert any("link_ids' is outdated" in error for error in validator.errors)
            assert any("ormd update" in error for error in validator.errors)
            
        finally:
            os.unlink(temp_path)

    def test_asset_existence_missing_files(self):
        """Test detection of missing asset files."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
asset_ids:
  - "assets/existing.png"
  - "assets/missing.pdf"
  - "data/nonexistent.csv"
---

# Test Document

References to assets.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            # Create one of the asset files
            temp_dir = Path(temp_path).parent
            assets_dir = temp_dir / "assets"
            assets_dir.mkdir(exist_ok=True)
            (assets_dir / "existing.png").write_text("fake image")
            
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert not result
            assert any("Asset not found: assets/missing.pdf" in error for error in validator.errors)
            assert any("Asset not found: data/nonexistent.csv" in error for error in validator.errors)
            # Should not complain about existing.png
            assert not any("existing.png" in error for error in validator.errors)
            assert any("Run 'ormd update' to resync" in error for error in validator.errors)
            
        finally:
            os.unlink(temp_path)
            # Clean up created directories
            if assets_dir.exists():
                (assets_dir / "existing.png").unlink()
                assets_dir.rmdir()

    def test_asset_existence_skips_urls(self):
        """Test that URL assets are skipped in existence checks."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
asset_ids:
  - "https://example.com/remote.png"
  - "http://example.com/other.pdf"
  - "/absolute/path/file.txt"
---

# Test Document

References to remote and absolute assets.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert result  # Should pass - URLs and absolute paths are skipped
            assert not validator.errors
            
        finally:
            os.unlink(temp_path)

    def test_malformed_field_types_guidance(self):
        """Test helpful guidance for malformed field types."""
        content = '''<!-- ormd:0.1 -->
---
title: 123  # Should be string
authors: "Single Author"  # Should be list
links: "not a list"  # Should be list
---

# Test

Content here.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert not result
            assert any("title: My Document Title" in error for error in validator.errors)
            assert any("authors: [John Doe, jane@example.com]" in error for error in validator.errors)
            assert any("links: []" in error for error in validator.errors)
            
        finally:
            os.unlink(temp_path)

    def test_validation_summary_formatting(self):
        """Test the validation summary formatting."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links:
  - id: "unused-link"
    rel: "supports"
    to: "#section"
unknown_field: "not allowed"
---

# Test Document

No link references, so unused-link will be warned about.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            summary = validator.get_validation_summary()
            
            assert "❌ Validation failed" in summary
            assert "error(s):" in summary
            assert "Unknown fields" in summary
            
        finally:
            os.unlink(temp_path)

    def test_valid_document_with_warnings(self):
        """Test valid document that generates warnings."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links:
  - id: "unused-link"
    rel: "supports"
    to: "#section"
---

# Test Document

Valid document but with an unused link definition.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert result  # Should pass validation
            assert len(validator.warnings) > 0
            assert len(validator.errors) == 0
            
            summary = validator.get_validation_summary()
            assert "⚠️" in summary
            assert "warning(s):" in summary
            assert "unused-link" in summary
            
        finally:
            os.unlink(temp_path)

    def test_perfect_valid_document(self):
        """Test perfectly valid document with no warnings."""
        content = '''<!-- ormd:0.1 -->
---
title: "Perfect Document"
authors: ["Test Author"]
links:
  - id: "used-link"
    rel: "supports"
    to: "#section"
---

# Perfect Document

This references [[used-link]] properly.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            assert result
            assert len(validator.errors) == 0
            assert len(validator.warnings) == 0
            
            summary = validator.get_validation_summary()
            assert "✅ Document is valid ORMD 0.1" in summary
            
        finally:
            os.unlink(temp_path) 