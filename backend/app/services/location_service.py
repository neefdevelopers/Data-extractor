import re
import json
import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_, desc, asc
from app.models.customer import Customer
from app.models.location_audit import LocationCorrectionAudit
from app.models.postal import PostalMaster
from app.services.postal_service import PostalService
from app.services.district_resolution_service import DistrictResolutionService
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
from app.utils.district_normalization import match_kerala_canonical_district, normalize_district_name

def sql_is_unknown_pin():
    return or_(
        Customer.pincode.is_(None),
        func.trim(Customer.pincode) == "",
        func.lower(func.trim(Customer.pincode)).in_(["unknown", "unassigned", "n/a", "null", "none", "nan", "000000", "nil"]),
        func.length(func.trim(Customer.pincode)) != 6
    )

def sql_is_unknown_district():
    return or_(
        and_(Customer.district_id.is_(None), or_(Customer.district.is_(None), func.trim(Customer.district) == "")),
        Customer.district.is_(None),
        func.trim(Customer.district) == "",
        func.lower(func.trim(Customer.district)).in_(["unknown", "unassigned", "unassigned / unknown", "n/a", "null", "none", "nan", "unknown district", "nil"]),
        func.lower(func.trim(Customer.district)).like("%unknown%"),
        func.lower(func.trim(Customer.district)).like("%unassigned%")
    )

def is_unknown_pin(pin: Optional[str]) -> bool:
    if not pin:
        return True
    s = str(pin).strip().lower()
    if s in ["", "unknown", "unassigned", "n/a", "null", "none", "nan", "000000", "nil"]:
        return True
    digits = re.sub(r"\D", "", s)
    return len(digits) != 6

