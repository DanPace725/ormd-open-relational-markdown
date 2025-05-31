# Contributing to ORMD

Thank you for contributing to the Open Relational Markdown (ORMD) project! This guide will help you set up your development environment and understand our workflows.

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- pip or poetry for dependency management

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ormd
```

2. Install the development version:
```bash
cd ormd_cli
pip install -e .
```

3. Install development dependencies:
```bash
pip install pytest pytest-cov black flake8
```

## Git Hooks for ORMD Validation

We provide git hooks that automatically validate ORMD files before commits to maintain code quality and prevent invalid documents from entering the repository.

### Installing the Pre-commit Hook

The pre-commit hook validates all staged `.ormd` files and blocks commits if validation errors are found.

#### Quick Setup

Run the setup script from the `ormd_cli` directory:

```bash
python hooks/setup_hooks.py install
```

#### Manual Setup

1. Copy the hook to your git hooks directory:
```bash
cp hooks/pre-commit-ormd .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### How the Hook Works

When you commit files, the hook will:

1. **Detect staged ORMD files** - Only `.ormd` files that are staged for commit
2. **Run validation** - Uses `ormd validate` on each file
3. **Show results** - Displays validation results with detailed error messages
4. **Block commits** - Prevents commit if any validation errors are found
5. **Allow warnings** - Commits proceed with warnings, but errors block the commit

#### Example Hook Output

**Success with warnings:**
```bash
🔍 Checking staged ORMD files...
Found 2 ORMD file(s) to validate:
  • docs/example.ormd
  • guides/tutorial.ormd

📝 Validating docs/example.ormd...
✅ docs/example.ormd is valid
   ⚠️  Link 'unused-ref' is defined but not referenced in document body

📝 Validating guides/tutorial.ormd...
✅ guides/tutorial.ormd is valid

✅ All 2 ORMD file(s) are valid. Commit allowed.
```

**Failure with errors:**
```bash
🔍 Checking staged ORMD files...
Found 1 ORMD file(s) to validate:
  • docs/invalid.ormd

📝 Validating docs/invalid.ormd...
❌ docs/invalid.ormd failed validation:
   ❌ Validation failed with 3 error(s):
   1. Missing required field 'title'. Add 'title: Your Document Title' to front-matter
   2. Unknown fields in front-matter: custom_field, experimental
   3. Undefined link reference [[bad-link]] - add definition to 'links' section or run 'ormd update' to sync

❌ Commit blocked: 1 ORMD file(s) failed validation

Failed files:
  • docs/invalid.ormd

Fix validation errors and try again, or use 'git commit --no-verify' to skip validation.
```

### Hook Management Commands

Test the installed hook:
```bash
python hooks/setup_hooks.py test
```

Uninstall the hook:
```bash
python hooks/setup_hooks.py uninstall
```

### Bypassing Validation

If you need to commit invalid ORMD files (e.g., for debugging or work-in-progress), you can bypass the hook:

```bash
git commit --no-verify -m "WIP: debugging validation issues"
```

**Note:** Use `--no-verify` sparingly, as invalid ORMD files should generally not be committed to the main branch.

## Validation Rules

The pre-commit hook enforces the same validation rules as `ormd validate`:

### Phase 1 Requirements

- **Version tag**: `<!-- ormd:0.1 -->` at the top
- **Required fields**: `title`, `authors`, `links` in front-matter
- **Schema compliance**: Only Phase 1 allowed fields
- **Link consistency**: All `[[link-id]]` references must be defined in `links`
- **Asset existence**: All paths in `asset_ids` must exist on disk

### Allowed Front-matter Fields

**Required:**
- `title` (string)
- `authors` (list of strings or objects)
- `links` (list of link objects)

**Optional organized metadata:**
- `dates` (object with `created`, `modified`)
- `metrics` (object with `word_count`, `reading_time`)
- `permissions` (object with `mode`, `editable`, `signed`)

**Optional simple fields:**
- `version`, `status`, `description`, `language`, `license`, `keywords`

**Auto-populated fields (from `ormd update`):**
- `link_ids`, `asset_ids`

## Development Workflow

### 1. Making Changes

1. Create a feature branch:
```bash
git checkout -b feature/my-feature
```

2. Make your changes to ORMD files or code

