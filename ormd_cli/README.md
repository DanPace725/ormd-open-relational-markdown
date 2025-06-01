# ormd-cli

**A command-line tool for working with Open Relational Markdown (`.ormd`) files**

---

## 🚀 Project Overview

`ormd-cli` provides lightweight commands to **create, validate, update, pack, unpack, render, convert, and interactively open/edit** `.ormd` documents—combining the simplicity of Markdown with a relational metadata layer and open packaging.

Learn more in the [ORMD 0.1 Specification](https://github.com/open-relational-markdown/spec/blob/main/ormd-0.1.md).

---

## ⚙️ Prerequisites

* **Python** (>= 3.8 recommended, as used by the CLI)
* **Git** for cloning the repo

---

## 🛠️ Installation

```bash
# Clone the repo
git clone https://github.com/open-relational-markdown/ormd-cli.git
cd ormd_cli

# Install the CLI (editable mode recommended for development)
pip install -e .

# Verify installation
ormd --version
# or
ormd --help
```
*Note: The original README mentioned Rust/Node.js; this has been updated to Python as per project structure.*

---

## 📚 CLI Commands

All commands support `--help` for detailed options directly from the command line.

---

### `ormd create`

Creates a new ORMD file with minimal front-matter.

**Arguments:**
*   `file_path`: The path where the new ORMD file will be created.

**Options:**
*   `--help`: Show help message and exit.

**Example:**
```bash
ormd create my-new-document.ormd
```

---

### `ormd convert`

Converts various file formats (e.g., plain text, Markdown, PDF) to the ORMD 0.1 format. This command uses `pdfminer.six` for PDF processing, which is now a project dependency.

**Arguments:**
*   `INPUT_FILE_PATH`: The path to the input file to be converted (e.g., `mydoc.txt`, `notes.md`).
*   `OUTPUT_ORMD_PATH`: The desired path for the new output ORMD file (e.g., `converted_doc.ormd`).

**Options:**
*   `--input-format, -f [txt|md|pdf]`: Specify the input file format. Currently supports `txt` (plain text), `md` (Markdown), and `pdf`. If omitted, the format is auto-detected from the input file's extension.
*   `--help`: Show help message and exit.

**Usage Examples:**

*   **Converting a plain text file:**
    ```bash
    ormd convert my-document.txt my-document.ormd
    ```
    (This will also work if you explicitly add `--input-format txt`)

*   **Converting a Markdown file:**
    ```bash
    ormd convert my-notes.md my-notes.ormd --input-format md
    ```
    (If the `.md` extension is present, `--input-format md` is often optional)

*   **Converting a PDF file:**
    ```bash
    ormd convert my-report.pdf my-report.ormd
    ```

**Notes on PDF Conversion:**
*   Currently supports text-based PDF conversion. It attempts to extract text content and preserve paragraph structure using layout analysis.
*   Metadata such as Title, Author, Keywords, CreationDate, and ModDate will be extracted from the PDF's properties if available and included in the ORMD front-matter.
*   Conversion of image-based (scanned) PDFs or PDFs with very complex layouts might result in limited or poorly structured text output. OCR for scanned PDFs is not yet implemented.

**Note:** Support for other input formats like HTML and DOCX is planned for future releases.

---

### `ormd validate`

Validates an ORMD file against the 0.1 specification with comprehensive Phase 1 checks.

**Arguments:**
*   `file_path`: The ORMD file to validate.

**Options:**
*   `--verbose, -v`: Show detailed validation info.
*   `--help`: Show help message and exit.

**Example:**
```bash
ormd validate path/to/document.ormd
```

---

### `ormd update`

Updates and syncs front-matter fields (date_modified, word_count, link_ids, asset_ids).

**Arguments:**
*   `file_path`: The ORMD file to update.

**Options:**
*   `--dry-run, -n`: Show what would be updated without making changes.
*   `--force-update, -f`: Update locked fields (ignore `locked: true`).
*   `--verbose, -v`: Show detailed update information.
*   `--help`: Show help message and exit.

**Example:**
```bash
ormd update path/to/document.ormd --verbose
```
For details on locking fields, refer to the `main.py` or specific documentation on the update mechanism.

---

### `ormd pack`

Packs a `content.ormd` file and a `meta.json` file into a single `.ormd` package.

**Arguments:**
*   `content_file`: Path to the ORMD content file (e.g., `content.ormd`).
*   `meta_file`: Path to the metadata JSON file (e.g., `meta.json`).

**Options:**
*   `--out, -o <filename>`: Output package file name (default: `package.ormd`).
*   `--validate / --no-validate`: Validate content before packing (default: True).
*   `--help`: Show help message and exit.

**Example:**
```bash
ormd pack my-document.ormd my-metadata.json --out my-package.ormd
```

---

### `ormd unpack`

Unpacks a `.ormd` package for editing.

**Arguments:**
*   `package_file`: The `.ormd` package file to unpack.

**Options:**
*   `--out-dir, -d <dirname>`: Output directory for unpacked files (default: `./unpacked`).
*   `--overwrite`: Overwrite existing files in the output directory if it's not empty.
*   `--help`: Show help message and exit.

**Example:**
```bash
ormd unpack my-package.ormd --out-dir ./details --overwrite
```

---

### `ormd render`

Renders an ORMD file or package to HTML with sidebar features.

**Arguments:**
*   `input_file`: The ORMD file or package (`.ormd`) to render.

**Options:**
*   `--out, -o <filename>`: Output HTML file name. If not provided, it defaults to the input filename with an `.html` extension.
*   `--help`: Show help message and exit.

**Example:**
```bash
ormd render my-document.ormd --out my-document.html
```

---

### `ormd open`

Opens an ORMD document in the browser for viewing (read-only).

**Arguments:**
*   `file_path`: The ORMD file or package to open.

**Options:**
*   `--port, -p <port_number>`: Local server port (0 for a random available port, default is 0).
*   `--no-browser`: Don't automatically open the browser.
*   `--show-url`: Just show the URL that would be opened, without starting the server (for testing).
*   `--help`: Show help message and exit.

**Example:**
```bash
ormd open my-document.ormd -p 8080
```

---

### `ormd edit`

Opens an ORMD document in the browser for editing.

**Arguments:**
*   `file_path`: The ORMD file or package to edit.

**Options:**
*   `--port, -p <port_number>`: Local server port (0 for a random available port, default is 0).
*   `--no-browser`: Don't automatically open the browser.
*   `--force, -f`: Force edit even if permissions deny it (e.g., `editable: false` or `signed: true`).
*   `--show-url`: Just show the URL that would be opened, without starting the server (for testing).
*   `--help`: Show help message and exit.

**Example:**
```bash
ormd edit my-document.ormd --force
```

---

## 🏗️ Examples

See the `examples/` directory for working samples:

* **`examples/hello.ormd`** — Simple living document
* **`examples/climate-report.ormd`** — Sample document with more complex metadata

---

## 🤝 Contributing

We welcome all contributions! Please:

1. Fork the repo & create a new branch (`feature/xxx` or `fix/yyy`).
2. Make your changes, ensuring to add or update tests as appropriate.
3. Run tests (`pytest`) and ensure linting passes.
4. Submit a Pull Request with clear descriptions and test cases.

Read our [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## 📝 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

*ormd-cli* — building the future of living documents, one command at a time.
