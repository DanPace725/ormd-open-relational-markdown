# ORMD TextMate Grammar Update Notes

Date: 2025-06-01

This document summarizes the refinements made to the ORMD TextMate grammar (`syntaxes/ormd.tmLanguage.json`).

## Key Changes and Enhancements:

1.  **Improved Structure:**
    *   The top-level `patterns` now clearly separate the document into `#frontmatter` and a `#markdown_body`. This ensures that front-matter is parsed first and distinctly from the rest of the document.

2.  **Front-matter Highlighting:**
    *   The `#frontmatter` rule remains robust using `^---$` for `begin` and `end` delimiters.
    *   `beginCaptures` and `endCaptures` were added to specifically scope the `---` delimiters themselves (as `punctuation.definition.heading.yaml`).
    *   The content within the front-matter continues to be highlighted by including `source.yaml`, relying on VSCode's built-in or another extension's YAML grammar. The scope was named `meta.embedded.block.frontmatter.yaml.ormd` for specificity.

3.  **ORMD Link Highlighting (`[[link-id]]`):**
    *   The rule for ORMD links (now `#ormd_link`) was refined:
        *   It uses `(\\[\\[)([^\\]]+)(\\]\\])` to capture the opening brackets, the link ID, and the closing brackets separately.
        *   Distinct scopes are applied:
            *   `markup.underline.link.ormd` for the whole link.
            *   `punctuation.definition.link.begin.ormd` for `[[`.
            *   `markup.underline.link.internal.ormd` for the `link-id` itself.
            *   `punctuation.definition.link.end.ormd` for `]]`.
        *   This allows for more granular styling if desired.

4.  **Markdown Body Content:**
    *   A new `#markdown_body` section was introduced in the repository.
    *   Its `patterns` array first tries to match `#ormd_link`.
    *   It then includes `text.html.markdown`. This strategy aims to ensure that custom ORMD links are correctly identified and highlighted, even when they appear within standard Markdown structures. The `text.html.markdown` grammar is expected to provide comprehensive highlighting for common Markdown elements like headers, lists, bold, italics, code blocks, etc.

5.  **Comments:**
    *   Comments (`"comment": "..."`) were added throughout the grammar JSON to explain the purpose of different sections and rules, improving maintainability.

## Rationale:

The primary goal of these refinements was to:
*   Ensure robust and distinct highlighting for ORMD-specific constructs (front-matter, `[[link-id]]`).
*   Leverage existing, comprehensive Markdown grammars (`text.html.markdown`) for standard Markdown features, rather than re-implementing them.
*   Improve the overall structure and readability of the grammar file.

These changes should provide a more accurate and useful syntax highlighting experience for ORMD documents.
