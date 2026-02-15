import json
import yaml
from typing import Dict, Any
from .models import Document, Field, FieldValue


class MDMLImporter:
    """Imports Document from various formats"""

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Document:
        """Create Document from dictionary"""
        doc = Document()

        if 'frontmatter' in data and data['frontmatter']:
            doc.frontmatter = data['frontmatter']

        if 'fields' in data:
            for field_name, field_data in data['fields'].items():
                values = []
                for val_data in field_data.get('values', []):
                    fv = MDMLImporter._import_field_value(val_data)
                    values.append(fv)

                field = Field(
                    name=field_data.get('name', field_name),
                    is_list=field_data.get('is_list', False),
                    values=values,
                    raw_content='',
                    parse_errors=field_data.get('parse_errors', [])
                )
                doc.fields[field_name] = field

        return doc

    @staticmethod
    def _import_field_value(val_data: Dict[str, Any]) -> FieldValue:
        """
        Recursively import a FieldValue from dictionary

        Args:
            val_data: Dictionary containing field value data

        Returns:
            FieldValue object with all nested data restored
        """
        fv = FieldValue(
            value=val_data.get('value', ''),
            details=val_data.get('details'),
            is_strikethrough=val_data.get('is_strikethrough', False),
            is_array=val_data.get('is_array', False),
            array_values=val_data.get('array_values', []),
            is_raw=val_data.get('is_raw', False),
            is_raw_url=val_data.get('is_raw_url', False),
            is_wiki_link=val_data.get('is_wiki_link', False),
            wiki_link=val_data.get('wiki_link'),
            link_url=val_data.get('link_url'),
            parse_error=val_data.get('parse_error')
        )

        # Import datetime
        if val_data.get('datetime'):
            parts = val_data['datetime'].split()
            fv.date = parts[0] if parts else None
            fv.time = parts[1] if len(parts) > 1 else None

        # Import sub_items (named sub-fields) recursively
        if val_data.get('sub_items'):
            for sub_name, sub_data in val_data['sub_items'].items():
                fv.sub_items[sub_name] = MDMLImporter._import_field_value(sub_data)

        # Import list_sub_items recursively
        if val_data.get('list_sub_items'):
            for sub_data in val_data['list_sub_items']:
                fv.list_sub_items.append(MDMLImporter._import_field_value(sub_data))

        return fv

    @staticmethod
    def from_json(json_str: str) -> Document:
        """Create Document from JSON string"""
        data = json.loads(json_str)
        return MDMLImporter.from_dict(data)

    @staticmethod
    def from_yaml(yaml_str: str) -> Document:
        """Create Document from YAML string"""
        data = yaml.safe_load(yaml_str)
        return MDMLImporter.from_dict(data)
