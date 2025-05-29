# ORMD (Open Relational Markdown)

> **Living, relational documents for humans and machines.**

---

## 🚀 Project Overview

ORMD is a next-generation document format that combines the simplicity and ubiquity of Markdown with a relational metadata layer, verifiable provenance, and open packaging. Our goal is to empower authors and readers with documents that are:

* **Readable & writable** as plain text
* **Inspectable & editable** anywhere
* **Relational**—connect ideas semantically
* **Integrity-preserving** with digital signatures
* **Collaborative** and future-proof

This monorepo contains all you need to **spec**, **build**, and **demo** ORMD.

---

## ✨ ORMD Format Update

ORMD has recently updated its format specification to enhance clarity and parsing robustness:

*   **Front-matter:** Now uses `+++` on lines by themselves to open and close the front-matter block.
*   **Metadata Blocks:** A new structured format `+++meta <optional_id>` (to open) and `+++end-meta` (to close) allows for embedding distinct metadata sections within the document body. If `<optional_id>` is omitted, it defaults to a standard identifier (e.g., "default").
*   **Parsing:** The reference parser has been upgraded to a state machine implementation. This makes parsing more robust and avoids previous ambiguities if `---` or `+++` sequences appeared in the document body.
*   **Backward Compatibility:** The original `---` delimiters for front-matter are still fully supported for backward compatibility with existing documents.

These updates are reflected in the [ORMD 0.1 specification](./spec/ormd-0.1.md) and supported by the `ormd-cli` tool.

---

## 📁 Repository Structure

```
ormd/                   ← Monorepo root
├── README.md           ← (This file) High-level overview & navigation
├── spec/               ← ORMD 0.1 specification, test vectors, and context
│   └── ormd-0.1.md     ← Core spec document
├── cli/                ← `ormd-cli` command-line tool
│   ├── README.md       ← Usage & installation for CLI
│   └── src/            ← Source code for `ormd-cli`
├── examples/           ← Sample ORMD documents (plain & packaged)
│   ├── hello.ormd
│   └── invoice.ormd.zip
├── docs/               ← (Optional) Tutorials, deep dives, roadmaps
└── .github/            ← Issue & PR templates, workflows, contributing GUIDELINES
```

---

## 🏁 Getting Started

1. **Read the Spec**: everything begins with the [ORMD 0.1 specification](./spec/ormd-0.1.md).
2. **Try the CLI**:

   * Jump into the `cli/` directory and follow its [README](./cli/README.md).
3. **Explore Examples**:

   * Open `examples/hello.ormd` in your favorite editor.
   * Unpack and inspect `examples/invoice.ormd.zip`.
4. **Contribute**:

   * Check out [CONTRIBUTING.md](./.github/CONTRIBUTING.md) for guidelines.

---

## 📦 CLI (ormd-cli)

`ormd-cli` provides commands to validate, pack, and unpack ORMD documents. See [`cli/README.md`](./cli/README.md) for details.

---

## 📘 Specification (spec)

The `spec/` directory holds the official ORMD 0.1 spec, including syntax rules, packaging format, metadata structure, and validation criteria.

---

## 🔌 Examples

Browse the `examples/` folder to see real `.ormd` files in action, including:

* **hello.ormd** — A simple living document example
* **invoice.ormd.zip** — A signed invoice package

---

## 🤝 Contributing

We welcome all contributions! Please:

1. Review our [Code of Conduct](./.github/CODE_OF_CONDUCT.md).
2. Read [CONTRIBUTING.md](./.github/CONTRIBUTING.md) for workflow and style.
3. Open issues, discuss features, and submit PRs under the `open-relational-markdown` GitHub org.

---

## ⚖️ License

The spec is published under **CC0**. Tooling and examples are under **MIT** or **Apache-2.0**—see each subproject for details.

---

*ORMD: Dog-food from day one. Build living, relational documents that respect human authorship and collaboration.*
