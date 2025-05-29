# tests/test_validator.py
import pytest
from ormd_cli.validator import ORMDValidator

def test_valid_document():
    validator = ORMDValidator()
    # Test with examples/hello.ormd
    assert validator.validate_file('ormd_cli/examples/hello.ormd') == True

def test_missing_version_tag():
    validator = ORMDValidator()
    # Test file without <!-- ormd:0.1 -->
    assert validator.validate_file('tests/fixtures/no_version.ormd') == False
    assert any('version tag' in error for error in validator.errors)
