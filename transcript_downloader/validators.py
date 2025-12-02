"""Validation and escaping utilities for safe data handling."""

import re
from xml.sax.saxutils import escape as xml_escape


# UUID regex pattern for GUID validation
GUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def is_valid_guid(value: str) -> bool:
    """
    Check if a string is a valid GUID/UUID.

    Args:
        value: String to validate.

    Returns:
        True if valid GUID format, False otherwise.
    """
    if not isinstance(value, str):
        return False
    return GUID_PATTERN.match(value) is not None


def validate_guid(value: str, field_name: str = "value") -> str:
    """
    Validate that a string is a valid GUID and return it.

    Args:
        value: String to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated GUID string.

    Raises:
        ValueError: If the value is not a valid GUID.
    """
    if not is_valid_guid(value):
        raise ValueError(f"Invalid GUID format for {field_name}: {value}")
    return value


def escape_xml_value(value: str) -> str:
    """
    Escape a value for safe use in XML/FetchXML.

    Args:
        value: String to escape.

    Returns:
        XML-escaped string.
    """
    return xml_escape(str(value))


def escape_odata_string(value: str) -> str:
    """
    Escape a value for safe use in OData filter strings.

    Args:
        value: String to escape.

    Returns:
        OData-escaped string.
    """
    # Escape single quotes by doubling them
    return str(value).replace("'", "''")


def is_safe_path_component(value: str) -> bool:
    """
    Check if a string is safe to use as a path component.

    Args:
        value: String to validate.

    Returns:
        True if safe for path use, False otherwise.
    """
    if not value:
        return False
    # Check for path traversal attempts
    if ".." in value or value.startswith("/") or value.startswith("\\"):
        return False
    # Check for other problematic characters
    if any(c in value for c in [":", "*", "?", '"', "<", ">", "|", "\0"]):
        return False
    return True
