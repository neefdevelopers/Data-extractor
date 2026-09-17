from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.employee import Employee
from app.models.rfm import RFMScore
from app.services.revenue_service import RevenueService
from app.services.rfm_service import RFMService
from app.utils.text_normalization import canonical_key, clean_display_text

class DeduplicationService:
    @staticmethod
    def merge_all_duplicates(db: Session) -> Dict[str, Any]:
        """
        Safely identifies and merges existing records created only due to casing or whitespace differences.
        Re-assigns foreign keys, recalculates spend/order aggregates, and preserves clean display casing.
        """
        customer_merges = DeduplicationService._merge_duplicate_customers(db)
        product_merges = DeduplicationService._merge_duplicate_products(db)
        employee_merges = DeduplicationService._merge_duplicate_employees(db)

        # Recalculate RFM scores across all customers if any customer was merged
        if customer_merges["merged_count"] > 0:
            try:
                RFMService.calculate_rfm(db)
            except Exception:
                pass

        return {
            "status": "COMPLETED",
            "customers": customer_merges,
            "products": product_merges,
            "employees": employee_merges,
            "total_merged_records": (
                customer_merges["merged_count"] +
                product_merges["merged_count"] +
                employee_merges["merged_count"]
            )
        }

    @staticmethod
    def _merge_duplicate_customers(db: Session) -> Dict[str, Any]:
        customers = db.query(Customer).all()
        
        # Group by normalized phone OR (canonical_name, clean_pin)
        phone_groups: Dict[str, List[Customer]] = {}
        name_pin_groups: Dict[Tuple[str, str], List[Customer]] = {}

        for c in customers:
            if c.normalized_contact and len(c.normalized_contact) == 10:
                phone_groups.setdefault(c.normalized_contact, []).append(c)
            elif c.customer_name and c.pincode:
                k = (canonical_key(c.customer_name), c.pincode.strip())
                if k[0] and k[1]:
                    name_pin_groups.setdefault(k, []).append(c)

        merged_count = 0
        merged_ids = set()

        eligible_statuses = RevenueService.get_eligible_statuses(db)

        # Process phone-based duplicates
        for phone, group in phone_groups.items():
            if len(group) > 1:
                primary = group[0]
                for duplicate in group[1:]:
                    if duplicate.id in merged_ids or duplicate.id == primary.id:
                        continue
                    
                    # Re-link orders to primary customer
                    db.query(Order).filter(Order.customer_id == duplicate.id).update(
                        {"customer_id": primary.id}, synchronize_session=False
                    )

                    from app.services.district_service import DistrictService

                    # Merge non-empty customer profile fields
                    if not primary.full_address and duplicate.full_address:
                        primary.full_address = duplicate.full_address
                    if not primary.pincode and duplicate.pincode:
                        primary.pincode = duplicate.pincode
                    
                    dist_to_resolve = primary.district or duplicate.district
                    if dist_to_resolve:
                        dist_obj, c_name, c_state = DistrictService.get_or_create_district(dist_to_resolve, state_hint=primary.state or duplicate.state, db=db)
                        if dist_obj:
                            primary.district_id = dist_obj.id
                            primary.district = dist_obj.canonical_name
                            primary.state = dist_obj.state or primary.state
                        elif c_name:
                            primary.district = c_name
                    
                    if not primary.state and duplicate.state:
                        primary.state = clean_display_text(duplicate.state, title_case=True)
                    if not primary.post_office and duplicate.post_office:
                        primary.post_office = clean_display_text(duplicate.post_office, title_case=True)

                    # Delete duplicate customer
                    db.delete(duplicate)
                    merged_ids.add(duplicate.id)
                    merged_count += 1

                # Recalculate lifetime metrics for primary customer
                cust_orders = db.query(Order).filter(
                    Order.customer_id == primary.id,
                    Order.order_status.in_(eligible_statuses)
                ).all()

                primary.total_orders = len(cust_orders)
                primary.total_spend = sum(float(o.total_amount or 0.0) for o in cust_orders)
                primary.average_order_value = (primary.total_spend / primary.total_orders) if primary.total_orders > 0 else 0.0
                if cust_orders:
                    primary.first_order_date = min(o.order_date for o in cust_orders)
                    primary.last_order_date = max(o.order_date for o in cust_orders)

        # Process name+pin based duplicates
        for key, group in name_pin_groups.items():
            active_group = [c for c in group if c.id not in merged_ids]
            if len(active_group) > 1:
                primary = active_group[0]
                for duplicate in active_group[1:]:
                    if duplicate.id in merged_ids or duplicate.id == primary.id:
                        continue
                    
                    db.query(Order).filter(Order.customer_id == duplicate.id).update(
                        {"customer_id": primary.id}, synchronize_session=False
                    )

                    if not primary.contact_number and duplicate.contact_number:
                        primary.contact_number = duplicate.contact_number
                        primary.normalized_contact = duplicate.normalized_contact
                    if not primary.full_address and duplicate.full_address:
                        primary.full_address = duplicate.full_address
                    
                    dist_to_resolve = primary.district or duplicate.district
                    if dist_to_resolve:
                        from app.services.district_service import DistrictService
                        dist_obj, c_name, c_state = DistrictService.get_or_create_district(dist_to_resolve, state_hint=primary.state or duplicate.state, db=db)
                        if dist_obj:
                            primary.district_id = dist_obj.id
                            primary.district = dist_obj.canonical_name
                            primary.state = dist_obj.state or primary.state
                        elif c_name:
                            primary.district = c_name

                    if not primary.state and duplicate.state:
                        primary.state = clean_display_text(duplicate.state, title_case=True)

                    db.delete(duplicate)
                    merged_ids.add(duplicate.id)
                    merged_count += 1

                cust_orders = db.query(Order).filter(
                    Order.customer_id == primary.id,
                    Order.order_status.in_(eligible_statuses)
                ).all()

                primary.total_orders = len(cust_orders)
                primary.total_spend = sum(float(o.total_amount or 0.0) for o in cust_orders)
                primary.average_order_value = (primary.total_spend / primary.total_orders) if primary.total_orders > 0 else 0.0
                if cust_orders:
                    primary.first_order_date = min(o.order_date for o in cust_orders)
                    primary.last_order_date = max(o.order_date for o in cust_orders)

        db.commit()
        return {"merged_count": merged_count, "merged_customer_ids": list(merged_ids)}

    @staticmethod
    def _merge_duplicate_products(db: Session) -> Dict[str, Any]:
        products = db.query(Product).all()
        prod_groups: Dict[str, List[Product]] = {}

        for p in products:
            k = canonical_key(p.product_name)
            if k:
                prod_groups.setdefault(k, []).append(p)

        merged_count = 0
        merged_ids = set()

        for key, group in prod_groups.items():
            if len(group) > 1:
                primary = group[0]
                for duplicate in group[1:]:
                    if duplicate.id in merged_ids or duplicate.id == primary.id:
                        continue
                    
                    # Re-link order items to primary product
                    db.query(OrderItem).filter(OrderItem.product_id == duplicate.id).update(
                        {"product_id": primary.id}, synchronize_session=False
                    )

                    if not primary.sku and duplicate.sku:
                        primary.sku = duplicate.sku
                    if not primary.category and duplicate.category:
                        primary.category = duplicate.category

                    db.delete(duplicate)
                    merged_ids.add(duplicate.id)
                    merged_count += 1

        db.commit()
        return {"merged_count": merged_count, "merged_product_ids": list(merged_ids)}

    @staticmethod
    def _merge_duplicate_employees(db: Session) -> Dict[str, Any]:
        employees = db.query(Employee).all()
        emp_groups: Dict[str, List[Employee]] = {}

        for e in employees:
            k = canonical_key(e.employee_name)
            if k:
                emp_groups.setdefault(k, []).append(e)

        merged_count = 0
        merged_ids = set()

        for key, group in emp_groups.items():
            if len(group) > 1:
                primary = group[0]
                for duplicate in group[1:]:
                    if duplicate.id in merged_ids or duplicate.id == primary.id:
                        continue
                    
                    # Re-link orders to primary employee
                    db.query(Order).filter(Order.employee_id == duplicate.id).update(
                        {"employee_id": primary.id}, synchronize_session=False
                    )

                    if not primary.employee_code and duplicate.employee_code:
                        primary.employee_code = duplicate.employee_code

                    db.delete(duplicate)
                    merged_ids.add(duplicate.id)
                    merged_count += 1

        db.commit()
        return {"merged_count": merged_count, "merged_employee_ids": list(merged_ids)}
