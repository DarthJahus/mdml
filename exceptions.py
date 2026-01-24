class MDMLException(Exception):
    """Base class for all MDML exceptions"""

class MDMLParseError(MDMLException):
    """Critical parsing error (document invalid)"""

class MDMLFieldError(MDMLException):
    """Error related to a specific field"""

class MDMLValueError(MDMLException):
    """Error while parsing a value"""
