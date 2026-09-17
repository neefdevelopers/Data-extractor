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
from app.services.district_resolution_service import DistrictResolutionService
from app.utils.text_normalization import canonical_key, clean_display_text, ci_contains, ci_equals
from app.utils.district_normalization import match_kerala_canonical_district, normalize_district_name

class AnalyticsService:
    @staticmethod
    def parse_date_preset(preset: Optional[str], start_date: Optional[str] = None, end_date: Optional[str] = None) -> Tuple[Optional[datetime.datetime], Optional[datetime.datetime]]:
        import calendar
        now = datetime.datetime.now()
        today_start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
        today_end = datetime.datetime(now.year, now.month, now.day, 23, 59, 59)

        def _parse_iso(d_str: Optional[str], is_end: bool = False) -> Optional[datetime.datetime]:
            if not d_str or not str(d_str).strip():
                return None
            val = str(d_str).strip()
            try:
                dt = datetime.datetime.fromisoformat(val)
                if is_end and dt.hour == 0 and dt.minute == 0 and dt.second == 0:
                    dt = dt.replace(hour=23, minute=59, second=59)
                return dt
            except Exception:
                try:
                    d = datetime.date.fromisoformat(val)
                    if is_end:
                        return datetime.datetime(d.year, d.month, d.day, 23, 59, 59)
                    return datetime.datetime(d.year, d.month, d.day, 0, 0, 0)
                except Exception:
                    return None

        if not preset or preset.strip().lower() in ["all", "all_time", "alltime"]:
            s = _parse_iso(start_date, is_end=False)
            e = _parse_iso(end_date, is_end=True)
            return s, e

        p = preset.strip().lower().replace("_", "").replace("-", "")

        if p in ["today", "1d"]:
            return today_start, today_end
        elif p in ["yesterday"]:
            y = today_start - datetime.timedelta(days=1)
            y_end = datetime.datetime(y.year, y.month, y.day, 23, 59, 59)
            return y, y_end
        elif p in ["last7days", "7d", "last7d", "7days"]:
            s = today_start - datetime.timedelta(days=6)
            return s, today_end
        elif p in ["last30days", "30d", "last30d", "30days"]:
            s = today_start - datetime.timedelta(days=29)
            return s, today_end
        elif p in ["thismonth", "month", "thism", "currentmonth"]:
            last_day = calendar.monthrange(now.year, now.month)[1]
            s = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
            e = datetime.datetime(now.year, now.month, last_day, 23, 59, 59)
            return s, e
        elif p in ["prevmonth", "previousmonth", "lastmonth", "lastm", "prevm"]:
            first_this_month = datetime.datetime(now.year, now.month, 1, 0, 0, 0)
            last_month_end = first_this_month - datetime.timedelta(seconds=1)
            last_month_start = datetime.datetime(last_month_end.year, last_month_end.month, 1, 0, 0, 0)
            return last_month_start, last_month_end
        elif p in ["thisyear", "year", "currentyear"]:
            s = datetime.datetime(now.year, 1, 1, 0, 0, 0)
            e = datetime.datetime(now.year, 12, 31, 23, 59, 59)
            return s, e
        elif p in ["lastyear", "prevyear", "previousyear"]:
            s = datetime.datetime(now.year - 1, 1, 1, 0, 0, 0)
            e = datetime.datetime(now.year - 1, 12, 31, 23, 59, 59)
            return s, e
        elif p in ["custom"] or (start_date or end_date):
            s = _parse_iso(start_date, is_end=False)
            e = _parse_iso(end_date, is_end=True)
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
        order_q = AnalyticsService._build_filtered_orders_query(
            db=db,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id,
            payment_mode=payment_mode,
            product_id=product_id,
            district=district,
            pincode=pincode,
            rfm_segment=rfm_segment,
            customer_id=customer_id,
            order_status=order_status,
            search=search
        )
        orders = order_q.all()

        total_orders = len(orders)
        total_revenue = sum(float(o.total_amount or 0.0) for o in orders)
        aov = (total_revenue / total_orders) if total_orders > 0 else 0.0
        
        # Unique customers in filtered orders
        dt_start, dt_end = AnalyticsService.parse_date_preset(preset, start_date, end_date)
        unique_customer_ids = set(o.customer_id for o in orders if o.customer_id)
        has_filter = bool(dt_start or dt_end or employee_id or customer_id or payment_mode or district or pincode or product_id or rfm_segment or order_status or search)
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
    def _build_filtered_orders_query(
        db: Session,
        preset: Optional[str] = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        employee_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        product_id: Optional[int] = None,
        district: Optional[str] = None,
        district_id: Optional[int] = None,
        pincode: Optional[str] = None,
        post_office: Optional[str] = None,
        rfm_segment: Optional[str] = None,
        customer_id: Optional[int] = None,
        order_status: Optional[str] = None,
        search: Optional[str] = None
    ):
        eligible_statuses = RevenueService.get_eligible_statuses(db)
        dt_start, dt_end = AnalyticsService.parse_date_preset(preset, start_date, end_date)

        order_q = db.query(Order).join(Customer, Order.customer_id == Customer.id, isouter=True)

        if order_status:
            clean_status = canonical_key(order_status)
            order_q = order_q.filter(func.lower(func.trim(Order.order_status)) == clean_status)
        else:
            eligible_norm = [canonical_key(s) for s in eligible_statuses]
            order_q = order_q.filter(func.lower(func.trim(Order.order_status)).in_(eligible_norm))

        if dt_start and dt_end:
            order_q = order_q.filter(Order.order_date >= dt_start, Order.order_date <= dt_end)
        elif dt_start:
            order_q = order_q.filter(Order.order_date >= dt_start)
        elif dt_end:
            order_q = order_q.filter(Order.order_date <= dt_end)
        if employee_id:
            order_q = order_q.filter(Order.employee_id == employee_id)
        if customer_id:
            order_q = order_q.filter(Order.customer_id == customer_id)
        if payment_mode:
            clean_pay = canonical_key(payment_mode)
            order_q = order_q.filter(func.lower(func.trim(Order.payment_mode)) == clean_pay)
        
        if district_id:
            order_q = order_q.filter(Customer.district_id == district_id)
        elif district:
            clean_dist = district.strip()
            if clean_dist.lower() in ["unknown", "unknown district", "unassigned"]:
                order_q = order_q.filter(or_(Customer.district == None, Customer.district == "Unknown", Customer.district == ""))
            else:
                dist_res = DistrictResolutionService.resolve_district(clean_dist, db=db, allow_postal_lookup=False)
                if dist_res.is_resolved:
                    conds = [func.lower(func.trim(Customer.district)) == dist_res.canonical_name.lower()]
                    if dist_res.district_id:
                        conds.append(Customer.district_id == dist_res.district_id)
                    order_q = order_q.filter(or_(*conds))
                else:
                    d_key = canonical_key(clean_dist)
                    order_q = order_q.filter(func.lower(func.trim(Customer.district)).like(f"%{d_key}%"))

        if pincode:
            clean_pin = pincode.strip()
            if clean_pin.lower() in ["unknown", "unknown pincode"]:
                order_q = order_q.filter(or_(Customer.pincode == None, Customer.pincode == "Unknown", Customer.pincode == ""))
            else:
                order_q = order_q.filter(func.trim(Customer.pincode) == clean_pin)

        if post_office:
            clean_po = post_office.strip()
            if clean_po.lower() in ["unknown", "unknown post office"]:
                order_q = order_q.filter(or_(Customer.post_office == None, Customer.post_office == "Unknown", Customer.post_office == ""))
            else:
                order_q = order_q.filter(func.lower(func.trim(Customer.post_office)) == canonical_key(clean_po))

        if rfm_segment:
            clean_rfm = canonical_key(rfm_segment)
            order_q = order_q.filter(func.lower(func.trim(Customer.rfm_segment)) == clean_rfm)
        if product_id:
            order_q = order_q.join(OrderItem, Order.id == OrderItem.order_id).filter(OrderItem.product_id == product_id).distinct()

        if search:
            search_clean = canonical_key(search)
            s = f"%{search_clean}%"
            search_conds = [
                func.lower(func.trim(Customer.customer_name)).like(s),
                func.lower(func.trim(Customer.contact_number)).like(s),
                func.lower(func.trim(Order.order_number)).like(s),
                func.lower(func.trim(Customer.district)).like(s),
                func.lower(func.trim(Customer.pincode)).like(s),
                func.lower(func.trim(Customer.post_office)).like(s)
            ]
            search_dist_match = match_kerala_canonical_district(search)
            if search_dist_match:
                c_name = search_dist_match[0]
                search_conds.append(func.lower(func.trim(Customer.district)) == c_name.lower())
                dist_res = DistrictResolutionService.resolve_district(search, db=db, allow_postal_lookup=False)
                if dist_res.district_id:
                    search_conds.append(Customer.district_id == dist_res.district_id)
            order_q = order_q.filter(or_(*search_conds))

        return order_q

    @staticmethod
    def get_geographic_overview(
        db: Session,
        preset: Optional[str] = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        employee_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        product_id: Optional[int] = None,
        district: Optional[str] = None,
        district_id: Optional[int] = None,
        pincode: Optional[str] = None,
        post_office: Optional[str] = None,
        rfm_segment: Optional[str] = None,
        customer_id: Optional[int] = None,
        order_status: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        order_q = AnalyticsService._build_filtered_orders_query(
            db=db,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id,
            payment_mode=payment_mode,
            product_id=product_id,
            district=district,
            district_id=district_id,
            pincode=pincode,
            post_office=post_office,
            rfm_segment=rfm_segment,
            customer_id=customer_id,
            order_status=order_status,
            search=search
        )
        orders = order_q.all()
        total_orders = len(orders)
        total_revenue = sum(float(o.total_amount or 0.0) for o in orders)
        aov = (total_revenue / total_orders) if total_orders > 0 else 0.0
        unique_customers = set(o.customer_id for o in orders if o.customer_id)
        total_customers = len(unique_customers)

        return {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "total_customers": total_customers,
            "average_order_value": round(aov, 2)
        }

    @staticmethod
    def get_district_analytics(
        db: Session,
        preset: Optional[str] = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        employee_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        product_id: Optional[int] = None,
        district: Optional[str] = None,
        district_id: Optional[int] = None,
        pincode: Optional[str] = None,
        post_office: Optional[str] = None,
        rfm_segment: Optional[str] = None,
        customer_id: Optional[int] = None,
        order_status: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "revenue",
        sort_order: Optional[str] = "desc"
    ) -> List[Dict[str, Any]]:
        order_q = AnalyticsService._build_filtered_orders_query(
            db=db,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id,
            payment_mode=payment_mode,
            product_id=product_id,
            district=district,
            district_id=district_id,
            pincode=pincode,
            post_office=post_office,
            rfm_segment=rfm_segment,
            customer_id=customer_id,
            order_status=order_status,
            search=search
        )
        orders = order_q.all()

        district_data: Dict[str, Dict[str, Any]] = {}
        cust_map: Dict[str, Set[int]] = {}

        for o in orders:
            c = o.customer
            if c:
                if c.district_master:
                    d_id = c.district_master.id
                    d_name = c.district_master.canonical_name
                    d_key = c.district_master.normalized_key
                    d_state = c.district_master.state
                elif c.district and c.district.strip():
                    dist_res = DistrictResolutionService.resolve_district(c.district, pincode=c.pincode, db=db, allow_postal_lookup=False)
                    if dist_res.is_resolved:
                        d_id = dist_res.district_id
                        d_name = dist_res.canonical_name
                        d_key = canonical_key(dist_res.canonical_name)
                        d_state = dist_res.state or "Kerala"
                    else:
                        d_id = None
                        d_name = "Unknown District"
                        d_key = "unknown_district"
                        d_state = "Kerala"
                else:
                    d_id = None
                    d_name = "Unknown District"
                    d_key = "unknown_district"
                    d_state = "Kerala"
            else:
                d_id = None
                d_name = "Unknown District"
                d_key = "unknown_district"
                d_state = "Kerala"

            if d_key not in district_data:
                district_data[d_key] = {
                    "district_id": d_id,
                    "district": d_name,
                    "state": d_state,
                    "customer_count": 0,
                    "total_orders": 0,
                    "total_revenue": 0.0
                }
                cust_map[d_key] = set()

            district_data[d_key]["total_orders"] += 1
            district_data[d_key]["total_revenue"] += float(o.total_amount or 0.0)
            if o.customer_id:
                cust_map[d_key].add(o.customer_id)

        if not orders and (preset == "all" or not preset) and not start_date and not end_date and not product_id and not employee_id and not payment_mode and not order_status:
            cust_q = db.query(Customer)
            if district_id:
                cust_q = cust_q.filter(Customer.district_id == district_id)
            elif district:
                clean_dist = district.strip()
                dist_res = DistrictResolutionService.resolve_district(clean_dist, db=db, allow_postal_lookup=False)
                if dist_res.is_resolved:
                    conds = [func.lower(func.trim(Customer.district)) == dist_res.canonical_name.lower()]
                    if dist_res.district_id:
                        conds.append(Customer.district_id == dist_res.district_id)
                    cust_q = cust_q.filter(or_(*conds))
                else:
                    d_key = canonical_key(clean_dist)
                    cust_q = cust_q.filter(func.lower(func.trim(Customer.district)).like(f"%{d_key}%"))
            if pincode:
                cust_q = cust_q.filter(func.trim(Customer.pincode) == pincode.strip())
            if search:
                search_clean = canonical_key(search)
                s = f"%{search_clean}%"
                search_conds = [
                    func.lower(func.trim(Customer.customer_name)).like(s),
                    func.lower(func.trim(Customer.contact_number)).like(s),
                    func.lower(func.trim(Customer.district)).like(s),
                    func.lower(func.trim(Customer.pincode)).like(s),
                    func.lower(func.trim(Customer.post_office)).like(s)
                ]
                search_dist_match = match_kerala_canonical_district(search)
                if search_dist_match:
                    search_conds.append(func.lower(func.trim(Customer.district)) == search_dist_match[0].lower())
                cust_q = cust_q.filter(or_(*search_conds))

            for c in cust_q.all():
                if c.district_master:
                    d_id = c.district_master.id
                    d_name = c.district_master.canonical_name
                    d_key = c.district_master.normalized_key
                    d_state = c.district_master.state
                elif c.district and c.district.strip():
                    dist_res = DistrictResolutionService.resolve_district(c.district, pincode=c.pincode, db=db, allow_postal_lookup=False)
                    if dist_res.is_resolved:
                        d_id = dist_res.district_id
                        d_name = dist_res.canonical_name
                        d_key = canonical_key(dist_res.canonical_name)
                        d_state = dist_res.state or "Kerala"
                    else:
                        d_id = None
                        d_name = "Unknown District"
                        d_key = "unknown_district"
                        d_state = "Kerala"
                else:
                    d_id = None
                    d_name = "Unknown District"
                    d_key = "unknown_district"
                    d_state = "Kerala"

                if d_key not in district_data:
                    district_data[d_key] = {
                        "district_id": d_id,
                        "district": d_name,
                        "state": d_state,
                        "customer_count": 0,
                        "total_orders": 0,
                        "total_revenue": 0.0
                    }
                    cust_map[d_key] = set()
                district_data[d_key]["total_orders"] += (c.total_orders or 0)
                district_data[d_key]["total_revenue"] += float(c.total_spend or 0.0)
                cust_map[d_key].add(c.id)

        for d_key, data in district_data.items():
            data["customer_count"] = len(cust_map[d_key])
            data["total_revenue"] = round(data["total_revenue"], 2)

        results = [
            d for d in district_data.values()
            if d.get("total_orders", 0) > 0 or d.get("total_revenue", 0) > 0 or d.get("customer_count", 0) > 0
        ]
        reverse = (sort_order or "desc").lower() != "asc"
        if sort_by == "orders":
            results.sort(key=lambda x: x["total_orders"], reverse=reverse)
        elif sort_by == "customers":
            results.sort(key=lambda x: x["customer_count"], reverse=reverse)
        elif sort_by == "district" or sort_by == "name":
            results.sort(key=lambda x: x["district"].lower(), reverse=not reverse)
        else:
            results.sort(key=lambda x: x["total_revenue"], reverse=reverse)

        return results

    @staticmethod
    def get_pincode_analytics(
        db: Session,
        preset: Optional[str] = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        employee_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        product_id: Optional[int] = None,
        district: Optional[str] = None,
        district_id: Optional[int] = None,
        pincode: Optional[str] = None,
        post_office: Optional[str] = None,
        rfm_segment: Optional[str] = None,
        customer_id: Optional[int] = None,
        order_status: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        sort_by: Optional[str] = "revenue",
        sort_order: Optional[str] = "desc"
    ) -> List[Dict[str, Any]]:
        order_q = AnalyticsService._build_filtered_orders_query(
            db=db,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id,
            payment_mode=payment_mode,
            product_id=product_id,
            district=district,
            district_id=district_id,
            pincode=pincode,
            post_office=post_office,
            rfm_segment=rfm_segment,
            customer_id=customer_id,
            order_status=order_status,
            search=search
        )
        orders = order_q.all()

        pin_data: Dict[str, Dict[str, Any]] = {}
        cust_map: Dict[str, Set[int]] = {}

        for o in orders:
            c = o.customer
            pin = (c.pincode or "").strip() if c else ""
            pin_display = pin if (pin and pin.isdigit() and len(pin) == 6) else "Unknown Pincode"
            pin_key = pin_display.lower()

            if c:
                if c.district_master:
                    d_name = c.district_master.canonical_name
                    d_state = c.district_master.state
                elif c.district and c.district.strip():
                    dist_res = DistrictResolutionService.resolve_district(c.district, pincode=c.pincode, db=db, allow_postal_lookup=False)
                    d_name = dist_res.canonical_name if dist_res.is_resolved else "Unknown District"
                    d_state = dist_res.state or "Kerala"
                else:
                    d_name = "Unknown District"
                    d_state = "Kerala"
            else:
                d_name = "Unknown District"
                d_state = "Kerala"

            if pin_key not in pin_data:
                pin_data[pin_key] = {
                    "pincode": pin_display,
                    "district": d_name,
                    "state": d_state,
                    "customer_count": 0,
                    "total_orders": 0,
                    "total_revenue": 0.0
                }
                cust_map[pin_key] = set()

            pin_data[pin_key]["total_orders"] += 1
            pin_data[pin_key]["total_revenue"] += float(o.total_amount or 0.0)
            if o.customer_id:
                cust_map[pin_key].add(o.customer_id)

        if not orders and (preset == "all" or not preset) and not start_date and not end_date and not product_id and not employee_id and not payment_mode and not order_status:
            cust_q = db.query(Customer)
            if district_id:
                cust_q = cust_q.filter(Customer.district_id == district_id)
            elif district:
                clean_dist = district.strip()
                dist_res = DistrictResolutionService.resolve_district(clean_dist, db=db, allow_postal_lookup=False)
                if dist_res.is_resolved:
                    conds = [func.lower(func.trim(Customer.district)) == dist_res.canonical_name.lower()]
                    if dist_res.district_id:
                        conds.append(Customer.district_id == dist_res.district_id)
                    cust_q = cust_q.filter(or_(*conds))
                else:
                    d_key = canonical_key(clean_dist)
                    cust_q = cust_q.filter(func.lower(func.trim(Customer.district)).like(f"%{d_key}%"))
            if pincode:
                cust_q = cust_q.filter(func.trim(Customer.pincode) == pincode.strip())
            if search:
                search_clean = canonical_key(search)
                s = f"%{search_clean}%"
                search_conds = [
                    func.lower(func.trim(Customer.customer_name)).like(s),
                    func.lower(func.trim(Customer.contact_number)).like(s),
                    func.lower(func.trim(Customer.district)).like(s),
                    func.lower(func.trim(Customer.pincode)).like(s),
                    func.lower(func.trim(Customer.post_office)).like(s)
                ]
                search_dist_match = match_kerala_canonical_district(search)
                if search_dist_match:
                    search_conds.append(func.lower(func.trim(Customer.district)) == search_dist_match[0].lower())
                cust_q = cust_q.filter(or_(*search_conds))

            for c in cust_q.all():
                pin = (c.pincode or "").strip()
                pin_display = pin if (pin and pin.isdigit() and len(pin) == 6) else "Unknown Pincode"
                pin_key = pin_display.lower()

                if c.district_master:
                    d_name = c.district_master.canonical_name
                    d_state = c.district_master.state
                elif c.district and c.district.strip():
                    dist_res = DistrictResolutionService.resolve_district(c.district, pincode=c.pincode, db=db, allow_postal_lookup=False)
                    d_name = dist_res.canonical_name if dist_res.is_resolved else "Unknown District"
                    d_state = dist_res.state or "Kerala"
                else:
                    d_name = "Unknown District"
                    d_state = "Kerala"

                if pin_key not in pin_data:
                    pin_data[pin_key] = {
                        "pincode": pin_display,
                        "district": d_name,
                        "state": d_state,
                        "customer_count": 0,
                        "total_orders": 0,
                        "total_revenue": 0.0
                    }
                    cust_map[pin_key] = set()
                pin_data[pin_key]["total_orders"] += (c.total_orders or 0)
                pin_data[pin_key]["total_revenue"] += float(c.total_spend or 0.0)
                cust_map[pin_key].add(c.id)

        for pin_key, data in pin_data.items():
            data["customer_count"] = len(cust_map[pin_key])
            data["total_revenue"] = round(data["total_revenue"], 2)

        results = list(pin_data.values())
        reverse = (sort_order or "desc").lower() != "asc"
        if sort_by == "orders":
            results.sort(key=lambda x: x["total_orders"], reverse=reverse)
        elif sort_by == "customers":
            results.sort(key=lambda x: x["customer_count"], reverse=reverse)
        elif sort_by == "pincode":
            results.sort(key=lambda x: x["pincode"], reverse=not reverse)
        else:
            results.sort(key=lambda x: x["total_revenue"], reverse=reverse)

        if limit and limit > 0:
            results = results[:limit]

        return results

    @staticmethod
    def get_post_office_analytics(
        db: Session,
        preset: Optional[str] = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        employee_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        product_id: Optional[int] = None,
        district: Optional[str] = None,
        district_id: Optional[int] = None,
        pincode: Optional[str] = None,
        post_office: Optional[str] = None,
        rfm_segment: Optional[str] = None,
        customer_id: Optional[int] = None,
        order_status: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        sort_by: Optional[str] = "revenue",
        sort_order: Optional[str] = "desc"
    ) -> List[Dict[str, Any]]:
        order_q = AnalyticsService._build_filtered_orders_query(
            db=db,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
            employee_id=employee_id,
            payment_mode=payment_mode,
            product_id=product_id,
            district=district,
            district_id=district_id,
            pincode=pincode,
            post_office=post_office,
            rfm_segment=rfm_segment,
            customer_id=customer_id,
            order_status=order_status,
            search=search
        )
        orders = order_q.all()

        po_data: Dict[str, Dict[str, Any]] = {}
        cust_map: Dict[str, Set[int]] = {}

        for o in orders:
            c = o.customer
            po_raw = (c.post_office or "").strip() if c else ""
            if (not po_raw or po_raw.lower() in ["unknown", "unknown post office", "none", "null", "na", "n/a", ""]) and c:
                from app.services.postal_service import PostalService
                resolved_po = PostalService.resolve_post_office(
                    address=c.full_address,
                    pincode=c.pincode,
                    source_post_office=c.post_office,
                    db=db
                )
                if resolved_po:
                    po_raw = resolved_po

            po_display = clean_display_text(po_raw, title_case=True) if po_raw else "Unknown Post Office"
            pin = (c.pincode or "").strip() if c else ""
            pin_display = pin if (pin and pin.isdigit() and len(pin) == 6) else ""

            if c:
                if c.district_master:
                    d_name = c.district_master.canonical_name
                    d_state = c.district_master.state
                elif c.district and c.district.strip():
                    dist_res = DistrictResolutionService.resolve_district(c.district, pincode=c.pincode, db=db, allow_postal_lookup=False)
                    d_name = dist_res.canonical_name if dist_res.is_resolved else "Unknown District"
                    d_state = dist_res.state or "Kerala"
                else:
                    d_name = "Unknown District"
                    d_state = "Kerala"
            else:
                d_name = "Unknown District"
                d_state = "Kerala"

            po_key = f"{po_display.lower()}_{pin_display.lower()}_{d_name.lower()}"

            if po_key not in po_data:
                po_data[po_key] = {
                    "post_office": po_display,
                    "pincode": pin_display or "Unknown",
                    "district": d_name,
                    "state": d_state,
                    "customer_count": 0,
                    "total_orders": 0,
                    "total_revenue": 0.0
                }
                cust_map[po_key] = set()

            po_data[po_key]["total_orders"] += 1
            po_data[po_key]["total_revenue"] += float(o.total_amount or 0.0)
            if o.customer_id:
                cust_map[po_key].add(o.customer_id)

        for po_key, data in po_data.items():
            data["customer_count"] = len(cust_map[po_key])
            data["total_revenue"] = round(data["total_revenue"], 2)

        results = list(po_data.values())
        reverse = (sort_order or "desc").lower() != "asc"
        if sort_by == "orders":
            results.sort(key=lambda x: x["total_orders"], reverse=reverse)
        elif sort_by == "customers":
            results.sort(key=lambda x: x["customer_count"], reverse=reverse)
        elif sort_by == "post_office":
            results.sort(key=lambda x: x["post_office"].lower(), reverse=not reverse)
        else:
            results.sort(key=lambda x: x["total_revenue"], reverse=reverse)

        if limit and limit > 0:
            results = results[:limit]

        return results
