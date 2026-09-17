from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from app.models.customer import Customer
from app.models.order import Order
from app.models.rfm import RFMScore
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerDetail, CustomerRFMInfo
from app.utils.cleaning import normalize_name, normalize_mobile, normalize_pincode, clean_address
from app.utils.text_normalization import canonical_key, clean_display_text, sql_ci_like, sql_ci_equals
from app.services.district_resolution_service import DistrictResolutionService
from app.utils.district_normalization import match_kerala_canonical_district

class CustomerService:
    @staticmethod
    def get_formatted_clipboard_text(cust: Customer) -> str:
        lines = [
            "CUSTOMER DETAILS",
            "----------------------------",
            f"Name: {cust.customer_name or ''}",
            f"Phone: {cust.contact_number or cust.normalized_contact or ''}",
            f"Address: {cust.full_address or ''}",
            f"Post Office: {cust.post_office or ''}",
            f"District: {cust.district or ''}",
            f"State: {cust.state or ''}",
            f"PIN Code: {cust.pincode or ''}",
            "",
            "CUSTOMER METRICS",
            "----------------------------",
            f"Total Orders: {cust.total_orders}",
            f"Total Lifetime Spend: ₹{cust.total_spend:,.2f}",
            f"Average Order Value: ₹{cust.average_order_value:,.2f}",
            f"RFM Segment: {cust.rfm_segment or 'N/A'}",
            f"RFM Score: {cust.rfm_score or 'N/A'}",
            f"First Order Date: {cust.first_order_date.strftime('%d-%m-%Y %H:%M') if cust.first_order_date else 'N/A'}",
            f"Last Order Date: {cust.last_order_date.strftime('%d-%m-%Y %H:%M') if cust.last_order_date else 'N/A'}"
        ]
        return "\n".join(lines)

    @staticmethod
    def get_customers(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        district: Optional[str] = None,
        post_office: Optional[str] = None,
        pincode: Optional[str] = None,
        rfm_segment: Optional[str] = None,
        min_orders: Optional[int] = None,
        max_orders: Optional[int] = None,
        min_spend: Optional[float] = None,
        max_spend: Optional[float] = None,
        sort_by: str = "id",
        sort_order: str = "desc"
    ) -> Tuple[List[Customer], int]:
        query = db.query(Customer)

        if search:
            search_clean = canonical_key(search)
            s = f"%{search_clean}%"
            search_conds = [
                func.lower(func.trim(Customer.customer_name)).like(s),
                func.lower(func.trim(Customer.contact_number)).like(s),
                func.lower(func.trim(Customer.normalized_contact)).like(s),
                func.lower(func.trim(Customer.pincode)).like(s),
                func.lower(func.trim(Customer.district)).like(s),
                func.lower(func.trim(Customer.post_office)).like(s),
                func.lower(func.trim(Customer.full_address)).like(s)
            ]
            search_dist_match = match_kerala_canonical_district(search)
            if search_dist_match:
                c_name = search_dist_match[0]
                search_conds.append(func.lower(func.trim(Customer.district)) == c_name.lower())
                dist_res = DistrictResolutionService.resolve_district(search, db=db, allow_postal_lookup=False)
                if dist_res.district_id:
                    search_conds.append(Customer.district_id == dist_res.district_id)
            query = query.filter(or_(*search_conds))

        if district:
            dist_res = DistrictResolutionService.resolve_district(district, db=db, allow_postal_lookup=False)
            if dist_res.is_resolved:
                conds = [func.lower(func.trim(Customer.district)) == dist_res.canonical_name.lower()]
                if dist_res.district_id:
                    conds.append(Customer.district_id == dist_res.district_id)
                query = query.filter(or_(*conds))
            else:
                clean_dist = canonical_key(district)
                query = query.filter(func.lower(func.trim(Customer.district)).like(f"%{clean_dist}%"))

        if post_office:
            clean_po = canonical_key(post_office)
            query = query.filter(func.lower(func.trim(Customer.post_office)).like(f"%{clean_po}%"))
        if pincode:
            clean_pin = pincode.strip()
            query = query.filter(func.trim(Customer.pincode) == clean_pin)
        if rfm_segment:
            clean_rfm = canonical_key(rfm_segment)
            query = query.filter(func.lower(func.trim(Customer.rfm_segment)) == clean_rfm)
        if min_orders is not None:
            query = query.filter(Customer.total_orders >= min_orders)
        if max_orders is not None:
            query = query.filter(Customer.total_orders <= max_orders)
        if min_spend is not None:
            query = query.filter(Customer.total_spend >= min_spend)
        if max_spend is not None:
            query = query.filter(Customer.total_spend <= max_spend)

        total = query.count()

        # Sorting
        sort_attr = getattr(Customer, sort_by, Customer.id)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_attr))
        else:
            query = query.order_by(desc(sort_attr))

        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        return items, total

    @staticmethod
    def get_customer_by_id(db: Session, customer_id: int) -> Optional[CustomerDetail]:
        cust = db.query(Customer).filter(Customer.id == customer_id).first()
        if not cust:
            return None
            
        rfm_info = None
        if cust.rfm_details:
            rfm_info = CustomerRFMInfo(
                recency_days=cust.rfm_details.recency_days,
                frequency=cust.rfm_details.frequency,
                monetary_value=cust.rfm_details.monetary_value,
                r_score=cust.rfm_details.r_score,
                f_score=cust.rfm_details.f_score,
                m_score=cust.rfm_details.m_score,
                rfm_score=cust.rfm_details.rfm_score,
                segment=cust.rfm_details.segment
            )
            
        clipboard_text = CustomerService.get_formatted_clipboard_text(cust)

        # Aggregate products purchased
        from app.models.order_item import OrderItem
        from app.models.product import Product
        from app.schemas.customer import CustomerProductSummary

        prod_rows = (
            db.query(
                OrderItem.product_name,
                Product.sku,
                Product.category,
                func.sum(OrderItem.quantity).label("total_qty"),
                func.sum(OrderItem.item_total).label("total_spend"),
                func.max(Order.order_date).label("last_purchased")
            )
            .join(Order, OrderItem.order_id == Order.id)
            .outerjoin(Product, OrderItem.product_id == Product.id)
            .filter(Order.customer_id == customer_id)
            .group_by(OrderItem.product_name, Product.sku, Product.category)
            .order_by(desc("total_spend"))
            .all()
        )

        purchased_products = [
            CustomerProductSummary(
                product_name=r.product_name,
                sku=r.sku,
                category=r.category,
                total_quantity=int(r.total_qty or 0),
                total_spend=float(r.total_spend or 0.0),
                last_purchased_date=r.last_purchased
            )
            for r in prod_rows
        ]

        return CustomerDetail(
            id=cust.id,
            customer_id_str=cust.customer_id_str,
            customer_name=cust.customer_name,
            contact_number=cust.contact_number,
            normalized_contact=cust.normalized_contact,
            full_address=cust.full_address,
            pincode=cust.pincode,
            post_office=cust.post_office,
            district_id=cust.district_id,
            district=cust.district,
            state=cust.state,
            district_resolution_source=getattr(cust, "district_resolution_source", "UNRESOLVED") or "UNRESOLVED",
            district_status=getattr(cust, "district_status", "UNRESOLVED") or "UNRESOLVED",
            first_order_date=cust.first_order_date,
            last_order_date=cust.last_order_date,
            total_orders=cust.total_orders,
            total_spend=cust.total_spend,
            average_order_value=cust.average_order_value,
            rfm_score=cust.rfm_score,
            rfm_segment=cust.rfm_segment,
            created_at=cust.created_at,
            updated_at=cust.updated_at,
            rfm_details=rfm_info,
            formatted_clipboard_text=clipboard_text,
            purchased_products=purchased_products
        )

    @staticmethod
    def create_customer(
        db: Session,
        data: CustomerCreate
    ) -> Customer:
        norm_name = normalize_name(data.customer_name)
        norm_phone, phone_valid = normalize_mobile(data.contact_number) if data.contact_number else (None, False)
        clean_addr = clean_address(data.full_address) if data.full_address else None
        clean_po = clean_display_text(data.post_office, title_case=True) if data.post_office else None
        clean_pin, pin_valid = normalize_pincode(data.pincode) if data.pincode else (None, False)

        # Automatic District Resolution based on Pincode-first priority
        dist_res = DistrictResolutionService.resolve_district(
            raw_district=data.source_district or data.district,
            pincode=clean_pin if pin_valid else data.pincode,
            source_post_office=clean_po,
            address_hint=clean_addr,
            state_hint=data.state,
            db=db,
            allow_postal_lookup=True
        )

        cust = Customer(
            customer_id_str=data.customer_id_str,
            customer_name=norm_name or data.customer_name,
            contact_number=data.contact_number,
            normalized_contact=norm_phone,
            full_address=clean_addr,
            pincode=clean_pin if pin_valid else (data.pincode if data.pincode else None),
            post_office=clean_po,
            source_district=data.source_district or data.district,
            district_id=dist_res.district_id if dist_res.is_resolved else None,
            district=dist_res.canonical_name if dist_res.is_resolved else None,
            district_resolution_source=dist_res.resolution_source,
            district_status=dist_res.district_status,
            district_mismatch=dist_res.district_mismatch,
            state=dist_res.state or data.state or "Kerala"
        )
        db.add(cust)
        db.commit()
        db.refresh(cust)
        return cust

    @staticmethod
    def update_customer(
        db: Session,
        customer_id: int,
        data: CustomerUpdate
    ) -> Customer:
        cust = db.query(Customer).filter(Customer.id == customer_id).first()
        if not cust:
            raise ValueError(f"Customer with ID {customer_id} not found.")

        if data.customer_name is not None:
            norm_name = normalize_name(data.customer_name)
            cust.customer_name = norm_name or data.customer_name
        if data.contact_number is not None:
            norm_phone, phone_valid = normalize_mobile(data.contact_number)
            cust.contact_number = data.contact_number
            cust.normalized_contact = norm_phone
        if data.full_address is not None:
            cust.full_address = clean_address(data.full_address)
        if data.post_office is not None:
            cust.post_office = clean_display_text(data.post_office, title_case=True)

        # Determine target location parameters for recalculation
        target_pin = data.pincode if data.pincode is not None else cust.pincode
        target_dist = data.district if data.district is not None else (data.source_district or cust.source_district or cust.district)
        target_po = data.post_office if data.post_office is not None else cust.post_office
        target_state = data.state if data.state is not None else cust.state

        clean_pin, pin_valid = normalize_pincode(target_pin) if target_pin else (None, False)

        # Automatic District Resolution based on Pincode-first priority
        dist_res = DistrictResolutionService.resolve_district(
            raw_district=target_dist,
            pincode=clean_pin if pin_valid else target_pin,
            source_post_office=target_po,
            address_hint=cust.full_address,
            state_hint=target_state,
            db=db,
            allow_postal_lookup=True
        )

        cust.pincode = clean_pin if pin_valid else (target_pin if target_pin else None)
        if target_dist and not cust.source_district:
            cust.source_district = target_dist

        if dist_res.is_resolved:
            cust.district_id = dist_res.district_id
            cust.district = dist_res.canonical_name
            cust.state = dist_res.state or target_state or "Kerala"
            cust.district_resolution_source = dist_res.resolution_source
            cust.district_status = dist_res.district_status
            cust.district_mismatch = dist_res.district_mismatch
        else:
            cust.district_id = None
            cust.district = None
            cust.state = target_state or "Kerala"
            cust.district_resolution_source = "UNRESOLVED"
            cust.district_status = "UNRESOLVED"
            cust.district_mismatch = False

        if dist_res.district_mismatch and target_dist:
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
                    message=f"Customer ID #{cust.id}: {dist_res.mismatch_message}",
                    suggested_fix=f"Verified as '{dist_res.canonical_name}' via Pincode {clean_pin}"
                ))

        db.commit()
        db.refresh(cust)
        return cust

