# ORMD Front-Matter Schema Implementation

This document describes the implementation of the YAML front-matter schema for ORMD 0.1, following the front-matter plan to move all metadata into the YAML block.

## Overview

The schema defines a single source-of-truth for ORMD front-matter validation, replacing the previous simple field checking with comprehensive type and structure validation.

## Schema Definition

The schema is defined in `src/ormd_cli/schema.py` using Python dataclasses and a comprehensive validator.

### Required Fields

All ORMD documents must have these fields in the front-matter:

- `title` (string): Document title
- `authors` (list): List of authors (strings or objects)
- `links` (list): List of semantic link objects

### Optional Organized Metadata

These replace the `+++meta` blocks and organize related metadata:

#### `dates:` namespace
- `created` (ISO 8601 string): Document creation timestamp
- `modified` (ISO 8601 string): Last modification timestamp

#### `metrics:` namespace  
- `word_count` (integer): Number of words in document
- `reading_time` (string): Estimated reading time

#### `permissions:` namespace
- `mode` (enum): One of "draft", "published", "private"
- `editable` (boolean): Whether document can be edited
- `signed` (boolean): Whether document is cryptographically signed

### Optional Simple Fields

- `version` (string): Document version
- `status` (enum): One of "draft", "published", "archived"
- `description` (string): Document description
- `language` (string): Language code (e.g., "en-US")
- `license` (string): License identifier (e.g., "CC-BY-4.0")
- `keywords` (list of strings): Document keywords/tags

## Validation Features

### Type Validation
- Ensures fields have correct types (string, list, object, boolean, integer)
- Validates nested object structures
- Checks list contents

### Format Validation
- ISO 8601 date format validation with timezone support
- ORCID format validation (0000-0000-0000-0000)
- Enum value validation for status and permission modes

### Structure Validation
- Required fields presence
- Author object structure (id, display, optional email/affiliation/orcid)
- Link object structure (id, rel, to)
- Nested metadata object validation

### Human-Readable Error Messages

The validator provides clear, actionable error messages:

```
❌ document.ormd failed validation:
  • Field 'authors' must be a list
  • Link 0 missing required field 'to'
  • Field 'dates.created' must be a valid ISO 8601 date (e.g., 2025-05-29T10:00:00Z)
  • Field 'permissions.mode' must be one of: draft, published, private
```

## Integration

### Validator Integration

The schema is integrated into the existing validator in `src/ormd_cli/validator.py`:

```python
from .schema import validate_front_matter_schema

# In _validate_front_matter_schema method:
is_valid, schema_errors = validate_front_matter_schema(front_matter)
self.errors.extend(schema_errors)
```

### Command Line Usage

The schema validation is automatically applied when using the validate command:

```bash
python -m src.ormd_cli.main validate document.ormd
```

## Example Document

See `examples/schema_example.ormd` for a complete example showing all schema features:

```yaml
---
title: "ORMD Schema Example: Climate Change Analysis"
authors:
  - id: dr.sarah.chen
    display: Dr. Sarah Chen
    email: s.chen@marinereserach.org
    orcid: 0000-0002-1825-0097
links:
  - id: intro-ref
    rel: supports
    to: "#introduction"

# Organized metadata (replaces +++meta blocks)
dates:
  created: "2025-05-29T10:00:00Z"
  modified: "2025-05-29T14:30:00Z"

metrics:
  word_count: 1247
  reading_time: "6 minutes"

permissions:
  mode: draft
  editable: true
  signed: false

# Optional simple fields
version: "1.2"
status: draft
description: "Document description"
language: en-US
license: CC-BY-4.0
keywords:
  - climate change
  - coastal cities
---
```

## Testing

Comprehensive tests are provided in `tests/test_schema_validation.py` covering:

- Valid minimal and complete front-matter
- All validation error conditions
- Edge cases and format validation
- Mixed author formats (strings and objects)
- ISO 8601 date validation

Run tests with:
```bash
python -m pytest tests/test_schema_validation.py -v
```

## Benefits

1. **Single Source of Truth**: All validation logic centralized in schema.py
2. **Standard YAML**: Uses standard front-matter that all markdown tools understand
3. **Organized Structure**: Related metadata grouped in logical namespaces
4. **Extensible**: Easy to add new fields without breaking existing documents
5. **Human-Readable Errors**: Clear validation messages with examples
6. **Type Safety**: Comprehensive type and format validation
7. **Tool Friendly**: Works with existing markdown editors and processors

## Consolidation of Metadata (Replacing +++meta Blocks)

The new schema consolidates all metadata into the single YAML front-matter block at the beginning of the document. Separate `+++meta` blocks in the document body are no longer supported.

**Example of All Metadata in Front-matter:**
```yaml
---
title: Document
authors: [...]
links: [...]
dates:
  created: "2025-05-29T10:00:00Z" # Was potentially in a +++meta block
metrics:
  word_count: 247 # Was potentially in a +++meta block
# ... other standard and custom metadata fields ...
---

# Content
```

This approach follows the design philosophy that "ALL metadata should be in the front-matter YAML block" for maximum compatibility and editability.