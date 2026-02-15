from datetime import datetime
from typing import Tuple, Optional, List
from .patterns import Patterns
from re import compile, IGNORECASE


def count_leading_tabs(line: str) -> int:
    """Count leading tabs in a line"""
    match = Patterns.TAB_INDENT.match(line)
    if match:
        return len(match.group(0))
    return 0


def detect_strikethrough(text: str) -> bool:
    """
    Detects if text has strikethrough formatting ~~text~~

    Args:
        text: The text to check

    Returns:
        True if ~~...~~ pattern is found
    """
    return bool(Patterns.STRIKETHROUGH.search(text))


def clean_markdown(text: str) -> Tuple[str, Optional[str]]:
    """
    Removes markdown formatting (strikethrough, backticks, links)
    Does NOT detect strikethrough - use detect_strikethrough() first

    Returns:
        tuple: (cleaned_text, link_url)
    """
    link_url = None

    # Extract link
    link_match = Patterns.LINK.search(text)
    if link_match:
        text = Patterns.LINK.sub(r'\1', text)  # Replace [text](url) with text
        link_url = link_match.group(2)

    # Remove strikethrough
    text = Patterns.STRIKETHROUGH.sub(r'\1', text)

    # Remove code blocks
    text = Patterns.CODE_BLOCK.sub(r'\1', text)

    return text.strip(), link_url


def extract_details(text: str) -> Tuple[str, Optional[str]]:
    """
    Extracts details from the LAST parentheses pair at end of text
    Supports nested parentheses and markdown links within details

    Returns:
        tuple: (text_without_details, details)
    """
    text = text.rstrip()

    # Must end with )
    if not text.endswith(')'):
        return text, None

    # Walk backwards to find matching opening paren
    paren_count = 1
    pos = len(text) - 2  # Start before last )

    while pos >= 0:
        if text[pos] == ')':
            paren_count += 1
        elif text[pos] == '(':
            paren_count -= 1

            # Found a matching opening paren
            if paren_count == 0:
                # Check if this is part of a markdown link ](...)
                if pos > 0 and text[pos - 1] == ']':
                    # This (...) is a markdown link, continue searching for outer pair
                    paren_count = 1  # Reset and keep searching
                else:
                    # This is our detail block!
                    break

        pos -= 1

    if paren_count != 0 or pos < 0:
        # Unbalanced parens or not found
        return text, None

    open_pos = pos

    # Extract detail content
    details = text[open_pos + 1:-1].strip()
    text_clean = text[:open_pos].strip()

    return text_clean, details


def extract_datetime(text: str) -> Tuple[str, Optional[str], Optional[str], Optional[datetime]]:
    """
    Extracts datetime suffix from text

    Returns:
        tuple: (text_without_date, date_str, time_str, datetime_obj)
    """
    match = Patterns.DATETIME_SUFFIX.search(text)
    if not match:
        return text, None, None, None

    # Remove datetime from text
    text_clean = text[:match.start()].strip()

    date_str = match.group(1)
    time_str = match.group(2)  # May be None

    # Parse datetime
    dt_obj = None
    try:
        if time_str:
            dt_obj = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        else:
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass  # Invalid datetime format - non-blocking

    return text_clean, date_str, time_str, dt_obj


def extract_array(text: str) -> Tuple[Optional[List[str]], str]:
    """
    Extracts array values from { el1 ; el2 ; el3 } format

    Returns:
        tuple: (array_values, text_without_array)
    """
    match = Patterns.ARRAY.search(text)
    if not match:
        return None, text

    # Extract array content
    array_content = match.group(1)
    # Split by ; and clean each element
    array_values = [val.strip() for val in array_content.split(';')]

    # Clean backticks from each element if present
    cleaned_values = []
    for val in array_values:
        # Remove surrounding backticks if present
        if val.startswith('`') and val.endswith('`'):
            val = val[1:-1]
        cleaned_values.append(val)

    # Remove array from text
    text_without = text[:match.start()].strip() + ' ' + text[match.end():].strip()
    text_without = text_without.strip()

    return cleaned_values, text_without


def extract_raw_text(text: str) -> Tuple[Optional[str], bool]:
    """
    Extracts raw text from | raw text | format

    Format is resilient:
    - | text | → captures "text"
    - | text (no closing pipe) → captures "text" until end of line

    Returns:
        tuple: (raw_text, is_raw)
    """
    match = Patterns.RAW_TEXT.search(text)
    if not match:
        return None, False

    # Extract raw content - NO processing at all
    raw_content = match.group(1).strip()
    return raw_content, True


def extract_wiki_link(text: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Extracts wiki link from [[link]] or [[link|display]] format

    Returns:
        tuple: (wiki_link, display_text, is_wiki_link)
    """
    match = Patterns.WIKI_LINK.search(text)
    if not match:
        return None, None, False

    wiki_link = match.group(1).strip()
    display = match.group(2).strip() if match.group(2) else wiki_link

    return wiki_link, display, True


def is_url(text: str) -> bool:
    """
    Checks if text is a pure URL (http, https, ftp, ws, wss, etc.)

    Returns:
        True if text is a valid URL with protocol
    """
    url_pattern = compile(
        r'^(https?|ftp|ftps|ws|wss|file)://'  # Protocol
        r'[^\s]+$',  # Rest of URL (no whitespace)
        IGNORECASE
    )
    return bool(url_pattern.match(text.strip()))
