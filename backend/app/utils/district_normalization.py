import re
from typing import Optional, Dict, Tuple
from app.utils.text_normalization import canonical_key, clean_display_text

# Canonical Kerala Districts and their aliases, spelling variations, old names, and Malayalam script equivalents
KERALA_DISTRICT_MAP: Dict[str, Tuple[str, str]] = {
    # District Canonical Name: (Display Name, State)
    # 1. Kozhikode
    "kozhikode": ("Kozhikode", "Kerala"),
    "calicut": ("Kozhikode", "Kerala"),
    "kozhikkode": ("Kozhikode", "Kerala"),
    "kozhikod": ("Kozhikode", "Kerala"),
    "kozhikkod": ("Kozhikode", "Kerala"),
    "kozhikide": ("Kozhikode", "Kerala"),
    "kozhikot": ("Kozhikode", "Kerala"),
    "kozikkode": ("Kozhikode", "Kerala"),
    "kozikkod": ("Kozhikode", "Kerala"),
    "kozohide": ("Kozhikode", "Kerala"),
    "കോഴിക്കോട്": ("Kozhikode", "Kerala"),
    "കാലിക്കറ്റ്": ("Kozhikode", "Kerala"),

    # 2. Malappuram
    "malappuram": ("Malappuram", "Kerala"),
    "malapuram": ("Malappuram", "Kerala"),
    "malppuram": ("Malappuram", "Kerala"),
    "mlp": ("Malappuram", "Kerala"),
    "മലപ്പുറം": ("Malappuram", "Kerala"),

    # 3. Ernakulam
    "ernakulam": ("Ernakulam", "Kerala"),
    "eranakulam": ("Ernakulam", "Kerala"),
    "earnakulam": ("Ernakulam", "Kerala"),
    "enranakulam": ("Ernakulam", "Kerala"),
    "cochin": ("Ernakulam", "Kerala"),
    "cochi": ("Ernakulam", "Kerala"),
    "kochi": ("Ernakulam", "Kerala"),
    "എറണാകുളം": ("Ernakulam", "Kerala"),
    "എറന്നാകുളം": ("Ernakulam", "Kerala"),

    # 4. Thrissur
    "thrissur": ("Thrissur", "Kerala"),
    "trissur": ("Thrissur", "Kerala"),
    "thirssur": ("Thrissur", "Kerala"),
    "thrissuur": ("Thrissur", "Kerala"),
    "thrissure": ("Thrissur", "Kerala"),
    "trichur": ("Thrissur", "Kerala"),
    "തൃശ്ശൂർ": ("Thrissur", "Kerala"),
    "തൃശൂർ": ("Thrissur", "Kerala"),

    # 5. Kannur
    "kannur": ("Kannur", "Kerala"),
    "cannanore": ("Kannur", "Kerala"),
    "കണ്ണൂർ": ("Kannur", "Kerala"),

    # 6. Palakkad
    "palakkad": ("Palakkad", "Kerala"),
    "palakad": ("Palakkad", "Kerala"),
    "paalakkad": ("Palakkad", "Kerala"),
    "plakkad": ("Palakkad", "Kerala"),
    "palghat": ("Palakkad", "Kerala"),
    "പാലക്കാട്": ("Palakkad", "Kerala"),

    # 7. Alappuzha
    "alappuzha": ("Alappuzha", "Kerala"),
    "alapuzha": ("Alappuzha", "Kerala"),
    "alleppey": ("Alappuzha", "Kerala"),
    "ആലപ്പുഴ": ("Alappuzha", "Kerala"),

    # 8. Kollam
    "kollam": ("Kollam", "Kerala"),
    "kollom": ("Kollam", "Kerala"),
    "quilon": ("Kollam", "Kerala"),
    "കൊല്ലം": ("Kollam", "Kerala"),

    # 9. Kottayam
    "kottayam": ("Kottayam", "Kerala"),
    "kottyam": ("Kottayam", "Kerala"),
    "കോട്ടയം": ("Kottayam", "Kerala"),

    # 10. Thiruvananthapuram
    "thiruvananthapuram": ("Thiruvananthapuram", "Kerala"),
    "trivandrum": ("Thiruvananthapuram", "Kerala"),
    "tvm": ("Thiruvananthapuram", "Kerala"),
    "tiruvanthapuram": ("Thiruvananthapuram", "Kerala"),
    "tiruvananthpuram": ("Thiruvananthapuram", "Kerala"),
    "thiruvanandhapuram": ("Thiruvananthapuram", "Kerala"),
    "thiruvunanthapuram": ("Thiruvananthapuram", "Kerala"),
    "തിരുവനന്തപുരം": ("Thiruvananthapuram", "Kerala"),

    # 11. Wayanad
    "wayanad": ("Wayanad", "Kerala"),
    "wayand": ("Wayanad", "Kerala"),
    "wynad": ("Wayanad", "Kerala"),
    "വയനാട്": ("Wayanad", "Kerala"),

    # 12. Kasaragod
    "kasaragod": ("Kasaragod", "Kerala"),
    "kasargod": ("Kasaragod", "Kerala"),
    "kasargood": ("Kasaragod", "Kerala"),
    "kasrgod": ("Kasaragod", "Kerala"),
    "kasarkod": ("Kasaragod", "Kerala"),
    "കാസർഗോഡ്": ("Kasaragod", "Kerala"),

    # 13. Idukki
    "idukki": ("Idukki", "Kerala"),
    "iduki": ("Idukki", "Kerala"),
    "ഇടുക്കി": ("Idukki", "Kerala"),

    # 14. Pathanamthitta
    "pathanamthitta": ("Pathanamthitta", "Kerala"),
    "pathanamtitta": ("Pathanamthitta", "Kerala"),
    "പത്തനംതിട്ട": ("Pathanamthitta", "Kerala"),

    # Other common neighboring regions / major cities
    "bengaluru": ("Bengaluru", "Karnataka"),
    "bangalore": ("Bengaluru", "Karnataka"),
    "bangalore rural": ("Bengaluru", "Karnataka"),
    "banglore": ("Bengaluru", "Karnataka"),
    "bangloore": ("Bengaluru", "Karnataka"),
    "chennai": ("Chennai", "Tamil Nadu"),
    "madras": ("Chennai", "Tamil Nadu"),
    "coimbatore": ("Coimbatore", "Tamil Nadu"),
    "mumbai": ("Mumbai", "Maharashtra"),
    "bombay": ("Mumbai", "Maharashtra"),
    "hyderabad": ("Hyderabad", "Telangana"),
    "kolkata": ("Kolkata", "West Bengal"),
    "calcutta": ("Kolkata", "West Bengal"),
    "new delhi": ("New Delhi", "Delhi"),
    "delhi": ("New Delhi", "Delhi"),
    "dakshina kannada": ("Dakshina Kannada", "Karnataka"),
    "mangalore": ("Dakshina Kannada", "Karnataka"),
    "mangaluru": ("Dakshina Kannada", "Karnataka"),
    "lakshadweep": ("Lakshadweep", "Lakshadweep"),
    "india lakshadweep": ("Lakshadweep", "Lakshadweep"),
    "salem": ("Salem", "Tamil Nadu"),
    "vellore": ("Vellore", "Tamil Nadu"),
    "nilgiris": ("Nilgiris", "Tamil Nadu"),
    "pune": ("Pune", "Maharashtra"),
    "jaipur": ("Jaipur", "Rajasthan"),
    "ahmedabad": ("Ahmedabad", "Gujarat"),
    "chandigarh": ("Chandigarh", "Chandigarh")
}

