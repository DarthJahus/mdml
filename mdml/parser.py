import re
from typing import Optional, List, Dict, Tuple
from .models import FieldValue, Field, Document, FieldBlock
from .patterns import Patterns
from .utils import (
    count_leading_tabs,
    clean_markdown,
    detect_strikethrough,
    extract_details,
    extract_datetime,
    extract_array,
    extract_raw_text,
    extract_wiki_link,
    is_url
)


class MDMLParser:
    """MDML Parser - Resilient parsing with error recovery"""

    @staticmethod
    def split_into_blocks(content: str) -> Tuple[List[FieldBlock], Dict[str, str]]:
        """
        Split document into field blocks in a single pass

        Args:
            content: Full document content

        Returns:
            tuple: (list of FieldBlock objects, frontmatter dict)
        """
        # Parse frontmatter first
        frontmatter, body = MDMLParser.parse_frontmatter(content)

        # Calculate line offset (frontmatter lines + separator)
        frontmatter_lines = 0
        if frontmatter:
            match = Patterns.FRONTMATTER.match(content)
            if match:
                frontmatter_lines = content[:match.end()].count('\n')

        blocks = []
        lines = body.split('\n')
        current_block = None
        current_block_lines = []

        for line_idx, line in enumerate(lines, start=1):
            # Adjust line number for frontmatter offset
            absolute_line_num = line_idx + frontmatter_lines

            # Check if line starts a new field
            field_match = Patterns.FIELD_START.match(line)

            if field_match:
                # Save previous block if exists
                if current_block is not None:
                    current_block.raw_content = '\n'.join(current_block_lines)
                    blocks.append(current_block)

                # Start new block
                field_name = field_match.group(1).strip()
                current_block = FieldBlock(
                    name=field_name,
                    raw_content='',  # Will be filled when block ends
                    start_line=absolute_line_num
                )
                current_block_lines = [line]

            elif current_block is not None:
                # Continue current block
                current_block_lines.append(line)

        # Don't forget last block
        if current_block is not None:
            current_block.raw_content = '\n'.join(current_block_lines)
            blocks.append(current_block)

        return blocks, frontmatter

    @staticmethod
    def parse_value(raw_value: str, line_num: Optional[int] = None, strict: bool = False) -> FieldValue:
        """
        Parses a single value with all metadata

        Logic:
        1. Extract datetime (always at the end)
        2. Detect backticks BEFORE cleaning
        3. Clean markdown (links, strikethrough, etc.)
        4. Extract details (after markdown is cleaned)
        5. Detect explicit datatypes (RAW pipes, array, wiki_link)
        6. Fallback to RAW or regular value
        """
        original = raw_value
        text = raw_value
        link_url = None

        try:
            text, date_str, time_str, dt_obj = extract_datetime(text)

            text, details = extract_details(text)

            is_strikethrough = detect_strikethrough(text)

            text_has_backticks = text.strip().startswith('`') and text.strip().endswith('`')

            text, link_url = clean_markdown(text)

            if is_url(text):
                return FieldValue(
                    value=text.strip(),
                    date=date_str,
                    time=time_str,
                    datetime_obj=dt_obj,
                    details=details,
                    is_strikethrough=is_strikethrough,
                    link_url=link_url,
                    is_raw_url=True
                )

            # Detect explicit datatypes

            # 1: RAW text with pipes (highest priority)
            raw_text, is_raw = extract_raw_text(text)
            if is_raw:
                return FieldValue(
                    value=raw_text,
                    is_raw=True,
                    date=date_str,
                    time=time_str,
                    datetime_obj=dt_obj,
                    details=details,
                    link_url=link_url,
                    parse_error=None
                )

            # 2: Array format
            array_values, text_without_array = extract_array(text)
            if array_values is not None:
                return FieldValue(
                    value="",
                    is_array=True,
                    array_values=array_values,
                    date=date_str,
                    time=time_str,
                    datetime_obj=dt_obj,
                    details=details,
                    link_url=link_url,
                    parse_error=None
                )

            # 3: Wiki link format
            wiki_link, display, is_wiki = extract_wiki_link(text)
            if is_wiki:
                return FieldValue(
                    value=display,
                    is_wiki_link=True,
                    wiki_link=wiki_link,
                    date=date_str,
                    time=time_str,
                    datetime_obj=dt_obj,
                    details=details,
                    link_url=link_url,
                    parse_error=None
                )

            # Detect intentional formatting
            clean_text = text

            # Detect intentional formatting (backticks were checked earlier)
            has_intentional_formatting = (
                    is_strikethrough or  # ~~...~~
                    link_url or  # [...](...)
                    text_has_backticks  # `...` (detected before cleaning)
            )

            # Fallback to RAW (only for multi-word text without formatting)
            should_fallback_raw = (
                    not has_intentional_formatting and
                    ' ' in clean_text
            )

            if should_fallback_raw:
                return FieldValue(
                    value=clean_text,
                    is_raw=True,
                    date=date_str,
                    time=time_str,
                    datetime_obj=dt_obj,
                    details=details,
                    link_url=link_url,
                    parse_error=None
                )

            # Regular value (single word or with intentional formatting)
            return FieldValue(
                value=clean_text,
                date=date_str,
                time=time_str,
                datetime_obj=dt_obj,
                details=details,
                is_strikethrough=is_strikethrough,
                link_url=link_url,
                parse_error=None
            )

        except Exception as e:
            error_msg = f"Parse error at line {line_num}: {str(e)}" if line_num else str(e)
            return FieldValue(
                value=original.strip(),
                parse_error=error_msg
            )


    @staticmethod
    def parse_sub_items(lines: List[Tuple[int, str]], base_indent: int) -> Tuple[
        Dict[str, FieldValue], List[FieldValue], List[str]]:
        """
        Parses sub-items (both named fields and list items)

        Args:
            lines: List of (indent_level, content) tuples
            base_indent: Base indentation level to compare against

        Returns:
            tuple: (sub_fields_dict, sub_list_items, errors)
        """
        sub_fields = {}
        sub_list = []
        errors = []

        i = 0
        while i < len(lines):
            indent, content = lines[i]

            # Must be exactly one tab deeper than base
            if indent != base_indent + 1:
                i += 1
                continue

            # Check if it's a named sub-field: "- field: value"
            sub_field_match = Patterns.SUB_FIELD.match(content)
            if sub_field_match:
                field_name = sub_field_match.group(1).strip()
                field_value = sub_field_match.group(2)

                # Check if this sub-field has its own nested items
                nested_lines = []
                j = i + 1
                while j < len(lines) and lines[j][0] > indent:
                    nested_lines.append(lines[j])
                    j += 1

                parsed_value = MDMLParser.parse_value(field_value)

                # Parse nested items if any
                if nested_lines:
                    nested_fields, nested_list, nested_errors = MDMLParser.parse_sub_items(
                        nested_lines, indent
                    )
                    parsed_value.sub_items = nested_fields
                    parsed_value.list_sub_items = nested_list
                    errors.extend(nested_errors)

                sub_fields[field_name] = parsed_value
                i = j
                continue

            # Check if it's a list item: "- value"
            list_match = Patterns.LIST_ITEM.match(content)
            if list_match:
                item_value = list_match.group(1)

                # Check for nested items
                nested_lines = []
                j = i + 1
                while j < len(lines) and lines[j][0] > indent:
                    nested_lines.append(lines[j])
                    j += 1

                parsed_value = MDMLParser.parse_value(item_value)

                # Parse nested items
                if nested_lines:
                    nested_fields, nested_list, nested_errors = MDMLParser.parse_sub_items(
                        nested_lines, indent
                    )
                    parsed_value.sub_items = nested_fields
                    parsed_value.list_sub_items = nested_list
                    errors.extend(nested_errors)

                sub_list.append(parsed_value)
                i = j
                continue

            i += 1

        return sub_fields, sub_list, errors

    @staticmethod
    def parse_field_block(block: FieldBlock) -> Optional[Field]:
        """
        Parses a field from a FieldBlock (linear parsing, no scanning)

        Args:
            block: FieldBlock containing field name, content, and line number

        Returns:
            Field object or None if parsing fails
        """
        lines = block.raw_content.split('\n')
        errors = []

        # First line contains field name and possibly inline value
        first_line = lines[0]
        field_match = Patterns.FIELD_START.match(first_line)

        if not field_match:
            return None

        inline_value = field_match.group(2).strip()

        # Check if next line starts with '-'
        is_list_format = False
        if len(lines) > 1:
            for line in lines[1:]:
                stripped = line.lstrip('\t').lstrip(' ')
                if stripped:
                    is_list_format = stripped.startswith('-')
                    break

        # CASE 1: Inline value (has value on same line AND next line doesn't start with '-')
        if inline_value and not is_list_format:
            try:
                value = MDMLParser.parse_value(inline_value, block.start_line)
                return Field(
                    name=block.name,
                    is_list=False,
                    values=[value],
                    raw_content=block.raw_content,
                    parse_errors=errors
                )
            except Exception as e:
                errors.append(f"Error parsing inline field '{block.name}': {str(e)}")
                return Field(
                    name=block.name,
                    is_list=False,
                    values=[FieldValue(value=inline_value, parse_error=str(e))],
                    raw_content=block.raw_content,
                    parse_errors=errors
                )

        # CASE 2: List format (with or without inline value to convert)
        # Parse all lines with indentation
        indexed_lines = []

        # If there's an inline value with list format, convert it to first list item
        if inline_value and is_list_format:
            indexed_lines.append((0, f"- {inline_value}"))

        # Add rest of lines
        for line_idx, line in enumerate(lines[1:], start=1):  # Skip field name line
            if not line.strip():
                continue
            indent = count_leading_tabs(line)
            content_stripped = line.lstrip('\t')
            indexed_lines.append((indent, content_stripped))

        if not indexed_lines:
            return None  # Empty field

        # Parse top-level items (indent = 0)
        values = []
        i = 0
        while i < len(indexed_lines):
            indent, item_content = indexed_lines[i]

            if indent != 0:
                i += 1
                continue

            # Must be a list item
            list_match = Patterns.LIST_ITEM.match(item_content)
            if not list_match:
                errors.append(f"Invalid list item format at line {block.start_line + i + 1}: {item_content}")
                i += 1
                continue

            item_value = list_match.group(1)

            # Collect sub-items (indent > 0)
            sub_lines = []
            j = i + 1
            while j < len(indexed_lines) and indexed_lines[j][0] > 0:
                sub_lines.append(indexed_lines[j])
                j += 1

            # Parse main value
            try:
                parsed_value = MDMLParser.parse_value(item_value, block.start_line + i + 1)

                # Parse sub-items
                if sub_lines:
                    sub_fields, sub_list, sub_errors = MDMLParser.parse_sub_items(sub_lines, 0)
                    parsed_value.sub_items = sub_fields
                    parsed_value.list_sub_items = sub_list
                    errors.extend(sub_errors)

                values.append(parsed_value)
            except Exception as e:
                errors.append(f"Error parsing list item at line {block.start_line + i + 1}: {str(e)}")
                values.append(FieldValue(value=item_value, parse_error=str(e)))

            i = j

        if not values:
            return None

        return Field(
            name=block.name,
            is_list=True,
            values=values,
            raw_content=block.raw_content,
            parse_errors=errors
        )

    @staticmethod
    def parse_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
        """
        Parses YAML frontmatter

        Returns:
            tuple: (frontmatter_dict, content_without_frontmatter)
        """
        match = Patterns.FRONTMATTER.match(content)
        if not match:
            return {}, content

        yaml_text = match.group(1)
        content_without = content[match.end():]

        # Simple YAML parser
        frontmatter = {}
        for line in yaml_text.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip()

        return frontmatter, content_without

    @staticmethod
    def parse_document(content: str) -> Document:
        """
        Parses a complete MDML document with linear complexity

        Args:
            content: Full document content

        Returns:
            Document object with all fields parsed
        """
        doc = Document(raw_content=content)

        try:
            # Split document into blocks in single pass
            blocks, frontmatter = MDMLParser.split_into_blocks(content)
            doc.frontmatter = frontmatter

            # Parse each block independently
            for block in blocks:
                try:
                    field = MDMLParser.parse_field_block(block)
                    if field:
                        doc.fields[field.name] = field
                except Exception as e:
                    doc.parse_errors.append(f"Error parsing field '{block.name}': {str(e)}")
                    # Continue parsing other fields

        except Exception as e:
            doc.parse_errors.append(f"Critical parsing error: {str(e)}")

        return doc
