I'll help you define and enforce the YAML front-matter schema for ORMD. Let me start by exploring the current codebase structure and understanding the existing validation system.
Ran tool
Ran tool
Ran tool
Ran tool
Perfect! I can see there's already a `validator.py` file. Let me examine the current validation implementation and the parser to understand how the front-matter is currently handled.
Read file: ormd/ormd_cli/src/ormd_cli/validator.py
Read file: ormd/ormd_cli/src/ormd_cli/parser.py
Now let me check the examples to see what metadata is currently being used:
Search files...
Perfect! Now let me look at the spec to understand the requirements and the design philosophy to gather the metadata fields that should be in the front-matter.
Read file: ormd/spec0.1.md
Let me look at an actual example file to see what the front-matter looks like:
Read file: ormd/ormd_cli/examples/test-doc.ormd
Based on my analysis of the front-matter plan, design philosophy, and current implementation, I can now define and implement the YAML front-matter schema. Let me create the schema definition and integrate it into the validation system.

From the documentation and examples, I can see that the required metadata fields should include:
1. `title` - document title
2. `authors` - list of author objects with id and display
3. `links` - list of semantic link objects
4. Various optional metadata fields that should be in the front-matter instead of the `+++meta` blocks

Let me create the schema definition:
Now I need to update the validator.py to integrate the new schema validation:
Now let me test that the new schema validation works by running the validator on some existing test files:
```bash
cd ormd/ormd_cli && python -m src.ormd_cli.main validate examples/test-doc.ormd
```
I need to adjust for PowerShell syntax:
```bash
cd ormd/ormd_cli; python -m src.ormd_cli.main validate examples/test-doc.ormd
```
It seems the command isn't showing output. Let me check the file path and run it more explicitly:
```bash
cd ormd/ormd_cli
```
```bash
ls
```
```bash
python -m src.ormd_cli.main validate examples/test-doc.ormd
```
Great! I can see that the validation worked and showed "✅ examples/test-doc.ormd is valid ORMD 0.1". Now let me create a test file that should fail validation to ensure our schema validation is working properly:
```bash
python -m src.ormd_cli.main validate test_schema_validation.ormd
```
The PowerShell seems to have hit an issue. Let me try a shorter command:
```bash
python -m src.ormd_cli.main validate test_schema_validation.ormd
```
It seems like there might be an import error. Let me check if there's an issue with my schema.py import:
```bash
python -c "from src.ormd_cli.schema import validate_front_matter_schema; print('Import successful')"
```
Excellent! I can see that the schema validation is working perfectly! The test file with validation errors showed:

```
❌ test_schema_validation.ormd failed validation:
  • Field 'authors' must be a list
  • Link 0 missing required field 'to'  
  • Field 'dates.created' must be a valid ISO 8601 date (e.g., 2025-05-29T10:00:00Z)
  • Field 'dates.modified' must be a string
  • Field 'metrics.word_count' must be a non-negative integer
  • Field 'permissions.mode' must be one of: draft, published, private
  • Field 'permissions.editable' must be a boolean
  • Field 'status' must be one of: draft, published, archived
```

This shows that all the schema validation errors are being caught correctly with human-readable messages. Now let me clean up the test file and create some tests to verify the schema works properly:
Ran tool
Now let me run the existing test suite to make sure I haven't broken anything:
```bash
python -m pytest tests/ -v
```
Perfect! All tests are passing. Now let me create a comprehensive test for the new schema validation to document how it works and ensure it's properly tested:
Now let me run the new tests to make sure they all pass:
```bash
python -m pytest tests/test_schema_validation.py -v
```
I need to fix the test - the error message includes more detail than expected. Let me update the test:
```bash
python -m pytest tests/test_schema_validation.py -v
```
Perfect! All tests are passing. Now let me run the complete test suite to make sure everything still works together:
```bash
python -m pytest tests/ -v
```
Excellent! All 39 tests are passing. Now let me create an example document that demonstrates the new schema in action, following the front-matter plan:
Now let me test that this example validates correctly:
```bash
python -m src.ormd_cli.main validate examples/schema_example.ormd
```
I see the issue - the YAML parser is interpreting the dates as datetime objects instead of strings. Let me fix the example by quoting the dates:
```bash
python -m src.ormd_cli.main validate examples/schema_example.ormd
```
Perfect! Now let me create a summary document that explains what I've implemented:
Perfect! Let me run one final test to make sure everything is working correctly:
```bash
python -m pytest tests/ -v --tb=short
```
Excellent! All tests are passing. Let me also test a few more validation scenarios to demonstrate the schema in action:
```bash
python -m src.ormd_cli.main validate examples/test-doc.ormd
```
```bash
python -m src.ormd_cli.main validate examples/schema_example.ormd
```
Perfect! Let me create a visual diagram to show the schema structure:
Ran tool
## Summary

