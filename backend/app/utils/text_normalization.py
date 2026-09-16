import re
from typing import Optional, List, Any
from sqlalchemy import func, or_, and_

def canonical_key(val: Optional[Any]) -> str:
    """
    Normalizes a string for internal comparison, deduplication, hash mapping, and grouping.
    - Strips leading/trailing whitespace
    - Collapses multiple internal whitespace characters into a single space
    - Converts to lowercase
    - Returns empty string for None/Null-like values
    """
    if val is None:
        return ""
    s = str(val).strip()
    if s.lower() in ["nan", "none", "null", "undefined", ""]:
        return ""
    return " ".join(s.split()).lower()

def clean_display_text(val: Optional[Any], title_case: bool = False) -> Optional[str]:
    """
    Cleans string whitespace while preserving display-quality casing.
    - Strips leading/trailing whitespace
    - Collapses consecutive whitespace
    - Preserves case (or converts to Title Case if specified)
    - Returns None for empty/null values
    """
    if val is None:
        return None
    s = str(val).strip()
    if s.lower() in ["nan", "none", "null", "undefined", ""]:
        return None
    cleaned = " ".join(s.split())
    if title_case:
        # Title case while preserving acronyms/parentheses cleanly
        return cleaned.title()
    return cleaned

def ci_equals(val1: Optional[Any], val2: Optional[Any]) -> bool:
    """
    Case-insensitive, whitespace-agnostic equality check.
    "Malappuram" == "  malappuram  " == "MALAPPURAM" -> True
    """
    k1 = canonical_key(val1)
    k2 = canonical_key(val2)
    if not k1 and not k2:
        return True
    return k1 == k2

def ci_contains(text: Optional[Any], query: Optional[Any]) -> bool:
    """
    Case-insensitive, whitespace-agnostic substring check.
    """
    t = canonical_key(text)
    q = canonical_key(query)
    if not q:
        return True
    return q in t

def sql_ci_equals(column, val: Optional[Any]):
    """
    SQLAlchemy expression for case-insensitive and trimmed equality comparison.
    Works reliably across SQLite, PostgreSQL, and other SQL engines.
    """
    target = canonical_key(val)
    return func.lower(func.trim(column)) == target

def sql_ci_like(column, query: Optional[Any]):
    """
    SQLAlchemy expression for case-insensitive and trimmed contains/like query.
    """
    target = canonical_key(query)
    return func.lower(func.trim(column)).like(f"%{target}%")

def sql_ci_in(column, values: List[str]):
    """
    SQLAlchemy expression for case-insensitive membership check.
    """
    norm_vals = [canonical_key(v) for v in values if canonical_key(v)]
    return func.lower(func.trim(column)).in_(norm_vals)
