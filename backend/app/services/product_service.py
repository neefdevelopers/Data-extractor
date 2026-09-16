from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem
from app.services.revenue_service import RevenueService
from app.utils.text_normalization import canonical_key, clean_display_text, sql_ci_like, sql_ci_equals

class ProductService:
    @staticmethod
    def get_products_analytics(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: str = "total_revenue",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        eligible_statuses = RevenueService.get_eligible_statuses(db)

        # Calculate total platform qualifying product items revenue for percentage contribution
        total_products_revenue = db.query(
            func.coalesce(func.sum(OrderItem.item_total), 0.0)
        ).join(Order, OrderItem.order_id == Order.id).filter(Order.order_status.in_(eligible_statuses)).scalar() or 1.0

        query = db.query(Product)
        if search:
            s = f"%{canonical_key(search)}%"
            query = query.filter(
                or_(
                    func.lower(func.trim(Product.product_name)).like(s),
                    func.lower(func.trim(Product.sku)).like(s),
                    func.lower(func.trim(Product.category)).like(s)
                )
            )
        if category:
            c_key = canonical_key(category)
            query = query.filter(func.lower(func.trim(Product.category)).like(f"%{c_key}%"))

        total = query.count()
        products = query.all()


        results = []
        for p in products:
            # Query order items connected to eligible orders
            items_query = db.query(OrderItem).join(Order, OrderItem.order_id == Order.id).filter(
                OrderItem.product_id == p.id,
                Order.order_status.in_(eligible_statuses)
            )

            units_sold = items_query.with_entities(func.coalesce(func.sum(OrderItem.quantity), 0)).scalar() or 0
            orders_count = items_query.with_entities(func.count(func.distinct(OrderItem.order_id))).scalar() or 0
            revenue = items_query.with_entities(func.coalesce(func.sum(OrderItem.item_total), 0.0)).scalar() or 0.0
            avg_rev = (revenue / orders_count) if orders_count > 0 else 0.0
            contrib = min((revenue / total_products_revenue * 100.0) if total_products_revenue > 0 else 0.0, 100.0)

            results.append({
                "id": p.id,
                "product_name": p.product_name,
                "sku": p.sku,
                "category": p.category,
                "price": p.price,
                "total_units_sold": int(units_sold),
                "total_orders": int(orders_count),
                "total_revenue": float(revenue),
                "avg_revenue_per_order": float(avg_rev),
                "revenue_contribution_pct": round(float(contrib), 2),
                "created_at": p.created_at,
                "updated_at": p.updated_at
            })

        # Python sorting for aggregated fields
        reverse = (sort_order.lower() == "desc")
        results.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

        start = (page - 1) * page_size
        paginated_items = results[start:start + page_size]
        return paginated_items, total
