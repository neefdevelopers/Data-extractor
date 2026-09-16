from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.postal import PostalMaster, PostalOffice
from app.models.data_quality import DataQualityIssue
from app.utils.postal_api import fetch_postal_info_from_api

class PostalService:
    @staticmethod
    def get_or_enrich_pincode(
        pincode: Optional[str],
        db: Session,
        client_district: Optional[str] = None,
        client_po: Optional[str] = None,
        auto_commit: bool = True
    ) -> Optional[PostalMaster]:
        if not pincode or len(pincode) != 6 or not pincode.isdigit():
            return None

        # Check local database cache first
        postal = db.query(PostalMaster).filter(PostalMaster.pincode == pincode).first()
        if postal:
            PostalService._check_conflict(postal, client_district, client_po, db, auto_commit=auto_commit)
            return postal

        # Fetch from India Post API
        api_data = fetch_postal_info_from_api(pincode)
        if not api_data:
            return None

        # Save to local Postal Master
        postal = PostalMaster(
            pincode=pincode,
            district=api_data.get("district"),
            state=api_data.get("state"),
            region=api_data.get("region"),
            division=api_data.get("division"),
            circle=api_data.get("circle"),
            country=api_data.get("country", "India")
        )
        db.add(postal)
        db.flush()

        # Save all associated post offices (1:N)
        for po in api_data.get("offices", []):
            office = PostalOffice(
                pincode=pincode,
                office_name=po.get("office_name"),
                office_type=po.get("office_type"),
                delivery_status=po.get("delivery_status"),
                district=po.get("district"),
                state=po.get("state")
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
            if client_district.strip().lower() != postal.district.strip().lower():
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
        return db.query(PostalOffice).filter(
            PostalOffice.office_name.ilike(f"%{query}%")
        ).limit(limit).all()