def clean_district_string(raw: Optional[str]) -> str:
    """
    Cleans punctuation, leading symbols, trailing commas/dots from district input.
    """
    if not raw:
        return ""
    s = str(raw).strip()
    # Strip leading/trailing punctuation like '-,:;./'
    s = re.sub(r"^[\s\-_,:;./\\|]+", "", s)
    s = re.sub(r"[\s\-_,:;./\\|]+$", "", s)
    return " ".join(s.split()).strip()

def normalize_district_name(raw_district: Optional[str], state_hint: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalizes a district name to its canonical display name and state.
    Returns (canonical_district, canonical_state) or (clean_display_text, state) if unknown.
    """
    if not raw_district:
        return None, state_hint

    cleaned = clean_district_string(raw_district)
    if not cleaned or cleaned.lower() in ["nan", "none", "null", "undefined", "unknown", "unassigned", "unassigned / unknown", "n/a", "unknown district"]:
        return None, state_hint

    key = canonical_key(cleaned)
    
    # 1. Direct exact map lookup
    if key in KERALA_DISTRICT_MAP:
        dist_name, dist_state = KERALA_DISTRICT_MAP[key]
        return dist_name, dist_state

    # 2. Check Malayalam direct string match
    cleaned_lower = cleaned.lower()
    if cleaned_lower in KERALA_DISTRICT_MAP:
        return KERALA_DISTRICT_MAP[cleaned_lower]

    # 3. Substring / compound district pattern (e.g. "Malappuram (Manjeri)", "Calicut vadakar", "Kozhikode, Feroke kallikkudam", "Palakkad, mannarkkad")
    for alias_key, (canonical_name, canonical_st) in KERALA_DISTRICT_MAP.items():
        # Word boundary or prefix match for key district aliases
        if len(alias_key) >= 4 and (alias_key in key or alias_key in cleaned_lower):
            # Check if it starts with alias or has alias as distinct token
            tokens = re.split(r"[\s,/\-()]+", key)
            if alias_key in tokens or any(t.startswith(alias_key) for t in tokens):
                return canonical_name, canonical_st

    # 4. Fallback: clean display text with Title Case
    return clean_display_text(cleaned, title_case=True), state_hint or "Kerala"
