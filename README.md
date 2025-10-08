# PyLyX

PyLyX is a Python package for programmatically working with LyX document files. It provides tools for parsing, manipulating, and exporting LyX documents to various formats, with special emphasis on XHTML export functionality.

## Overview

LyX is a document processor that combines the power and flexibility of TeX/LaTeX with the ease of use of a graphical interface. PyLyX allows you to:

- Load and parse LyX document files (.lyx)
- Manipulate document structure and content programmatically
- Export LyX documents to XHTML with full styling support
- Convert LyX documents to other formats using the LyX processor
- Search and replace text within LyX documents
- Work with LyX document elements as Python objects

## Installation

### Prerequisites

- Python 3.10 or higher (uses modern type hints)
- LyX 2.x installed on your system (Windows)
- The package currently expects LyX to be installed in `C:\Program Files\LyX 2.x`

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yeahBOYYYYY/PyLyX.git
cd PyLyX
```

2. The package will automatically detect your LyX installation during import.

## Quick Start

### Basic Usage

```python
from PyLyX import LyX

# Load an existing LyX file
doc = LyX('path/to/document.lyx')

# Export to XHTML
doc.export2xhtml(output_path='output.xhtml')

# Export to PDF using LyX processor
doc.export('pdf4', output_path='output.pdf')

# Search for text
element = doc.find('search query')

# Find and replace text
doc.find_and_replace('old text', 'new text')

# Save changes
doc.save()
```

### Creating a New Document

```python
from PyLyX import LyX
from PyLyX.objects.Environment import Environment

# Create document structure
body = Environment('body')
# Add content to body...

doc_root = Environment('document')
doc_root.append(header)
doc_root.append(body)

# Create LyX file
doc = LyX('new_document.lyx', doc_obj=doc_root)
doc.save()
```

## Architecture and Data Flow

### Package Structure

```
PyLyX/
├── __init__.py              # Main LyX class for document manipulation
├── package_helper.py        # Utility functions for path handling and text processing
├── init_helper.py           # Helper functions for LyX file operations
├── data/
│   ├── data.py             # Package configuration and data loading
│   ├── objects/            # JSON schemas for LyX objects
│   └── templates/          # LyX document templates
├── objects/
│   ├── LyXobj.py           # Base LyX object class
│   ├── Environment.py      # Environment and Container classes
│   └── loader.py           # LyX file parser
├── xhtml/
│   ├── converter.py        # Main XHTML conversion logic
│   ├── helper.py           # XHTML generation helpers
│   ├── special_objects.py  # Handlers for special elements
│   ├── exporter.py         # XHTML export utilities
│   ├── css/                # Default stylesheets
│   ├── data/               # XHTML conversion mappings
│   └── modules/            # LyX module-specific converters
├── shortcuts/
│   ├── bind2lyx.py         # Convert LyX keybindings to readable format
│   ├── extract_macros.py   # Extract LaTeX macros from documents
│   └── ...
└── solver/
    └── bugline_finder.py   # Debug utility for finding problematic content
```

### Core Classes

#### `LyX` (in `__init__.py`)
The main interface for working with LyX documents. Provides high-level methods for:
- Loading existing documents
- Saving and backing up documents
- Exporting to various formats
- Searching and replacing content

#### `LyXobj` (in `objects/LyXobj.py`)
Base class representing a LyX object. Extends Python's `xml.etree.ElementTree.Element` to provide:
- Command, category, and details attributes
- Rank-based nesting validation
- Conversion to LyX syntax

#### `Environment` (in `objects/Environment.py`)
Represents LyX environments (layouts, insets, etc.) with:
- Automatic validation of object properties
- Nested structure management
- LyX syntax serialization

#### `Container` (in `objects/Environment.py`)
Special wrapper for layout objects that form document sections.

### Data Flow

#### Loading a LyX Document

1. **File Reading** (`objects/loader.py`):
   - `load()` function reads .lyx file line by line
   - Extracts document format version
   - Creates root `Environment` object

2. **Parsing** (`objects/loader.py`):
   - `one_line()` processes each line
   - Identifies commands, environments, and text
   - Builds hierarchical object tree using `order_object()`

3. **Object Creation**:
   - Known objects → `Environment` instances
   - Unknown objects → `LyXobj` instances
   - Section titles → wrapped in `Container`

#### XHTML Export Flow

1. **Initialization** (`LyX.export2xhtml()`):
   - Sets output path and handles file conflicts
   - Calls `xhtml/converter.convert()`

2. **Document Processing** (`xhtml/converter.py`):
   - **Header Scan**: `scan_head()` extracts document metadata
   - **Language Setup**: Adds appropriate RTL/LTR CSS
   - **Recursive Conversion**: `recursive_convert()` transforms document tree
     - Each `LyXobj`/`Environment` → HTML element
     - Special objects handled by dedicated functions
     - Text formatting preserved
   
3. **Structure Generation**:
   - **Table of Contents**: `numbering_and_toc()` creates ToC structure
   - **Numbering**: Sections, figures, and footnotes numbered
   - **Modules**: LyX modules processed via `xhtml/modules/`

4. **Finalization**:
   - MathJax script added for formulas
   - CSS files linked or embedded
   - JavaScript files added
   - Output formatted and written

#### Key Conversion Functions

- `create_info()`: Determines HTML tag for LyX object
- `create_attributes()`: Converts LyX attributes to HTML
- `one_obj()`: Converts single object (non-recursive)
- `recursive_convert()`: Converts object and all children
- Special handlers:
  - `perform_table()`: Table conversion
  - `perform_box()`: Box inset conversion
  - `perform_image()`: Graphics conversion
  - `correct_formula()`: LaTeX formula formatting

### Object Hierarchy and Ranks

LyX objects have ranks that determine valid nesting:
- Lower rank objects can nest in higher rank objects
- Prevents invalid document structures
- Validated during `append()` operations

Example ranks:
- Part: 0
- Chapter: 1
- Section: 2
- Subsection: 3
- Standard layout: 100 (default)

### LyX File Format

PyLyX works with LyX's native format:
```
#LyX 2.x created this file...
\lyxformat 620
\begin_document
\begin_header
...
\end_header
\begin_body
\begin_layout Standard
Text content here
\end_layout
\end_body
\end_document
```

## Utility Scripts

### Keyboard Shortcuts Documentation

Convert LyX keybinding files to a readable LyX document:

```bash
python shortcuts/bind2lyx.py [bind_file] [output_file]
```

This creates a formatted table showing:
- Keyboard shortcuts
- Associated commands
- Output/action descriptions

### Macro Extraction

Extract LaTeX macros from LyX documents:

```bash
python shortcuts/extract_macros.py input.lyx [output.json]
```

Outputs a JSON dictionary of macros defined in the document.

### Bug Finder

Find problematic elements preventing document export:

```python
from solver.bugline_finder import finder

