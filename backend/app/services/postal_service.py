from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.postal import PostalMaster, PostalOffice
from app.models.data_quality import DataQualityIssue
from app.utils.postal_api import fetch_postal_info_from_api
from app.utils.text_normalization import canonical_key, clean_display_text, ci_equals, sql_ci_like

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
            return None

        # Save to local Postal Master with clean display formatting
        postal = PostalMaster(
            pincode=pin,
            district=clean_display_text(api_data.get("district"), title_case=True),
            state=clean_display_text(api_data.get("state"), title_case=True),
            region=clean_display_text(api_data.get("region"), title_case=True),
            division=clean_display_text(api_data.get("division"), title_case=True),
            circle=clean_display_text(api_data.get("circle"), title_case=True),
            country=clean_display_text(api_data.get("country", "India"), title_case=True) or "India"
        )
        db.add(postal)
        db.flush()

        # Save all associated post offices (1:N)
        for po in api_data.get("offices", []):
            office = PostalOffice(
                pincode=pin,
                office_name=clean_display_text(po.get("office_name"), title_case=True) or "",
                office_type=po.get("office_type"),
                delivery_status=po.get("delivery_status"),
                district=clean_display_text(po.get("district"), title_case=True),
                state=clean_display_text(po.get("state"), title_case=True)
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
            if not ci_equals(client_district, postal.district):
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

