# ORMD 0.1 Specification (MVP)

**Version:** 0.1 | **Date:** 2025-05-28

---

## 1. Overview

Open Relational Markdown (`.ormd`) 0.1 is a minimal specification that:

* Extends CommonMark with a lightweight relational layer.
* Defines a canonical plain-text or ZIP-packed package.
* Embeds verifiable metadata and versioning.

This spec is intentionally limited to core syntax, packaging, and validation rules. Features like CRDT change-feeds and embedded comments will follow in v0.2.

## 2. File Version Tag

Every `.ormd` file **MUST** begin with an HTML comment version marker:

```ormd
<!-- ormd:0.1 -->
```

* Ensures toolchains can detect and validate against the correct spec.

## 3. Base Syntax

1. **CommonMark 0.30** compliance for all Markdown constructs.
2. **YAML front-matter** uses `+++` delimiters on lines by themselves to open and close the block.
   *   The original `---` delimiters are also supported for backward compatibility.
   *   The parser implementation has been updated to a more robust state machine, which correctly distinguishes these delimiters from thematic breaks (`---`) or other `+++` sequences within the document body.

```ormd
<!-- ormd:0.1 -->
+++
title: Example
authors:
  - id: alice
    display: Alice L.
links: []
+++
# Heading

Body text…
```

### 3.3 Metadata Blocks

Beyond front-matter, ORMD allows for arbitrary metadata blocks to be embedded within the document body. These blocks are delimited as follows:

*   **Opening Delimiter:** `+++meta <optional_id>` on a line by itself.
    *   `<optional_id>` is an alphanumeric string used to identify the metadata block.
    *   If `<optional_id>` is omitted, the block is assigned a default identifier (e.g., "default" or an auto-generated sequence).
*   **Closing Delimiter:** `+++end-meta` on a line by itself.
*   **Content:** The content between these delimiters is treated as a raw string. It can be any format (e.g., YAML, JSON, plain text). The interpretation of this content is up to the tooling or application processing the ORMD document.

```ormd
<!-- ormd:0.1 -->
+++
title: Document with Metadata Blocks
links: []
+++
# Content Section 1

Some text.

+++meta custom_data
info: Additional custom data
format: yaml
values:
  - item1
  - item2
+++end-meta

# Content Section 2

More text.

+++meta notes
This is a plain text metadata block, perhaps for editor notes or annotations.
+++end-meta
```
The state machine parser correctly identifies these blocks and separates their content from the main document body.

## 4. Relational Layer

### 4.1 Front-Matter Field `links:`

* Must be a YAML **list of objects** each with keys:

  * `id` — unique identifier (string)
  * `rel` — relation type (string, e.g. `supports`, `refutes`)
  * `to` — target URI or internal anchor

```yaml
links:
  - id: g1
    rel: supports
    to: "#goal"
```

### 4.2 Inline Shortcut `[[link-id]]`

* Anywhere in the body, `[[g1]]` expands to a hyperlink to the target defined in front-matter.

```ormd
See [[g1]] for the goal section.
```

## 5. Packaging

A `.ormd` artifact **MUST** be one of:

1. **Plain `.ormd` file** (text-only): contains version tag, front-matter, and body.
2. **Zipped package** (`.ormd` extension on a zip): with this structure:

```
archive.ormd/
├── content.ormd      # canonical text file
├── meta.json         # JSON-LD metadata & signatures
├── ops/              # optional CRDT binary patches
└── render.css        # default stylesheet for HTML/print
```

* Tools must prefer unpacking the zip and validating `content.ormd`.

## 6. Metadata & Signatures

* **meta.json** follows JSON-LD, containing at least:

  * `@context`: JSON-LD context URL or inline.
  * `title`, `authors`, `created`, `modified`.
  * `provenance` object with C2PA-style hash chain and signature references.

```json
{
  "@context": "https://openrel.org/ormd/context.jsonld",
  "title": "Example",
  "authors": [...],
  "provenance": {
    "hash": "SHA256:...",
    "sigRef": "provenance.sig"
  }
}
```

* Detached signature file (e.g. `provenance.sig`) may accompany the package.

## 7. Validation

An `.ormd` validator **MUST** check:

1. Presence and correct format of version tag.
2. Valid YAML front-matter and required keys.
3. CommonMark-compliant body parse.
4. Every `[[id]]` matches a `links.id` entry.
5. For packages: existence of `content.ormd` and `meta.json`.

Failure to meet any rule **MUST** result in a non-zero exit code.

## 8. Example: Hello ORMD

```ormd
<!-- ormd:0.1 -->
+++
title: Hello ORMD
authors:
  - id: daniel.pace
    display: Daniel Pace
links:
  - id: g1
    rel: supports
    to: "#goal"
+++
# Hello ORMD

This is a **living document** that combines Markdown and semantic links.

See [[g1]] for the guiding principle.

## <a id="goal"></a>Goal

Open. Relational. Markdown.
```

## 9. Test Vectors

* **Missing version tag** → invalid.
* **Broken YAML** in front-matter → invalid.
* **Undefined `[[link]]`** → invalid.
* **Valid plain `.ormd`** → valid.
* **Valid zipped `.ormd`** with correct structure → valid.

## 10. CLI Commands (v0.1)

* `ormd-cli validate [file.ormd|package.ormd]`
* `ormd-cli pack content.ormd meta.json [--out=package.ormd]`
* `ormd-cli unpack package.ormd --out-dir=./`

## 11. Next Steps (for v0.2)

* CRDT change-feed embedding and merge rules.
* Inline commenting and annotation syntax.
* GUI reference implementation and Conformance Test Suite.

---


