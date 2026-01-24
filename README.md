# MDML Parser

A Python library for parsing and generating MDML (Markdown Metadata List) documents - a lightweight format for structured data with Markdown-like syntax.

## Features

- **Resilient parsing** with error recovery
- **Flexible syntax** supporting inline and list formats
- **Rich metadata** including dates, times, details and strikethrough
- **Markdown links** with automatic URL extraction
- **Nested structures** with sub-fields and sub-items
- **Array values** using `{ ; }` syntax
- **Raw text** using pipe `| |` syntax
- **Wiki links** using `[[ ]]` syntax
- **YAML frontmatter** support
- **Multiple export formats** (JSON, YAML, dict)
- **Generator** for creating MDML from Python data structures

## Installation

(Soon)

## Quick Start

```python
from mdml import parse_document, generate_markup

content = """
name: `John Doe`
status: `active`, `2024-01-15`
website: [My Site](https://example.com)
"""
doc = parse_document(content)
print(doc.to_json())

data = {
    'fields': {
        'name': {
            'name': 'name',
            'is_list': False,
            'values': [
                {
                    'value': 'John Doe',
                    'datetime': '2026-01-24 14:45'
                }
            ]
        }
    }
}
markup = generate_markup(data)
print(markup)
```

## MDML Syntax

### Inline Fields

Simple key-value pairs:

```
name: `John Doe`
age: `30`
email: `john@example.com`
```

### List Fields

Multiple values with timestamps and metadata:

```
tasks:
- `Write documentation`, `2024-01-15 14:30`
- `Review code` (urgent), `2024-01-15`
- ~~`Old task`~~
```

### Details

Add contextual information in parentheses:

```
status: `completed` (reviewed by team)
price: `$99.99` (discounted)
```

### Dates and Times

Append timestamps after values:

```
deadline: `Submit report`, `2024-12-31`
meeting: `Team sync`, `2024-01-20 10:00`
```

### Strikethrough

Mark deprecated or completed items:

```
tasks:
- ~~`Obsolete task`~~
- `Active task`

invite: ~~https://t.me/+ABC~~ (expired)
```

### Markdown Links

Links are automatically parsed and URLs are extracted:

```
website: [Visit our site](https://example.com)
documentation: [Read the docs](https://docs.example.com) (external)
references:
- [GitHub](https://github.com)
- [Stack Overflow](https://stackoverflow.com) (plz don't use), `2026-01-24`
```

The link text is stored in `value` and the URL in `link_url`.

### Arrays

Store multiple related values using curly braces and semicolons:

```
tags: { python ; parsing ; markdown }
colors: { red ; blue ; green }
languages: { en ; fr ; es }
```

### Raw Text

For text with special characters, use pipe delimiters:

```
note: | This text can have: commas, (parentheses), and | pipes |
description: | Raw text preserves everything as-is |
```

The closing pipe is optional but recommended.

### Wiki Links

Internal links using double brackets:

```
related: [[Other Document]]
see also: [[Configuration|Config guide]]
```

### Nested Structures

Create hierarchical data with sub-fields and sub-items:

```
project:
- `Website Redesign`
	- status: `in progress`
	- priority: `high`
	- deadline: `2024-06-30`
	- `Phase 1: Research`
	- `Phase 2: Design`
```

### Frontmatter

Optional YAML metadata at document start:

```
---
version: 1.0
author: John Doe
created: 2026-01-15
---

content: `Main document content`
```

## API Reference

### Parsing Functions

```python
# Parse complete document
doc = parse_document(content: str) -> Document
```

### Generation Functions

```python
# Generate MDML markup from dictionary
markup = generate_markup(data: Dict[str, Any]) -> str
```

### Import Functions

```python
# Create Document from dictionary
doc = from_dict(data: Dict[str, Any]) -> Document

# Create Document from JSON
doc = from_json(json_str: str) -> Document
```

### Document Methods

```python
# Get field by name
field = doc.get_field('field_name') -> Optional[Field]

# Get specific value from field
value = doc.get_value('field_name', index=0) -> Optional[FieldValue]

# Get all values from field
values = doc.get_values('field_name') -> List[FieldValue]

# Check for parse errors
has_errors = doc.has_errors() -> bool

# Export to different formats
json_str = doc.to_json(indent=2) -> str
yaml_str = doc.to_yaml() -> str
data_dict = doc.to_dict() -> Dict[str, Any]
```

### Field Properties

```python
field.name           # Field name
field.is_list        # Boolean: list or inline format
field.values         # List of FieldValue objects
field.first_value    # Most recent value
field.last_value     # Oldest value
field.parse_errors   # List of non-critical errors
```

