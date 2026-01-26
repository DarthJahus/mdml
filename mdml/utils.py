from datetime import datetime
from typing import Tuple, Optional, List
from .patterns import Patterns


def count_leading_tabs(line: str) -> int:
    """Count leading tabs in a line"""
    match = Patterns.TAB_INDENT.match(line)
    if match:
        return len(match.group(0))
    return 0


def clean_markdown(text: str) -> Tuple[str, bool, Optional[str]]:
    """
    Removes markdown formatting and detects strikethrough

    Returns:
        tuple: (cleaned_text, is_strikethrough, link_url)
    """
    is_strikethrough = bool(Patterns.STRIKETHROUGH.search(text))
    link_url = None

    # Extract link
    link_match = Patterns.LINK.search(text)
    if link_match:
        text = Patterns.LINK.sub(r'\1', text)  # ← Remplace [text](url) par text
        link_url = link_match.group(2)

    # Remove strikethrough
    text = Patterns.STRIKETHROUGH.sub(r'\1', text)

    # Remove code blocks
    text = Patterns.CODE_BLOCK.sub(r'\1', text)

    return text.strip(), is_strikethrough, link_url


def extract_details(text: str) -> Tuple[str, Optional[str]]:
    """
    Extracts details from parentheses (before datetime)

    Returns:
        tuple: (text_without_details, details)
    """
    match = Patterns.DETAILS.search(text)
    if not match:
        return text, None

    # Remove details from text
    text_clean = text[:match.start()].strip()
    details = match.group(1).strip()

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

