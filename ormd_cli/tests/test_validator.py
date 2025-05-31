# tests/test_validator.py
import pytest
from src.ormd_cli.validator import ORMDValidator

# Ensure the original valid document test still passes (backwards compatibility)
def test_original_valid_document():
    validator = ORMDValidator()
    # Assumes examples/hello.ormd uses '---' and is valid
    result = validator.validate_file('examples/hello.ormd') # Path relative to /app/ormd_cli
    if not result:
        print("Errors for test_original_valid_document:", validator.errors)
    assert result == True
    assert not validator.errors

def test_missing_version_tag():
    validator = ORMDValidator()
    # No version tag - file should fail validation
    result = validator.validate_file('../tests/fixtures/no_version.ormd')
    assert not result
    assert any("Missing or invalid version tag" in error for error in validator.errors)

# --- Tests for new '+++' delimiters and metadata features ---

def test_valid_hyphen_fm():
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/valid_hyphen_fm.ormd')
    assert not validator.errors

def test_valid_plus_fm():
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/valid_plus_fm.ormd')
    assert not validator.errors

def test_valid_plus_fm_meta():
    """Test files with migrated metadata in front-matter."""
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/valid_plus_fm_meta.ormd')
    assert not validator.errors

def test_valid_plus_fm_meta_with_id():
    """Test files with migrated named metadata sections."""
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/valid_plus_fm_meta_with_id.ormd')
    assert not validator.errors

def test_valid_plus_fm_multiple_meta():
    """Test files with multiple migrated metadata sections."""
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/valid_plus_fm_multiple_meta.ormd')
    assert not validator.errors

def test_meta_before_body():
    """Test files with metadata in front-matter before body."""
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/meta_before_body.ormd')
    assert not validator.errors

def test_meta_only_no_body():
    """Test files with only front-matter metadata and minimal body."""
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/meta_only_no_body.ormd')
    assert not validator.errors

def test_valid_empty_fm():
    validator = ORMDValidator()
    # This should fail because empty front-matter lacks required fields
    result = validator.validate_file('../tests/fixtures/valid_empty_fm.ormd')
    assert not result
    assert any("No front-matter found" in error for error in validator.errors)

def test_valid_empty_meta():
    """Test files with empty metadata sections in front-matter."""
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/valid_empty_meta.ormd')
    assert not validator.errors


# --- Tests for delimiter collision scenarios ---

def test_collision_plus_fm_body_has_hyphens():
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/collision_plus_fm_body_has_hyphens.ormd')
    assert not validator.errors

def test_collision_hyphen_fm_body_has_plus():
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/collision_hyphen_fm_body_has_plus.ormd')
    assert not validator.errors

def test_collision_plus_fm_body_has_plus():
    """Test that +++ in body content doesn't interfere with parsing."""
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/collision_plus_fm_body_has_plus.ormd')
    assert not validator.errors


def test_meta_content_has_delimiters():
    """Test metadata content that contains delimiter characters."""
    validator = ORMDValidator()
    assert validator.validate_file('../tests/fixtures/meta_content_has_delimiters.ormd')
    assert not validator.errors

# --- Tests for malformed delimiter scenarios ---

def test_malformed_unclosed_plus_fm():
    """Test files with unclosed front-matter delimiters."""
    validator = ORMDValidator()
    # Unclosed front-matter should cause parsing issues
    result = validator.validate_file('../tests/fixtures/malformed_unclosed_plus_fm.ormd')
    assert not result
    # Should have some kind of parsing or validation error
    assert validator.errors


def test_malformed_mismatched_fm_delimiters():
    """Test files with mismatched front-matter delimiters."""
    validator = ORMDValidator()
    result = validator.validate_file('../tests/fixtures/malformed_mismatched_fm_delimiters.ormd')
    assert not result
    assert validator.errors


# Ensure all fixture files are used by at least one test
# This is a meta-test, usually done by test coverage tools, but good to keep in mind.
