import re


class Patterns:
    """Regex patterns for MDML parsing"""

    # Frontmatter
    FRONTMATTER = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL | re.MULTILINE)

    # Field detection
    FIELD_START = re.compile(r'^([a-z][a-z0-9_. ]*):\s*(.*)$', re.MULTILINE)

    # List item with TAB indentation
    LIST_ITEM = re.compile(r'^-\s+(.+)$')

    # Sub-item detection (starts with TAB)
    TAB_INDENT = re.compile(r'^\t+')

    # Date/time extraction (at end of value, after comma)
    DATETIME_SUFFIX = re.compile(r',\s*`?(\d{4}-\d{2}-\d{2})(?:\s+(\d{2}:\d{2}))?`?\s*$')

    # Details in parentheses (after value, before datetime)
    #DETAILS = re.compile(r'(?<!\])\s*\(([^)]+)\)\s*$')

    # Markdown formatting
    STRIKETHROUGH = re.compile(r'~~(.+?)~~')
    CODE_BLOCK = re.compile(r'`([^`]+)`')
    LINK = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')

    # Sub-field format: "- field: value"
    SUB_FIELD = re.compile(r'^-\s+([a-z][a-z0-9_\s]*):\s*(.*)$')

    # Array format: { el1 ; el2 ; el3 }
    ARRAY = re.compile(r'\{\s*([^}]+)\s*\}')

    # Raw text format: | anything | (resilient - closing pipe optional)
    RAW_TEXT = re.compile(r'\|\s*(.*?)(?:\s*\|)?\s*$')

    # Wiki link format: [[link_name]]
    WIKI_LINK = re.compile(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]')

    NUMBER = re.compile(r'^\d{1,3}(,\d{3})*(\.\d+)?$')

    DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

    TIME = re.compile(r'^\d{2}:\d{2}(:\d{2})?$')

    DATETIME = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$')

    SCIENTIFIC = re.compile(r'^-?\d+(\.\d+)?[eE][+-]?\d+$')

    IPv4 = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')

    # Matches: 2001:0db8:85a3:0000:0000:8a2e:0370:7334
    #          2001:db8:85a3::8a2e:370:7334
    #          ::1
    #          fe80::
    IPv6 = re.compile(r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$')
