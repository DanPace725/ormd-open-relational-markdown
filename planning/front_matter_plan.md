Progressive Path to Universal Editing
Phase 1: Simplify the Single-File Format (Immediate)
The current +++meta / +++end-meta syntax is weird and breaks the "looks like normal markdown" principle. Let's fix this:
Instead of:
ormd<!-- ormd:0.1 -->
---
title: Document
links: [...]
---

# Content here

+++meta
created: 2025-05-29
+++end-meta
Do this:
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