import re
import json
import logging
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Set, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.district import DistrictMaster
from app.models.customer import Customer
from app.models.data_quality import DataQualityIssue
from app.models.postal import PostalMaster, PostalOffice
from app.utils.district_normalization import (
    KERALA_14_DISTRICTS,
    match_kerala_canonical_district,
    normalize_district_name,
    get_normalized_district_key,
    clean_district_string,
    strip_district_suffixes,
)
from app.utils.text_normalization import canonical_key, clean_display_text, ci_equals
from app.utils.cleaning import normalize_pincode

logger = logging.getLogger(__name__)


# Standard India Post Kerala PIN Code 3-digit & 4-digit prefix mapping tables
KERALA_PINCODE_PREFIXES: Dict[str, str] = {
    "670": "Kannur",
    "671": "Kasaragod",
    "673": "Kozhikode",
    "676": "Malappuram",
    "678": "Palakkad",
    "680": "Thrissur",
    "682": "Ernakulam",
    "683": "Ernakulam",
    "685": "Idukki",
    "686": "Kottayam",
    "688": "Alappuzha",
    "689": "Pathanamthitta",
    "690": "Alappuzha",
    "691": "Kollam",
    "695": "Thiruvananthapuram"
}

KERALA_PINCODE_4DIGIT_PREFIXES: Dict[str, str] = {
    "6793": "Malappuram",
    "6795": "Malappuram",
    "6797": "Malappuram",
    "6791": "Palakkad",
    "6792": "Palakkad",
    "6796": "Palakkad",
    "6731": "Kozhikode",
    "6733": "Kozhikode",
    "6735": "Kozhikode",
    "6736": "Kozhikode",
    "6737": "Wayanad",
    "6707": "Wayanad",
    "6831": "Ernakulam",
    "6835": "Ernakulam",
    "6800": "Thrissur",
    "6806": "Thrissur",
    "6805": "Thrissur",
    "6905": "Alappuzha",
    "6915": "Kollam"
}