3. Update ORMD files if needed:
```bash
ormd update docs/my-document.ormd
```

4. Validate your changes:
```bash
ormd validate docs/my-document.ormd
```

### 2. Committing Changes

1. Stage your files:
```bash
git add docs/my-document.ormd
```

2. Commit (hook will run automatically):
```bash
git commit -m "Add new documentation for feature X"
```

3. If validation fails, fix the errors and try again:
```bash
# Fix validation errors
ormd validate docs/my-document.ormd  # Check status
git add docs/my-document.ormd       # Re-stage
git commit -m "Add new documentation for feature X"
```

### 3. Testing

Run the test suite:
```bash
pytest tests/
```

Run validation tests specifically:
```bash
pytest tests/test_validator*.py -v
```

### 4. Code Quality

We use the following tools for code quality:

- **Black** for code formatting:
```bash
black src/ormd_cli/
```

- **Flake8** for linting:
```bash
flake8 src/ormd_cli/
```

- **pytest** for testing:
```bash
pytest tests/ --cov=src/ormd_cli/
```

## Writing ORMD Documents

### Best Practices

1. **Always include required fields**:
```yaml
---
title: "Clear, Descriptive Title"
authors: ["Your Name <email@example.com>"]
links: []  # At minimum, empty list
---
```

2. **Use semantic links consistently**:
```yaml
links:
  - id: "related-doc"
    rel: "supports"
    to: "other-document.ormd"
```

Then reference in body: `See [[related-doc]] for details.`

3. **Keep front-matter organized**:
```yaml
---
# Required fields first
title: "Document Title"
authors: ["Author Name"]
links: []

# Organized metadata
dates:
  created: "2025-01-01T10:00:00Z"
metrics:
  word_count: 150
  reading_time: "2 min"

# Simple optional fields
version: "1.0"
status: "published"
keywords: ["documentation", "guide"]
---
```

4. **Run updates before committing**:
```bash
ormd update docs/my-document.ormd
```

This auto-populates `date_modified`, `word_count`, `link_ids`, and `asset_ids`.

### Common Validation Errors

1. **Missing required fields**:
```
Missing required field 'title'. Add 'title: Your Document Title' to front-matter
```
**Fix**: Add the missing field to your front-matter.

2. **Unknown fields**:
```
Unknown fields in front-matter: custom_field
Phase 1 only allows these fields: title, authors, links, dates, metrics, ...
```
**Fix**: Remove the unknown field or move it to an allowed namespace.

3. **Undefined link references**:
```
Undefined link reference [[my-link]] - add definition to 'links' section
```
**Fix**: Add the link definition to your `links` array or run `ormd update`.

4. **Missing assets**:
```
Asset not found: images/diagram.png
```
**Fix**: Create the asset file or remove it from `asset_ids`, then run `ormd update`.

## Troubleshooting

### Hook Not Running

- Check if the hook is installed: `ls -la .git/hooks/pre-commit`
- Verify it's executable: `chmod +x .git/hooks/pre-commit`
- Test manually: `python hooks/setup_hooks.py test`

### ORMD CLI Not Found

- Install in development mode: `pip install -e .`
- Check Python path: `python -c "import ormd_cli; print(ormd_cli.__file__)"`
- Use absolute path in hook if needed

### Validation Seems Wrong

- Test manually: `ormd validate path/to/file.ormd --verbose`
- Check file encoding (should be UTF-8)
- Verify front-matter YAML syntax

## Contributing Guidelines

1. **All ORMD files must pass validation** before merging
2. **Add tests** for new validation rules or features
3. **Update documentation** when changing validation behavior
4. **Use descriptive commit messages** that explain the change
5. **Include issue references** in commit messages when applicable

## Getting Help

- **Documentation issues**: Open an issue with the `documentation` label
- **Validation bugs**: Open an issue with the `validation` label
- **Hook problems**: Open an issue with the `git-hooks` label
- **General questions**: Start a discussion in the repository

## Review Process

1. **Automated checks**: All commits are validated by the pre-commit hook
2. **CI validation**: Pull requests run full test suite including validation tests
3. **Manual review**: Maintainers review changes for correctness and style
4. **Documentation review**: ORMD documents are reviewed for clarity and accuracy

Thank you for helping improve ORMD! 🎉 