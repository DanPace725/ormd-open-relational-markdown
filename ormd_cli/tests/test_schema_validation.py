"""Tests for ORMD front-matter schema validation."""

import pytest
from ormd_cli.schema import validate_front_matter_schema, FrontMatterValidator


class TestFrontMatterSchemaValidation:
    """Test the ORMD front-matter schema validation."""

    def test_valid_minimal_front_matter(self):
        """Test validation of minimal valid front-matter."""
        front_matter = {
            "title": "Test Document",
            "authors": ["Test Author"],
            "links": []
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert is_valid
        assert len(errors) == 0

    def test_valid_complete_front_matter(self):
        """Test validation of complete front-matter with all optional fields."""
        front_matter = {
            "title": "Complete Test Document",
            "authors": [
                {
                    "id": "test.author",
                    "display": "Test Author",
                    "email": "test@example.com",
                    "affiliation": "Test University",
                    "orcid": "0000-0000-0000-0000"
                }
            ],
            "links": [
                {
                    "id": "test-link",
                    "rel": "supports",
                    "to": "#section1"
                }
            ],
            "dates": {
                "created": "2025-05-29T10:00:00Z",
                "modified": "2025-05-29T14:30:00Z"
            },
            "metrics": {
                "word_count": 247,
                "reading_time": "2 minutes"
            },
            "permissions": {
                "mode": "draft",
                "editable": True,
                "signed": False
            },
            "version": "1.0",
            "status": "draft",
            "description": "A test document",
            "language": "en-US",
            "license": "CC-BY-4.0",
            "keywords": ["test", "example"]
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert is_valid
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test validation fails when required fields are missing."""
        front_matter = {
            "title": "Test Document"
            # Missing authors and links
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Missing required field: authors" in errors
        assert "Missing required field: links" in errors

    def test_invalid_title_type(self):
        """Test validation fails when title is not a string."""
        front_matter = {
            "title": 123,  # Should be string
            "authors": ["Test Author"],
            "links": []
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Field 'title' must be a string" in errors

    def test_empty_title(self):
        """Test validation fails when title is empty."""
        front_matter = {
            "title": "",
            "authors": ["Test Author"],
            "links": []
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Field 'title' cannot be empty" in errors

    def test_invalid_authors_type(self):
        """Test validation fails when authors is not a list."""
        front_matter = {
            "title": "Test Document",
            "authors": "Not a list",
            "links": []
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Field 'authors' must be a list" in errors

    def test_empty_authors_list(self):
        """Test validation fails when authors list is empty."""
        front_matter = {
            "title": "Test Document",
            "authors": [],
            "links": []
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Field 'authors' cannot be empty" in errors

    def test_invalid_author_object(self):
        """Test validation fails when author object is missing required fields."""
        front_matter = {
            "title": "Test Document",
            "authors": [
                {
                    "id": "test.author"
                    # Missing display field
                }
            ],
            "links": []
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Author 0 missing required field 'display'" in errors

    def test_invalid_orcid_format(self):
        """Test validation fails when ORCID format is invalid."""
        front_matter = {
            "title": "Test Document",
            "authors": [
                {
                    "id": "test.author",
                    "display": "Test Author",
                    "orcid": "invalid-orcid"
                }
            ],
            "links": []
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Author 0 field 'orcid' must be in format 0000-0000-0000-0000" in errors

    def test_invalid_links_type(self):
        """Test validation fails when links is not a list."""
        front_matter = {
            "title": "Test Document",
            "authors": ["Test Author"],
            "links": "Not a list"
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Field 'links' must be a list" in errors

    def test_invalid_link_object(self):
        """Test validation fails when link object is missing required fields."""
        front_matter = {
            "title": "Test Document",
            "authors": ["Test Author"],
            "links": [
                {
                    "id": "test-link",
                    "rel": "supports"
                    # Missing 'to' field
                }
            ]
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Link 0 missing required field 'to'" in errors

    def test_invalid_dates_structure(self):
        """Test validation fails when dates structure is invalid."""
        front_matter = {
            "title": "Test Document",
            "authors": ["Test Author"],
            "links": [],
            "dates": {
                "created": "not-an-iso-date",
                "modified": 123  # Should be string
            }
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert any("Field 'dates.created' must be a valid ISO 8601 date" in error for error in errors)
        assert "Field 'dates.modified' must be a string" in errors

    def test_invalid_metrics_structure(self):
        """Test validation fails when metrics structure is invalid."""
        front_matter = {
            "title": "Test Document",
            "authors": ["Test Author"],
            "links": [],
            "metrics": {
                "word_count": "not a number",
                "reading_time": 123  # Should be string
            }
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Field 'metrics.word_count' must be a non-negative integer" in errors
        assert "Field 'metrics.reading_time' must be a string" in errors

    def test_invalid_permissions_structure(self):
        """Test validation fails when permissions structure is invalid."""
        front_matter = {
            "title": "Test Document",
            "authors": ["Test Author"],
            "links": [],
            "permissions": {
                "mode": "invalid-mode",
                "editable": "not a boolean",
                "signed": "not a boolean"
            }
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Field 'permissions.mode' must be one of: draft, published, private" in errors
        assert "Field 'permissions.editable' must be a boolean" in errors
        assert "Field 'permissions.signed' must be a boolean" in errors

    def test_invalid_status_value(self):
        """Test validation fails when status has invalid value."""
        front_matter = {
            "title": "Test Document",
            "authors": ["Test Author"],
            "links": [],
            "status": "invalid-status"
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Field 'status' must be one of: draft, published, archived" in errors

    def test_invalid_keywords_type(self):
        """Test validation fails when keywords is not a list."""
        front_matter = {
            "title": "Test Document",
            "authors": ["Test Author"],
            "links": [],
            "keywords": "not a list"
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Field 'keywords' must be a list" in errors

    def test_invalid_keyword_type(self):
        """Test validation fails when keyword is not a string."""
        front_matter = {
            "title": "Test Document",
            "authors": ["Test Author"],
            "links": [],
            "keywords": ["valid", 123, "also valid"]
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert not is_valid
        assert "Keyword 1 must be a string" in errors

    def test_valid_iso_dates(self):
        """Test validation passes for valid ISO 8601 dates."""
        valid_dates = [
            "2025-05-29T10:00:00Z",
            "2025-05-29T10:00:00.123Z",
            "2025-05-29T10:00:00+02:00",
            "2025-05-29T10:00:00-05:00"
        ]
        
        for date_str in valid_dates:
            front_matter = {
                "title": "Test Document",
                "authors": ["Test Author"],
                "links": [],
                "dates": {
                    "created": date_str
                }
            }
            
            is_valid, errors = validate_front_matter_schema(front_matter)
            assert is_valid, f"Date {date_str} should be valid, but got errors: {errors}"

    def test_invalid_iso_dates(self):
        """Test validation fails for invalid ISO 8601 dates."""
        invalid_dates = [
            "2025-05-29",  # Missing time
            "10:00:00",    # Missing date
            "not-a-date",  # Invalid format
            "2025/05/29T10:00:00Z",  # Wrong separator
        ]
        
        for date_str in invalid_dates:
            front_matter = {
                "title": "Test Document",
                "authors": ["Test Author"],
                "links": [],
                "dates": {
                    "created": date_str
                }
            }
            
            is_valid, errors = validate_front_matter_schema(front_matter)
            assert not is_valid, f"Date {date_str} should be invalid"
            assert any("ISO 8601 date" in error for error in errors)

    def test_non_dict_front_matter(self):
        """Test validation fails when front-matter is not a dictionary."""
        is_valid, errors = validate_front_matter_schema("not a dict")
        assert not is_valid
        assert "Front-matter must be a YAML object/dictionary" in errors

    def test_mixed_author_formats(self):
        """Test validation passes with mixed author formats (strings and objects)."""
        front_matter = {
            "title": "Test Document",
            "authors": [
                "Simple Author",
                {
                    "id": "complex.author",
                    "display": "Complex Author"
                }
            ],
            "links": []
        }
        
        is_valid, errors = validate_front_matter_schema(front_matter)
        assert is_valid
        assert len(errors) == 0 