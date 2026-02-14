from .models import Document, Field, FieldValue
from .parser import MDMLParser
from .generator import MDMLGenerator
from .importer import MDMLImporter
from typing import Dict, Any, Union


# Convenience functions
def parse_document(content: str) -> Document:
    """Parse MDML document from string"""
    return MDMLParser.parse_document(content)


def generate_markup(data: Union[Dict[str, Any], Document]) -> str:
    """Generate MDML markup from dictionary or Document"""
    # If it's a Document, convert to dict first
    # ToDo: native conversion without going through dict?
    if isinstance(data, Document):
        data = data.to_dict()
    return MDMLGenerator.generate_markup(data)


def from_dict(data: Dict[str, Any]) -> Document:
    """Create Document from dictionary"""
    return MDMLImporter.from_dict(data)


def from_json(json_str: str) -> Document:
    """Create Document from JSON"""
    return MDMLImporter.from_json(json_str)


__all__ = [
    "parse_document",
    "generate_markup",
    "Document",
    "Field",
    "FieldValue",
]