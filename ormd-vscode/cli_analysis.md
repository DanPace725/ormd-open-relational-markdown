# ORMD CLI Reusable Components Analysis

This document analyzes the ORMD CLI (`ormd_cli/src/ormd_cli/`) to identify components that can be reused for the ORMD VSCode extension.

## Overall Summary

The ORMD CLI is structured with a `main.py` that handles Click command definitions and user interaction, while core logic for parsing, validation, metadata updates, and packaging is mostly encapsulated in separate modules. This separation is beneficial for reuse.

**Most Promising Modules for Reuse:**

*   **`parser.py`**: Core functions for parsing ORMD file content (front-matter and body) and serializing front-matter back to string. Essential for the extension.
*   **`schema.py`**: Defines the ORMD front-matter data structure (via dataclasses) and provides schema validation. Crucial for understanding front-matter and validating it.
*   **`validator.py`**: Contains the `ORMDValidator` class, which performs comprehensive validation of ORMD documents. Key for providing diagnostics (linting) in the editor.
*   **`updater.py`**: The `ORMDUpdater` class, particularly its methods for calculating dynamic fields (word count, link/asset IDs, dates), is highly reusable for features like "update metadata on save" or specific commands.
*   **`packager.py`**: The `ORMDPackager` class can be used directly if the extension needs to support ORMD package creation or extraction.

**General Challenges for Integration:**

*   **CLI Coupling in `main.py`**: `main.py` is tightly coupled with the `click` library. Its direct functions are not reusable, but it serves as a good example of how the core modules are orchestrated.
*   **User Feedback and Error Handling**: The CLI uses `click.echo` for output. The VSCode extension will need to use VSCode-specific APIs for diagnostics, notifications, etc. The core modules that return errors as lists of strings or structured objects are well-suited for this adaptation.
*   **File I/O vs. Editor Content**: Some CLI functions operate on file paths. The extension will primarily work with document content from the editor. Most core logic functions (e.g., `parse_document`) already accept string content, which is ideal.
*   **HTML Rendering/Web Server**: The `render`, `open`, and `edit` commands in `main.py` include HTML generation and a local web server. For a VSCode live preview, this logic would need to be significantly re-architected to use VSCode Webviews, though some underlying parsing and HTML snippet generation might be adaptable.

---

## File-by-File Analysis

### 1. `main.py`

*   **Purpose**: Defines the CLI application structure and commands using the `click` library. Orchestrates calls to other modules.
*   **Key Components**:
    *   `cli`: Main `click.group`.
    *   `validate`, `pack`, `unpack`, `update`, `render`, `open`, `edit`: Click commands.
    *   `_generate_viewable_html`, `_generate_editable_html`: Helper functions for HTML generation for the `open` and `edit` commands.
    *   `_serve_and_open`: Helper to run a local HTTP server.
*   **Inputs/Outputs**: Varies by command; generally file paths as input, console messages or files as output.
*   **Dependencies**: `click`, `markdown`, `yaml`, `pathlib`, and all other local modules (`validator`, `packager`, `updater`, `parser`, `utils`).
*   **Reusability Assessment**:
    *   **Low direct reusability**: Due to heavy reliance on `@click` decorators and `click.echo` for UI.
    *   **Indirect value**: Shows how core logic modules are used.
    *   The HTML generation functions (`_generate_..._html`) and the Markdown rendering logic within the `render` command contain logic that could be adapted for a live preview feature in the VSCode extension, but would require decoupling from Click and the HTTP server.

### 2. `packager.py`

*   **Purpose**: Handles the creation (.ormd zip) and extraction of ORMD package files.
*   **Key Components**:
    *   `ORMDPackager` class:
        *   `pack(content_file: str, meta_file: str, output: str) -> bool`: Creates a zip archive.
        *   `unpack(package_file: str, output_dir: str) -> bool`: Extracts a zip archive.
*   **Inputs/Outputs**: File paths for inputs, boolean success status for outputs.
*   **Dependencies**: `zipfile`, `json`, `pathlib`.
*   **Reusability Assessment**:
    *   **High**: The class is self-contained and uses standard libraries. It can be imported and used directly if the VSCode extension requires ORMD package management features.

### 3. `parser.py`

*   **Purpose**: Provides functions to parse an ORMD document string into its constituent parts (front-matter dictionary and body string) and to serialize front-matter back.
*   **Key Components**:
    *   `parse_document(content: str) -> Tuple[Optional[Dict], str, Optional[Dict[str, str]], List[str]]`: The main parsing function. Takes raw ORMD string content. Returns front-matter dict, body string, (deprecated) metadata dict, and a list of parsing error strings.
    *   `_parse_front_matter_and_body(content: str)`: Internal helper.
    *   `_extract_yaml_block(content: str, delimiter: str)`: Internal helper.
    *   `migrate_legacy_metadata(front_matter: Dict, legacy_metadata: Optional[Dict[str, str]]) -> Dict`: For migrating older ORMD formats.
    *   `serialize_front_matter(front_matter: Dict) -> str`: Converts a front-matter dictionary back into a YAML string, ready for file insertion.
*   **Inputs/Outputs**: String content or dictionary for inputs; dictionary, string, and list of strings for outputs.
*   **Dependencies**: `re`, `yaml`.
*   **Reusability Assessment**:
    *   **Very High**: These functions are fundamental for the extension to understand and manipulate ORMD files. They are not tied to any CLI specifics. `parse_document` will be used for reading, and `serialize_front_matter` for writing changes.

