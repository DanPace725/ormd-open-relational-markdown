# ormd-cli

**A command-line tool for working with Open Relational Markdown (`.ormd`) files**

---

## 🚀 Project Overview

`ormd-cli` provides lightweight commands to **validate**, **pack**, and **unpack** `.ormd` documents—combining the simplicity of Markdown with a relational metadata layer and open packaging.

* **Validate**: Ensure your `.ormd` file adheres to the 0.1 spec
* **Pack**: Bundle your text and metadata into a single `.ormd` package
* **Unpack**: Extract content for editing or inspection

Learn more in the [ORMD 0.1 Specification](https://github.com/open-relational-markdown/spec/blob/main/ormd-0.1.md).

---

## ⚙️ Prerequisites

* **Node.js** (>= 16) or **Rust** toolchain (see language-specific section below)
* **Git** for cloning the repo

---

## 🛠️ Installation

### Rust (recommended)

```bash
# Clone the repo
git clone https://github.com/open-relational-markdown/ormd-cli.git
cd ormd-cli
# Build release binary
cargo build --release
# (Optional) Install globally
cargo install --path .
```

### Node.js

```bash
git clone https://github.com/open-relational-markdown/ormd-cli.git
cd ormd-cli
npm install
npm run build
# (Optional) Link for local use
npm link
```

---

## 📚 Usage

> All commands support `--help` for detailed options.

### 1. Validate

Check a file or package against the ORMD 0.1 spec:

```bash
ormd-cli validate path/to/document.ormd
```

The validator supports the latest ORMD format specifications:
*   **Front-matter:** Uses `+++` delimiters (e.g., for YAML metadata). The older `---` delimiters are also supported for backward compatibility.
*   **Metadata Blocks:** Supports `+++meta <optional_id> ... +++end-meta` blocks for structured metadata within the document body.
*   **Robust Parsing:** The underlying parser uses a state machine for improved accuracy in distinguishing delimiters from document content.

* **Success:** Exit code `0`
* **Failure:** Non-zero exit code and printed errors

### 2. Update

Auto-populate and sync front-matter fields in your ORMD documents:

```bash
ormd-cli update path/to/document.ormd
```

The update command automatically computes and updates:
* **`dates.modified`** — Current timestamp in ISO 8601 format
* **`metrics.word_count`** — Word count of the document body (excluding code blocks)
* **`metrics.reading_time`** — Estimated reading time based on word count
* **`link_ids`** — All `[[id]]` references found in the document
* **`asset_ids`** — All local asset references (images, PDFs, etc.)

**Options:**
* `--dry-run` — Show what would be updated without making changes
* `--force-update` — Update even locked fields (ignore `locked: true`)
* `--verbose` — Show detailed information about changes

**Locking fields:** Add `locked: true` or `locked: ["field_name"]` to prevent updates:

```yaml
dates:
  created: "2025-01-01T00:00:00Z"
  modified: "2025-01-01T00:00:00Z"
  locked: ["modified"]  # Don't update the modified date

metrics:
  word_count: 50
  reading_time: "1 min"
  locked: true  # Don't update any metrics
```

### 3. Pack

Bundle a plain `.ormd` and `meta.json` into a single package:

```bash
ormd-cli pack content.ormd meta.json --out packaged.ormd
```

### 4. Unpack

Extract a zipped `.ormd` for editing:

```bash
ormd-cli unpack packaged.ormd --out-dir ./work
```

---

## 🏗️ Examples

See the `examples/` directory for working samples:

* **`examples/hello.ormd`** — Simple living document
* **`examples/invoice.ormd`** — Sample invoice with metadata

---

## 🤝 Contributing

We welcome all contributions! Please:

1. Fork the repo & create a new branch (`feature/xxx`)
2. Run tests and ensure linting passes
3. Submit a PR with clear descriptions and test cases

Read our [CONTRIBUTING.md](.github/CONTRIBUTING.md) for more details.

---

## 📝 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

*ormd-cli* — building the future of living documents, one command at a time.
