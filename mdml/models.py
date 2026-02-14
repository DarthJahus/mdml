import json
import yaml
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class FieldValue:
    """Represents a parsed field value with metadata"""
    value: str
    date: Optional[str] = None
    time: Optional[str] = None
    datetime_obj: Optional[datetime] = None
    details: Optional[str] = None  # Content inside parentheses (detail)
    is_strikethrough: bool = False
    is_array: bool = False
    array_values: List[str] = field(default_factory=list)
    is_raw: bool = False
    is_wiki_link: bool = False
    link_url: Optional[str] = None
    wiki_link: Optional[str] = None
    sub_items: Dict[str, 'FieldValue'] = field(default_factory=dict)  # Named sub-fields
    list_sub_items: List['FieldValue'] = field(default_factory=list)  # List sub-items
    parse_error: Optional[str] = None  # Non-blocking parse error

    @property
    def datetime_str(self) -> Optional[str]:
        """Returns formatted datetime string if available"""
        if self.date and self.time:
            return f"{self.date} {self.time}"
        elif self.date:
            return self.date
        return None

    def has_error(self) -> bool:
        """Check if this value has parse errors"""
        return self.parse_error is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export"""
        result = {
            'value': self.value,
            'datetime': self.datetime_str,
            'is_strikethrough': self.is_strikethrough,
        }
        if self.is_array:
            result['is_array'] = True
            result['array_values'] = self.array_values
        if self.is_raw:
            result['is_raw'] = True
        if self.is_wiki_link:
            result['is_wiki_link'] = True
        if self.link_url:
            result['link_url'] = self.link_url
        if self.wiki_link:
            result['wiki_link'] = self.wiki_link
        if self.details:
            result['details'] = self.details
        if self.sub_items:
            result['sub_items'] = {k: v.to_dict() for k, v in self.sub_items.items()}
        if self.list_sub_items:
            result['list_sub_items'] = [v.to_dict() for v in self.list_sub_items]
        if self.parse_error:
            result['parse_error'] = self.parse_error
        return result

@dataclass
class FieldBlock:
    """Represents a raw field block for linear parsing"""
    name: str
    raw_content: str  # Complete text of the field block
    start_line: int   # Line number where field starts (1-indexed)

@dataclass
class Field:
    """Represents a parsed field (inline or list)"""
    name: str
    is_list: bool
    values: List[FieldValue]
    raw_content: str
    parse_errors: List[str] = field(default_factory=list)

    @property
    def first_value(self) -> Optional[FieldValue]:
        """Returns the first (most recent) value"""
        return self.values[0] if self.values else None

    @property
    def last_value(self) -> Optional[FieldValue]:
        """Returns the last (oldest) value"""
        return self.values[-1] if self.values else None

    def has_errors(self) -> bool:
        """Check if this field has parse errors"""
        return len(self.parse_errors) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export"""
        return {
            'name': self.name,
            'is_list': self.is_list,
            'values': [v.to_dict() for v in self.values],
            'parse_errors': self.parse_errors if self.parse_errors else None
        }


@dataclass
class Document:
    """Represents a parsed MDML document"""
    fields: Dict[str, Field] = field(default_factory=dict)
    frontmatter: Dict[str, str] = field(default_factory=dict)
    parse_errors: List[str] = field(default_factory=list)
    raw_content: str = ""

    def __str__(self) -> str:
        """Generate MDML markup representation of this document"""
        from .generator import MDMLGenerator
        return MDMLGenerator.generate_markup(self.to_dict())

    def get_field(self, name: str) -> Optional[Field]:
        """Get field by name"""
        return self.fields.get(name)

    def get_value(self, name: str, index: int = 0) -> Optional[FieldValue]:
        """Get a specific value from a field"""
        field = self.get_field(name)
        if not field or not field.values:
            return None
        try:
            return field.values[index]
        except IndexError:
            return None

    def get_values(self, name: str) -> List[FieldValue]:
        """Get all values from a field"""
        field = self.get_field(name)
        return field.values if field else []

    def has_errors(self) -> bool:
        """Check if document has any parse errors"""
        if self.parse_errors:
            return True
        return any(f.has_errors() for f in self.fields.values())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for export"""
        return {
            'frontmatter': self.frontmatter if self.frontmatter else None,
            'fields': {name: field.to_dict() for name, field in self.fields.items()},
            'parse_errors': self.parse_errors if self.parse_errors else None
        }

    def to_json(self, indent: int = 2) -> str:
        """Export as JSON"""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_yaml(self) -> str:
        """Export as YAML"""
        return yaml.dump(self.to_dict(), default_flow_style=False, allow_unicode=True)
