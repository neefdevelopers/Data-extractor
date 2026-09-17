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
        Calculates R, F, M for all customers using optimized SQL group aggregations.
        Assigns 1-5 scores and updates both RFMScore and Customer summary tables in bulk.
        """
        eligible_statuses = RevenueService.get_eligible_statuses(db)
        now = datetime.datetime.utcnow()

        # 1. Fast SQL aggregation of eligible orders grouped by customer_id
        order_aggs = db.query(
            Order.customer_id,
            func.min(Order.order_date).label("first_order"),
            func.max(Order.order_date).label("last_order"),
            func.count(Order.id).label("total_orders"),
            func.sum(func.coalesce(Order.total_amount, 0.0)).label("total_spend")
        ).filter(
            Order.order_status.in_(eligible_statuses),
            Order.order_date.isnot(None),
            Order.customer_id.isnot(None)
        ).group_by(Order.customer_id).all()

        if not order_aggs:
            return {"total_processed": db.query(Customer).count(), "rfm_calculated": 0}

        records = []
        for agg in order_aggs:
            cid = agg.customer_id
            first_order = agg.first_order
            last_order = agg.last_order
            total_orders = int(agg.total_orders or 0)
            total_spend = float(agg.total_spend or 0.0)
            aov = (total_spend / total_orders) if total_orders > 0 else 0.0
            recency_days = max(0, (now - last_order).days) if last_order else 0

            records.append({
                "customer_id": cid,
                "first_order_date": first_order,
                "last_order_date": last_order,
                "total_orders": total_orders,
                "total_spend": total_spend,
                "average_order_value": aov,
                "recency_days": recency_days,
                "frequency": total_orders,
                "monetary_value": total_spend
            })

        df = pd.DataFrame(records)

        # Calculate quintiles (1-5 scores)
        try:
            if len(df) >= 5:
                df['r_score'] = pd.qcut(df['recency_days'].rank(method='first'), q=5, labels=[5, 4, 3, 2, 1]).astype(int)
                df['f_score'] = pd.qcut(df['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
                df['m_score'] = pd.qcut(df['monetary_value'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
            else:
                df['r_score'] = df['recency_days'].apply(lambda x: 5 if x < 30 else (4 if x < 60 else (3 if x < 90 else (2 if x < 180 else 1))))
                df['f_score'] = df['frequency'].apply(lambda x: 5 if x >= 5 else (4 if x >= 4 else (3 if x >= 3 else (2 if x >= 2 else 1))))
                df['m_score'] = df['monetary_value'].apply(lambda x: 5 if x >= 5000 else (4 if x >= 3000 else (3 if x >= 1500 else (2 if x >= 500 else 1))))
        except Exception:
            df['r_score'] = 3
            df['f_score'] = 3
            df['m_score'] = 3

        existing_rfms = {r.customer_id: r for r in db.query(RFMScore).all()}
        customer_updates = []

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

            customer_updates.append({
                "id": cid,
                "first_order_date": row['first_order_date'],
                "last_order_date": row['last_order_date'],
                "total_orders": int(row['total_orders']),
                "total_spend": float(row['total_spend']),
                "average_order_value": float(row['average_order_value']),
                "rfm_score": rfm_str,
                "rfm_segment": segment
            })

        if customer_updates:
            db.bulk_update_mappings(Customer, customer_updates)

        total_cust_count = db.query(Customer).count()
        db.commit()
        return {"total_processed": total_cust_count, "rfm_calculated": len(records)}

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