### FieldValue Properties

```python
value.value              # Main text value
value.date               # Date string (YYYY-MM-DD)
value.time               # Time string (HH:MM)
value.datetime_obj       # Python datetime object
value.datetime_str       # Formatted datetime string
value.details            # Details from parentheses
value.is_strikethrough   # Boolean for strikethrough
value.is_array           # Boolean for array values
value.array_values       # List of array elements
value.is_raw             # Boolean for raw text
value.is_wiki_link       # Boolean for wiki links
value.link_url           # URL from markdown links
value.sub_items          # Dict of named sub-fields
value.list_sub_items     # List of sub-items
value.parse_error        # Error message if parsing failed
```

## Error Handling

MDML uses resilient parsing with error recovery:

```python
doc = parse_document(content)

# Check for errors
if doc.has_errors():
    print("Document errors:", doc.parse_errors)
    
    for field_name, field in doc.fields.items():
        if field.has_errors():
            print(f"Field '{field_name}' errors:", field.parse_errors)
        
        for value in field.values:
            if value.has_error():
                print(f"Value error: {value.parse_error}")
                print(f"Raw value: {value.value}")
```

Even with errors, the parser returns usable data structures with error annotations.

## Advanced Usage

### Working with Nested Data

```python
doc = parse_document("""
project:
- `Alpha Release`
	- phase: `Planning`
	- deadline: `2024-06-30`
	- `Define requirements`
	- `Create timeline`
""")

project = doc.get_field('project')
first_item = project.first_value

# Access named sub-fields
phase = first_item.sub_items['phase'].value
deadline = first_item.sub_items['deadline'].value

# Access list sub-items
tasks = [item.value for item in first_item.list_sub_items]
```

### Working with Arrays

```python
doc = parse_document("tags: { python ; parsing ; data }")
value = doc.get_value('tags')

if value.is_array:
    print(value.array_values)  # ['python', 'parsing', 'data']
```

### Working with Markdown Links

```python
doc = parse_document("""
links:
- [GitHub](https://github.com)
- [Documentation](https://docs.example.com) (official)
""")

links = doc.get_field('links')
for link in links.values:
    print(f"Text: {link.value}")
    print(f"URL: {link.link_url}")
    if link.details:
        print(f"Details: {link.details}")
```

### Working with Raw Text

```python
doc = parse_document("note: | Text with: special, (chars) |")
value = doc.get_value('note')

if value.is_raw:
    print(value.value)  # 'Text with: special, (chars)'
```

### Generating MDML

```python
from mdml import MDMLGenerator
from mdml.models import Field, FieldValue

# Create field programmatically
field = Field(
    name='tasks',
    is_list=True,
    values=[
        FieldValue(
            value='Complete project',
            date='2024-01-20',
            time='15:00',
            details='high priority'
        )
    ],
    raw_content=''
)

# Generate markup
lines = MDMLGenerator.generate_field(field)
print('\n'.join(lines))
```

## Exception Handling

Work in progress.

```python
from mdml.exceptions import (
    MDMLException,        # Base exception
    MDMLParseError,       # Critical parsing errors
    MDMLFieldError,       # Field-specific errors
    MDMLValueError        # Value parsing errors
)

try:
    doc = parse_document(content)
except MDMLParseError as e:
    print(f"Parse error: {e}")
except MDMLException as e:
    print(f"MDML error: {e}")
```

## Syntax Rules

### Field Names
- Lowercase letters, numbers, spaces, and underscores
- Must start with a letter
- Example: `field_name`, `field name`, `field123`

### Values
- Wrap in backticks when inline: `` `value` ``
- Optional backticks in lists unless value has metadata
- Use pipe delimiters for raw text: `| raw text |`

### Dates and Times
- Dates: ISO format `YYYY-MM-DD`
- Times: 24-hour format `HH:MM`
- Combined: `` `2024-01-20 15:30` ``

### Arrays
- Use curly braces: `{ item1 ; item2 ; item3 }`
- Semicolon-separated values
- Spaces around semicolons are trimmed

### Links
- Markdown format: `[text](url)`
- Wiki links: `[[link]]`
- URLs are automatically extracted

### Nesting
- Use tabs (not spaces) for indentation
- List items start with `-`
- Named sub-fields: `- field: value`
- List sub-items: `- value`

### Automatic RAW Detection
Text with spaces and no explicit formatting (backticks, links, strikethrough) is automatically treated as raw text:

```
description: This is automatically raw text
note: `This requires backticks because it's explicit`
```

## License

Licensed under the Apache License, Version 2.0.

See [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please submit issues and pull requests on GitHub.