### 4. `schema.py`

*   **Purpose**: Defines the data structure (schema) for ORMD front-matter using Python dataclasses and provides a validator for this schema.
*   **Key Components**:
    *   Dataclasses (`Author`, `Link`, `Permissions`, `Dates`, `Metrics`, `ORMDFrontMatter`): Define the expected structure of the front-matter.
    *   `FrontMatterValidator` class:
        *   `validate(self, front_matter: Dict[str, Any]) -> bool`: Validates a dictionary against the defined schema. Errors are stored in `self.errors`.
    *   `validate_front_matter_schema(front_matter: Dict[str, Any]) -> tuple[bool, List[str]]`: A utility function that uses `FrontMatterValidator`.
*   **Inputs/Outputs**: Dictionaries for input, boolean and list of error strings for output.
*   **Dependencies**: `dataclasses`, `typing`, `re`, `enum`.
*   **Reusability Assessment**:
    *   **Very High**: The dataclasses provide a clear object model for the front-matter, useful for IntelliSense and structured editing. The `FrontMatterValidator` is essential for validating changes made by the user or by automated processes.

### 5. `updater.py`

*   **Purpose**: Automatically updates dynamic front-matter fields like `date_modified`, `word_count`, `link_ids` (references like `[[link]]` in the body), and `asset_ids`.
*   **Key Components**:
    *   `ORMDUpdater` class:
        *   `update_file(self, file_path: str, dry_run: bool, force_update: bool, verbose: bool) -> Dict[str, Any]`: Orchestrates the update process for a file.
        *   `_compute_updates(self, front_matter: Dict[str, Any], body: str, force_update: bool) -> Dict[str, Any]`: Core logic for calculating new values for front-matter fields.
        *   `_update_dates`, `_update_metrics`, `_update_ids`: Implement logic for specific field categories.
        *   `_extract_link_ids(self, body: str) -> List[str]`: Finds all `[[link]]` style references.
        *   `_extract_asset_ids(self, body: str) -> List[str]`: Finds image and other asset references.
        *   `_count_words(self, text: str) -> int`: Calculates word count, excluding non-prose elements.
        *   `_write_updated_file(self, file_path: Path, original_content: str, updated_front_matter: Dict[str, Any])`: Reconstructs the file with updated front-matter.
*   **Inputs/Outputs**: File paths, dictionaries, strings. Outputs dictionaries summarizing changes or updated file content.
*   **Dependencies**: `re`, `yaml`, `datetime`, `pathlib`, `.parser`.
*   **Reusability Assessment**:
    *   **High**: The core logic methods (`_compute_updates`, `_extract_link_ids`, `_extract_asset_ids`, `_count_words`) are highly reusable. The file-based `update_file` and `_write_updated_file` methods contain logic that can be adapted for editor-based "update metadata" commands or on-save hooks.

### 6. `utils.py`

*   **Purpose**: Contains utility constants and functions, primarily for the CLI's HTML rendering and console output.
*   **Key Components**:
    *   `HTML_TEMPLATE`: A large string defining the HTML structure for the `render`, `open`, and `edit` commands.
    *   `get_symbols() -> dict`, `SYMBOLS`: Provide Unicode/ASCII symbols for CLI feedback.
*   **Inputs/Outputs**: `get_symbols` has no input, outputs a dict. `HTML_TEMPLATE` is a constant.
*   **Dependencies**: `sys`, `locale`.
*   **Reusability Assessment**:
    *   **Low to Medium**: `HTML_TEMPLATE` is specific to the CLI's rendering approach and would likely be replaced by Webview-specific HTML/CSS/JS in a VSCode extension. `SYMBOLS` are for CLI console output and not directly applicable to VSCode UI.

### 7. `validator.py`

*   **Purpose**: Validates ORMD documents against the specification, including schema checks, link consistency, and asset existence.
*   **Key Components**:
    *   `ORMDValidator` class:
        *   `validate_file(self, file_path: str) -> bool`: Main public method.
        *   `_check_version_tag(self, content: str) -> bool`: Validates `<!-- ormd:0.1 -->`.
        *   `_validate_required_fields_with_guidance(self, front_matter: Dict[str, Any]) -> bool`.
        *   `_validate_schema_strict(self, front_matter: Dict[str, Any]) -> bool`: Uses `schema.validate_front_matter_schema`.
        *   `_validate_semantic_link_consistency(self, front_matter: Dict[str, Any], body: str) -> bool`.
        *   `_validate_asset_existence(self, front_matter: Dict[str, Any], base_dir: Path) -> bool`.
        *   `get_validation_summary(self) -> str`: Returns a formatted string of errors/warnings.
*   **Inputs/Outputs**: File path or content strings/dictionaries for input. Boolean status and lists of error/warning strings as output.
*   **Dependencies**: `re`, `yaml`, `markdown`, `pathlib`, `.parser`, `.schema`.
*   **Reusability Assessment**:
    *   **Very High**: The `ORMDValidator` class is crucial for providing diagnostics in the VSCode extension. Its methods for collecting errors and warnings can be directly used, with the results transformed into VSCode `Diagnostic` objects. It's not tied to Click.
