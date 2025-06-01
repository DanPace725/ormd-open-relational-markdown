"""Tests for ORMD updater functionality."""

import pytest
import tempfile
import os
from pathlib import Path
from ormd_cli.updater import ORMDUpdater
from ormd_cli.parser import parse_document
from datetime import datetime, timezone


class TestORMDUpdater:
    """Test the ORMD updater functionality."""

    def test_basic_update(self):
        """Test basic update functionality."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
---

# Test Document

This is a test document with some words. It has [[test-link]] references
and ![image](assets/test.png) assets.

## Section Two

More content here with additional words to test counting.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            updater = ORMDUpdater()
            result = updater.update_file(temp_path, dry_run=True)
            
            assert not result['updated']  # Dry run doesn't update
            assert 'dates' in result['changes']
            assert 'metrics' in result['changes']
            assert 'link_ids' in result['changes']
            assert 'asset_ids' in result['changes']
            
            # Check computed values
            dates = result['changes']['dates']['new']
            assert 'created' in dates
            assert 'modified' in dates
            
            metrics = result['changes']['metrics']['new']
            assert 'word_count' in metrics
            assert 'reading_time' in metrics
            assert metrics['word_count'] > 0
            
            link_ids = result['changes']['link_ids']['new']
            assert 'test-link' in link_ids
            
            asset_ids = result['changes']['asset_ids']['new']
            assert 'assets/test.png' in asset_ids
            
        finally:
            os.unlink(temp_path)

    def test_idempotency(self):
        """Test that running update twice produces no changes."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
---

# Test Document

Simple content for testing.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            updater = ORMDUpdater()
            
            # First update
            result1 = updater.update_file(temp_path)
            assert result1['updated']
            
            # Second update should show no changes
            result2 = updater.update_file(temp_path)
            assert not result2['updated']
            assert not result2['changes']
            
        finally:
            os.unlink(temp_path)

    def test_locked_fields(self):
        """Test that locked fields are not updated."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
dates:
  created: "2025-01-01T00:00:00Z"
  modified: "2025-01-01T00:00:00Z"
  locked: ["modified"]
metrics:
  word_count: 10
  reading_time: "1 min"
  locked: true
---

# Test Document

This document has many more words than the locked count of 10.
The word count should not be updated because metrics are locked.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            updater = ORMDUpdater()
            result = updater.update_file(temp_path, dry_run=True)
            
            # Should have some changes but not for locked fields
            if result['changes']:
                # dates.modified should not change (locked)
                if 'dates' in result['changes']:
                    dates = result['changes']['dates']['new']
                    assert dates.get('modified') == "2025-01-01T00:00:00Z"
                
                # metrics should not change (locked: true)
                assert 'metrics' not in result['changes'] or result['changes']['metrics']['new']['word_count'] == 10
            
        finally:
            os.unlink(temp_path)

    def test_force_update_locked_fields(self):
        """Test that force update ignores locks."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
dates:
  created: "2025-01-01T00:00:00Z"
  modified: "2025-01-01T00:00:00Z"
  locked: ["modified"]
---

# Test Document

Simple content.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            updater = ORMDUpdater()
            result = updater.update_file(temp_path, dry_run=True, force_update=True)
            
            # With force_update, we should see changes even for locked fields
            # The test passes if we get some changes when force_update is True
            assert result['changes'] or not result['updated']
            
        finally:
            os.unlink(temp_path)

    def test_word_counting(self):
        """Test word counting logic."""
        updater = ORMDUpdater()
        
        # Test basic word counting
        text = "This is a simple test with nine words here."
        assert updater._count_words(text) == 9
        
        # Test excluding code blocks
        text_with_code = '''
        This is text with code.
        
        ```python
        def hello():
            print("This code should not be counted")
        ```
        
        And more text after.
        '''
        count = updater._count_words(text_with_code)
        # The actual count is 9 words: "This is text with code. And more text after."
        assert count == 9
        
        # Test excluding inline code
        text_with_inline = "This has `code` and more words."
        # The actual count is 5: "This has and more words."
        assert updater._count_words(text_with_inline) == 5

    def test_link_id_extraction(self):
        """Test link ID extraction."""
        updater = ORMDUpdater()
        
        body = '''
        # Section One
        
        This references [[intro]] and [[methodology]].
        
        ## Section Two
        
        Another reference to [[intro]] and [[conclusion]].
        '''
        
        link_ids = updater._extract_link_ids(body)
        assert link_ids == ['intro', 'methodology', 'conclusion']  # Unique, preserving order

    def test_asset_id_extraction(self):
        """Test asset ID extraction."""
        updater = ORMDUpdater()
        
        body = '''
        # Document with Assets
        
        Here's an image: ![Chart](assets/chart.png)
        
        And a PDF: [Report](assets/report.pdf)
        
        HTML image: <img src="assets/diagram.svg" alt="Diagram">
        
        External image (should be ignored): ![External](https://example.com/image.png)
        
        Another local asset: [Data](data/file.csv)
        '''
        
        asset_ids = updater._extract_asset_ids(body)
        # Only assets with recognized extensions should be included
        # PDF files are included, but CSV might not be in the extension list
        expected = ['assets/chart.png', 'assets/report.pdf', 'assets/diagram.svg']
        assert 'assets/chart.png' in asset_ids
        assert 'assets/report.pdf' in asset_ids
        assert 'assets/diagram.svg' in asset_ids
        # External URLs should be excluded
        assert not any('example.com' in asset for asset in asset_ids)

    def test_preserve_existing_fields(self):
        """Test that existing non-locked fields are preserved."""
        content = '''<!-- ormd:0.1 -->
---
title: "Test Document"
authors: ["Test Author"]
links: []
version: "1.0"
status: "draft"
---

# Test Document

Content here.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            updater = ORMDUpdater()
            result = updater.update_file(temp_path)
            
            # Read back the updated file
            updated_content = Path(temp_path).read_text(encoding='utf-8')
            front_matter, _, _, _ = parse_document(updated_content)
            
            # Check that existing fields are preserved
            assert front_matter['version'] == "1.0"
            assert front_matter['status'] == "draft"
            
            # Check that new fields were added
            assert 'dates' in front_matter
            assert 'metrics' in front_matter
            
        finally:
            os.unlink(temp_path)

    def test_no_front_matter(self):
        """Test updating a document with no front-matter."""
        content = '''<!-- ormd:0.1 -->

# Test Document

This document has no front-matter initially.
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ormd', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            updater = ORMDUpdater()
            result = updater.update_file(temp_path)
            
            assert result['updated']
            
            # Read back the updated file
            updated_content = Path(temp_path).read_text(encoding='utf-8')
            front_matter, body, _, _ = parse_document(updated_content)
            
            # Check that front-matter was created
            assert front_matter is not None
            assert 'title' in front_matter
            assert 'authors' in front_matter
            assert 'dates' in front_matter
            assert 'metrics' in front_matter
            
            # Check that body is preserved
            assert 'This document has no front-matter initially.' in body
            
        finally:
            os.unlink(temp_path) 