# ORMD Design Philosophy

## The Problem We're Solving

PDF has dominated document sharing for 30 years despite being terrible at almost everything except "looking the same everywhere." We're not trying to build a better PDF - we're trying to **replace** PDF with something that doesn't hate humans.

## Core Principles

### 1. **Simplicity Over Features**

> "The best feature is no feature." - Every feature request should be met with: "What can we remove instead?"
> 
- **Default to saying NO** to new features
- **Plain text beats binary** every time
- **One file beats multiple files** when possible
- **Inline beats external dependencies** for documents

### 2. **Portability is King**

> "If it doesn't work when copied to a USB drive and opened on a different computer, it's broken."
> 
- **Self-contained by default** - no missing CSS, JS, or asset files
- **Human-readable source** - always editable in any text editor
- **Future-proof formats** - builds on standards that will exist in 20 years
- **Zero vendor lock-in** - you own your content completely

### 3. **User Intent Over Developer Convenience**

> "Optimize for the person using the document, not the person building the tool."
> 
- **Reading experience** matters more than development ergonomics
- **Sharing friction** should be zero (email one file, it works)
- **Editing barrier** should be minimal (any text editor works)
- **Complex workflows** should be opt-in, not default

### 4. **Semantic Meaning Over Visual Fidelity**

> "Relationships between ideas matter more than pixel-perfect layouts."
> 
- **Content structure** is more important than visual design
- **Semantic links** (`supports`, `refutes`, `related`) over generic hyperlinks
- **Machine-readable** relationships while staying human-readable
- **Progressive enhancement** - works without styling, better with it

## Anti-Patterns We Reject

### ❌ **Microservice Mentality**

- Don't split every function into a separate package/service
- Don't create APIs when file operations suffice
- Don't require network connectivity for basic operations

### ❌ **Framework Addiction**

- Don't add React/Vue/Angular for document rendering
- Don't require build steps for basic functionality
- Don't assume users want to install Node.js to read a document

### ❌ **Configuration Explosion**

- Don't create 20 config files for simple operations
- Don't make users choose between 47 theme options
- Don't require setup wizards or initialization scripts

### ❌ **Separation of Concerns Orthodoxy**

- Don't separate CSS from HTML when portability matters
- Don't create 15 files when 1 file would work fine
- Don't optimize for "enterprise development teams" over end users

## Decision Framework

When evaluating any change, ask these questions **in order**:

### 1. **Does this make documents more portable?**

- ✅ YES: Inline CSS instead of external files
- ❌ NO: Require database for metadata storage

### 2. **Does this reduce complexity for end users?**

- ✅ YES: Single command to render HTML
- ❌ NO: Require Docker to validate a text file

### 3. **Does this work without special software?**

- ✅ YES: Plain text editing in any editor
- ❌ NO: Custom IDE plugin required for syntax highlighting

### 4. **Will this still work in 10 years?**

- ✅ YES: Built on Markdown, YAML, ZIP standards
- ❌ NO: Depends on specific cloud service API

### 5. **Does this solve a real user problem?**

- ✅ YES: Academic papers need provenance tracking
- ❌ NO: Developers want hot module reloading for documents

## Implementation Guidelines

### **File Strategy**

- **Plain text** for working/editing (`.ormd`)
- **ZIP packages** only when assets are needed
- **Single HTML output** for sharing/viewing
- **No databases** for document storage

### **Dependency Strategy**

- **Standard library first** - prefer built-in Python modules
- **Minimal external deps** - each dependency must justify its existence
- **Inline resources** - CSS/JS goes in the HTML when reasonable
- **Web standards** - HTML/CSS/JS that works in any browser

### **Feature Strategy**

- **Core features only** - validate, render, pack/unpack
- **Extensions as separate tools** - don't bloat the main CLI
- **Backward compatibility** - old documents must always work
- **Graceful degradation** - works without advanced features

### **UI/UX Strategy**

- **CLI first** - power users and automation
- **Web rendering** - universal viewing without software
- **Text editor friendly** - syntax is readable by humans
- **Progressive disclosure** - advanced features hidden by default

## Technology Choices

### **Approved Technologies**

- **Python** - ubiquitous, stable, readable
- **Markdown** - proven, simple, extensible
- **YAML** - human-readable configuration
- **HTML/CSS/JS** - universal rendering platform
- **ZIP** - universal archive format

### **Rejected Technologies**

- **Node.js/npm** - too much complexity for document tools
- **Electron** - bloated for simple document rendering
- **Complex databases** - files are the database
- **CSS frameworks** - inline styles are more portable
- **Bundlers/transpilers** - add complexity without user value

## Success Metrics

### **Primary Goals**

1. **Anyone can edit ORMD in Notepad** and it still works
2. **Email an ORMD HTML file** and recipient sees it perfectly
3. **Convert Excel → ORMD** preserving formulas and meaning
4. **10 years from now** old ORMD files still open correctly

### **Anti-Goals**

- Don't aim to replace every document format
- Don't aim to support every possible workflow
- Don't aim to satisfy enterprise software buyers
- Don't aim to compete with modern web frameworks

## Breaking Changes Policy

### **Acceptable Breaking Changes**

- Removing unused features that add complexity
- Simplifying APIs that confuse users
- Dropping dependencies that cause reliability issues

### **Unacceptable Breaking Changes**

- Making old documents unreadable
- Requiring new software to view existing files
- Adding mandatory cloud dependencies
- Breaking plain-text editability

## Contribution Guidelines

### **Before Adding Any Feature**

1. Write the user story: "As a [person], I need [capability] because [reason]"
2. Identify what existing feature could be removed instead
3. Prove it can't be solved by better documentation
4. Show how it maintains portability and simplicity

### **Code Review Questions**

- Does this increase or decrease the number of files a user needs to manage?
- Can this functionality be achieved by editing a text file?
- Will this work on a computer without internet access?
- Would a non-technical user understand what this does?

---

## The Endgame

We succeed when:

- **Sharing a document** is as easy as sharing a PDF but the recipient can actually edit it
- **Version control** works on document content because it's plain text
- **Collaboration** doesn't require signing up for another service
- **Document archives** remain readable decades later
- **PDF becomes irrelevant** for 90% of its current use cases

We fail when:

- Users need a computer science degree to use basic features
- Documents break when moved between computers
- Simple tasks require complex toolchains
- We've recreated the problems we set out to solve

**Remember: We're not building software for developers. We're building software for people who need to share ideas.**