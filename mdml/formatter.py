from .patterns import Patterns

class MDMLFormatter:
    """Centralized formatting rules for MDML generation"""

    INDENT_CHAR = '\t'
    SPECIAL_CHARS = {' ', ',', '(', ')', ';', '|'}

    @staticmethod
    def needs_quoting(text: str) -> bool:
        """
        Determines if a text value needs backtick quoting

        Args:
            text: The text to check

        Returns:
            True if text contains special characters requiring quotes
        """
        return any(c in text for c in MDMLFormatter.SPECIAL_CHARS)

    @staticmethod
    def quote_value(text: str, context: str, has_metadata: bool = False, is_raw: bool = False, is_wiki_link: bool = False, is_raw_url: bool = False) -> str:
        """
        Applies quoting rules based on context

        Args:
            text: The text value to quote
            context: Either 'inline' or 'list'
            has_metadata: quote if one word
            is_raw: Ignored (kept for compatibility)
            is_wiki_link: Avoid wrapping wikilinks in backticks

        Returns:
            Properly quoted text according to context rules

        Rules:
            Inline: backticks always mandatory
            List: backticks always OPTIONAL (never added by generator)
        """
        # Wiki links are never wrapped
        if is_wiki_link:
            return f"[[{text}]]"

        if is_raw_url:
            return text.strip()

        if has_metadata:
            return f"`{text}`"

        if context == 'inline':
            # Inline values: backticks required UNLESS it's a known datatype
            escaped = text.replace('`', '\\`')
            return f"`{escaped}`"

        elif context == 'list':
            # List values:
            #   backticks are OPTIONAL
            #   Generator adds them in certain situations
            #   Parser always accepts them
            if MDMLFormatter.needs_quoting(text):
                return f"`{text}`"
            if MDMLFormatter.needs_quoting_in_list(text):
                return f"`{text}`"
            return text

        else:
            raise ValueError(f"Invalid context: {context}. Must be 'inline' or 'list'")

    @staticmethod
    def make_indent(level: int) -> str:
        """
        Creates consistent indentation string

        Args:
            level: Indentation level (0 = no indent)

        Returns:
            Indentation string (tabs)
        """
        return MDMLFormatter.INDENT_CHAR * level

    @staticmethod
    def needs_quoting_in_list(text: str) -> bool:
        """
        Determine if a list value needs backticks.

        Cases requiring backticks:
        - Pure numbers: 56467, 312.54, 416,578
        - Dates: 2026-02-15
        - Times: 21:24, 21:24:30
        - Datetimes: 2026-02-15 21:24
        - Handles: @something
        - Variables/emojis: %something%
        """

        # Handle/mention (@ at the start only)
        if text.startswith('@') and ' ' not in text and '@' not in text[1:]:
            return True

        # Variable/emoji (wrapped in %)
        if text.startswith('%') and text.endswith('%') and ' ' not in text:
            return True

        # Pure number (int or float, with optional thousand separators)
        # Matches: 123, 123.45, 1,234, 1,234.56
        if Patterns.NUMBER.match(text):
            return True

        if Patterns.NUMBER_FORMATTED.match(text):
            return True

        # Date (ISO format: YYYY-MM-DD)
        if Patterns.DATE.match(text):
            return True

        # Time (HH:MM or HH:MM:SS)
        if Patterns.TIME.match(text):
            return True

        # Datetime (YYYY-MM-DD HH:MM or YYYY-MM-DD HH:MM:SS)
        if Patterns.DATETIME.match(text):
            return True

        # Scientific notation: 1.5e10, 2.3E-5, -1.5e10
        # Matches: 1e10, 1.5e10, 1.5E-10, -1.5e10
        if Patterns.SCIENTIFIC.match(text):
            return True

        # IPv4
        if Patterns.IPv4.match(text):
            return True

        # IPv6 (supports full and compressed formats)
        if Patterns.IPv6.match(text) or text == '::':
            return True

        return False
