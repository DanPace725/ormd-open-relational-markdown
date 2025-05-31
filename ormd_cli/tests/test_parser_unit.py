"""Unit tests for ORMD parser functionality.

These tests focus on parser behavior with minimal sample files and edge cases.
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.ormd_cli.parser import parse_document, serialize_front_matter


class TestParserUnit:
    """Unit tests for ORMD parser functionality."""

    def test_minimal_valid_document(self):
        """Test parsing minimal valid ORMD document."""
        content = '''<!-- ormd:0.1 -->
---
title: "Minimal Document"
authors: ["Test Author"]
links: []
---

# Minimal Content

Just a simple paragraph.
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        assert not errors
        assert front_matter is not None
        assert front_matter['title'] == "Minimal Document"
        assert front_matter['authors'] == ["Test Author"]
        assert front_matter['links'] == []
        assert "# Minimal Content" in body
        assert "Just a simple paragraph." in body

    def test_empty_body_document(self):
        """Test parsing document with empty body content."""
        content = '''<!-- ormd:0.1 -->
---
title: "Empty Body Document"
authors: ["Test Author"]
links: []
---

'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        assert not errors
        assert front_matter is not None
        assert front_matter['title'] == "Empty Body Document"
        assert body.strip() == ""

    def test_no_links_document(self):
        """Test parsing document with no links defined."""
        content = '''<!-- ormd:0.1 -->
---
title: "No Links Document"
authors: ["Test Author"]
links: []
---

# Content Without Links

This document has no semantic links defined.
No [[references]] to anything.
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        assert not errors
        assert front_matter['links'] == []
        assert "[[references]]" in body

    def test_plus_delimiter_parsing(self):
        """Test parsing document with +++ delimiters."""
        content = '''<!-- ormd:0.1 -->
+++
title: "Plus Delimiter Document"
authors: ["Test Author"]
links:
  - id: "test-link"
    rel: "supports"
    to: "#section"
+++

# Content

This uses +++ delimiters and references [[test-link]].
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        assert not errors
        assert front_matter['title'] == "Plus Delimiter Document"
        assert len(front_matter['links']) == 1
        assert front_matter['links'][0]['id'] == "test-link"

    def test_complex_front_matter_parsing(self):
        """Test parsing document with complex front-matter structure."""
        content = '''<!-- ormd:0.1 -->
---
title: "Complex Document"
authors:
  - id: "author1"
    display: "John Doe"
    email: "john@example.com"
  - "Jane Smith"
links:
  - id: "ref1"
    rel: "supports"
    to: "#section1"
  - id: "ref2"
    rel: "extends"
    to: "other.ormd"
dates:
  created: "2025-01-01T10:00:00Z"
  modified: "2025-01-02T15:30:00Z"
metrics:
  word_count: 150
  reading_time: "2 min"
permissions:
  mode: "published"
  editable: false
  signed: true
version: "1.0"
status: "published"
keywords: ["test", "complex", "metadata"]
---

# Complex Document

This document has complex front-matter with all optional fields.

## Section 1

Content referencing [[ref1]] and [[ref2]].
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        assert not errors
        assert front_matter['title'] == "Complex Document"
        assert len(front_matter['authors']) == 2
        assert isinstance(front_matter['authors'][0], dict)
        assert front_matter['authors'][0]['display'] == "John Doe"
        assert front_matter['authors'][1] == "Jane Smith"
        assert len(front_matter['links']) == 2
        assert front_matter['dates']['created'] == "2025-01-01T10:00:00Z"
        assert front_matter['metrics']['word_count'] == 150
        assert front_matter['permissions']['mode'] == "published"
        assert front_matter['version'] == "1.0"
        assert "complex" in front_matter['keywords']

    def test_malformed_yaml_parsing(self):
        """Test parsing document with malformed YAML."""
        content = '''<!-- ormd:0.1 -->
---
title: "Malformed Document"
authors: ["Test Author"
links: []
invalid_yaml: this is not valid: yaml: syntax
---

# Content

Body content here.
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        assert errors
        assert any("Invalid YAML" in error for error in errors)
        assert front_matter is None

    def test_missing_version_tag_parsing(self):
        """Test parsing document without version tag."""
        content = '''---
title: "No Version Document"
authors: ["Test Author"]
links: []
---

# Content

Body without version tag.
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        # Parser should fail when missing version tag
        assert front_matter is None
        assert errors
        assert any("Missing or invalid version tag" in error for error in errors)

    def test_no_front_matter_parsing(self):
        """Test parsing document with no front-matter."""
        content = '''<!-- ormd:0.1 -->

# Just Content

This document has no front-matter at all.
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        assert not errors
        assert front_matter == {}  # Parser converts None to empty dict
        assert "# Just Content" in body

    def test_unclosed_front_matter_parsing(self):
        """Test parsing document with unclosed front-matter."""
        content = '''<!-- ormd:0.1 -->
---
title: "Unclosed Document"
authors: ["Test Author"]
links: []

# Content

This front-matter is never closed.
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        # Should return None when front-matter is unclosed and treat entire content as body
        assert front_matter is None
        assert "title:" in body

    def test_legacy_meta_block_warning(self):
        """Test that legacy +++meta blocks generate deprecation warnings."""
        content = '''<!-- ormd:0.1 -->
---
title: "Legacy Document"
authors: ["Test Author"]
links: []
---

# Content

Some content here.

+++meta
legacy_field: "This should generate a warning"
+++end-meta

More content.
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        assert front_matter is not None
        assert any("+++meta blocks are deprecated" in error for error in errors)

    def test_serialize_front_matter_ordering(self):
        """Test that front-matter serialization maintains stable field ordering."""
        front_matter = {
            'keywords': ['test', 'ordering'],
            'title': "Test Document",
            'version': "1.0",
            'authors': ["Test Author"],
            'links': [],
            'metrics': {
                'word_count': 100,
                'reading_time': "1 min"
            },
            'status': "draft",
            'dates': {
                'created': "2025-01-01T10:00:00Z"
            }
        }
        
        serialized = serialize_front_matter(front_matter)
        
        # Check that required fields come first
        lines = serialized.split('\n')
        yaml_lines = [line for line in lines if line and not line.startswith('---')]
        
        # Find indices of key fields
        title_idx = next(i for i, line in enumerate(yaml_lines) if line.startswith('title:'))
        authors_idx = next(i for i, line in enumerate(yaml_lines) if line.startswith('authors:'))
        links_idx = next(i for i, line in enumerate(yaml_lines) if line.startswith('links:'))
        
        # Required fields should come first in order
        assert title_idx < authors_idx < links_idx
        
        # Check that organized namespaces come after required fields
        dates_idx = next((i for i, line in enumerate(yaml_lines) if line.startswith('dates:')), -1)
        metrics_idx = next((i for i, line in enumerate(yaml_lines) if line.startswith('metrics:')), -1)
        
        if dates_idx != -1:
            assert dates_idx > links_idx
        if metrics_idx != -1:
            assert metrics_idx > links_idx

    def test_serialize_empty_front_matter(self):
        """Test serializing empty front-matter."""
        serialized = serialize_front_matter({})
        
        assert serialized == "---\n---\n"

    def test_serialize_minimal_front_matter(self):
        """Test serializing minimal required front-matter."""
        front_matter = {
            'title': "Minimal Document",
            'authors': ["Test Author"],
            'links': []
        }
        
        serialized = serialize_front_matter(front_matter)
        
        assert 'title: Minimal Document' in serialized
        assert 'authors:' in serialized
        assert '- Test Author' in serialized
        assert 'links: []' in serialized
        assert serialized.startswith('---\n')
        assert serialized.endswith('---\n')

    def test_delimiter_collision_handling(self):
        """Test parsing when body content contains front-matter delimiters."""
        content = '''<!-- ormd:0.1 -->
---
title: "Delimiter Collision Document"
authors: ["Test Author"]
links: []
---

# Content with Delimiters

This content has some --- delimiters in it.

```yaml
---
some: yaml
---
```

And some +++ text too.

+++
not front-matter
+++
'''
        
        front_matter, body, metadata, errors = parse_document(content)
        
        assert not errors
        assert front_matter['title'] == "Delimiter Collision Document"
        assert "---" in body
        assert "+++" in body
        assert "not front-matter" in body 