KNOWN_KERALA_PLACES: Dict[str, str] = {
    "manjeri": "Malappuram", "perinthalmanna": "Malappuram", "tirur": "Malappuram",
    "malappuram": "Malappuram", "kondotty": "Malappuram", "nilambur": "Malappuram",
    "kottakkal": "Malappuram", "ponnani": "Malappuram", "kuttippuram": "Malappuram",
    "valanchery": "Malappuram", "edappal": "Malappuram", "ayikarapadi": "Malappuram",
    "payyanad": "Malappuram", "pulamanthole": "Malappuram", "kannamangalam": "Malappuram",
    "pukottoor": "Malappuram", "pookkottur": "Malappuram", "pookottoor": "Malappuram",
    "vazhayoor": "Malappuram", "vazhayur": "Malappuram", "vazhakkad": "Malappuram",
    "calicut": "Kozhikode", "kozhikode": "Kozhikode", "vadakara": "Kozhikode",
    "koyilandy": "Kozhikode", "feroke": "Kozhikode", "atholi": "Kozhikode",
    "kallunira": "Kozhikode", "ulliyeri": "Kozhikode", "balussery": "Kozhikode",
    "thamarassery": "Kozhikode", "koduvally": "Kozhikode", "mukkam": "Kozhikode",
    "malaparamba": "Kozhikode", "malaparamub": "Kozhikode", "naduvattam": "Kozhikode", "kappad": "Kozhikode",
    "ramanattukara": "Kozhikode", "vaidyarangadi": "Kozhikode",
    "kochi": "Ernakulam", "cochin": "Ernakulam", "ernakulam": "Ernakulam",
    "aluva": "Ernakulam", "perumbavoor": "Ernakulam", "angamaly": "Ernakulam",
    "kakkanad": "Ernakulam", "edappally": "Ernakulam", "tripunithura": "Ernakulam",
    "iringole": "Ernakulam", "kaloor": "Ernakulam", "palatt": "Ernakulam",
    "moovatupuzha": "Ernakulam", "muvattupuzha": "Ernakulam", "kizhakkekara": "Ernakulam", "kothamangalam": "Ernakulam",
    "thrissur": "Thrissur", "trichur": "Thrissur", "guruvayur": "Thrissur",
    "chalakudy": "Thrissur", "kodungallur": "Thrissur", "ollur": "Thrissur",
    "kunnamkulam": "Thrissur", "cheruthuruthy": "Thrissur", "marathakkara": "Thrissur",
    "trikkur": "Thrissur", "wadakkanchery": "Thrissur", "irinjalakuda": "Thrissur", "chengaloor": "Thrissur",
    "trivandrum": "Thiruvananthapuram", "thiruvananthapuram": "Thiruvananthapuram",
    "karamana": "Thiruvananthapuram", "kazhakkoottam": "Thiruvananthapuram",
    "neyyattinkara": "Thiruvananthapuram", "attingal": "Thiruvananthapuram", "varkala": "Thiruvananthapuram",
    "vallakkadavoo": "Thiruvananthapuram", "vallakkadavu": "Thiruvananthapuram", "tiruvanthpuram": "Thiruvananthapuram",
    "kollam": "Kollam", "quilon": "Kollam", "kottarakkara": "Kollam", "punalur": "Kollam",
    "karunagappally": "Kollam", "paravur": "Kollam", "chathannoor": "Kollam",
    "alappuzha": "Alappuzha", "alleppey": "Alappuzha", "kayamkulam": "Alappuzha",
    "mavelikkara": "Alappuzha", "cherthala": "Alappuzha", "haripad": "Alappuzha",
    "chingoli": "Alappuzha", "krishnapuram": "Alappuzha", "kappil": "Alappuzha", "nooranad": "Alappuzha",
    "kottayam": "Kottayam", "changanassery": "Kottayam", "pala": "Kottayam",
    "ettumanoor": "Kottayam", "kanjirappally": "Kottayam", "vaikom": "Kottayam",
    "muttappally": "Kottayam", "mukkoottuthara": "Kottayam",
    "palakkad": "Palakkad", "palghat": "Palakkad", "ottapalam": "Palakkad",
    "shoranur": "Palakkad", "chittur": "Palakkad", "mannarkkad": "Palakkad", "pattambi": "Palakkad",
    "kannur": "Kannur", "cannannore": "Kannur", "thalassery": "Kannur",
    "payyanur": "Kannur", "taliparamba": "Kannur", "mattannur": "Kannur", "koothuparamba": "Kannur",
    "karikkottakary": "Kannur", "കരിക്കോട്ടക്കരി": "Kannur", "koomanthode": "Kannur",
    "kasaragod": "Kasaragod", "kanhangad": "Kasaragod", "trikaripur": "Kasaragod",
    "nileshwar": "Kasaragod", "manjeshwar": "Kasaragod", "elambachi": "Kasaragod",
    "wayanad": "Wayanad", "kalpetta": "Wayanad", "sulthan bathery": "Wayanad", "mananthavady": "Wayanad",
    "idukki": "Idukki", "thodupuzha": "Idukki", "munnar": "Idukki", "kattappana": "Idukki", "vengalloor": "Idukki",
    "pathanamthitta": "Pathanamthitta", "thiruvalla": "Pathanamthitta", "adoor": "Pathanamthitta", "ranni": "Pathanamthitta",
    "chathenthara": "Pathanamthitta", "thulappally": "Pathanamthitta", "pallickal": "Pathanamthitta"
}

@dataclass
class DistrictResolutionResult:
    district_id: Optional[int] = None
    canonical_name: Optional[str] = None
    state: Optional[str] = None
    resolution_source: str = "UNRESOLVED"  # PINCODE, DISTRICT_DIRECT_MATCH, DISTRICT_ALIAS, DISTRICT_FALLBACK, MANUAL_CONFIRMATION, UNRESOLVED
    district_status: str = "UNRESOLVED"    # RESOLVED, NEEDS_CONFIRMATION, UNRESOLVED
    source_district: Optional[str] = None
    district_mismatch: bool = False
    mismatch_message: Optional[str] = None
    post_offices: List[Dict[str, Any]] = field(default_factory=list)
    unresolved_reason: Optional[str] = None

    @property
    def is_resolved(self) -> bool:
        return bool(self.district_id is not None or self.canonical_name is not None)