def is_unknown_district(dist: Optional[str], dist_id: Optional[int] = None) -> bool:
    if dist_id is not None:
        return False
    if not dist:
        return True
    s = str(dist).strip().lower()
    if s in ["", "unknown", "unassigned", "n/a", "null", "none", "nan", "unknown district", "unassigned / unknown", "nil"]:
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
            u_dist = is_unknown_district(c.district, c.district_id)

            if u_pin and u_dist:
                m_type = "BOTH_UNKNOWN"
                reason = "Both 6-digit Pincode and Kerala District are missing or unverified"
            elif u_pin:
                m_type = "UNKNOWN_PINCODE"
                reason = "Invalid or missing 6-digit Pincode"
            else:
                m_type = "UNKNOWN_DISTRICT"
                reason = "District is missing or does not match any of the 14 Kerala canonical districts"

            raw_data_dict = None
            if getattr(c, "raw_row_data", None):
                try:
                    raw_data_dict = json.loads(c.raw_row_data)
                except Exception:
                    raw_data_dict = None

            if not raw_data_dict:
                # Provide a structured fallback dictionary of customer fields
                raw_data_dict = {
                    "Customer Name": c.customer_name or "",
                    "Contact Number": c.contact_number or c.normalized_contact or "",
                    "Full Address": c.full_address or "",
                    "Pincode": c.pincode or "",
                    "Post Office": c.post_office or "",
                    "Uploaded District": getattr(c, "source_district", None) or c.district or "",
                    "State": c.state or "Kerala",
                    "Total Orders": str(c.total_orders or 0),
                    "Total Spend": f"₹{c.total_spend:,.2f}" if c.total_spend else "₹0.00"
                }

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
                    source_district=getattr(c, "source_district", None),
                    district_id=c.district_id,
                    district=c.district if not u_dist else None,
                    state=c.state or "Kerala",
                    district_resolution_source=getattr(c, "district_resolution_source", "UNRESOLVED") or "UNRESOLVED",
                    district_status=getattr(c, "district_status", "UNRESOLVED") or "UNRESOLVED",
                    unresolved_reason=reason,
                    total_orders=c.total_orders,
                    total_spend=c.total_spend,
                    missing_type=m_type,
                    source_file_name=getattr(c, "source_file_name", None) or "Manual / System Record",
                    source_row_number=getattr(c, "source_row_number", None),
                    raw_row_data=raw_data_dict,
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

        target_pin = req.pincode if req.pincode is not None else cust.pincode
        target_dist = req.district if req.district is not None else cust.district
        target_po = req.post_office if req.post_office is not None else cust.post_office
        target_state = req.state if req.state is not None else cust.state

        # Validate pincode if entered
        clean_pin, pin_valid = normalize_pincode(target_pin) if target_pin else (None, False)
        if target_pin and target_pin.strip() and not pin_valid:
            raise ValueError(f"Invalid PIN code '{target_pin}'. Must be a 6-digit number.")

        # Resolve via centralized DistrictResolutionService
        clean_po = clean_display_text(target_po, title_case=True) if target_po else None
        res = DistrictResolutionService.resolve_district(
            raw_district=target_dist,
            pincode=clean_pin,
            source_post_office=clean_po,
            address_hint=cust.full_address,
            state_hint=target_state,
            db=db,
            allow_postal_lookup=True
        )

        cust.pincode = clean_pin if clean_pin else None
        cust.post_office = clean_po
        if target_dist and not getattr(cust, "source_district", None):
            cust.source_district = target_dist

        if res.is_resolved:
            cust.district_id = res.district_id
            cust.district = res.canonical_name
            cust.state = res.state or target_state or "Kerala"
            cust.district_resolution_source = res.resolution_source
            cust.district_status = res.district_status
            cust.district_mismatch = res.district_mismatch
        else:
            cust.district_id = None
            cust.district = None
            cust.state = target_state or "Kerala"
            cust.district_resolution_source = "UNRESOLVED"
            cust.district_status = "UNRESOLVED"
            cust.district_mismatch = False

        if res.district_mismatch and target_dist:
            from app.models.data_quality import DataQualityIssue
            issue = db.query(DataQualityIssue).filter(
                DataQualityIssue.entity_type == "CUSTOMER",
                DataQualityIssue.entity_id == str(cust.id),
                DataQualityIssue.issue_type == "DISTRICT_MISMATCH"
            ).first()
            if not issue:
                db.add(DataQualityIssue(
                    entity_type="CUSTOMER",
                    entity_id=str(cust.id),
                    field_name="district",
                    issue_type="DISTRICT_MISMATCH",
                    raw_value=target_dist,
                    message=f"Customer ID #{cust.id}: {res.mismatch_message}",
                    suggested_fix=f"Verified as '{res.canonical_name}' via Pincode {clean_pin}"
                ))

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
        if req.pincode and req.pincode.strip() and not pin_valid:
            raise ValueError(f"Invalid PIN code '{req.pincode}'. Must be a 6-digit number.")

        res = None
        if req.district or (clean_pin and pin_valid):
            res = DistrictResolutionService.resolve_district(
                raw_district=req.district,
                pincode=clean_pin,
                state_hint=req.state,
                db=db,
                allow_postal_lookup=True
            )

        clean_po = clean_display_text(req.post_office, title_case=True) if req.post_office else None

        customers = db.query(Customer).filter(Customer.id.in_(req.customer_ids)).all()
        updated_count = 0

        for cust in customers:
            prev_pin = cust.pincode
            prev_dist = cust.district
            prev_po = cust.post_office
            prev_state = cust.state

            has_change = False

            if req.pincode is not None:
                cust.pincode = clean_pin if clean_pin else None
                has_change = True

            if req.post_office is not None:
                cust.post_office = clean_po
                has_change = True

            if req.state is not None:
                cust.state = req.state or "Kerala"
                has_change = True

            if req.district is not None or (clean_pin and pin_valid):
                if res and res.is_resolved:
                    cust.district_id = res.district_id
                    cust.district = res.canonical_name
                    cust.state = res.state or cust.state or "Kerala"
                    cust.district_resolution_source = res.resolution_source if res.resolution_source == "PINCODE" else "BULK_UPDATE"
                    cust.district_status = res.district_status
                    cust.district_mismatch = res.district_mismatch
                    has_change = True
                elif req.district is not None:
                    cust.district_id = None
                    cust.district = None
                    cust.district_resolution_source = "UNRESOLVED"
                    cust.district_status = "UNRESOLVED"
                    cust.district_mismatch = False
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
