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
    def quote_value(text: str, context: str, has_metadata: bool = False, is_raw: bool = False, is_wiki_link: bool = False) -> str:
        """
        Applies quoting rules based on context

        Args:
            text: The text value to quote
            context: Either 'inline' or 'list'
            has_metadata: Ignored (kept for compatibility)
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

        if context == 'inline':
            # Inline values: backticks required UNLESS it's a known datatype
            escaped = text.replace('`', '\\`')
            return f"`{escaped}`"

        elif context == 'list':
            # List values: backticks are OPTIONAL
            # Generator never adds them, but parser accepts them
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
