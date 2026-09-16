import datetime
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.models.customer import Customer
from app.models.order import Order
from app.models.rfm import RFMScore, RFMSegmentRule
from app.services.revenue_service import RevenueService

DEFAULT_SEGMENT_COLORS = {
    "Champions": "#10b981",          # Emerald
    "Loyal Customers": "#3b82f6",    # Blue
    "Potential Loyalists": "#6366f1",# Indigo
    "New Customers": "#8b5cf6",      # Purple
    "At Risk": "#f59e0b",            # Amber
    "Dormant Customers": "#f97316",  # Orange
    "Lost Customers": "#ef4444",     # Red
}

class RFMService:
    @staticmethod
    def assign_segment(r_score: int, f_score: int, m_score: int) -> str:
        """
        Determines customer RFM segment based on (R, F, M) quintiles.
        """
        # Champions: bought recently, buy often and spend the most
        if r_score >= 4 and f_score >= 4 and m_score >= 4:
            return "Champions"
        
        # Loyal Customers: spend good money and often, responsive to promotions
        if f_score >= 3 and m_score >= 3 and r_score >= 3:
            return "Loyal Customers"
        
        # Potential Loyalists: recent customers with average frequency
        if r_score >= 4 and f_score in [1, 2]:
            return "Potential Loyalists"
        
        # New Customers: bought recently (R 4-5), but only 1 order
        if r_score >= 4 and f_score == 1:
            return "New Customers"
        
        # At Risk: spent big money and purchased often, but long time ago (R 1-2, F 3-5)
        if r_score <= 2 and (f_score >= 3 or m_score >= 3):
            return "At Risk"
        
        # Dormant Customers: low frequency, low monetary, moderate recency
        if r_score == 3 and f_score <= 2:
            return "Dormant Customers"
        
        # Lost Customers: lowest recency, lowest frequency and lowest monetary
        if r_score <= 2 and f_score <= 2:
            return "Lost Customers"

        return "Potential Loyalists"

    @staticmethod
    def recalculate_all_rfm(db: Session) -> Dict[str, Any]:
        """
        Calculates R, F, M for all customers from actual qualifying orders in PostgreSQL.
        Assigns 1-5 scores and updates both RFMScore and Customer summary tables.
        """
        eligible_statuses = RevenueService.get_eligible_statuses(db)
        now = datetime.datetime.utcnow()

        # Query all customers with their qualifying orders (eager loaded in single query)
        customers = db.query(Customer).options(joinedload(Customer.orders)).all()
        if not customers:
            return {"total_processed": 0}

        records = []
        for cust in customers:
            qualifying_orders = [
                o for o in cust.orders 
                if o.order_status in eligible_statuses and o.order_date is not None
            ]
            
            if not qualifying_orders:
                # Customer has no eligible orders yet
                cust.total_orders = 0
                cust.total_spend = 0.0
                cust.average_order_value = 0.0
                cust.first_order_date = None
                cust.last_order_date = None
                cust.rfm_score = "111"
                cust.rfm_segment = "New Customers"
                continue

            order_dates = [o.order_date for o in qualifying_orders]
            first_order = min(order_dates)
            last_order = max(order_dates)
            total_orders = len(qualifying_orders)
            total_spend = sum(float(o.total_amount or 0.0) for o in qualifying_orders)
            aov = total_spend / total_orders if total_orders > 0 else 0.0

            # Update cached customer aggregates
            cust.first_order_date = first_order
            cust.last_order_date = last_order
            cust.total_orders = total_orders
            cust.total_spend = total_spend
            cust.average_order_value = aov

            recency_days = max(0, (now - last_order).days)
            records.append({
                "customer_id": cust.id,
                "recency_days": recency_days,
                "frequency": total_orders,
                "monetary_value": total_spend
            })

        if not records:
            db.commit()
            return {"total_processed": len(customers), "rfm_calculated": 0}

        df = pd.DataFrame(records)

        # Calculate quintiles (1-5 scores)
        # Recency: lower recency_days = higher score (5 is best)
        # Frequency: higher frequency = higher score (5 is best)
        # Monetary: higher monetary_value = higher score (5 is best)
        try:
            if len(df) >= 5:
                # Use qcut with duplicates handling
                df['r_score'] = pd.qcut(df['recency_days'].rank(method='first'), q=5, labels=[5, 4, 3, 2, 1]).astype(int)
                df['f_score'] = pd.qcut(df['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
                df['m_score'] = pd.qcut(df['monetary_value'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
            else:
                # For small test datasets (< 5 customers), apply linear/threshold scoring
                df['r_score'] = df['recency_days'].apply(lambda x: 5 if x < 30 else (4 if x < 60 else (3 if x < 90 else (2 if x < 180 else 1))))
                df['f_score'] = df['frequency'].apply(lambda x: 5 if x >= 5 else (4 if x >= 4 else (3 if x >= 3 else (2 if x >= 2 else 1))))
                df['m_score'] = df['monetary_value'].apply(lambda x: 5 if x >= 5000 else (4 if x >= 3000 else (3 if x >= 1500 else (2 if x >= 500 else 1))))
        except Exception:
            df['r_score'] = 3
            df['f_score'] = 3
            df['m_score'] = 3

        existing_rfms = {r.customer_id: r for r in db.query(RFMScore).all()}
        cust_map = {c.id: c for c in customers}

        # Update RFM scores and segments
        for _, row in df.iterrows():
            cid = int(row['customer_id'])
            r = int(row['r_score'])
            f = int(row['f_score'])
            m = int(row['m_score'])
            rfm_str = f"{r}{f}{m}"
            segment = RFMService.assign_segment(r, f, m)

            # Update or create RFMScore record
            rfm_entry = existing_rfms.get(cid)
            if not rfm_entry:
                rfm_entry = RFMScore(customer_id=cid)
                db.add(rfm_entry)
                existing_rfms[cid] = rfm_entry

            rfm_entry.recency_days = int(row['recency_days'])
            rfm_entry.frequency = int(row['frequency'])
            rfm_entry.monetary_value = float(row['monetary_value'])
            rfm_entry.r_score = r
            rfm_entry.f_score = f
            rfm_entry.m_score = m
            rfm_entry.rfm_score = rfm_str
            rfm_entry.segment = segment

            # Update Customer summary
            cust = cust_map.get(cid)
            if cust:
                cust.rfm_score = rfm_str
                cust.rfm_segment = segment

        db.commit()
        return {"total_processed": len(customers), "rfm_calculated": len(records)}

    @staticmethod
    def recalculate_single_customer(customer_id: int, db: Session):
        """Recalculates a single customer when an order changes"""
        cust = db.query(Customer).filter(Customer.id == customer_id).first()
        if not cust:
            return
        
        eligible_statuses = RevenueService.get_eligible_statuses(db)
        qualifying_orders = [
            o for o in cust.orders 
            if o.order_status in eligible_statuses and o.order_date is not None
        ]

        if not qualifying_orders:
            cust.total_orders = 0
            cust.total_spend = 0.0
            cust.average_order_value = 0.0
            cust.first_order_date = None
            cust.last_order_date = None
            cust.rfm_score = "111"
            cust.rfm_segment = "New Customers"
            db.commit()
            return

        order_dates = [o.order_date for o in qualifying_orders]
        cust.first_order_date = min(order_dates)
        cust.last_order_date = max(order_dates)
        cust.total_orders = len(qualifying_orders)
        cust.total_spend = sum(float(o.total_amount or 0.0) for o in qualifying_orders)
        cust.average_order_value = cust.total_spend / cust.total_orders

        # Full recalculation across dataset gives best percentile accuracy
        RFMService.recalculate_all_rfm(db)
