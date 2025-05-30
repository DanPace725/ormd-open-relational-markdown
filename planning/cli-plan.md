Here’s a **focused 2-week plan** to get the `ormd-cli` MVP up and running. You can adapt the pacing to your team size or time availability:

---

## 📅 Sprint 0 (Day 1–2): Project Setup

1. **Create GitHub repo** `open-relational-markdown/ormd-cli`

   * Add README stub, license (MIT/Apache-2.0), Code of Conduct.
   * Set up issue & PR templates.
2. **Define tech stack**

   * Pick language (e.g. Rust for a single static binary, or Node.js/Python for faster iteration).
   * Scaffold project directory:

     ```
     ormd-cli/
     ├── src/
     ├── examples/
     ├── tests/
     ├── README.md
     ├── LICENSE
     └── .github/
     ```
3. **Install CI**

   * Configure GitHub Actions for linting & running tests on each push.

---

## 🔍 Sprint 1 (Day 3–6): `validate` Command

**Goal:** Ensure any `.ormd` file is structurally correct.

* **Day 3:**

  * Parse input file (plain or zip).
  * Extract and verify the `<!-- ormd:0.1 -->` tag.
* **Day 4:**

  * Parse YAML front-matter (title, authors, links array).
  * Fail on syntax errors.
* **Day 5:**

  * Parse Markdown body. Collect all `[[id]]` usages.
  * Cross-check against `links.id`.
* **Day 6:**

  * Write unit tests for each failure mode (missing tag, bad YAML, undefined link).
  * Document `ormd-cli validate <file>` in README.

---

## 📦 Sprint 2 (Day 7–10): `pack` & `unpack`

**Goal:** Bundle / unbundle an ORMD package.

* **Day 7:**

  * Implement `ormd-cli unpack mydoc.ormd --out-dir=./work/`

    * Detect zip vs text, extract `content.ormd` and `meta.json`.
* **Day 8:**

  * Implement `ormd-cli pack content.ormd meta.json --out=doc.ormd`

    * Zip up required files into a single `.ormd` archive.
* **Day 9:**

  * Handle optional `ops/` and `render.css` if present.
  * Add validation step in `pack` to reject malformed inputs.
* **Day 10:**

  * End-to-end tests: pack → unpack → validate yields no errors.
  * Update README with `pack`/`unpack` usage.

---

## 🧪 Sprint 3 (Day 11–13): Examples, Docs & Branding

1. **Populate `examples/`**

   * “Hello ORMD” (plain)
   * Sample invoice with signature metadata (zipped)
2. **CLI UX polish**

   * Add `--help` text, verbose vs quiet modes, exit codes.
3. **Write “Getting Started” guide**

   * Quickstart in README: install, validate, pack, unpack.
   * Link to full spec in `open-relational-markdown/spec/`.
4. **Logo & ASCII banner** (optional)

   * A small touch to make `ormd-cli` feel official.

---

## 🚀 Sprint 4 (Day 14): Release & Feedback

* **Publish v0.1-alpha** on GitHub Releases.
* **Announce** in your WG channel (Discord/Matrix) and Twitter/DevConf.
* **Collect issues** and tag roadmap items (v0.2 CRDT, comments, etc.).

---

### 🎯 Success Criteria for MVP

* `ormd-cli validate` rejects all malformed tests, accepts valid ones.
* `pack` + `unpack` round-trip fidelity.
* At least two example files that anyone can try.
* Clear docs so a newcomer can install and run in under 5 minutes.

---

With this plan, by end of Week 1 you’ll have a solid validating CLI, and by end of Week 2 a shippable alpha you can demo and iterate on. Let me know if you’d like boilerplate code examples or help bootstrapping any of these sprints!
