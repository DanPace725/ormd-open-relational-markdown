# ORMD VSCode Extension: Next Steps and Advanced Features Plan

## 1. Introduction

This document outlines the immediate next steps for enhancing the ORMD VSCode extension, focusing on integrating core ORMD CLI functionalities. It also includes a preliminary assessment of adopting the Language Server Protocol (LSP) for more advanced features in the future. This plan is based on the analysis of the existing ORMD CLI components and aligns with the goals set out in the initial project instructions.

## 2. Validator Integration for Live Diagnostics

The ORMD CLI has a robust `validator.py` module, which is highly reusable for providing live diagnostics (linting) within the VSCode editor.

**Identified Core Validation Components (from `cli_analysis.md`):**

*   `ormd_cli.validator.ORMDValidator`: The main class for validation.
    *   `validate_file(file_path)`: Method that orchestrates validation. While it takes a file path, its internal logic largely relies on parsing content and applying rules.
    *   The validator collects errors and warnings in `self.errors` and `self.warnings` lists.
*   `ormd_cli.parser.parse_document(content)`: Used by the validator to get front-matter and body.
*   `ormd_cli.schema.validate_front_matter_schema(front_matter_dict)`: Used to validate the front-matter structure.

**Strategy for Integration:**

1.  **Python Execution Environment:**
    *   The extension will need to execute Python code. This could be achieved by:
        *   Requiring the user to have Python installed and the `ormd_cli` package available in their environment (e.g., in the active Python interpreter or a virtual environment). The extension would then spawn a Python process to call the validation logic.
        *   Alternatively, bundling a minimal Python interpreter and the necessary ORMD CLI scripts with the extension (more complex, increases extension size, but fewer user prerequisites).
    *   For now, assume the user has Python and `ormd_cli` accessible. The extension should allow configuration of the Python path.

2.  **Triggering Validation:**
    *   **On File Open:** When an `.ormd` file is opened.
    *   **On File Change:** When the content of an active `.ormd` document is modified. This should be debounced (e.g., trigger 500ms after the last keystroke) to avoid excessive validation calls during typing.
    *   **On File Save:** When an `.ormd` file is saved.

3.  **Passing File Content:**
    *   The VSCode extension will get the current document content as a string using `vscode.TextDocument.getText()`.
    *   This string content will be passed to a Python script that acts as a bridge to the `ORMDValidator`. The Python script will need to be modified or a new entry point created to accept content via stdin or a temporary file, rather than just a file path, if `ORMDValidator.validate_file` cannot be easily adapted to take string content directly.
    *   Alternatively, and preferably, refactor `ORMDValidator` slightly to have a method like `validate_content(content_string: str, base_dir_for_assets: str) -> Tuple[List[str], List[str]]` that returns errors and warnings. The `base_dir_for_assets` would be the directory of the document being edited, needed for asset validation.

4.  **Receiving Validation Results:**
    *   The Python bridge script will call the ORMD validator logic.
    *   Results (lists of errors and warnings, including line numbers if available from the validator, and messages) should be formatted as JSON and printed to stdout by the Python script.
    *   The VSCode extension will capture this JSON output. Line number information is critical; the `ORMDValidator` might need enhancements if it doesn't already provide precise line/character ranges for errors. (Currently, it seems to return lists of error strings; these would need to be parseable or structured to include ranges).

5.  **Displaying Results in VSCode:**
    *   Use the `vscode.languages.createDiagnosticCollection()` API.
    *   For each error/warning from the validator:
        *   Create a `vscode.Diagnostic` object.
        *   Specify the `range` (requires line/character information from the validator). If only line numbers are available, the range can span the whole line.
        *   Set the `message`.
        *   Set the `severity` (`vscode.DiagnosticSeverity.Error` or `vscode.DiagnosticSeverity.Warning`).
    *   Update the `DiagnosticCollection` with the diagnostics for the processed document. This will display squiggles in the editor and list problems in the "Problems" panel.

**Challenges:**