class DistrictResolutionService:
    """
    Centralized District Resolution Service for Kerala Districts.
    Enforces Pincode-First priority verification and canonical 14 Kerala master resolution.
    
    Resolution Priority:
    1. Valid Pincode available: Lookup India Post / Postal cache -> Post Office result(s) -> District from postal data -> Match against 14 Kerala master -> Canonical District (Source: PINCODE).
       If postal API has no record but Pincode matches standard Kerala prefix range, resolves from canonical prefix table.
       Detects and flags any mismatch with supplied Excel district.
    2. No valid Pincode or Postal lookup unresolved: Supplied District / Post Office / Address text -> Normalize -> Match against 14 Kerala master / aliases -> Canonical District.
    3. Unresolved fallback: Cannot resolve -> Unknown Location Data (Source: UNRESOLVED).
    """

    @classmethod
    def resolve_district(
        cls,
        raw_district: Optional[str],
        pincode: Optional[str] = None,
        source_post_office: Optional[str] = None,
        address_hint: Optional[str] = None,
        state_hint: Optional[str] = None,
        db: Optional[Session] = None,
        allow_postal_lookup: bool = True
    ) -> DistrictResolutionResult:
        """
        Executes the exact Pincode-First district resolution priority flow.
        """
        clean_pin, pin_valid = normalize_pincode(pincode) if pincode else (None, False)

        # If pincode was not directly provided, check if a 6-digit PIN exists inside address_hint
        if (not clean_pin or not pin_valid) and address_hint:
            match_pin = re.search(r'\b([1-9][0-9]{5})\b', str(address_hint))
            if match_pin:
                e_pin, e_valid = normalize_pincode(match_pin.group(1))
                if e_valid:
                    clean_pin, pin_valid = e_pin, e_valid

        # ----------------------------------------------------------------------
        # STEP 1: Pincode-First Resolution (Valid 6-digit Pincode available)
        # ----------------------------------------------------------------------
        if clean_pin and pin_valid:
            from app.services.postal_service import PostalService

            # 1A. Check local database cache first
            postal_info = None
            if db is not None:
                postal_info = db.query(PostalMaster).filter(PostalMaster.pincode == clean_pin).first()

            # 1B. If not in DB cache, check Kerala prefix tables before making network calls
            if not postal_info:
                prefix4 = clean_pin[:4]
                prefix3 = clean_pin[:3]
                inferred_kerala_district = KERALA_PINCODE_4DIGIT_PREFIXES.get(prefix4) or KERALA_PINCODE_PREFIXES.get(prefix3)

                if inferred_kerala_district:
                    m = match_kerala_canonical_district(inferred_kerala_district)
                    if m:
                        canonical_name, canonical_state, norm_key = m[0], m[1], m[2]
                        master_entry = cls._get_or_create_master_entry(canonical_name, canonical_state, norm_key, db)
                        
                        # Cache to PostalMaster so subsequent lookups are immediate
                        if db is not None:
                            try:
                                new_pm = PostalMaster(
                                    pincode=clean_pin,
                                    district=canonical_name,
                                    state=canonical_state or "Kerala",
                                    country="India"
                                )
                                db.add(new_pm)
                                db.flush()
                                postal_info = new_pm
                            except Exception:
                                pass

                        district_mismatch = False
                        mismatch_msg = None
                        if raw_district and str(raw_district).strip():
                            raw_matched = match_kerala_canonical_district(raw_district)
                            if not raw_matched or raw_matched[0] != canonical_name:
                                district_mismatch = True
                                mismatch_msg = f"Uploaded district '{raw_district}' does not match the district '{canonical_name}' associated with Pincode {clean_pin}"

                        return DistrictResolutionResult(
                            district_id=master_entry.id if master_entry else None,
                            canonical_name=canonical_name,
                            state=canonical_state or "Kerala",
                            resolution_source="PINCODE",
                            district_status="RESOLVED",
                            source_district=raw_district,
                            district_mismatch=district_mismatch,
                            mismatch_message=mismatch_msg
                        )

            # 1C. If still not found and postal lookup is allowed, query external API
            if not postal_info and allow_postal_lookup and db is not None:
                postal_info = PostalService.get_or_enrich_pincode(
                    clean_pin, db=db, client_district=raw_district, client_po=source_post_office, auto_commit=False
                )

            if postal_info:
                # Gather candidate district strings from master and post offices
                candidate_districts: List[str] = []
                po_list: List[Dict[str, Any]] = []

                # If source post office is supplied, check if an office matches specifically
                matched_po_district: Optional[str] = None
                clean_source_po = canonical_key(source_post_office) if source_post_office else None

                for off in (postal_info.offices or []):
                    po_list.append({
                        "office_name": off.office_name,
                        "office_type": off.office_type,
                        "delivery_status": off.delivery_status,
                        "district": off.district,
                        "state": off.state
                    })
                    if off.district:
                        candidate_districts.append(off.district)
                    if clean_source_po and off.office_name and canonical_key(off.office_name) == clean_source_po:
                        matched_po_district = off.district

                if postal_info.district and not candidate_districts:
                    candidate_districts.append(postal_info.district)

                # If a specific post office matched, prioritize its district
                if matched_po_district:
                    candidate_districts = [matched_po_district]

                # Resolve all candidate districts to canonical Kerala districts
                resolved_districts: Set[Tuple[str, str, str]] = set()
                for c_dist in candidate_districts:
                    m = match_kerala_canonical_district(c_dist)
                    if m:
                        resolved_districts.add((m[0], m[1], m[2]))

                # If all post offices map to exactly one canonical Kerala district
                if len(resolved_districts) == 1:
                    canonical_name, canonical_state, norm_key = list(resolved_districts)[0]
                    master_entry = cls._get_or_create_master_entry(canonical_name, canonical_state, norm_key, db)
                    
                    # Detect mismatch with supplied Excel district
                    district_mismatch = False
                    mismatch_msg = None
                    if raw_district and str(raw_district).strip():
                        raw_matched = match_kerala_canonical_district(raw_district)
                        if not raw_matched or raw_matched[0] != canonical_name:
                            district_mismatch = True
                            mismatch_msg = f"Uploaded district '{raw_district}' does not match the district '{canonical_name}' associated with Pincode {clean_pin}"

                    return DistrictResolutionResult(
                        district_id=master_entry.id if master_entry else None,
                        canonical_name=canonical_name,
                        state=canonical_state or "Kerala",
                        resolution_source="PINCODE",
                        district_status="RESOLVED",
                        source_district=raw_district,
                        district_mismatch=district_mismatch,
                        mismatch_message=mismatch_msg,
                        post_offices=po_list
                    )
                elif len(resolved_districts) > 1:
                    # Multi-district boundary PIN code (e.g. 673633 Kozhikode/Malappuram, 686510 Kottayam/Pathanamthitta)
                    # 1. Try to disambiguate by checking if source_post_office matches any office or known place under this PIN
                    selected_candidate: Optional[Tuple[str, str, str]] = None
                    if clean_source_po:
                        po_place_dist = KNOWN_KERALA_PLACES.get(clean_source_po) or KNOWN_KERALA_PLACES.get(clean_source_po.replace("oo", "u"))
                        if po_place_dist:
                            m_po = match_kerala_canonical_district(po_place_dist)
                            if m_po:
                                for d_cand in resolved_districts:
                                    if d_cand[0] == m_po[0]:
                                        selected_candidate = d_cand
                                        break

                        if not selected_candidate:
                            for off in (postal_info.offices or []):
                                if off.office_name:
                                    off_key = canonical_key(off.office_name)
                                    if (off_key in clean_source_po or clean_source_po in off_key or 
                                        off_key.replace("oo", "u") == clean_source_po.replace("oo", "u")):
                                        m_off = match_kerala_canonical_district(off.district)
                                        if m_off:
                                            selected_candidate = (m_off[0], m_off[1], m_off[2])
                                            break

                    # 2. Try to disambiguate by checking address_hint tokens against post office names
                    if not selected_candidate and address_hint:
                        addr_str = str(address_hint).lower()
                        for off in (postal_info.offices or []):
                            off_name_clean = canonical_key(off.office_name) if off.office_name else ""
                            off_words = re.split(r'[\s,.\-\(\)]+', off_name_clean)
                            for w in off_words:
                                if w and len(w) >= 4 and w in addr_str:
                                    m_off = match_kerala_canonical_district(off.district)
                                    if m_off:
                                        selected_candidate = (m_off[0], m_off[1], m_off[2])
                                        break
                            if selected_candidate:
                                break

                    # 3. Try to disambiguate using supplied raw_district if it matches one of candidate districts
                    if not selected_candidate and raw_district and str(raw_district).strip():
                        raw_matched = match_kerala_canonical_district(raw_district)
                        if raw_matched:
                            for d_cand in resolved_districts:
                                if d_cand[0] == raw_matched[0]:
                                    selected_candidate = d_cand
                                    break

                    # 4. Try to disambiguate using Sub Post Office (SO) or Head Post Office (HO)
                    if not selected_candidate:
                        for off in (postal_info.offices or []):
                            o_type = (off.office_type or "").lower()
                            o_name = (off.office_name or "").lower()
                            if "sub" in o_type or "head" in o_type or " s.o" in o_name or " h.o" in o_name or " so" in o_name or " ho" in o_name:
                                m_off = match_kerala_canonical_district(off.district)
                                if m_off:
                                    selected_candidate = (m_off[0], m_off[1], m_off[2])
                                    break

                    # 5. Fallback to standard Kerala prefix table
                    if not selected_candidate:
                        prefix_dist = KERALA_PINCODE_4DIGIT_PREFIXES.get(clean_pin[:4]) or KERALA_PINCODE_PREFIXES.get(clean_pin[:3])
                        if prefix_dist:
                            m_pfx = match_kerala_canonical_district(prefix_dist)
                            if m_pfx:
                                selected_candidate = (m_pfx[0], m_pfx[1], m_pfx[2])

                    if selected_candidate:
                        canonical_name, canonical_state, norm_key = selected_candidate
                        master_entry = cls._get_or_create_master_entry(canonical_name, canonical_state, norm_key, db)

                        return DistrictResolutionResult(
                            district_id=master_entry.id if master_entry else None,
                            canonical_name=canonical_name,
                            state=canonical_state or "Kerala",
                            resolution_source="PINCODE",
                            district_status="RESOLVED",
                            source_district=raw_district,
                            district_mismatch=False,
                            post_offices=po_list
                        )
                    else:
                        return DistrictResolutionResult(
                            district_id=None,
                            canonical_name=None,
                            state="Kerala",
                            resolution_source="PINCODE",
                            district_status="NEEDS_CONFIRMATION",
                            source_district=raw_district,
                            district_mismatch=False,
                            post_offices=po_list,
                            unresolved_reason=f"Multiple Kerala districts ({', '.join(d[0] for d in resolved_districts)}) mapped to PIN {clean_pin}"
                        )
                elif postal_info.district:
                    # Postal data returned non-Kerala district
                    non_kerala_dist = clean_display_text(postal_info.district, title_case=True)
                    non_kerala_state = clean_display_text(postal_info.state, title_case=True) or state_hint or "Unknown"
                    return DistrictResolutionResult(
                        district_id=None,
                        canonical_name=non_kerala_dist,
                        state=non_kerala_state,
                        resolution_source="PINCODE",
                        district_status="RESOLVED",
                        source_district=raw_district,
                        district_mismatch=False,
                        post_offices=po_list
                    )

            # ------------------------------------------------------------------
            # STEP 1B: Kerala Postal Prefix Mapping fallback (Offline / New PINs)
            # ------------------------------------------------------------------
            prefix4 = clean_pin[:4]
            prefix3 = clean_pin[:3]
            inferred_kerala_district = KERALA_PINCODE_4DIGIT_PREFIXES.get(prefix4) or KERALA_PINCODE_PREFIXES.get(prefix3)

            if inferred_kerala_district:
                m = match_kerala_canonical_district(inferred_kerala_district)
                if m:
                    canonical_name, canonical_state, norm_key = m[0], m[1], m[2]
                    master_entry = cls._get_or_create_master_entry(canonical_name, canonical_state, norm_key, db)
                    
                    # Cache to PostalMaster so subsequent lookups are immediate
                    if db is not None:
                        try:
                            new_pm = PostalMaster(
                                pincode=clean_pin,
                                district=canonical_name,
                                state=canonical_state,
                                country="India"
                            )
                            db.add(new_pm)
                            db.flush()
                        except Exception:
                            pass

                    district_mismatch = False
                    mismatch_msg = None
                    if raw_district and str(raw_district).strip():
                        raw_matched = match_kerala_canonical_district(raw_district)
                        if not raw_matched or raw_matched[0] != canonical_name:
                            district_mismatch = True
                            mismatch_msg = f"Uploaded district '{raw_district}' does not match the district '{canonical_name}' associated with Pincode {clean_pin}"

                    return DistrictResolutionResult(
                        district_id=master_entry.id if master_entry else None,
                        canonical_name=canonical_name,
                        state=canonical_state or "Kerala",
                        resolution_source="PINCODE",
                        district_status="RESOLVED",
                        source_district=raw_district,
                        district_mismatch=district_mismatch,
                        mismatch_message=mismatch_msg
                    )

        # ----------------------------------------------------------------------
        # STEP 2: Fallback to Supplied District / Post Office / Address Text
        # ----------------------------------------------------------------------
        # 2A. Check raw_district
        if raw_district and str(raw_district).strip():
            matched = match_kerala_canonical_district(raw_district)
            if matched:
                canonical_name, canonical_state, norm_key, source = matched
                dist_id = None
                if db is not None:
                    master_entry = cls._get_or_create_master_entry(canonical_name, canonical_state, norm_key, db)
                    if master_entry:
                        dist_id = master_entry.id
                
                if pincode and not pin_valid:
                    res_source = "DISTRICT_FALLBACK"
                elif source == "DIRECT_MATCH":
                    res_source = "DISTRICT_DIRECT_MATCH"
                else:
                    res_source = "DISTRICT_ALIAS"

                return DistrictResolutionResult(
                    district_id=dist_id,
                    canonical_name=canonical_name,
                    state=canonical_state or "Kerala",
                    resolution_source=res_source,
                    district_status="RESOLVED",
                    source_district=raw_district,
                    district_mismatch=False
                )

        # 2B. Check source_post_office
        if source_post_office and str(source_post_office).strip():
            po_clean = canonical_key(source_post_office)
            po_dist = KNOWN_KERALA_PLACES.get(po_clean)
            if not po_dist:
                m_po = match_kerala_canonical_district(source_post_office)
                if m_po:
                    po_dist = m_po[0]

            if po_dist:
                m = match_kerala_canonical_district(po_dist)
                if m:
                    canonical_name, canonical_state, norm_key = m[0], m[1], m[2]
                    dist_id = None
                    if db is not None:
                        master_entry = cls._get_or_create_master_entry(canonical_name, canonical_state, norm_key, db)
                        if master_entry:
                            dist_id = master_entry.id

                    return DistrictResolutionResult(
                        district_id=dist_id,
                        canonical_name=canonical_name,
                        state=canonical_state or "Kerala",
                        resolution_source="DISTRICT_ALIAS",
                        district_status="RESOLVED",
                        source_district=raw_district,
                        district_mismatch=False
                    )

        # 2C. Check address_hint tokens
        if address_hint and str(address_hint).strip():
            addr_tokens = re.split(r'[\s,.\-\(\)]+', str(address_hint).lower())
            for token in addr_tokens:
                token_clean = token.strip()
                if not token_clean or len(token_clean) < 3:
                    continue
                place_dist = KNOWN_KERALA_PLACES.get(token_clean)
                if place_dist:
                    m = match_kerala_canonical_district(place_dist)
                    if m:
                        canonical_name, canonical_state, norm_key = m[0], m[1], m[2]
                        dist_id = None
                        if db is not None:
                            master_entry = cls._get_or_create_master_entry(canonical_name, canonical_state, norm_key, db)
                            if master_entry:
                                dist_id = master_entry.id

                        return DistrictResolutionResult(
                            district_id=dist_id,
                            canonical_name=canonical_name,
                            state=canonical_state or "Kerala",
                            resolution_source="DISTRICT_ALIAS",
                            district_status="RESOLVED",
                            source_district=raw_district,
                            district_mismatch=False
                        )
                
                m_tok = match_kerala_canonical_district(token_clean)
                if m_tok:
                    canonical_name, canonical_state, norm_key = m_tok[0], m_tok[1], m_tok[2]
                    dist_id = None
                    if db is not None:
                        master_entry = cls._get_or_create_master_entry(canonical_name, canonical_state, norm_key, db)
                        if master_entry:
                            dist_id = master_entry.id

                    return DistrictResolutionResult(
                        district_id=dist_id,
                        canonical_name=canonical_name,
                        state=canonical_state or "Kerala",
                        resolution_source="DISTRICT_ALIAS",
                        district_status="RESOLVED",
                        source_district=raw_district,
                        district_mismatch=False
                    )

        # ----------------------------------------------------------------------
        # STEP 3: Unresolved fallback (No guess, routes to Unknown Location Data)
        # ----------------------------------------------------------------------
        reason = "Invalid or unmapped district"
        if not raw_district:
            reason = "District is missing"
        if not clean_pin or not pin_valid:
            reason += " and Pincode is invalid or missing"

        return DistrictResolutionResult(
            district_id=None,
            canonical_name=None,
            state=state_hint or "Kerala",
            resolution_source="UNRESOLVED",
            district_status="UNRESOLVED",
            source_district=raw_district,
            district_mismatch=False,
            unresolved_reason=reason
        )

    @classmethod
    def _get_or_create_master_entry(
        cls,
        canonical_name: str,
        state: str,
        norm_key: str,
        db: Session
    ) -> Optional[DistrictMaster]:
        """
        Retrieves or creates a DistrictMaster record guaranteed to be unique on normalized_key.
        """
        existing = db.query(DistrictMaster).filter(
            DistrictMaster.normalized_key == norm_key
        ).first()

        if existing:
            return existing

        try:
            # Find default aliases from master list
            aliases_list = []
            for c_name, _, k, eng, mal in KERALA_14_DISTRICTS:
                if k == norm_key:
                    aliases_list = eng + mal
                    break

            new_master = DistrictMaster(
                canonical_name=canonical_name,
                state=state or "Kerala",
                normalized_key=norm_key,
                aliases=json.dumps(aliases_list, ensure_ascii=False)
            )
            db.add(new_master)
            db.flush()
            return new_master
        except Exception as e:
            db.rollback()
            return db.query(DistrictMaster).filter(
                DistrictMaster.normalized_key == norm_key
            ).first()

    @classmethod
    def cleanup_duplicates_in_master(cls, db: Session) -> int:
        """
        Scans district_master table and merges any duplicate records that share the same normalized key.
        Re-points all customer foreign keys to the primary record and deletes the duplicate records.
        """
        all_records = db.query(DistrictMaster).order_by(DistrictMaster.id.asc()).all()
        grouped: Dict[str, List[DistrictMaster]] = {}
        for r in all_records:
            k = canonical_key(r.normalized_key or r.canonical_name)
            if k:
                grouped.setdefault(k, []).append(r)

        merged_count = 0
        for norm_key, records in grouped.items():
            if len(records) > 1:
                primary = records[0]
                for dup in records[1:]:
                    # Re-link customers pointing to dup.id to primary.id
                    db.query(Customer).filter(Customer.district_id == dup.id).update(
                        {"district_id": primary.id, "district": primary.canonical_name},
                        synchronize_session=False
                    )
                    # Merge aliases
                    try:
                        primary_aliases = set(json.loads(primary.aliases or "[]"))
                        dup_aliases = set(json.loads(dup.aliases or "[]"))
                        merged_aliases = list(primary_aliases.union(dup_aliases))
                        primary.aliases = json.dumps(merged_aliases, ensure_ascii=False)
                    except Exception:
                        pass
                    
                    db.delete(dup)
                    merged_count += 1

        if merged_count > 0:
            db.commit()
            logger.info(f"Cleaned up {merged_count} duplicate records in district_master.")
        return merged_count

    @classmethod
    def seed_master_districts(cls, db: Session) -> int:
        """
        Seeds exactly the 14 standard Kerala districts into district_master.
        Guarantees that unique normalized keys exist in DB.
        """
        cls.cleanup_duplicates_in_master(db)
        seeded = 0

        for canonical_name, state, norm_key, eng_aliases, mal_aliases in KERALA_14_DISTRICTS:
            existing = db.query(DistrictMaster).filter(
                DistrictMaster.normalized_key == norm_key
            ).first()

            all_aliases = eng_aliases + mal_aliases

            if not existing:
                master_entry = DistrictMaster(
                    canonical_name=canonical_name,
                    state=state,
                    normalized_key=norm_key,
                    aliases=json.dumps(all_aliases, ensure_ascii=False)
                )
                db.add(master_entry)
                seeded += 1
            else:
                # Ensure canonical name and state are accurate
                if existing.canonical_name != canonical_name:
                    existing.canonical_name = canonical_name
                if existing.state != state:
                    existing.state = state
                # Ensure all official aliases are present
                try:
                    curr_aliases = set(json.loads(existing.aliases or "[]"))
                    new_aliases = curr_aliases.union(set(all_aliases))
                    existing.aliases = json.dumps(list(new_aliases), ensure_ascii=False)
                except Exception:
                    existing.aliases = json.dumps(all_aliases, ensure_ascii=False)

        db.commit()
        return seeded

    @classmethod
    def migrate_existing_data(cls, db: Session, force_all: bool = False) -> Dict[str, int]:
        """
        Safe Migration:
        1. Ensures 14 master districts are seeded and duplicates cleaned.
        2. Scans Customer records.
        3. Resolves each customer's district using Pincode-First priority.
        4. Detects and logs district mismatches where uploaded district disagreed with Pincode district.
        5. Updates customer.source_district, customer.district_id, customer.district, customer.district_resolution_source, customer.district_status, customer.district_mismatch.
        6. Preserves all customer and order records without deletion.
        """
        cls.seed_master_districts(db)

        customers = db.query(Customer).all()
        updated_count = 0
        unknown_count = 0
        mismatch_count = 0

        for cust in customers:
            # Skip records already correctly resolved unless force_all is requested
            if not force_all and cust.district_id is not None and cust.district and cust.district_status == "RESOLVED":
                continue

            raw_dist = cust.source_district or cust.district
            raw_pin = cust.pincode
            raw_po = cust.post_office
            raw_addr = cust.full_address
            raw_state = cust.state
            
            res = cls.resolve_district(
                raw_district=raw_dist,
                pincode=raw_pin,
                source_post_office=raw_po,
                address_hint=raw_addr,
                state_hint=raw_state,
                db=db,
                allow_postal_lookup=False
            )

            changed = False
            if not cust.source_district and raw_dist:
                cust.source_district = raw_dist
                changed = True

            if res.is_resolved:
                if cust.district_id != res.district_id:
                    cust.district_id = res.district_id
                    changed = True
                if cust.district != res.canonical_name:
                    cust.district = res.canonical_name
                    changed = True
                if res.state and cust.state != res.state:
                    cust.state = res.state
                    changed = True
                if hasattr(cust, "district_resolution_source") and cust.district_resolution_source != res.resolution_source:
                    cust.district_resolution_source = res.resolution_source
                    changed = True
                if hasattr(cust, "district_status") and cust.district_status != res.district_status:
                    cust.district_status = res.district_status
                    changed = True
                if hasattr(cust, "district_mismatch") and cust.district_mismatch != res.district_mismatch:
                    cust.district_mismatch = res.district_mismatch
                    changed = True
                if res.district_mismatch:
                    mismatch_count += 1
                if changed:
                    updated_count += 1
            else:
                if cust.district_id is not None:
                    cust.district_id = None
                    changed = True
                if cust.district and cust.district.lower() in ["unknown", "unassigned", "nan", "none", "null"]:
                    cust.district = None
                    changed = True
                if hasattr(cust, "district_resolution_source") and cust.district_resolution_source != "UNRESOLVED":
                    cust.district_resolution_source = "UNRESOLVED"
                    changed = True
                if hasattr(cust, "district_status") and cust.district_status != res.district_status:
                    cust.district_status = res.district_status
                    changed = True
                if hasattr(cust, "district_mismatch") and cust.district_mismatch:
                    cust.district_mismatch = False
                    changed = True
                if changed:
                    updated_count += 1
                unknown_count += 1

        db.commit()
        logger.info(f"District migration complete: {updated_count} customers updated, {mismatch_count} mismatches detected, {unknown_count} unknown location customers.")
        return {
            "total_customers": len(customers),
            "updated_count": updated_count,
            "mismatch_count": mismatch_count,
            "unknown_count": unknown_count
        }

