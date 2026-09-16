from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from app.models.employee import Employee
from app.models.order import Order
from app.services.revenue_service import RevenueService
from app.utils.text_normalization import canonical_key, clean_display_text, sql_ci_like, sql_ci_equals

class EmployeeService:
    @staticmethod
    def get_employees_analytics(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "total_revenue",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        eligible_statuses = RevenueService.get_eligible_statuses(db)

        query = db.query(Employee)
        if search:
            s = f"%{canonical_key(search)}%"
            query = query.filter(
                (func.lower(func.trim(Employee.employee_name)).like(s)) |
                (func.lower(func.trim(Employee.employee_code)).like(s))
            )
        if status:
            clean_status = canonical_key(status)
            query = query.filter(func.lower(func.trim(Employee.status)) == clean_status)

        total = query.count()
        employees = query.all()


        results = []
        for emp in employees:
            emp_orders = db.query(Order).filter(
                Order.employee_id == emp.id,
                Order.order_status.in_(eligible_statuses)
            ).all()

            order_count = len(emp_orders)
            revenue = sum(float(o.total_amount or 0.0) for o in emp_orders)
            aov = (revenue / order_count) if order_count > 0 else 0.0
            cust_count = len(set(o.customer_id for o in emp_orders))

            cod_rev = sum(float(o.total_amount or 0.0) for o in emp_orders if o.payment_mode == "COD")
            prepaid_rev = sum(float(o.total_amount or 0.0) for o in emp_orders if o.payment_mode == "PREPAID")

            results.append({
                "id": emp.id,
                "employee_name": emp.employee_name,
                "employee_code": emp.employee_code,
                "status": emp.status,
                "total_orders": order_count,
                "total_revenue": float(revenue),
                "average_order_value": round(float(aov), 2),
                "customer_count": cust_count,
                "cod_revenue": float(cod_rev),
                "prepaid_revenue": float(prepaid_rev),
                "created_at": emp.created_at,
                "updated_at": emp.updated_at
            })

        reverse = (sort_order.lower() == "desc")
        results.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

        start = (page - 1) * page_size
        paginated_items = results[start:start + page_size]
        return paginated_items, total
