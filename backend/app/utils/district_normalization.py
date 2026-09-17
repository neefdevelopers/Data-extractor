import re
import unicodedata
from typing import Optional, Dict, Tuple, List, Set
from app.utils.text_normalization import canonical_key, clean_display_text

# ==============================================================================
# CANONICAL 14 KERALA DISTRICT MASTER LIST & CONTROLLED ALIASES
# ==============================================================================
# Exactly these 14 canonical Kerala districts:
# 1. Alappuzha
# 2. Ernakulam
# 3. Idukki
# 4. Kannur
# 5. Kasaragod
# 6. Kollam
# 7. Kottayam
# 8. Kozhikode
# 9. Malappuram
# 10. Palakkad
# 11. Pathanamthitta
# 12. Thiruvananthapuram
# 13. Thrissur
# 14. Wayanad

KERALA_14_DISTRICTS: List[Tuple[str, str, str, List[str], List[str]]] = [
    # (canonical_name, state, normalized_key, english_aliases, malayalam_aliases)
    (
        "Alappuzha", "Kerala", "alappuzha",
        [
            "alappuzha", "alapuzha", "alleppey", "alleppy", "alappi",
            "alappuzha district", "alleppey district", "alappuzha dist", "alleppey dist",
            "alappuzha dt", "alleppey dt", "alappuzha jilla"
        ],
        ["ആലപ്പുഴ", "ആലപ്പുഴ ജില്ല", "ആലപ്പുഴ ഡിസ്ട്രിക്ട്", "ആലപ്പുഴ ജില"]
    ),
    (
        "Ernakulam", "Kerala", "ernakulam",
        [
            "ernakulam", "eranakulam", "earnakulam", "enranakulam", "ernakilam", "ernakulum",
            "cochin", "cochi", "kochi", "ernakulam district", "cochin district",
            "kochi district", "ernakulam dist", "cochin dist", "kochi dist",
            "ernakulam dt", "ernakulam jilla"
        ],
        ["എറണാകുളം", "എറന്നാകുളം", "കൊച്ചി", "എറണാകുളം ജില്ല", "കൊച്ചി ജില്ല", "എറണാകുളം ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Idukki", "Kerala", "idukki",
        [
            "idukki", "iduki", "idukki district", "idukki dist", "idukki dt", "idukki jilla"
        ],
        ["ഇടുക്കി", "ഇടുക്കി ജില്ല", "ഇടുക്കി ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Kannur", "Kerala", "kannur",
        [
            "kannur", "cannanore", "cananore", "kannur district", "cannanore district",
            "kannur dist", "cannanore dist", "kannur dt", "kannur jilla"
        ],
        ["കണ്ണൂർ", "കണ്ണൂർ ജില്ല", "കണ്ണൂർ ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Kasaragod", "Kerala", "kasaragod",
        [
            "kasaragod", "kasargod", "kasargood", "kasrgod", "kasarkod", "kasargode",
            "kasaragod district", "kasargod district", "kasaragod dist", "kasargod dist",
            "kasaragod dt", "kasaragod jilla"
        ],
        ["കാസർഗോഡ്", "കാസർകോട്", "കാസറഗോഡ്", "കാസറകോട്", "കാസർഗോഡ് ജില്ല", "കാസർകോട് ജില്ല", "കാസർഗോഡ് ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Kollam", "Kerala", "kollam",
        [
            "kollam", "kollom", "quilon", "quilon district", "kollam district",
            "kollam dist", "quilon dist", "kollam dt", "kollam jilla"
        ],
        ["കൊല്ലം", "കൊല്ലം ജില്ല", "കൊല്ലം ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Kottayam", "Kerala", "kottayam",
        [
            "kottayam", "kottyam", "kottayam district", "kottayam dist",
            "kottayam dt", "kottayam jilla"
        ],
        ["കോട്ടയം", "കോട്ടയം ജില്ല", "കോട്ടയം ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Kozhikode", "Kerala", "kozhikode",
        [
            "kozhikode", "calicut", "kozhikkode", "kozhikod", "kozhikkod", "kozhikide",
            "kozhikot", "kozikkode", "kozikkod", "kozohide", "kozhikode district",
            "calicut district", "kozhikode dist", "calicut dist", "kozhikode dt",
            "calicut dt", "kozhikode jilla"
        ],
        ["കോഴിക്കോട്", "കാലിക്കറ്റ്", "കോഴിക്കോട് ജില്ല", "കാലിക്കറ്റ് ജില്ല", "കോഴിക്കോട് ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Malappuram", "Kerala", "malappuram",
        [
            "malappuram", "malapuram", "malppuram", "mlp", "malappuram district",
            "malappuram dist", "malappuram jilla", "malapuram dist", "malappuram dt",
            "malapuram dt"
        ],
        ["മലപ്പുറം", "മലപ്പുറം ജില്ല", "മലപ്പുറം ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Palakkad", "Kerala", "palakkad",
        [
            "palakkad", "palakad", "paalakkad", "plakkad", "palghat", "palghat district",
            "palakkad district", "palakkad dist", "palghat dist", "palakkad dt", "palakkad jilla"
        ],
        ["പാലക്കാട്", "പാലക്കാട് ജില്ല", "പാലക്കാട് ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Pathanamthitta", "Kerala", "pathanamthitta",
        [
            "pathanamthitta", "pathanamtitta", "pathanthitta", "pathanamthitta district",
            "pathanamthitta dist", "pathanamthitta dt", "pathanamthitta jilla"
        ],
        ["പത്തനംതിട്ട", "പത്തനംതിട്ട ജില്ല", "പത്തനംതിട്ട ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Thiruvananthapuram", "Kerala", "thiruvananthapuram",
        [
            "thiruvananthapuram", "trivandrum", "tvm", "tiruvanthapuram", "tiruvananthpuram", "tiruvanthpuram",
            "thiruvanandhapuram", "thiruvunanthapuram", "thiruvananthapuram district",
            "trivandrum district", "trivandrum dist", "tvm district", "thiruvananthapuram dt",
            "trivandrum dt", "thiruvananthapuram jilla"
        ],
        ["തിരുവനന്തപുരം", "തിരുവനന്തപുരം ജില്ല", "തിരുവനന്തപുരം ഡിസ്ട്രിക്ട്", "ട്രിവാൻഡ്രം"]
    ),
    (
        "Thrissur", "Kerala", "thrissur",
        [
            "thrissur", "trissur", "thirssur", "thrissuur", "thrissure", "trichur",
            "trichur district", "thrissur district", "thrissur dist", "trichur dist",
            "thrissur dt", "thrissur jilla"
        ],
        ["തൃശ്ശൂർ", "തൃശൂർ", "തൃശൂർ ജില്ല", "തൃശ്ശൂർ ജില്ല", "തൃശ്ശൂർ ഡിസ്ട്രിക്ട്"]
    ),
    (
        "Wayanad", "Kerala", "wayanad",
        [
            "wayanad", "wayand", "wynad", "wayanadu", "wayanad district",
            "wynad district", "wayanad dist", "wynad dist", "wayanad dt", "wayanad jilla"
        ],
        ["വയനാട്", "വയനാട് ജില്ല", "വയനാട് ഡിസ്ട്രിക്ട്"]
    ),
]

# Backward compatibility alias for seeding
OFFICIAL_KERALA_DISTRICTS: List[Tuple[str, str, str, List[str]]] = [
    (canonical, state, norm_key, eng_aliases + mal_aliases)
    for canonical, state, norm_key, eng_aliases, mal_aliases in KERALA_14_DISTRICTS
]

OTHER_MAJOR_DISTRICTS: List[Tuple[str, str, str, List[str]]] = []

# Centralized lookup table for direct canonical matching
# Key -> (canonical_name, state, norm_key, resolution_source)
KERALA_LOOKUP_MAP: Dict[str, Tuple[str, str, str, str]] = {}
MALAYALAM_LOOKUP_MAP: Dict[str, Tuple[str, str, str, str]] = {}

for canonical_name, state, norm_key, eng_aliases, mal_aliases in KERALA_14_DISTRICTS:
    entry_direct = (canonical_name, state, norm_key, "DIRECT_MATCH")
    entry_malayalam = (canonical_name, state, norm_key, "MALAYALAM_ALIAS")

    # Canonical name itself
    KERALA_LOOKUP_MAP[canonical_name] = entry_direct
    KERALA_LOOKUP_MAP[canonical_name.lower()] = entry_direct
    KERALA_LOOKUP_MAP[norm_key] = entry_direct

    for alias in eng_aliases:
        a_clean = unicodedata.normalize("NFKC", str(alias).strip())
        if a_clean:
            KERALA_LOOKUP_MAP[a_clean] = entry_direct
            KERALA_LOOKUP_MAP[a_clean.lower()] = entry_direct
            a_key = canonical_key(a_clean)
            if a_key:
                KERALA_LOOKUP_MAP[a_key] = entry_direct

    for m_alias in mal_aliases:
        m_clean = unicodedata.normalize("NFKC", str(m_alias).strip())
        if m_clean:
            MALAYALAM_LOOKUP_MAP[m_clean] = entry_malayalam
            KERALA_LOOKUP_MAP[m_clean] = entry_malayalam
            m_key = canonical_key(m_clean)
            if m_key:
                MALAYALAM_LOOKUP_MAP[m_key] = entry_malayalam
                KERALA_LOOKUP_MAP[m_key] = entry_malayalam

# General DISTRICT_LOOKUP_MAP pointing to canonical entries
DISTRICT_LOOKUP_MAP: Dict[str, Tuple[str, str, str]] = {
    k: (v[0], v[1], v[2]) for k, v in KERALA_LOOKUP_MAP.items()
}

# 14 Canonical District Names as a fixed set for O(1) membership check
CANONICAL_14_NAMES: Set[str] = {c[0] for c in KERALA_14_DISTRICTS}


def clean_district_string(raw: Optional[str]) -> str:
    """
    Cleans punctuation, symbols, normalizes unicode, and standardizes spacing.
    """
    if not raw:
        return ""
    s = unicodedata.normalize("NFKC", str(raw).strip())
    # Strip leading/trailing punctuation like '-,:;./'
    s = re.sub(r"^[\s\-_,:;./\\|]+", "", s)
    s = re.sub(r"[\s\-_,:;./\\|]+$", "", s)
    return " ".join(s.split()).strip()


def strip_district_suffixes(raw: str) -> str:
    """
    Strips harmless words like 'district', 'dist', 'jilla', 'ജില്ല' from district text.
    """
    s = unicodedata.normalize("NFKC", raw.strip())
    # English suffixes
    s = re.sub(r"(?i)\b(district|dist|jilla|dt|d\.t)\b", "", s)
    # Malayalam suffixes
    s = re.sub(r"(ജില്ല|ഡിസ്ട്രിക്ട്|ജില)", "", s)
    return " ".join(s.split()).strip()


def match_kerala_canonical_district(raw_district: Optional[str]) -> Optional[Tuple[str, str, str, str]]:
    """
    Attempts to match raw_district directly against the 14 Kerala canonical master records & aliases.
    
    Returns:
        (canonical_name, state, normalized_key, resolution_source)
        e.g. ("Malappuram", "Kerala", "malappuram", "DIRECT_MATCH" or "MALAYALAM_ALIAS")
        OR None if not reliably matched.
    """
    if not raw_district:
        return None

    cleaned = clean_district_string(raw_district)
    if not cleaned or cleaned.lower() in [
        "nan", "none", "null", "undefined", "unknown", "unassigned",
        "unassigned / unknown", "n/a", "unknown district", "0", "-", "nil"
    ]:
        return None

    # Check Malayalam specific map first for exact Malayalam inputs
    if cleaned in MALAYALAM_LOOKUP_MAP:
        return MALAYALAM_LOOKUP_MAP[cleaned]

    # 1. Exact lookup with raw cleaned string & lowercase
    if cleaned in KERALA_LOOKUP_MAP:
        return KERALA_LOOKUP_MAP[cleaned]

    cleaned_lower = cleaned.lower()
    if cleaned_lower in KERALA_LOOKUP_MAP:
        return KERALA_LOOKUP_MAP[cleaned_lower]

    # 2. Key-based lookup after canonical normalization
    key = canonical_key(cleaned)
    if key in KERALA_LOOKUP_MAP:
        return KERALA_LOOKUP_MAP[key]

    # 3. Strip district suffixes (e.g. 'Malappuram District' -> 'Malappuram', 'മലപ്പുറം ജില്ല' -> 'മലപ്പുറം')
    stripped = strip_district_suffixes(cleaned)
    if stripped and stripped != cleaned:
        if stripped in MALAYALAM_LOOKUP_MAP:
            return MALAYALAM_LOOKUP_MAP[stripped]
        if stripped in KERALA_LOOKUP_MAP:
            return KERALA_LOOKUP_MAP[stripped]
        stripped_lower = stripped.lower()
        if stripped_lower in KERALA_LOOKUP_MAP:
            return KERALA_LOOKUP_MAP[stripped_lower]
        stripped_key = canonical_key(stripped)
        if stripped_key in KERALA_LOOKUP_MAP:
            return KERALA_LOOKUP_MAP[stripped_key]

    # 4. Token / Substring matching for compound district strings (e.g. "Malappuram (Manjeri)", "Kozhikode, Feroke")
    for alias_key, val in KERALA_LOOKUP_MAP.items():
        if len(alias_key) >= 4 and (alias_key in key or alias_key in cleaned_lower):
            tokens = re.split(r"[\s,/\-()]+", key)
            if alias_key in tokens or any(t.startswith(alias_key) for t in tokens):
                return val

    return None


def normalize_district_name(raw_district: Optional[str], state_hint: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalizes a district name to its canonical Kerala display name and state.
    Returns (canonical_district, canonical_state) or (None, state_hint) if unresolved.
    """
    if not raw_district:
        return None, state_hint

    matched = match_kerala_canonical_district(raw_district)
    if matched:
        return matched[0], matched[1]

    # If not a recognized Kerala canonical district or alias, return None
    return None, state_hint


def get_normalized_district_key(raw_district: Optional[str]) -> Optional[str]:
    """
    Returns the normalized key for comparison / DB unique lookup (e.g. 'malappuram'), or None if unknown.
    """
    matched = match_kerala_canonical_district(raw_district)
    if matched:
        return matched[2]
    return None
