from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.customer import Customer
from app.models.order import Order
from app.utils.text_normalization import canonical_key, sql_ci_equals

class DuplicateDetectionService:
    @staticmethod
    def find_matching_customer(
        db: Session,
        normalized_contact: Optional[str] = None,
        customer_name: Optional[str] = None,
        pincode: Optional[str] = None
    ) -> Tuple[Optional[Customer], str]:
        """
        Finds existing customer using primary (phone) or secondary (name + pin) matching.
        Returns (Customer or None, match_rule_used)
        """
        # Primary matching: Normalized Contact Number (10 digits)
        if normalized_contact and len(normalized_contact) == 10:
            cust = db.query(Customer).filter(
                Customer.normalized_contact == normalized_contact
            ).first()
            if cust:
                return cust, "PRIMARY_PHONE_MATCH"

        # Secondary matching: Customer Name + Pincode (case-insensitive & trimmed)
        if customer_name and pincode and len(pincode.strip()) == 6:
            clean_name = canonical_key(customer_name)
            clean_pin = pincode.strip()
            if clean_name:
                cust = db.query(Customer).filter(
                    func.lower(func.trim(Customer.customer_name)) == clean_name,
                    func.trim(Customer.pincode) == clean_pin
                ).first()
                if cust:
                    return cust, "SECONDARY_NAME_PIN_MATCH"

        return None, "NO_MATCH"

    @staticmethod
    def find_matching_order(db: Session, order_number: str) -> Optional[Order]:
        if not order_number:
            return None
        clean_ord = canonical_key(order_number)
        return db.query(Order).filter(func.lower(func.trim(Order.order_number)) == clean_ord).first()

