import json
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.customer import Customer
from app.models.settings import SystemSetting

DEFAULT_REVENUE_RULES = {
    "delivered_eligible": True,
    "completed_eligible": True,
    "cancelled_eligible": False,
    "returned_eligible": False,
    "refunded_eligible": False,
    "pending_eligible": False
}

class RevenueService:
    @staticmethod
    def get_revenue_rules(db: Session) -> Dict[str, bool]:
        setting = db.query(SystemSetting).filter(SystemSetting.key == "revenue_rules").first()
        if setting:
            try:
                rules = json.loads(setting.value)
                return {**DEFAULT_REVENUE_RULES, **rules}
            except Exception:
                pass
        return DEFAULT_REVENUE_RULES

    @staticmethod
    def is_revenue_eligible(status: Optional[str], rules: Optional[Dict[str, bool]] = None) -> bool:
        if not status:
            return False
        st = status.upper().strip()
        r = rules or DEFAULT_REVENUE_RULES
        
        if st in ["DELIVERED"] and r.get("delivered_eligible", True):
            return True
        if st in ["COMPLETED"] and r.get("completed_eligible", True):
            return True
        if st in ["CANCELLED", "CANCELED"] and r.get("cancelled_eligible", False):
            return True
        if st in ["RETURNED", "RTO"] and r.get("returned_eligible", False):
            return True
        if st in ["REFUNDED"] and r.get("refunded_eligible", False):
            return True
        if st in ["PENDING", "PROCESSING"] and r.get("pending_eligible", False):
            return True
        return False

    @staticmethod
    def get_eligible_statuses(db: Session) -> List[str]:
        rules = RevenueService.get_revenue_rules(db)
        eligible = []
        if rules.get("delivered_eligible", True):
            eligible.append("DELIVERED")
        if rules.get("completed_eligible", True):
            eligible.append("COMPLETED")
        if rules.get("cancelled_eligible", False):
            eligible.append("CANCELLED")
        if rules.get("returned_eligible", False):
            eligible.append("RETURNED")
        if rules.get("refunded_eligible", False):
            eligible.append("REFUNDED")
        if rules.get("pending_eligible", False):
            eligible.append("PENDING")
        return eligible

    @staticmethod
    def calculate_order_revenue(order: Order, db: Optional[Session] = None) -> float:
        rules = RevenueService.get_revenue_rules(db) if db else DEFAULT_REVENUE_RULES
        if RevenueService.is_revenue_eligible(order.order_status, rules):
            return float(order.total_amount or 0.0)
        return 0.0

    @staticmethod
    def calculate_customer_revenue(customer_id: int, db: Session) -> Dict[str, Any]:
        eligible_statuses = RevenueService.get_eligible_statuses(db)
        orders = db.query(Order).filter(
            Order.customer_id == customer_id,
            Order.order_status.in_(eligible_statuses)
        ).all()
        
        total_orders = len(orders)
        total_spend = sum(o.total_amount or 0.0 for o in orders)
        aov = (total_spend / total_orders) if total_orders > 0 else 0.0
        
        return {
            "total_orders": total_orders,
            "total_spend": total_spend,
            "average_order_value": aov
        }
