import re
import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc, asc
from app.models.customer import Customer
from app.models.location_audit import LocationCorrectionAudit
from app.models.postal import PostalMaster
from app.services.postal_service import PostalService
from app.schemas.location import (
    UnknownLocationSummary,
    UnknownLocationRecord,
    LocationCorrectionRequest,
    BulkLocationCorrectionRequest,
    LocationAuditLog,
    PaginatedUnknownLocations,
    PaginatedAuditLogs
)
from app.utils.text_normalization import canonical_key, clean_display_text, ci_contains
from app.utils.cleaning import normalize_pincode

def sql_is_unknown_pin():
    return or_(
        Customer.pincode.is_(None),
        func.trim(Customer.pincode) == "",
        func.lower(func.trim(Customer.pincode)).in_(["unknown", "unassigned", "n/a", "null", "none", "nan", "000000"]),
        func.length(func.trim(Customer.pincode)) != 6
    )

def sql_is_unknown_district():
    return or_(
        Customer.district.is_(None),
        func.trim(Customer.district) == "",
        func.lower(func.trim(Customer.district)).in_(["unknown", "unassigned", "unassigned / unknown", "n/a", "null", "none", "nan", "unknown district"]),
        func.lower(func.trim(Customer.district)).like("%unknown%"),
        func.lower(func.trim(Customer.district)).like("%unassigned%")
    )

def is_unknown_pin(pin: Optional[str]) -> bool:
    if not pin:
        return True
    s = str(pin).strip().lower()
    if s in ["", "unknown", "unassigned", "n/a", "null", "none", "nan", "000000"]:
        return True
    digits = re.sub(r"\D", "", s)
    return len(digits) != 6

def is_unknown_district(dist: Optional[str]) -> bool:
    if not dist:
        return True
    s = str(dist).strip().lower()
    if s in ["", "unknown", "unassigned", "n/a", "null", "none", "nan", "unknown district", "unassigned / unknown"]:
        return True
    if "unknown" in s or "unassigned" in s:
        return True
    return False