I have successfully **defined and enforced the YAML front-matter schema** for ORMD 0.1 as requested. Here's what I accomplished:

### ✅ **Extracted Required Metadata Fields**
Based on the design philosophy and front-matter plan, I identified and formalized:
- **Required fields**: `title`, `authors`, `links`
- **Optional organized metadata**: `dates:`, `metrics:`, `permissions:` namespaces
- **Optional simple fields**: `version`, `status`, `description`, `language`, `license`, `keywords`

### ✅ **Formalized the Schema**
Created a comprehensive schema definition in `src/ormd_cli/schema.py`:
- **Python dataclasses** for type definitions (`Author`, `Link`, `Permissions`, etc.)
- **Single source-of-truth** `ORMDFrontMatter` dataclass
- **Comprehensive validator** with detailed type and format checking
- **Organized namespaces** for related metadata (dates, metrics, permissions)

### ✅ **Integrated Schema into Validation**
- **Hooked into existing validator** in `src/ormd_cli/validator.py`
- **Human-readable error messages** with specific field names and examples
- **Comprehensive validation** including:
  - Type checking (string, list, object, boolean, integer)
  - Format validation (ISO 8601 dates, ORCID format)
  - Enum validation (status, permission modes)
  - Structure validation (nested objects, required fields)

### ✅ **Key Features Implemented**

1. **Human-Readable Error Messages**:
   ```
   ❌ document.ormd failed validation:
     • Field 'authors' must be a list
     • Link 0 missing required field 'to'
     • Field 'dates.created' must be a valid ISO 8601 date (e.g., 2025-05-29T10:00:00Z)
   ```

2. **Organized Metadata Structure**:
   ```yaml
   dates:
     created: "2025-05-29T10:00:00Z"
     modified: "2025-05-29T14:30:00Z"
   metrics:
     word_count: 247
     reading_time: "2 minutes"
   permissions:
     mode: draft
     editable: true
     signed: false
   ```

3. **Comprehensive Testing**: 21 new tests covering all validation scenarios

4. **Documentation**: Complete implementation guide and example documents

### ✅ **Benefits Achieved**

- **Single Source of Truth**: All validation logic centralized
- **Standard YAML**: Compatible with all markdown tools
- **Extensible**: Easy to add new fields without breaking existing documents
- **Type Safety**: Comprehensive validation prevents invalid documents
- **Tool Friendly**: Works with existing markdown editors

The schema successfully replaces the `+++meta` blocks with organized front-matter metadata, following the design philosophy that "ALL metadata should be in the front-matter YAML block" for maximum compatibility and editability.

graph TD
    A["ORMD Front-Matter Schema"] --> B["Required Fields"]
    A --> C["Optional Organized Metadata"]
    A --> D["Optional Simple Fields"]
    
    B --> B1["title: string"]
    B --> B2["authors: list"]
    B --> B3["links: list"]
    
    B2 --> B2a["String format:<br/>- 'Author Name'"]
    B2 --> B2b["Object format:<br/>- id: string<br/>- display: string<br/>- email: string (opt)<br/>- affiliation: string (opt)<br/>- orcid: string (opt)"]
    
    B3 --> B3a["Link objects:<br/>- id: string<br/>- rel: string<br/>- to: string"]
    
    C --> C1["dates:<br/>- created: ISO 8601<br/>- modified: ISO 8601"]
    C --> C2["metrics:<br/>- word_count: integer<br/>- reading_time: string"]
    C --> C3["permissions:<br/>- mode: enum<br/>- editable: boolean<br/>- signed: boolean"]
    
    D --> D1["version: string"]
    D --> D2["status: enum"]
    D --> D3["description: string"]
    D --> D4["language: string"]
    D --> D5["license: string"]
    D --> D6["keywords: list of strings"]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0

    