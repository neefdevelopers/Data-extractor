import re
from typing import Optional, Tuple
from app.utils.text_normalization import canonical_key, clean_display_text

def normalize_name(name: Optional[str]) -> Optional[str]:
    return clean_display_text(name, title_case=True)

def normalize_text_field(val: Optional[str], title_case: bool = False) -> Optional[str]:
    return clean_display_text(val, title_case=title_case)

def normalize_mobile(phone: Optional[str]) -> Tuple[Optional[str], bool]:
    """
    Normalizes Indian mobile numbers into standard 10-digit string.
    Returns (normalized_10_digit_string, is_valid)
    """
    if not phone or str(phone).strip().lower() in ["nan", "none", "null", ""]:
        return None, False
    
    # Remove float decimal points if read from excel (e.g. 9876543210.0)
    raw = str(phone).strip()
    if raw.endswith(".0"):
        raw = raw[:-2]
        
    # Strip all non-digit characters
    digits = re.sub(r"\D", "", raw)
    
    # If standard 10 digits starting with 6, 7, 8, 9
    if len(digits) == 10 and digits[0] in "6789":
        return digits, True
    
    # If 11 digits starting with 0 (e.g. 09876543210)
    if len(digits) == 11 and digits.startswith("0") and digits[1] in "6789":
        return digits[1:], True
        
    # If 12 digits starting with 91 (e.g. 919876543210)
    if len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
        return digits[2:], True

    # If 13 digits starting with 091
    if len(digits) == 13 and digits.startswith("091") and digits[3] in "6789":
        return digits[3:], True

    # Return raw digits if invalid
    return digits if digits else None, False

def normalize_pincode(pin: Optional[str]) -> Tuple[Optional[str], bool]:
    """
    Validates and standardizes 6-digit Indian PIN.
    Returns (cleaned_pin, is_valid)
    """
    if not pin or str(pin).strip().lower() in ["nan", "none", "null", ""]:
        return None, False
    
    raw = str(pin).strip()
    if raw.endswith(".0"):
        raw = raw[:-2]
        
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

