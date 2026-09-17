import re
from typing import Optional, Tuple, Any
from app.utils.text_normalization import canonical_key, clean_display_text

def normalize_name(name: Optional[Any]) -> Optional[str]:
    """
    Cleans customer / entity name while preserving Malayalam, Unicode, and numeric/mixed names.
    """
    if name is None:
        return None
    s = str(name).strip()
    if s.lower() in ["nan", "none", "null", "undefined", "n/a", "na", "-"] or not s:
        return None
    # Remove float decimal point if name was parsed as a number in excel (e.g. 101.0 -> 101)
    if s.endswith(".0") and s[:-2].replace("-", "").isdigit():
        s = s[:-2]
    return clean_display_text(s, title_case=True)

def normalize_text_field(val: Optional[Any], title_case: bool = False) -> Optional[str]:
    return clean_display_text(val, title_case=title_case)

def normalize_mobile(phone: Optional[Any]) -> Tuple[Optional[str], bool]:
    """
    Normalizes Indian mobile numbers into standard 10-digit string.
    Handles:
    - Floats/ints from Excel (e.g. 9847123456.0, 9.847123456e+09)
    - Country codes (+91, 91, 091, 0091, 0)
    - Multiple numbers in one cell ("9847123456 / 9447123456", "9847123456, 8089123456")
    - Text prefixes/suffixes ("Mob: 9847123456", "WhatsApp 9847123456")
    - Punctuation, dashes, and spacing
    Returns (normalized_10_digit_string, is_valid)
    """
    if phone is None:
        return None, False
    
    s = str(phone).strip()
    if s.lower() in ["nan", "none", "null", "undefined", "n/a", "na", "-"] or not s:
        return None, False
    
    # Handle scientific notation or float representations e.g. 9.84712e+09 or 9847123456.0
    try:
        if "e" in s.lower() or ("." in s and not s.startswith(".")):
            f_val = float(s)
            if f_val > 0:
                s = str(int(f_val))
    except (ValueError, OverflowError):
        pass

    # Extract first standard 10-digit Indian mobile starting with 6,7,8,9
    mobile_matches = re.findall(r"(?:(?:\+?91|0091|0)?[\s\-]*)?([6-9]\d{9})\b", s)
    if mobile_matches:
        return mobile_matches[0], True

    # Strip all non-digit characters
    raw = s
    if raw.endswith(".0"):
        raw = raw[:-2]
    digits = re.sub(r"\D", "", raw)
    
    if not digits:
        return None, False

    # If standard 10 digits starting with 6, 7, 8, 9
    if len(digits) == 10 and digits[0] in "6789":
        return digits, True
    
    # If 11 digits starting with 0 (e.g. 09876543210)
    if len(digits) == 11 and digits.startswith("0") and digits[1] in "6789":
        return digits[1:], True
        
    # If 12 digits starting with 91 (e.g. 919876543210)
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return digits[2:], True

    # If 13 or 14 digits starting with 091 / 0091
    if len(digits) == 13 and digits.startswith("091") and digits[3] in "6789":
        return digits[3:], True
    if len(digits) == 14 and digits.startswith("0091") and digits[4] in "6789":
        return digits[4:], True

    # Check if any 10-digit valid mobile chunk is embedded within digits
    for i in range(len(digits) - 9):
        chunk = digits[i:i+10]
        if chunk[0] in "6789":
            return chunk, True

    # Return raw digits if invalid (e.g. landline or short code)
    return digits if digits else None, False

def normalize_pincode(pin: Optional[Any]) -> Tuple[Optional[str], bool]:
    """
    Validates and standardizes 6-digit Indian PIN.
    Returns (cleaned_pin, is_valid)
    """
    if pin is None:
        return None, False
    
    s = str(pin).strip()
    if s.lower() in ["nan", "none", "null", "undefined", "n/a", "na", "-"] or not s:
        return None, False
    
    try:
        if "e" in s.lower() or ("." in s and not s.startswith(".")):
            f_val = float(s)
            if f_val > 0:
                s = str(int(f_val))
    except (ValueError, OverflowError):
        pass

    raw = s
    if raw.endswith(".0"):
        raw = raw[:-2]
        
    # First search for 6-digit PIN pattern starting with 1-9
    pin_matches = re.findall(r"\b([1-9]\d{5})\b", raw)
    if pin_matches:
        return pin_matches[0], True

    digits = re.sub(r"\D", "", raw)
    if len(digits) == 6 and digits[0] in "123456789":
        return digits, True
        
    return digits if digits else None, False

def normalize_payment_mode(mode: Optional[str]) -> str:
    if not mode or str(mode).strip().lower() in ["nan", "none", "null", ""]:
        return "COD"
    val = canonical_key(mode)
    if "pre" in val or "online" in val or "card" in val or "upi" in val or "net" in val or "paid" in val:
        return "PREPAID"
    return "COD"

def normalize_order_status(status: Optional[str]) -> str:
    if not status or str(status).strip().lower() in ["nan", "none", "null", ""]:
        return "DELIVERED"
    val = canonical_key(status)
    if "deliver" in val or "dispatch" in val or "complet" in val or "fulfill" in val:
        return "DELIVERED"
    if "cancel" in val:
        return "CANCELLED"
    if "return" in val or "rto" in val:
        return "RETURNED"
    if "refund" in val:
        return "REFUNDED"
    if "pend" in val or "hold" in val or "process" in val:
        return "PENDING"
    return "DELIVERED"

def clean_address(addr: Optional[str]) -> Optional[str]:
    return clean_display_text(addr)