problematic_obj = finder('path/to/document.lyx', fmt='pdf4')
```

Tests each document element individually to identify export failures.

## API Reference

### LyX Class Methods

#### `__init__(full_path, writeable=True, doc_obj=None)`
Create or load a LyX file.
- `full_path`: Path to .lyx file
- `writeable`: Allow modifications
- `doc_obj`: Environment object for new documents

#### `save(backup=True)`
Save the document to its current path.

#### `save_as(path)`
Save the document to a new path.

#### `backup()`
Create a backup copy in the backup directory.

#### `export(fmt, output_path='', timeout=60)`
Export using LyX's built-in converters.
- `fmt`: Format code (e.g., 'pdf4', 'xhtml')
- Returns: Boolean success status

#### `export2xhtml(...)`
Export to XHTML with extensive customization options:
- `output_path`: Output file path
- `css_files`: Additional CSS files to include
- `css_folder`: Custom CSS folder path
- `css_copy`: Copy CSS vs. embed inline
- `js_files`: JavaScript files to include
- `js_in_head`: Place JS in `<head>` vs. end of body
- `keep_data`: Preserve LyX metadata in output
- `replaces`: Dictionary for string replacements

#### `find(query, command='', category='', details='')`
Find first element containing query text.
- Returns: `LyXobj`, `Environment`, `Container`, or `None`

#### `find_and_replace(old_str, new_str, command='', category='', details='', backup=True)`
Replace all occurrences of text.

#### `append(obj)`
Append an object to the document body.

#### `get_doc()`
Returns the root `Environment` object.

#### `update_version(backup=True)`
Update document to current LyX version format.

### Working with Objects

```python
# Access document structure
doc = lyx_file.get_doc()
header = doc[0]  # Document header
body = doc[1]    # Document body

# Iterate through elements
for element in body:
    print(element.command(), element.category())
    
# Check object properties
if element.is_command('layout'):
    if element.is_category('Section'):
        print("Found a section!")

# Get object text
text = element.text
tail_text = element.tail

# Object hierarchy
element.append(child_obj)  # Add child
element.extend([obj1, obj2])  # Add multiple children
```

## Configuration

The package automatically configures itself based on your LyX installation:

- **LyX Version**: Auto-detected from `C:\Program Files\LyX 2.x`
- **User Directory**: `%APPDATA%\Roaming\LyX{version}`
- **Backup Directory**: From LyX preferences or Downloads folder
- **Current Format**: 620 (LyX 2.4)

Configuration is loaded in `data/data.py` on import.

## Limitations

- **Platform**: Currently Windows-only (paths use backslashes)
- **LyX Dependency**: Requires LyX installed for `export()` method
- **Format Version**: Optimized for LyX format 620
- **Python Version**: Requires Python 3.10+ for modern type hints

## Contributing

Contributions are welcome! Areas for improvement:
- Cross-platform support (Linux, macOS)
- Additional export formats
- More comprehensive tests
- Enhanced XHTML styling options
- Documentation improvements

## License

[Add license information here]

## Support

For issues and questions:
- GitHub Issues: https://github.com/yeahBOYYYYY/PyLyX/issues

## Version History

- **Current**: LyX format 620 support, XHTML export, document manipulation