*   **Python Interoperability:** Managing the Python process, ensuring dependencies are met, and handling data exchange (string content in, JSON results out) requires careful implementation.
*   **Line/Character Ranges:** The current `ORMDValidator` primarily returns error messages as strings. For precise squiggles, it needs to be adapted to also return start/end line and character positions for each issue. This might involve changes to the parser and validator logic to track positions.
*   **Performance:** For very large ORMD files, running Python validation on every change (even debounced) might impact performance. Strategies like validating only the changed sections (if feasible) or optimizing the Python validator could be explored if this becomes an issue. For now, full document validation is the initial approach.
*   **Asset Path Resolution:** The `_validate_asset_existence` function in `validator.py` uses `base_dir`. This needs to be correctly set to the workspace folder containing the ORMD file when validating content from the editor.

## 3. Command Palette Integration

Exposing key ORMD CLI functionalities via the VSCode Command Palette will improve user workflow.

**Identified CLI Commands for Integration (from `instructions_for_jules.ormd` and `cli_analysis.md`):**

*   `validate`
*   `pack`
*   `render` (Potential for live preview or render-to-file)
*   `update` (To update metadata like word count, dates, link_ids)

**Proposed Command Palette Entries:**

1.  **ORMD: Validate Document**
    *   **Command ID:** `ormd.validateDocument`
    *   **Display Name:** "ORMD: Validate Document"
    *   **Action:**
        *   Triggers the validation process described in Section 2 for the currently active `.ormd` editor.
        *   Focuses the "Problems" panel to show results.
    *   **Interaction:** Uses the active ORMD file.
    *   **Feedback:** Diagnostics in "Problems" panel; an information message like "ORMD validation complete. X errors, Y warnings found."

2.  **ORMD: Update Metadata**
    *   **Command ID:** `ormd.updateMetadata`
    *   **Display Name:** "ORMD: Update Document Metadata (dates, word count, links)"
    *   **Action:**
        *   Retrieves the content of the active `.ormd` editor.
        *   Uses the reusable logic from `ORMDUpdater` (specifically `_compute_updates` and related helpers like `_extract_link_ids`, `_count_words`) to calculate new front-matter values.
        *   Uses `parser.serialize_front_matter` to create the new front-matter string.
        *   Replaces the existing front-matter in the editor with the new one using VSCode's document editing APIs (e.g., `TextEditor.edit`).
    *   **Interaction:** Modifies the active ORMD file directly in the editor.
    *   **Feedback:** Information message "ORMD metadata updated." or error notification if parsing/updating fails.

3.  **ORMD: Pack Document**
    *   **Command ID:** `ormd.packDocument`
    *   **Display Name:** "ORMD: Pack ORMD Document"
    *   **Action:**
        *   This command is more complex as typical ORMD packages might involve a `content.ormd` and a separate `meta.json`. The current editor context is usually a single file.
        *   **Option A (Simple):** If the active file is `content.ormd` and a `meta.json` exists in the same directory, prompt the user for an output package name (e.g., `package.ormd`). Then use `ORMDPackager.pack()`.
        *   **Option B (More Flexible):** Prompt user to select the main content file (`.ormd`) and the metadata file (`.json`), then prompt for output package name.
        *   For initial implementation, Option A might be simpler if a common project structure is assumed.
    *   **Interaction:** Operates on files in the workspace. May prompt user for input (output file name, source files if Option B).
    *   **Feedback:** Information message "ORMD package created at [path]." or error notification. An output channel could show detailed logs from the packager.

4.  **ORMD: Render Document to HTML**
    *   **Command ID:** `ormd.renderDocument`
    *   **Display Name:** "ORMD: Render Document to HTML File"
    *   **Action:**
        *   Takes the active `.ormd` file.
        *   Uses logic similar to the CLI's `render` command (parsing via `parse_document`, Markdown rendering, applying `HTML_TEMPLATE` from `utils.py` or a new template).
        *   Prompts the user for an output HTML file path (defaulting to `<filename>.html`).
        *   Writes the generated HTML to the specified file.
    *   **Interaction:** Operates on the active ORMD file, creates a new HTML file.
    *   **Feedback:** Information message "Document rendered to [html_file_path]." and potentially an option to open the rendered file.

