import re
from typing import Optional, Dict, Tuple, List
from app.utils.text_normalization import canonical_key, clean_display_text

# Master list of 14 Kerala Districts for initial database seeding
OFFICIAL_KERALA_DISTRICTS: List[Tuple[str, str, str, List[str]]] = [
    # (canonical_name, state, normalized_key, aliases)
    (
        "Malappuram", "Kerala", "malappuram",
        ["malappuram", "malapuram", "malppuram", "mlp", "മലപ്പുറം", "മലപ്പുറം ജില്ല", "മലപ്പുറം ഡിസ്ട്രിക്ട്", "malappuram district", "malappuram dist", "malappuram jilla"]
    ),
    (
        "Kozhikode", "Kerala", "kozhikode",
        ["kozhikode", "calicut", "kozhikkode", "kozhikod", "kozhikkod", "kozhikide", "kozhikot", "kozikkode", "kozikkod", "kozohide", "കോഴിക്കോട്", "കാലിക്കറ്റ്", "കോഴിക്കോട് ജില്ല", "kozhikode district", "calicut district"]
    ),
    (
        "Ernakulam", "Kerala", "ernakulam",
        ["ernakulam", "eranakulam", "earnakulam", "enranakulam", "cochin", "cochi", "kochi", "എറണാകുളം", "എറന്നാകുളം", "കൊച്ചി", "എറണാകുളം ജില്ല", "ernakulam district", "cochin district"]
    ),
    (
        "Thrissur", "Kerala", "thrissur",
        ["thrissur", "trissur", "thirssur", "thrissuur", "thrissure", "trichur", "തൃശ്ശൂർ", "തൃശൂർ", "തൃശൂർ ജില്ല", "തൃശ്ശൂർ ജില്ല", "thrissur district", "trichur district"]
    ),
    (
        "Kannur", "Kerala", "kannur",
        ["kannur", "cannanore", "കണ്ണൂർ", "കണ്ണൂർ ജില്ല", "kannur district", "cannanore district"]
    ),
    (
        "Palakkad", "Kerala", "palakkad",
        ["palakkad", "palakad", "paalakkad", "plakkad", "palghat", "പാലക്കാട്", "പാലക്കാട് ജില്ല", "palakkad district", "palghat district"]
    ),
    (
        "Alappuzha", "Kerala", "alappuzha",
        ["alappuzha", "alapuzha", "alleppey", "ആലപ്പുഴ", "ആലപ്പുഴ ജില്ല", "alappuzha district", "alleppey district"]
    ),
    (
        "Kollam", "Kerala", "kollam",
        ["kollam", "kollom", "quilon", "കൊല്ലം", "കൊല്ലം ജില്ല", "kollam district", "quilon district"]
    ),
    (
        "Kottayam", "Kerala", "kottayam",
        ["kottayam", "kottyam", "കോട്ടയം", "കോട്ടയം ജില്ല", "kottayam district"]
    ),
    (
        "Thiruvananthapuram", "Kerala", "thiruvananthapuram",
        ["thiruvananthapuram", "trivandrum", "tvm", "tiruvanthapuram", "tiruvananthpuram", "thiruvanandhapuram", "thiruvunanthapuram", "തിരുവനന്തപുരം", "തിരുവനന്തപുരം ജില്ല", "thiruvananthapuram district", "trivandrum district"]
    ),
    (
        "Wayanad", "Kerala", "wayanad",
        ["wayanad", "wayand", "wynad", "വയനാട്", "വയനാട് ജില്ല", "wayanad district", "wynad district"]
    ),
    (
        "Kasaragod", "Kerala", "kasaragod",
        ["kasaragod", "kasargod", "kasargood", "kasrgod", "kasarkod", "കാസർഗോഡ്", "കാസർകോട്", "കാസർഗോഡ് ജില്ല", "കാസർകോട് ജില്ല", "kasaragod district", "kasargod district"]
    ),
    (
        "Idukki", "Kerala", "idukki",
        ["idukki", "iduki", "ഇടുക്കി", "ഇടുക്കി ജില്ല", "idukki district"]
    ),
    (
        "Pathanamthitta", "Kerala", "pathanamthitta",
        ["pathanamthitta", "pathanamtitta", "പത്തനംതിട്ട", "പത്തനംതിട്ട ജില്ല", "pathanamthitta district"]
    ),
]

# Major Indian Cities / Other Neighboring Districts
OTHER_MAJOR_DISTRICTS: List[Tuple[str, str, str, List[str]]] = [
    ("Bengaluru", "Karnataka", "bengaluru", ["bengaluru", "bangalore", "bangalore rural", "banglore", "bangloore", "ബെംഗളൂരു", "ബാംഗ്ലൂർ"]),
    ("Chennai", "Tamil Nadu", "chennai", ["chennai", "madras", "ചെന്നൈ"]),
    ("Coimbatore", "Tamil Nadu", "coimbatore", ["coimbatore", "കോയമ്പത്തൂർ"]),
    ("Mumbai", "Maharashtra", "mumbai", ["mumbai", "bombay", "മുംബൈ"]),
    ("Hyderabad", "Telangana", "hyderabad", ["hyderabad", "ഹൈദരാബാദ്"]),
    ("Kolkata", "West Bengal", "kolkata", ["kolkata", "calcutta", "കൊൽക്കത്ത"]),
    ("New Delhi", "Delhi", "new delhi", ["new delhi", "delhi", "ഡൽഹി"]),
    ("Dakshina Kannada", "Karnataka", "dakshina kannada", ["dakshina kannada", "mangalore", "mangaluru", "മംഗലാപുരം", "മംഗളൂരു"]),
    ("Lakshadweep", "Lakshadweep", "lakshadweep", ["lakshadweep", "india lakshadweep", "ലക്ഷദ്വീപ്"]),
    ("Salem", "Tamil Nadu", "salem", ["salem"]),
    ("Vellore", "Tamil Nadu", "vellore", ["vellore"]),
    ("Nilgiris", "Tamil Nadu", "nilgiris", ["nilgiris", "ooty"]),
    ("Pune", "Maharashtra", "pune", ["pune"]),
    ("Jaipur", "Rajasthan", "jaipur", ["jaipur"]),
    ("Ahmedabad", "Gujarat", "ahmedabad", ["ahmedabad"]),
    ("Chandigarh", "Chandigarh", "chandigarh", ["chandigarh"]),
]

