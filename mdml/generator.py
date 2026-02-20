from typing import List, Dict, Any
from .models import Field, FieldValue, Document
from .formatter import MDMLFormatter


class MDMLGenerator:
    """Generates MDML format from Python data structures"""

    @staticmethod
    def generate_value(value: FieldValue, indent: int = 0) -> List[str]:
        """
        Generates MDML text for a FieldValue

        Returns:
            List of lines
        """
        lines = []
        tabs = MDMLFormatter.make_indent(indent)

        # Build main value line
        # Handle RAW format first (highest priority)
        if value.is_raw:
            val = f"| {value.value} |"  # Always close pipes in generator (strict)
        elif value.is_array:
            # Array format: { `val1` ; `val2` ; `val3` }
            array_str = ' ; '.join(f"`{v}`" for v in value.array_values)
            val = f"{{ {array_str} }}"
        elif value.is_wiki_link:
            if value.wiki_link and value.wiki_link != value.value:
                val = f"[[{value.wiki_link}|{value.value}]]"
            else:
                val = f"[[{value.value}]]"
        else:
            # Apply quoting rules for list context
            has_metadata = bool(value.date or value.details)
            # Backticks are now OPTIONAL
            val = MDMLFormatter.quote_value(
                text=value.value,
                context='list',
                is_wiki_link=False,
                has_metadata=has_metadata,
                is_raw_url=value.is_raw_url
            )

            # Apply strikethrough AFTER quoting
            if value.is_strikethrough:
                val = f"~~{val}~~"

        # Add details (after value, before datetime)
        if value.details:
            val += f" ({value.details})"

        # Add datetime (always at the end)
        if value.date:
            if value.time:
                val += f", `{value.date} {value.time}`"
            else:
                val += f", `{value.date}`"

        lines.append(f"{tabs}- {val}")

        # Add named sub-fields (with full support for dates/details)
        for sub_name, sub_value in value.sub_items.items():
            sub_tabs = MDMLFormatter.make_indent(indent + 1)

            # Determine if sub-value has metadata
            has_metadata = bool(sub_value.date or sub_value.details)

            if value.is_raw_url:
                sub_val = sub_value.value  # no backticks for URL
            else:
                # Quote sub-field value
                sub_val = MDMLFormatter.quote_value(
                    text=sub_value.value,
                    context='list',
                    has_metadata=has_metadata,
                    is_raw=False,
                    is_raw_url=sub_value.is_raw_url
                )

            # Add details for sub-field
            if sub_value.details:
                sub_val += f" ({sub_value.details})"

            # Add datetime for sub-field
            if sub_value.date:
                if sub_value.time:
                    sub_val += f", `{sub_value.date} {sub_value.time}`"
                else:
                    sub_val += f", `{sub_value.date}`"

            lines.append(f"{sub_tabs}- {sub_name}: {sub_val}")

            # Recursively generate nested sub-items if present
            if sub_value.sub_items:
                for nested_name, nested_value in sub_value.sub_items.items():
                    nested_lines = MDMLGenerator.generate_value(nested_value, indent + 2)
                    # Convert to named sub-field format
                    for i, line in enumerate(nested_lines):
                        if i == 0:
                            # First line: add field name
                            lines.append(line.replace('- ', f'- {nested_name}: ', 1))
                        else:
                            lines.append(line)

            if sub_value.list_sub_items:
                for nested_item in sub_value.list_sub_items:
                    lines.extend(MDMLGenerator.generate_value(nested_item, indent + 2))

        # Add list sub-items (already recursive)
        for sub_item in value.list_sub_items:
            lines.extend(MDMLGenerator.generate_value(sub_item, indent + 1))

        return lines

    @staticmethod
    def generate_field(field: Field) -> List[str]:
        """
        Generates MDML text for a Field

        Returns:
            List of lines
        """
        lines = []

        if field.is_list:
            # List format
            lines.append(f"{field.name}:")
            for value in field.values:
                lines.extend(MDMLGenerator.generate_value(value, 0))
        else:
            # Inline format
            if field.values:
                value = field.values[0]

                if value.is_raw:
                    val = f"| {value.value} |"
                elif value.is_array:
                    # Array format: { `val1` ; `val2` ; `val3` }
                    array_str = ' ; '.join(f"`{v}`" for v in value.array_values)
                    val = f"{{ {array_str} }}"
                elif value.is_wiki_link:
                    if value.wiki_link and value.wiki_link != value.value:
                        val = f"[[{value.wiki_link}|{value.value}]]"
                    else:
                        val = f"[[{value.value}]]"
                elif value.is_raw_url:
                    val = value.value  # no backticks for URL
                else:
                    # Backticks by default for inline values
                    has_metadata = bool(value.date or value.details)
                    val = MDMLFormatter.quote_value(
                        text=value.value,
                        context='inline',
                        has_metadata=has_metadata,
                        is_raw=False
                    )

                # Add details
                if value.details:
                    val += f" ({value.details})"

                # Add datetime
                if value.date:
                    if value.time:
                        val += f", `{value.date} {value.time}`"
                    else:
                        val += f", `{value.date}`"

                lines.append(f"{field.name}: {val}")

        return lines

    @staticmethod
    def generate_markup_from_dict(data: Dict[str, Any], include_frontmatter: bool = True) -> str:
        """
        Converts a dictionary to MDML format

        Args:
            data: Dictionary with 'frontmatter' and 'fields' keys
            include_frontmatter: Whether to include YAML frontmatter

        Returns:
            MDML formatted string
        """
        lines = []

        # Frontmatter
        if include_frontmatter and 'frontmatter' in data and data['frontmatter']:
            lines.append('---')
            for key, value in data['frontmatter'].items():
                lines.append(f"{key}: {value}")
            lines.append('---')
            # lines.append('')  # Remove the extra line break after the frontmatter

        # Fields
        if 'fields' in data:
            for field_name, field_data in data['fields'].items():
                field = Field(
                    name=field_data.get('name', field_name),
                    is_list=field_data.get('is_list', False),
                    values=[],
                    raw_content=''
                )

                # Reconstruct values
                for val_data in field_data.get('values', []):
                    fv = FieldValue(
                        value=val_data.get('value', ''),
                        details=val_data.get('details'),
                        is_strikethrough=val_data.get('is_strikethrough', False),
                        is_array=val_data.get('is_array', False),
                        array_values=val_data.get('array_values', []),
                        is_raw=val_data.get('is_raw', False),
                        is_wiki_link=val_data.get('is_wiki_link', False),
                        wiki_link=val_data.get('wiki_link'),
                        link_url=val_data.get('link_url')
                    )
                    if val_data.get('datetime'):
                        parts = val_data['datetime'].split()
                        fv.date = parts[0] if parts else None
                        fv.time = parts[1] if len(parts) > 1 else None
                    field.values.append(fv)

                lines.extend(MDMLGenerator.generate_field(field))
                lines.append('')

        return '\n'.join(lines)

    @staticmethod
    def generate_markup_from_document(doc: 'Document', include_frontmatter: bool = True) -> str:
        """
        Generate MDML markup directly from a Document object

        Args:
            doc: Document instance
            include_frontmatter: Whether to include YAML frontmatter

        Returns:
            MDML formatted string
        """
        lines = []

        # Frontmatter
        if include_frontmatter and doc.frontmatter:
            lines.append('---')
            for key, value in doc.frontmatter.items():
                lines.append(f"{key}: {value}")
            lines.append('---')
            # lines.append('')  # Remove the extra line break after the frontmatter

        # Fields - iterate directly on Document's fields
        for field_name, field in doc.fields.items():
            lines.extend(MDMLGenerator.generate_field(field))
            lines.append('')

        return '\n'.join(lines)
