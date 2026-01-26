from .models import Document, Field, FieldValue
from .parser import MDMLParser
from .generator import MDMLGenerator
from .importer import MDMLImporter
from typing import Optional, Dict, Any


# Convenience functions
def parse_document(content: str) -> Document:
    """Parse MDML document from string"""
    return MDMLParser.parse_document(content)


def generate_markup(data: Dict[str, Any]) -> str:
    """Generate MDML markup from dictionary"""
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