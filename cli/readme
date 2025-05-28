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

* **Success:** Exit code `0`
* **Failure:** Non-zero exit code and printed errors

### 2. Pack

Bundle a plain `.ormd` and `meta.json` into a single package:

```bash
ormd-cli pack content.ormd meta.json --out packaged.ormd
```

### 3. Unpack

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
