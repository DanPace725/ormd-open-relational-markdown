"""Tests for legacy +++meta block deprecation and migration."""

import pytest
from ormd_cli.validator import ORMDValidator
from ormd_cli.parser import parse_document


class TestLegacyMetaBlocks:
    """Test handling of deprecated +++meta blocks."""

    def test_meta_blocks_generate_deprecation_warning(self):
        """Test that +++meta blocks generate deprecation warnings."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
---

# Body Content

+++meta
some_key: some_value
+++end-meta
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        # Should parse successfully but with a warning
        assert front_matter is not None
        assert "+++meta blocks are deprecated" in str(errors)

    def test_unclosed_meta_blocks_handled_gracefully(self):
        """Test that unclosed +++meta blocks don't crash the parser."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
---

# Body Content

+++meta
some_key: some_value
# Missing +++end-meta
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        # Should still parse the front-matter successfully
        assert front_matter is not None
        assert front_matter['title'] == "Test Document"
        
        # Should contain the unclosed meta content in the body
        assert '+++meta' in body
        assert 'some_key: some_value' in body

    def test_validator_fails_with_meta_blocks(self):
        """Test that validator fails files with +++meta blocks."""
        # Create a temporary test content
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
---

# Body Content

+++meta
some_key: some_value
+++end-meta
'''
        
        # Write to a temporary file for testing
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            validator = ORMDValidator()
            result = validator.validate_file(temp_path)
            
            # Should fail validation due to deprecation warning
            assert not result
            assert any("+++meta blocks are deprecated" in error for error in validator.errors)
        finally:
            os.unlink(temp_path)

    def test_migration_preserves_content(self):
        """Test that legacy content can be manually migrated."""
        # This would be for a migration tool, but for now just test the concept
        legacy_content = {
            'created': '2025-05-29T10:00:00Z',
            'word_count': 247,
            'mode': 'draft'
        }
        
        # Manual migration logic (this would be in a migration tool)
        migrated_front_matter = {
            'title': 'Test Document',
            'authors': ['Test Author'],
            'links': [],
            'dates': {
                'created': legacy_content['created']
            },
            'metrics': {
                'word_count': legacy_content['word_count']
            },
            'permissions': {
                'mode': legacy_content['mode']
            }
        }
        
        # Verify the migration worked
        assert migrated_front_matter['dates']['created'] == '2025-05-29T10:00:00Z'
        assert migrated_front_matter['metrics']['word_count'] == 247
        assert migrated_front_matter['permissions']['mode'] == 'draft' 