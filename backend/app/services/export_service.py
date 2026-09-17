import os
import uuid
import datetime
from typing import Optional, Dict, Any, List
import pandas as pd
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from app.models.employee import Employee
from app.models.rfm import RFMScore
from app.services.analytics_service import AnalyticsService
from app.services.product_service import ProductService
from app.services.employee_service import EmployeeService
from app.services.revenue_service import RevenueService

EXPORT_DIR = os.getenv("EXPORT_DIR", "../exports")

class ExportService:
    @staticmethod
    def _save_dataframe(df: pd.DataFrame, base_name: str, format_type: str = "xlsx") -> str:
        os.makedirs(EXPORT_DIR, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{base_name}_{timestamp}.{format_type}"
        filepath = os.path.join(EXPORT_DIR, filename)

        if format_type.lower() == "csv":
            df.to_csv(filepath, index=False)
        else:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=base_name[:30])

        return filepath

    @staticmethod
    def export_customers(
        db: Session,
        format_type: str = "xlsx",
        search: Optional[str] = None,
        district: Optional[str] = None,
        post_office: Optional[str] = None,
        pincode: Optional[str] = None,
        rfm_segment: Optional[str] = None,
        min_orders: Optional[int] = None,
        max_orders: Optional[int] = None,
        min_spend: Optional[float] = None,
        max_spend: Optional[float] = None,
        sort_by: str = "total_spend",
        sort_order: str = "desc"
    ) -> str:
        from app.services.customer_service import CustomerService
        customers, _ = CustomerService.get_customers(
            db,
            page=1,
            page_size=100000,
            search=search,
            district=district,
            post_office=post_office,
            pincode=pincode,
            rfm_segment=rfm_segment,
            min_orders=min_orders,
            max_orders=max_orders,
            min_spend=min_spend,
            max_spend=max_spend,
            sort_by=sort_by,
            sort_order=sort_order
        )
        data = []
        for c in customers:
            data.append({
                "Customer ID": c.id,
                "Customer Name": c.customer_name,
                "Contact Number": c.contact_number or c.normalized_contact or "",
                "Full Address": c.full_address or "",
                "Pincode": c.pincode or "",
                "Post Office": c.post_office or "",
                "District": c.district or "",
                "State": c.state or "",
                "Total Orders": c.total_orders,
                "Total Spend (₹)": round(c.total_spend, 2),
                "AOV (₹)": round(c.average_order_value, 2),
                "RFM Score": c.rfm_score or "",
                "RFM Segment": c.rfm_segment or "",
                "First Order Date": c.first_order_date.strftime("%Y-%m-%d %H:%M") if c.first_order_date else "",
                "Last Order Date": c.last_order_date.strftime("%Y-%m-%d %H:%M") if c.last_order_date else ""
            })

        df = pd.DataFrame(data) if data else pd.DataFrame(columns=["Customer ID", "Customer Name", "Contact Number", "District", "Total Spend (₹)"])
        return ExportService._save_dataframe(df, "customers_export", format_type)

    @staticmethod
    def export_orders(db: Session, format_type: str = "xlsx", payment_mode: Optional[str] = None, order_status: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        query = db.query(Order).join(Customer, Order.customer_id == Customer.id, isouter=True)
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
                query = query.filter(Order.order_date <= e_dt)
            except Exception:
                pass

        orders = query.all()
        data = []
        for o in orders:
            data.append({
                "Order ID": o.order_number,
                "Customer Name": o.customer.customer_name if o.customer else "",
                "Customer Contact": o.customer.contact_number if o.customer else "",
                "District": o.customer.district if o.customer else "",
                "Pincode": o.customer.pincode if o.customer else "",
                "Order Date": o.order_date.strftime("%Y-%m-%d %H:%M") if o.order_date else "",
                "Payment Mode": o.payment_mode,
                "Order Status": o.order_status,
                "Total Amount (₹)": o.total_amount,
                "Revenue Amount (₹)": o.revenue_amount,
                "Assigned Employee": o.employee.employee_name if o.employee else "Unassigned"
            })

        df = pd.DataFrame(data) if data else pd.DataFrame(columns=["Order ID", "Customer Name", "Order Date", "Payment Mode", "Total Amount (₹)"])
        return ExportService._save_dataframe(df, "orders_export", format_type)

    @staticmethod
    def export_rfm(db: Session, format_type: str = "xlsx") -> str:
        customers = db.query(Customer).join(RFMScore, Customer.id == RFMScore.customer_id, isouter=True).all()
        data = []
        for c in customers:
            rfm = c.rfm_details
            data.append({
                "Customer ID": c.id,
                "Customer Name": c.customer_name,
                "Contact": c.contact_number,
                "District": c.district,
                "Recency (Days)": rfm.recency_days if rfm else "",
                "Frequency (Orders)": rfm.frequency if rfm else c.total_orders,
                "Monetary Spend (₹)": rfm.monetary_value if rfm else c.total_spend,
                "R Score": rfm.r_score if rfm else "",
                "F Score": rfm.f_score if rfm else "",
                "M Score": rfm.m_score if rfm else "",
                "RFM Score": c.rfm_score,
                "RFM Segment": c.rfm_segment
            })

        df = pd.DataFrame(data) if data else pd.DataFrame(columns=["Customer ID", "Customer Name", "RFM Score", "RFM Segment"])
        return ExportService._save_dataframe(df, "rfm_analytics_export", format_type)

    @staticmethod
    def export_geographic(
        db: Session,
        format_type: str = "xlsx",
        preset: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        product_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        order_status: Optional[str] = None,
        customer_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> str:
        districts = AnalyticsService.get_district_analytics(
            db,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
            product_id=product_id,
            employee_id=employee_id,
            payment_mode=payment_mode,
            order_status=order_status,
            customer_id=customer_id,
            search=search
        )
        df = pd.DataFrame(districts) if districts else pd.DataFrame(columns=["district", "state", "total_orders", "total_revenue", "customer_count"])
        return ExportService._save_dataframe(df, "district_analytics_export", format_type)

    @staticmethod
    def export_pincodes(
        db: Session,
        format_type: str = "xlsx",
        preset: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        product_id: Optional[int] = None,
        district: Optional[str] = None,
        district_id: Optional[int] = None,
        employee_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        order_status: Optional[str] = None,
        customer_id: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "revenue",
        sort_order: str = "desc",
        limit: int = 1000
    ) -> str:
        pincodes = AnalyticsService.get_pincode_analytics(
            db,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
            product_id=product_id,
            district=district,
            district_id=district_id,
            employee_id=employee_id,
            payment_mode=payment_mode,
            order_status=order_status,
            customer_id=customer_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit
        )
        df = pd.DataFrame(pincodes) if pincodes else pd.DataFrame(columns=["pincode", "district", "state", "total_orders", "total_revenue", "customer_count"])
        return ExportService._save_dataframe(df, "pincode_analytics_export", format_type)

    @staticmethod
    def export_post_offices(
        db: Session,
        format_type: str = "xlsx",
        preset: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        product_id: Optional[int] = None,
        district: Optional[str] = None,
        pincode: Optional[str] = None,
        employee_id: Optional[int] = None,
        payment_mode: Optional[str] = None,
        order_status: Optional[str] = None,
        customer_id: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "revenue",
        sort_order: str = "desc",
        limit: int = 1000
    ) -> str:
        post_offices = AnalyticsService.get_post_office_analytics(
            db,
            preset=preset,
            start_date=start_date,
            end_date=end_date,
            product_id=product_id,
            district=district,
            pincode=pincode,
            employee_id=employee_id,
            payment_mode=payment_mode,
            order_status=order_status,
            customer_id=customer_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit
        )
        df = pd.DataFrame(post_offices) if post_offices else pd.DataFrame(columns=["post_office", "pincode", "district", "total_orders", "total_revenue", "customer_count"])
        return ExportService._save_dataframe(df, "post_office_analytics_export", format_type)

    @staticmethod
    def export_products(db: Session, format_type: str = "xlsx") -> str:
        items, _ = ProductService.get_products_analytics(db, page=1, page_size=1000)
        df = pd.DataFrame(items) if items else pd.DataFrame(columns=["product_name", "sku", "category", "total_units_sold", "total_revenue"])
        return ExportService._save_dataframe(df, "products_analytics_export", format_type)

    @staticmethod
    def export_employees(db: Session, format_type: str = "xlsx") -> str:
        items, _ = EmployeeService.get_employees_analytics(db, page=1, page_size=1000)
        df = pd.DataFrame(items) if items else pd.DataFrame(columns=["employee_name", "employee_code", "total_orders", "total_revenue"])
        return ExportService._save_dataframe(df, "employees_analytics_export", format_type)
