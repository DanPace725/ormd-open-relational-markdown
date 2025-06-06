Progressive Path to Universal Editing
Phase 1: Simplify the Single-File Format (Immediate)
The previous `+++meta` / `+++end-meta` syntax for separate metadata blocks in the document body is no longer supported. All metadata must be consolidated into the single YAML front-matter block at the beginning of the document. This approach aligns with the "looks like normal markdown" principle.

The standard way to define front-matter is:
ormd<!-- ormd:0.1 -->
---
title: Document
authors: [...]
links: [...]
# Document metadata
created: 2025-05-29T10:00:00Z
wordCount: 247
permissions:
  mode: draft
  editable: true
---

# Content here
Key insight: Put ALL metadata in the front-matter YAML block. It's standard, every markdown tool understands it, and it's infinitely more editable than custom syntax.