# Build lookup dictionary mapping every alias, variation, and Malayalam text to (canonical_name, state, normalized_key)
DISTRICT_LOOKUP_MAP: Dict[str, Tuple[str, str, str]] = {}

for canonical_name, state, norm_key, aliases in (OFFICIAL_KERALA_DISTRICTS + OTHER_MAJOR_DISTRICTS):
    # Map normalized key itself
    DISTRICT_LOOKUP_MAP[norm_key] = (canonical_name, state, norm_key)
    DISTRICT_LOOKUP_MAP[canonical_name.lower()] = (canonical_name, state, norm_key)
    for alias in aliases:
        a_clean = str(alias).strip()
        if a_clean:
            DISTRICT_LOOKUP_MAP[a_clean] = (canonical_name, state, norm_key)
            DISTRICT_LOOKUP_MAP[a_clean.lower()] = (canonical_name, state, norm_key)
            a_key = canonical_key(a_clean)
            if a_key:
                DISTRICT_LOOKUP_MAP[a_key] = (canonical_name, state, norm_key)

def clean_district_string(raw: Optional[str]) -> str:
    """
    Cleans punctuation, symbols, and standardizes spacing.
    """
    if not raw:
        return ""
    s = str(raw).strip()
    # Strip leading/trailing punctuation like '-,:;./'
    s = re.sub(r"^[\s\-_,:;./\\|]+", "", s)
    s = re.sub(r"[\s\-_,:;./\\|]+$", "", s)
    return " ".join(s.split()).strip()

def strip_district_suffixes(raw: str) -> str:
    """
    Strips generic words like 'district', 'dist', 'jilla', 'ജില്ല' from district text.
    """
    s = raw.strip()
    # English suffixes
    s = re.sub(r"(?i)\b(district|dist|jilla|dt|d\.t)\b", "", s)
    # Malayalam suffixes
    s = re.sub(r"(ജില്ല|ഡിസ്ട്രിക്ട്)", "", s)
    return " ".join(s.split()).strip()

def normalize_district_name(raw_district: Optional[str], state_hint: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalizes a district name to its canonical display name and state.
    Returns (canonical_district, canonical_state) or (clean_display_text, state) if unknown.
    """
    if not raw_district:
        return None, state_hint

    cleaned = clean_district_string(raw_district)
    if not cleaned or cleaned.lower() in [
        "nan", "none", "null", "undefined", "unknown", "unassigned",
        "unassigned / unknown", "n/a", "unknown district", "0", "-"
    ]:
        return None, state_hint

    # 1. Exact lookup with raw string & lowercase
    if cleaned in DISTRICT_LOOKUP_MAP:
        name, st, _ = DISTRICT_LOOKUP_MAP[cleaned]
        return name, st

    cleaned_lower = cleaned.lower()
    if cleaned_lower in DISTRICT_LOOKUP_MAP:
        name, st, _ = DISTRICT_LOOKUP_MAP[cleaned_lower]
        return name, st

    # 2. Key-based lookup after canonical normalization
    key = canonical_key(cleaned)
    if key in DISTRICT_LOOKUP_MAP:
        name, st, _ = DISTRICT_LOOKUP_MAP[key]
        return name, st

    # 3. Strip district suffixes (e.g. 'Malappuram District' -> 'Malappuram', 'മലപ്പുറം ജില്ല' -> 'മലപ്പുറം')
    stripped = strip_district_suffixes(cleaned)
    if stripped:
        if stripped in DISTRICT_LOOKUP_MAP:
            name, st, _ = DISTRICT_LOOKUP_MAP[stripped]
            return name, st
        stripped_lower = stripped.lower()
        if stripped_lower in DISTRICT_LOOKUP_MAP:
            name, st, _ = DISTRICT_LOOKUP_MAP[stripped_lower]
            return name, st
        stripped_key = canonical_key(stripped)
        if stripped_key in DISTRICT_LOOKUP_MAP:
            name, st, _ = DISTRICT_LOOKUP_MAP[stripped_key]
            return name, st

    # 4. Token / Substring matching for compound district names (e.g. "Malappuram (Manjeri)", "Calicut vadakara", "Kozhikode, Feroke")
    for alias_key, (canonical_name, canonical_st, _) in DISTRICT_LOOKUP_MAP.items():
        if len(alias_key) >= 4 and (alias_key in key or alias_key in cleaned_lower):
            tokens = re.split(r"[\s,/\-()]+", key)
            if alias_key in tokens or any(t.startswith(alias_key) for t in tokens):
                return canonical_name, canonical_st

    # 5. Fallback: clean title-cased display text
    return clean_display_text(stripped or cleaned, title_case=True), state_hint or "Kerala"

def get_normalized_district_key(raw_district: Optional[str]) -> Optional[str]:
    """
    Returns the normalized key for comparison / DB unique lookup (e.g. 'malappuram'), or None if unknown.
    """
    canonical_name, _ = normalize_district_name(raw_district)
    if not canonical_name:
        return None
    return canonical_key(canonical_name)
