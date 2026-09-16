import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.customer import Customer
from app.models.employee import Employee
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderUpdate, OrderOut, OrderItemOut
from app.services.revenue_service import RevenueService
from app.services.rfm_service import RFMService

class OrderService:
    @staticmethod
    def get_orders(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        customer_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        product_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        order_status: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "order_date",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = db.query(Order).join(Customer, Order.customer_id == Customer.id, isouter=True)

        if product_id:
            query = query.join(OrderItem, Order.id == OrderItem.order_id).filter(OrderItem.product_id == product_id).distinct()
        if customer_id:
            query = query.filter(Order.customer_id == customer_id)
        if employee_id:
            query = query.filter(Order.employee_id == employee_id)
        if payment_mode:
            query = query.filter(Order.payment_mode.ilike(payment_mode.strip()))
        if order_status:
            query = query.filter(Order.order_status.ilike(order_status.strip()))
            
        if start_date:
            try:
                s_dt = datetime.datetime.fromisoformat(start_date)
                query = query.filter(Order.order_date >= s_dt)
            except Exception:
                pass
        if end_date:
            try:
                e_dt = datetime.datetime.fromisoformat(end_date)
                # set to end of day if only date provided
                if e_dt.hour == 0 and e_dt.minute == 0:
                    e_dt = e_dt.replace(hour=23, minute=59, second=59)
                query = query.filter(Order.order_date <= e_dt)
            except Exception:
                pass

        if search:
            s = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Order.order_number.ilike(s),
                    Customer.customer_name.ilike(s),
                    Customer.contact_number.ilike(s),
                    Customer.pincode.ilike(s)
                )
            )

        total = query.count()

        sort_attr = getattr(Order, sort_by, Order.order_date)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_attr))
        else:
            query = query.order_by(desc(sort_attr))

        offset = (page - 1) * page_size
        orders = query.offset(offset).limit(page_size).all()

        results = []
        for o in orders:
            items_out = [
                OrderItemOut(
                    id=it.id,
                    order_id=it.order_id,
                    product_id=it.product_id,
                    product_name=it.product_name,
                    quantity=it.quantity,
                    unit_price=it.unit_price,
                    discount=it.discount,
                    item_total=it.item_total
                ) for it in o.items
            ]
            results.append({
                "id": o.id,
                "order_number": o.order_number,
                "customer_id": o.customer_id,
                "customer_name": o.customer.customer_name if o.customer else None,
                "customer_contact": o.customer.contact_number if o.customer else None,
                "customer_district": o.customer.district if o.customer else None,
                "customer_pincode": o.customer.pincode if o.customer else None,
                "order_date": o.order_date,
                "employee_id": o.employee_id,
                "employee_name": o.employee.employee_name if o.employee else None,
                "payment_mode": o.payment_mode,
                "order_status": o.order_status,
                "subtotal": o.subtotal,
                "discount": o.discount,
                "shipping_charge": o.shipping_charge,
                "tax": o.tax,
                "total_amount": o.total_amount,
                "revenue_amount": o.revenue_amount,
                "created_at": o.created_at,
                "updated_at": o.updated_at,
                "items": items_out
            })

        return results, total

    @staticmethod
    def get_order_by_id(db: Session, order_id: int) -> Optional[Dict[str, Any]]:
        o = db.query(Order).filter(Order.id == order_id).first()
        if not o:
            return None
        items_out = [
            OrderItemOut(
                id=it.id,
                order_id=it.order_id,
                product_id=it.product_id,
                product_name=it.product_name,
                quantity=it.quantity,
                unit_price=it.unit_price,
                discount=it.discount,
                item_total=it.item_total
            ) for it in o.items
        ]
        return {
            "id": o.id,
            "order_number": o.order_number,
            "customer_id": o.customer_id,
            "customer_name": o.customer.customer_name if o.customer else None,
            "customer_contact": o.customer.contact_number if o.customer else None,
            "customer_district": o.customer.district if o.customer else None,
            "customer_pincode": o.customer.pincode if o.customer else None,
            "order_date": o.order_date,
            "employee_id": o.employee_id,
            "employee_name": o.employee.employee_name if o.employee else None,
            "payment_mode": o.payment_mode,
            "order_status": o.order_status,
            "subtotal": o.subtotal,
            "discount": o.discount,
            "shipping_charge": o.shipping_charge,
            "tax": o.tax,
            "total_amount": o.total_amount,
            "revenue_amount": o.revenue_amount,
            "created_at": o.created_at,
            "updated_at": o.updated_at,
            "items": items_out
        }