**Considerations for Commands:**

*   **Python Dependency:** All these commands would likely rely on invoking the Python-based ORMD CLI logic.
*   **User Prompts:** `vscode.window.showInputBox()` for filenames/paths, `vscode.window.showQuickPick()` for options.
*   **Output Channels:** `vscode.window.createOutputChannel()` can be used for detailed logs from these operations.
*   **Configuration:** Settings for Python path, default output locations, etc., might be needed.

## 4. Language Server Protocol (LSP) Assessment

**What is LSP?**

The Language Server Protocol (LSP) is a protocol developed by Microsoft that standardizes communication between development tools (like VSCode) and language-specific servers. The language server runs as a separate process and provides features like auto-completion, go-to-definition, hover information, diagnostics, etc., to the editor via the protocol.

**Benefits of LSP:**

*   **Offloading Processing:** Heavy language analysis is done in a separate server process, preventing UI freezes in the editor.
*   **Rich Features:** Enables advanced IntelliSense (context-aware completions), code navigation (go-to-definition, find references), hover information, and more sophisticated refactoring.
*   **Multi-Editor Support:** A single language server can provide language features to multiple editors that support LSP (VSCode, Neovim, Sublime Text, Eclipse, etc.), reducing effort to support various tools.
*   **Decoupling:** The language-specific logic is cleanly separated from the editor-specific UI code.

**Applicability to ORMD:**

*   **Current State:** For the features planned immediately (syntax highlighting via TextMate, diagnostics via Python script, basic commands), a full LSP might be overkill. Direct integration of the Python CLI's reusable parts seems sufficient for now.
*   **Future Potential / Complexity of ORMD:**
    *   **Link Analysis:** ORMD's `[[link-id]]` syntax implies relationships. An LSP could provide:
        *   Auto-completion for existing `link-id`s in the document or workspace.
        *   Go-to-definition for `[[link-id]]` to jump to its definition in the `links` array in front-matter (or vice-versa).
        *   Validation of whether a `[[link-id]]` actually corresponds to a defined link.
        *   Hover information showing details of a link.
    *   **Relational Aspects:** If ORMD evolves to have more complex relational semantics (e.g., transclusion, queries across documents), an LSP would be highly beneficial to manage this complexity.
    *   **Schema-Aware Completions:** Auto-completion for front-matter fields based on `schema.py`.
    *   **Custom Snippets:** Dynamic snippets based on document context.

*   **Effort:**
    *   Building a robust LSP requires significant effort. It involves designing the server, implementing the protocol handlers, and managing the server's lifecycle.
    *   However, libraries exist in Python (e.g., `pygls`) that simplify LSP development. Given that the core ORMD logic is already in Python, this is a plus.

**Preliminary Recommendation:**

*   **Short-Term (Next 1-3 feature cycles):** Direct integration of the Python CLI's reusable modules for validation and commands is the more pragmatic approach. This will deliver value faster.
*   **Long-Term:** **Strongly consider developing an ORMD Language Server if:**
    *   The ORMD language gains more complex features around inter-document linking, queries, or semantic analysis.
    *   There's a desire for rich IntelliSense (e.g., context-aware completion of link IDs, front-matter keys based on schema).
    *   Support across multiple LSP-compatible editors becomes a goal.
*   The initial direct integration can be seen as a stepping stone. The Python logic developed for direct use (e.g., refined validator that returns structured data with ranges) can be later incorporated into an LSP.

## 5. Conclusion

The ORMD VSCode extension has a solid foundation with basic language support. The immediate next steps should focus on leveraging the existing ORMD CLI's Python codebase to provide users with in-editor diagnostics and useful commands. While direct integration is suitable for now, planning for a potential transition to a Language Server Protocol (LSP) architecture in the future is advisable to support more advanced IntelliSense and relational features as ORMD evolves.
