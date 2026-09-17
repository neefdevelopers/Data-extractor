from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.postal import PostalMaster, PostalOffice
from app.models.data_quality import DataQualityIssue
from app.utils.postal_api import fetch_postal_info_from_api
from app.utils.text_normalization import canonical_key, clean_display_text, ci_equals, sql_ci_like
from app.utils.district_normalization import match_kerala_canonical_district

class PostalService:
    @staticmethod
    def get_or_enrich_pincode(
        pincode: Optional[str],
        db: Session,
        client_district: Optional[str] = None,
        client_po: Optional[str] = None,
        auto_commit: bool = True
    ) -> Optional[PostalMaster]:
        if not pincode or len(pincode.strip()) != 6 or not pincode.strip().isdigit():
            return None
        pin = pincode.strip()

        # Check local database cache first
        postal = db.query(PostalMaster).filter(PostalMaster.pincode == pin).first()
        if postal:
            PostalService._check_conflict(postal, client_district, client_po, db, auto_commit=auto_commit)
            return postal

        # Fetch from India Post API
        api_data = fetch_postal_info_from_api(pin)
        if not api_data:
            try:
                unresolved = PostalMaster(
                    pincode=pin,
                    district=None,
                    state=None,
                    country="India"
                )
                db.add(unresolved)
                db.flush()
            except Exception:
                pass
            return None

        # Resolve canonical Kerala district representation via 14-district master
        from app.services.district_resolution_service import DistrictResolutionService
        raw_api_dist = api_data.get("district")
        raw_api_state = api_data.get("state")
        
        matched_dist = match_kerala_canonical_district(raw_api_dist)
        canon_dist = matched_dist[0] if matched_dist else clean_display_text(raw_api_dist, title_case=True)
        canon_state = matched_dist[1] if matched_dist else clean_display_text(raw_api_state, title_case=True)

        # Save to local Postal Master with clean display formatting & canonical district
        postal = PostalMaster(
            pincode=pin,
            district=canon_dist,
            state=canon_state or "Kerala",
            region=clean_display_text(api_data.get("region"), title_case=True),
            division=clean_display_text(api_data.get("division"), title_case=True),
            circle=clean_display_text(api_data.get("circle"), title_case=True),
            country=clean_display_text(api_data.get("country", "India"), title_case=True) or "India"
        )
        db.add(postal)
        db.flush()

        # Save all associated post offices (1:N)
        for po in api_data.get("offices", []):
            office_raw_dist = po.get("district") or raw_api_dist
            office_raw_state = po.get("state") or raw_api_state
            
            po_matched = match_kerala_canonical_district(office_raw_dist)
            po_canon_dist = po_matched[0] if po_matched else (canon_dist or clean_display_text(office_raw_dist, title_case=True))
            po_canon_state = po_matched[1] if po_matched else (canon_state or clean_display_text(office_raw_state, title_case=True))

            office = PostalOffice(
                pincode=pin,
                office_name=clean_display_text(po.get("office_name"), title_case=True) or "",
                office_type=po.get("office_type"),
                delivery_status=po.get("delivery_status"),
                district=po_canon_dist,
                state=po_canon_state or "Kerala"
            )
            db.add(office)
        
        if auto_commit:
            db.commit()
            db.refresh(postal)
        else:
            db.flush()

        PostalService._check_conflict(postal, client_district, client_po, db, auto_commit=auto_commit)
        return postal

    @staticmethod
    def _check_conflict(
        postal: PostalMaster,
        client_district: Optional[str],
        client_po: Optional[str],
        db: Session,
        auto_commit: bool = True
    ):
        """Creates a Data Quality warning if imported Excel values conflict with official postal database"""
        if client_district and postal.district:
            from app.utils.district_normalization import get_normalized_district_key
            client_norm_key = get_normalized_district_key(client_district)
            postal_norm_key = get_normalized_district_key(postal.district)

            is_same_district = False
            if client_norm_key and postal_norm_key and client_norm_key == postal_norm_key:
                is_same_district = True
            elif ci_equals(client_district, postal.district):
                is_same_district = True

            if not is_same_district:
                existing = db.query(DataQualityIssue).filter(
                    DataQualityIssue.entity_type == "POSTAL",
                    DataQualityIssue.entity_id == postal.pincode,
                    DataQualityIssue.issue_type == "POSTAL_CONFLICT"
                ).first()
                if not existing:
                    issue = DataQualityIssue(
                        entity_type="POSTAL",
                        entity_id=postal.pincode,
                        field_name="district",
                        issue_type="POSTAL_CONFLICT",
                        raw_value=client_district,
                        message=f"Imported district '{client_district}' differs from postal master '{postal.district}' for PIN {postal.pincode}",
                        suggested_fix=f"Use official district '{postal.district}' or verify PIN code"
                    )
                    db.add(issue)
                    if auto_commit:
                        db.commit()
                    else:
                        db.flush()

    @staticmethod
    def search_post_offices(query: str, db: Session, limit: int = 20) -> List[PostalOffice]:
        from sqlalchemy import func
        clean_q = canonical_key(query)
        return db.query(PostalOffice).filter(
            func.lower(func.trim(PostalOffice.office_name)).like(f"%{clean_q}%")
        ).limit(limit).all()

    @staticmethod
    def resolve_post_office(
        address: Optional[str] = None,
        pincode: Optional[str] = None,
        source_post_office: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Optional[str]:
        import re
        if source_post_office and str(source_post_office).strip():
            s_po = str(source_post_office).strip()
            if s_po.lower() not in ["unknown", "unknown post office", "none", "null", "na", "n/a", "-", ""]:
                return clean_display_text(s_po, title_case=True)

        pin = str(pincode).strip() if (pincode and str(pincode).strip().isdigit() and len(str(pincode).strip()) == 6) else None
        addr_str = str(address).strip() if address else ""

        if pin and db:
            offices = db.query(PostalOffice).filter(PostalOffice.pincode == pin).all()
            if offices:
                if len(offices) == 1:
                    return offices[0].office_name
                # Check if any office name is present in address text
                if addr_str:
                    addr_lower = addr_str.lower()
                    for off in offices:
                        if off.office_name.lower() in addr_lower:
                            return off.office_name
                # Fallback to delivery office or first office
                deliv_offices = [off.office_name for off in offices if (off.delivery_status or "").lower() == "delivery"]
                if deliv_offices:
                    return deliv_offices[0]
                return offices[0].office_name

        # Fallback to address extraction via regex
        if addr_str:
            patterns = [
                r"([A-Za-z\s]{3,30})\s*(?:P\.?O\.?|Post\s*Office|B\.?O\.?|S\.?O\.?)\b",
                r"(?:P\.?O\.?|Post\s*Office)\s*[:\-\s]\s*([A-Za-z\s]{3,30})\b"
            ]
            for pat in patterns:
                m = re.search(pat, addr_str, re.IGNORECASE)
                if m:
                    candidate = m.group(1).strip(" ,.-")
                    if candidate.lower() not in ["near", "opp", "opposite", "road", "street", "house", "building", "kerala", "india", "pin"]:
                        words = candidate.split()
                        if len(words) > 3:
                            words = words[-3:]
                        return clean_display_text(" ".join(words), title_case=True)

        return None

