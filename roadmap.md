# ORMD MVP Roadmap - Updated Vision

## 🎯 Core Vision
**Replace PDF with something that doesn't suck:** Human-readable, editable, semantically rich documents that preserve visual fidelity when needed, support real collaboration, and don't lock you into proprietary formats.

## 🏗️ Foundation Principles
- **Text-first**: Keep the core simple and clean (plain ORMD files)
- **Asset-ready**: Design packaging to support rich media without breaking simplicity
- **Permission-aware**: Clear read/write/signed states with proper sharing controls
- **Visual fidelity**: Path to "Excel → ORMD" that preserves structure + formulas
- **Collaboration-native**: Fork, merge, attribution baked into the workflow

## 🚀 Phase 1: "Actually Works Better Than PDF"
*Goal: Create something people want to use for basic documents*

### **1.1 HTML Renderer** (Immediate Priority)
- Convert `.ormd` → beautiful HTML
- `[[link-id]]` becomes clickable relationships  
- Different visual styling for `supports`, `refutes`, `related`
- CSS that looks professional (not "markdown blog")
- `ormd render document.ormd --open` launches in browser

### **1.2 Permission System**
- Clear document states: Draft → Published → Signed
- Read-only vs. read-write enforcement in tools
- Fork workflow when you can't edit original
- Visual indicators of document status

### **1.3 Sharing Foundation**
- `ormd publish` creates shareable ZIP packages
- Basic permission controls (who can edit)
- Metadata inspection without being intrusive
- Digital paper trail for changes

**Success Criteria:**
- [ ] Write research paper in ORMD, share as HTML, looks professional
- [ ] Collaborator can fork, edit, suggest changes back
- [ ] Signed documents can't be accidentally modified
- [ ] Visual quality matches what you'd expect from a "nice PDF"

## 🚀 Phase 2: "The Excel Killer Feature"
*Goal: Mind-blowing conversions that make people say "why didn't this exist before?"*

### **2.1 Asset Embedding Framework**
- ZIP package support for `assets/` directory
- Image embedding with proper references
- CSV data with rendered table views
- Consistent visual output across renderers

### **2.2 Excel → ORMD Converter**
```bash
ormd convert spreadsheet.xlsx --output=budget-report.ormd
```
- **Preserve formulas**: Store as both calculated values and formula text
- **Maintain structure**: Tables, charts, multiple sheets
- **Visual fidelity**: Rendered output looks like original Excel
- **Editability**: Text-based formulas you can modify

### **2.3 Rich Media Rendering**
- Embedded spreadsheet data renders as interactive tables
- Charts become SVG (scalable, searchable, editable)
- Images display properly in HTML output
- Print/PDF export maintains layout

**Success Criteria:**
- [ ] Convert Excel budget → ORMD → looks identical but is now text-based
- [ ] Formulas preserved and visible in plain text
- [ ] Charts become editable SVG instead of static images
- [ ] Version control works on spreadsheet logic (!)

## 🚀 Phase 3: "Collaboration Revolution"
*Goal: Make document collaboration actually pleasant*

### **3.1 Real Collaboration Features**
- Change tracking with attribution
- Comment threads on specific sections
- Merge conflict resolution for text
- Branch/fork visualization

### **3.2 Integration Ecosystem**
- VS Code extension with syntax highlighting
- Browser-based editor (no software installation)
- Git hooks for validation
- Pandoc filters for legacy format export

### **3.3 Advanced Conversions**
- Word → ORMD (structure + comments + track changes)
- PowerPoint → ORMD (slides + speaker notes + animations)
- PDF → ORMD via OCR (scanned documents become searchable/editable)

**Success Criteria:**
- [ ] Team collaboration beats Google Docs experience
- [ ] Can edit ORMD files without installing anything
- [ ] Convert existing document workflows seamlessly

## 🚀 Phase 4: "PDF Replacement Complete"
*Goal: Nobody misses PDF anymore*

### **4.1 Professional Publishing**
- Print-quality typography and layout
- Professional templates (academic, legal, technical)
- Citation management integration
- Multi-format export (PDF, Word, LaTeX)

### **4.2 Enterprise Features**
- Digital signature integration with existing PKI
- Compliance features (audit trails, retention policies)
- Bulk conversion tools
- Enterprise sharing and permission management

### **4.3 Ecosystem Maturity**
- Native support in major applications
- Mobile editing apps
- Cloud storage integration
- Format standardization (MIME types, file associations)

## 🎯 Decision Framework

### **Keep Simple:**
- Core ORMD syntax stays minimal
- Plain text files remain human-readable
- CLI tools do one thing well
- No vendor lock-in ever

### **Enable Complexity:**
- ZIP packaging supports any kind of asset
- Metadata can be as rich as needed
- Conversion tools handle edge cases
- Advanced features are opt-in

### **Key Architecture Decisions:**
- **Asset strategy**: Embed in ZIP for sharing, reference for editing
- **Collaboration model**: Fork-based with optional real-time
- **Visual fidelity**: CSS + embedded assets, not layout engines
- **Compatibility**: Always export to standard formats

## 💡 "Why Hasn't This Been Done?" Insights

**Excel → Text preservation:**
- Most converters throw away formulas (only keep values)
- ORMD can store both: calculated results AND formula logic
- Version control finally works on spreadsheet logic
- Collaborative editing of formulas becomes possible

**PDF's visual lock-in:**
- People accept broken workflows because "it looks the same"  
- ORMD maintains visual consistency with flexible underlying format
- You get PDF's reliability without PDF's editing nightmare

**Document collaboration mess:**
- Every tool has different sharing/permission models
- ORMD defines clear, universal permission semantics
- Git-style workflows for documents (finally!)

## 🎯 Next Immediate Steps

1. **HTML renderer** - Make ORMD documents actually viewable
2. **Permission enforcement** - Implement read-only/read-write/signed states  
3. **Basic asset embedding** - Images in ZIP packages
4. **Excel converter prototype** - Prove the concept works

The Excel converter will be the "holy grail" demo that makes everyone understand why ORMD matters. Imagine showing someone: "Here's your Excel file as editable text that version control understands, but it still looks and calculates exactly the same."

That's when PDF's monopoly starts to crack.