import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, distinct
from dateutil.relativedelta import relativedelta
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from app.models.employee import Employee
from app.models.order_item import OrderItem
from app.services.revenue_service import RevenueService
from app.utils.text_normalization import canonical_key, clean_display_text, ci_contains, ci_equals
from app.utils.district_normalization import normalize_district_name

class AnalyticsService:
    @staticmethod
    def parse_date_preset(preset: Optional[str], start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
        now = datetime.datetime.utcnow()
        today_start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
        today_end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59)

        if not preset or preset == "all":
            if start_date and end_date:
                s = datetime.datetime.fromisoformat(start_date)
                e = datetime.datetime.fromisoformat(end_date)
                if e.hour == 0 and e.minute == 0:
                    e = e.replace(hour=23, minute=59, second=59)
                return s, e
            return None, None

        p = preset.lower()
        if p == "today":
            return today_start, today_end
        elif p == "yesterday":
            y = today_start - datetime.timedelta(days=1)
            y_end = datetime.datetime(y.year, y.month, y.day, 23, 59, 59)
            return y, y_end
        elif p in ["last7days", "7d"]:
            s = today_start - datetime.timedelta(days=6)
            return s, today_end
        elif p in ["last30days", "30d"]:
            s = today_start - datetime.timedelta(days=29)
            return s, today_end
        elif p in ["thismonth", "month"]:
            s = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
            return s, today_end
        elif p in ["prevmonth", "previousmonth"]:
            first_this_month = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
            last_month_end = first_this_month - datetime.timedelta(seconds=1)
            last_month_start = datetime.datetime(last_month_end.year, last_month_end.month, 1, 0, 0, 0)
            return last_month_start, last_month_end
        elif p == "custom" and start_date and end_date:
            s = datetime.datetime.fromisoformat(start_date)
            e = datetime.datetime.fromisoformat(end_date)
            if e.hour == 0 and e.minute == 0:
                e = e.replace(hour=23, minute=59, second=59)
            return s, e

        return None, None

    @staticmethod
    def get_business_dashboard(
        db: Session,
        preset: Optional[str] = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        employee_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        product_id: Optional[int] = None,
        district: Optional[str] = None,
        pincode: Optional[str] = None,
        rfm_segment: Optional[str] = None,
        customer_id: Optional[int] = None,
        order_status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        eligible_statuses = RevenueService.get_eligible_statuses(db)
        dt_start, dt_end = AnalyticsService.parse_date_preset(preset, start_date, end_date)

        order_q = db.query(Order).join(Customer, Order.customer_id == Customer.id, isouter=True)

        # Order status filter: If user explicitly specifies order_status, filter by it; otherwise filter by revenue eligible statuses
        if order_status:
            clean_status = canonical_key(order_status)
            order_q = order_q.filter(func.lower(func.trim(Order.order_status)) == clean_status)
        else:
            eligible_norm = [canonical_key(s) for s in eligible_statuses]
            order_q = order_q.filter(func.lower(func.trim(Order.order_status)).in_(eligible_norm))

        if dt_start and dt_end:
            order_q = order_q.filter(Order.order_date >= dt_start, Order.order_date <= dt_end)
        if employee_id:
            order_q = order_q.filter(Order.employee_id == employee_id)
        if customer_id:
            order_q = order_q.filter(Order.customer_id == customer_id)
        if payment_mode:
            clean_pay = canonical_key(payment_mode)
            order_q = order_q.filter(func.lower(func.trim(Order.payment_mode)) == clean_pay)
        if district:
            clean_dist = canonical_key(district)
            order_q = order_q.filter(func.lower(func.trim(Customer.district)).like(f"%{clean_dist}%"))
        if pincode:
            clean_pin = pincode.strip()
            order_q = order_q.filter(func.trim(Customer.pincode) == clean_pin)
        if rfm_segment:
            clean_rfm = canonical_key(rfm_segment)
            order_q = order_q.filter(func.lower(func.trim(Customer.rfm_segment)) == clean_rfm)
        if product_id:
            order_q = order_q.join(OrderItem, Order.id == OrderItem.order_id).filter(OrderItem.product_id == product_id).distinct()
        if search:
            s = f"%{canonical_key(search)}%"
            order_q = order_q.filter(
                or_(
                    func.lower(func.trim(Customer.customer_name)).like(s),
                    func.lower(func.trim(Customer.contact_number)).like(s),
                    func.lower(func.trim(Order.order_number)).like(s),
                    func.lower(func.trim(Customer.district)).like(s),
                    func.lower(func.trim(Customer.pincode)).like(s)
                )
            )

        orders = order_q.all()

        total_orders = len(orders)
        total_revenue = sum(float(o.total_amount or 0.0) for o in orders)
        aov = (total_revenue / total_orders) if total_orders > 0 else 0.0
        
        # Unique customers in filtered orders
        unique_customer_ids = set(o.customer_id for o in orders)
        has_filter = bool(dt_start or employee_id or customer_id or payment_mode or district or pincode or product_id or rfm_segment or order_status or search)
        total_customers = len(unique_customer_ids) if has_filter else db.query(Customer).count()
        total_products = db.query(Product).count()

        # COD vs Prepaid breakdown (case-insensitive)
        cod_orders = [o for o in orders if canonical_key(o.payment_mode) == "cod"]
        prepaid_orders = [o for o in orders if canonical_key(o.payment_mode) in ["prepaid", "online", "upi", "card"]]

        cod_rev = sum(float(o.total_amount or 0.0) for o in cod_orders)
        prepaid_rev = sum(float(o.total_amount or 0.0) for o in prepaid_orders)
        cod_aov = round(cod_rev / len(cod_orders), 2) if len(cod_orders) > 0 else 0.0
        prepaid_aov = round(prepaid_rev / len(prepaid_orders), 2) if len(prepaid_orders) > 0 else 0.0

        payment_breakdown = [
            {
                "payment_mode": "COD",
                "revenue": float(cod_rev),
                "order_count": len(cod_orders),
                "average_order_value": cod_aov,
                "percentage_revenue": round((cod_rev / total_revenue * 100.0) if total_revenue > 0 else 0.0, 1),
                "percentage_orders": round((len(cod_orders) / total_orders * 100.0) if total_orders > 0 else 0.0, 1)
            },
            {
                "payment_mode": "PREPAID",
                "revenue": float(prepaid_rev),
                "order_count": len(prepaid_orders),
                "average_order_value": prepaid_aov,
                "percentage_revenue": round((prepaid_rev / total_revenue * 100.0) if total_revenue > 0 else 0.0, 1),
                "percentage_orders": round((len(prepaid_orders) / total_orders * 100.0) if total_orders > 0 else 0.0, 1)
            }
        ]

        # Date-wise trend points
        date_map: Dict[str, Dict[str, Any]] = {}
        for o in sorted(orders, key=lambda x: x.order_date):
            d_str = o.order_date.strftime("%Y-%m-%d")
            if d_str not in date_map:
                date_map[d_str] = {"date": d_str, "revenue": 0.0, "orders": 0}
            date_map[d_str]["revenue"] += float(o.total_amount or 0.0)
            date_map[d_str]["orders"] += 1

        revenue_trend = []
        for d_str, val in sorted(date_map.items()):
            cnt = val["orders"]
            rev = val["revenue"]
            revenue_trend.append({
                "date": d_str,
                "revenue": round(rev, 2),
                "orders": cnt,
                "aov": round(rev / cnt, 2) if cnt > 0 else 0.0
            })

        return {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "average_order_value": round(aov, 2),
            "total_customers": total_customers,
            "total_products": total_products,
            "cod_revenue": round(cod_rev, 2),
            "prepaid_revenue": round(prepaid_rev, 2),
            "cod_orders": len(cod_orders),
            "prepaid_orders": len(prepaid_orders),
            "cod_aov": cod_aov,
            "prepaid_aov": prepaid_aov,
            "revenue_trend": revenue_trend,
            "payment_breakdown": payment_breakdown
        }

    @staticmethod
    def get_district_analytics(db: Session, search: Optional[str] = None) -> List[Dict[str, Any]]:
        eligible_statuses = RevenueService.get_eligible_statuses(db)
        eligible_norm = {canonical_key(s) for s in eligible_statuses}
        customers = db.query(Customer).all()
        
        # Group districts using canonical key while preserving clean display name
        district_data: Dict[str, Dict[str, Any]] = {}
        for c in customers:
            canonical_dist, canonical_st = normalize_district_name(c.district, state_hint=c.state)
            dist_name = canonical_dist or (clean_display_text(c.district, title_case=True) if c.district else "Unassigned / Unknown")
            d_key = canonical_key(dist_name) or "unassigned"

            if search and not (ci_contains(dist_name, search) or (c.district and ci_contains(c.district, search))):
                continue

            if d_key not in district_data:
                district_data[d_key] = {
                    "district": dist_name,
                    "state": canonical_st or clean_display_text(c.state, title_case=True),
                    "customer_count": 0,
                    "total_orders": 0,
                    "total_revenue": 0.0
                }
            district_data[d_key]["customer_count"] += 1
            
            for o in c.orders:
                if canonical_key(o.order_status) in eligible_norm:
                    district_data[d_key]["total_orders"] += 1
                    district_data[d_key]["total_revenue"] += float(o.total_amount or 0.0)

        results = list(district_data.values())
        results.sort(key=lambda x: x["total_revenue"], reverse=True)
        return results

    @staticmethod
    def get_pincode_analytics(db: Session, district: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        eligible_statuses = RevenueService.get_eligible_statuses(db)
        eligible_norm = {canonical_key(s) for s in eligible_statuses}
        customers = db.query(Customer).all()
        
        target_dist_canonical, _ = normalize_district_name(district) if district else (None, None)
        target_dist_key = canonical_key(target_dist_canonical or district) if district else None

        pin_data: Dict[str, Dict[str, Any]] = {}
        for c in customers:
            c_dist_canonical, c_state_canonical = normalize_district_name(c.district, state_hint=c.state)
            c_dist_key = canonical_key(c_dist_canonical or c.district)

            if target_dist_key:
                if c_dist_key != target_dist_key and not ci_contains(c.district, district):
                    continue

            pin = (c.pincode or "Unknown").strip()
            pin_key = canonical_key(pin) or "unknown"

            if search:
                if not (ci_contains(pin, search) or (c.district and ci_contains(c.district, search)) or (c_dist_canonical and ci_contains(c_dist_canonical, search))):
                    continue

            if pin_key not in pin_data:
                display_dist = c_dist_canonical or clean_display_text(c.district, title_case=True) or "Unknown"
                pin_data[pin_key] = {
                    "pincode": pin,
                    "district": display_dist,
                    "state": c_state_canonical or clean_display_text(c.state, title_case=True),
                    "customer_count": 0,
                    "total_orders": 0,
                    "total_revenue": 0.0
                }
            pin_data[pin_key]["customer_count"] += 1
            for o in c.orders:
                if canonical_key(o.order_status) in eligible_norm:
                    pin_data[pin_key]["total_orders"] += 1
                    pin_data[pin_key]["total_revenue"] += float(o.total_amount or 0.0)

        results = list(pin_data.values())
        results.sort(key=lambda x: x["total_revenue"], reverse=True)
        return results

