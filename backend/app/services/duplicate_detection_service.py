from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.order import Order

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

        # Secondary matching: Customer Name + Pincode
        if customer_name and pincode and len(pincode) == 6:
            cust = db.query(Customer).filter(
                Customer.customer_name.ilike(customer_name.strip()),
                Customer.pincode == pincode.strip()
            ).first()
            if cust:
                return cust, "SECONDARY_NAME_PIN_MATCH"

        return None, "NO_MATCH"

    @staticmethod
    def find_matching_order(db: Session, order_number: str) -> Optional[Order]:
        if not order_number:
            return None
        return db.query(Order).filter(Order.order_number == str(order_number).strip()).first()