class LocationService:
    @staticmethod
    def get_unknown_summary(db: Session) -> UnknownLocationSummary:
        """
        Calculates exact unique counts of records with missing/unknown Pincode or District.
        Ensures accurate arithmetic with zero double counting.
        """
        cond_pin = sql_is_unknown_pin()
        cond_dist = sql_is_unknown_district()

        unknown_pincode_count = db.query(Customer).filter(cond_pin).count()
        unknown_district_count = db.query(Customer).filter(cond_dist).count()
        both_unknown_count = db.query(Customer).filter(and_(cond_pin, cond_dist)).count()
        
        # Unique records with at least one location issue
        total_unresolved = db.query(Customer).filter(or_(cond_pin, cond_dist)).count()

        return UnknownLocationSummary(
            unknown_pincode_count=unknown_pincode_count,
            unknown_district_count=unknown_district_count,
            both_unknown_count=both_unknown_count,
            total_unresolved=total_unresolved
        )

    @staticmethod
    def get_unknown_records(
        db: Session,
        filter_type: str = "all",  # 'all', 'unknown_pincode', 'unknown_district', 'both'
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "id",
        sort_order: str = "desc"
    ) -> PaginatedUnknownLocations:
        cond_pin = sql_is_unknown_pin()
        cond_dist = sql_is_unknown_district()

        query = db.query(Customer)

        if filter_type == "unknown_pincode":
            query = query.filter(cond_pin)
        elif filter_type == "unknown_district":
            query = query.filter(cond_dist)
        elif filter_type == "both":
            query = query.filter(and_(cond_pin, cond_dist))
        else:  # all
            query = query.filter(or_(cond_pin, cond_dist))

        if search:
            s = f"%{canonical_key(search)}%"
            query = query.filter(
                or_(
                    func.lower(func.trim(Customer.customer_name)).like(s),
                    func.lower(func.trim(Customer.contact_number)).like(s),
                    func.lower(func.trim(Customer.normalized_contact)).like(s),
                    func.lower(func.trim(Customer.full_address)).like(s),
                    func.lower(func.trim(Customer.district)).like(s),
                    func.lower(func.trim(Customer.post_office)).like(s),
                    func.lower(func.trim(Customer.pincode)).like(s)
                )
            )

        total = query.count()

        # Sorting
        sort_attr = getattr(Customer, sort_by, Customer.id)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_attr))
        else:
            query = query.order_by(desc(sort_attr))

        offset = (page - 1) * page_size
        customers = query.offset(offset).limit(page_size).all()

        records = []
        for c in customers:
            u_pin = is_unknown_pin(c.pincode)
            u_dist = is_unknown_district(c.district)

            if u_pin and u_dist:
                m_type = "BOTH_UNKNOWN"
            elif u_pin:
                m_type = "UNKNOWN_PINCODE"
            else:
                m_type = "UNKNOWN_DISTRICT"

            records.append(
                UnknownLocationRecord(
                    id=c.id,
                    customer_id_str=c.customer_id_str,
                    customer_name=c.customer_name,
                    contact_number=c.contact_number,
                    normalized_contact=c.normalized_contact,
                    full_address=c.full_address,
                    pincode=c.pincode if not u_pin else None,
                    post_office=c.post_office,
                    district=clean_display_text(c.district, title_case=True) if not u_dist else None,
                    state=clean_display_text(c.state, title_case=True),
                    total_orders=c.total_orders,
                    total_spend=c.total_spend,
                    missing_type=m_type,
                    created_at=c.created_at
                )
            )

        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedUnknownLocations(
            items=records,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    @staticmethod
    def correct_customer_location(
        db: Session,
        customer_id: int,
        req: LocationCorrectionRequest,
        changed_by: str = "Admin"
    ) -> Customer:
        cust = db.query(Customer).filter(Customer.id == customer_id).first()
        if not cust:
            raise ValueError(f"Customer with ID {customer_id} not found.")

        # Capture previous state for audit log
        prev_pin = cust.pincode
        prev_dist = cust.district
        prev_po = cust.post_office
        prev_state = cust.state

        # Clean and normalize new values
        clean_pin, pin_valid = normalize_pincode(req.pincode) if req.pincode else (None, False)
        clean_dist = clean_display_text(req.district, title_case=True)
        clean_po = clean_display_text(req.post_office, title_case=True)
        clean_st = clean_display_text(req.state, title_case=True)

        if req.pincode:
            if not pin_valid and req.pincode.strip():
                raise ValueError(f"Invalid PIN code '{req.pincode}'. Must be a 6-digit number.")
            cust.pincode = clean_pin

        if req.district is not None:
            cust.district = clean_dist

        if req.post_office is not None:
            cust.post_office = clean_po

        if req.state is not None:
            cust.state = clean_st

        # If valid PIN entered and district/state not explicitly provided, enrich from postal master
        if clean_pin and pin_valid and (not cust.district or not cust.state):
            postal = db.query(PostalMaster).filter(PostalMaster.pincode == clean_pin).first()
            if postal:
                if not cust.district and postal.district:
                    cust.district = postal.district
                if not cust.state and postal.state:
                    cust.state = postal.state

        # Create Audit Log
        audit = LocationCorrectionAudit(
            customer_id=cust.id,
            previous_pincode=prev_pin,
            new_pincode=cust.pincode,
            previous_district=prev_dist,
            new_district=cust.district,
            previous_post_office=prev_po,
            new_post_office=cust.post_office,
            previous_state=prev_state,
            new_state=cust.state,
            correction_source=req.source or "MANUAL",
            changed_by=changed_by,
            notes=req.notes
        )
        db.add(audit)
        db.commit()
        db.refresh(cust)

        return cust

    @staticmethod
    def bulk_correct_locations(
        db: Session,
        req: BulkLocationCorrectionRequest,
        changed_by: str = "Admin"
    ) -> Dict[str, Any]:
        if not req.customer_ids:
            return {"updated_count": 0, "message": "No customers selected."}

        clean_pin, pin_valid = normalize_pincode(req.pincode) if req.pincode else (None, False)
        clean_dist = clean_display_text(req.district, title_case=True)
        clean_po = clean_display_text(req.post_office, title_case=True)
        clean_st = clean_display_text(req.state, title_case=True)

        if req.pincode and not pin_valid:
            raise ValueError(f"Invalid PIN code '{req.pincode}'. Must be a 6-digit number.")

        customers = db.query(Customer).filter(Customer.id.in_(req.customer_ids)).all()
        updated_count = 0

        for cust in customers:
            prev_pin = cust.pincode
            prev_dist = cust.district
            prev_po = cust.post_office
            prev_state = cust.state

            has_change = False

            if req.pincode and pin_valid:
                cust.pincode = clean_pin
                has_change = True

            if req.district:
                cust.district = clean_dist
                has_change = True

            if req.post_office:
                cust.post_office = clean_po
                has_change = True

            if req.state:
                cust.state = clean_st
                has_change = True

            if has_change:
                audit = LocationCorrectionAudit(
                    customer_id=cust.id,
                    previous_pincode=prev_pin,
                    new_pincode=cust.pincode,
                    previous_district=prev_dist,
                    new_district=cust.district,
                    previous_post_office=prev_po,
                    new_post_office=cust.post_office,
                    previous_state=prev_state,
                    new_state=cust.state,
                    correction_source=req.source or "BULK_UPDATE",
                    changed_by=changed_by,
                    notes=req.notes
                )
                db.add(audit)
                updated_count += 1

        db.commit()
        return {
            "updated_count": updated_count,
            "message": f"Successfully updated location for {updated_count} records."
        }

    @staticmethod
    def get_audit_history(
        db: Session,
        customer_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedAuditLogs:
        query = db.query(LocationCorrectionAudit).join(Customer, LocationCorrectionAudit.customer_id == Customer.id)

        if customer_id:
            query = query.filter(LocationCorrectionAudit.customer_id == customer_id)

        if search:
            s = f"%{canonical_key(search)}%"
            query = query.filter(
                or_(
                    func.lower(func.trim(Customer.customer_name)).like(s),
                    func.lower(func.trim(LocationCorrectionAudit.new_district)).like(s),
                    func.lower(func.trim(LocationCorrectionAudit.new_pincode)).like(s),
                    func.lower(func.trim(LocationCorrectionAudit.changed_by)).like(s)
                )
            )

        total = query.count()
        offset = (page - 1) * page_size
        logs = query.order_by(desc(LocationCorrectionAudit.created_at)).offset(offset).limit(page_size).all()

        items = []
        for l in logs:
            items.append(
                LocationAuditLog(
                    id=l.id,
                    customer_id=l.customer_id,
                    customer_name=l.customer.customer_name if l.customer else "Unknown",
                    previous_pincode=l.previous_pincode,
                    new_pincode=l.new_pincode,
                    previous_district=l.previous_district,
                    new_district=l.new_district,
                    previous_post_office=l.previous_post_office,
                    new_post_office=l.new_post_office,
                    previous_state=l.previous_state,
                    new_state=l.new_state,
                    correction_source=l.correction_source,
                    changed_by=l.changed_by,
                    notes=l.notes,
                    created_at=l.created_at
                )
            )

        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedAuditLogs(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
