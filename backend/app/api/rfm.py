from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.session import get_db
from app.schemas.rfm import RFMDashboardResponse, RFMSegmentSummary, ScoreDistribution
from app.schemas.common import MessageResponse
from app.models.customer import Customer
from app.models.rfm import RFMScore
from app.services.rfm_service import RFMService, DEFAULT_SEGMENT_COLORS

router = APIRouter(prefix="/rfm", tags=["RFM Analytics"])

@router.get("/dashboard", response_model=RFMDashboardResponse)
def get_rfm_dashboard(db: Session = Depends(get_db)):
    customers_with_rfm = db.query(Customer).filter(Customer.rfm_score.isnot(None), Customer.total_orders > 0).all()
    customers_without = db.query(Customer).filter((Customer.rfm_score.is_(None)) | (Customer.total_orders == 0)).count()

    total_with = len(customers_with_rfm)
    if total_with == 0:
        return RFMDashboardResponse(
            total_customers_with_rfm=0,
            customers_without_sufficient_data=customers_without,
            avg_recency_days=0.0,
            avg_frequency=0.0,
            avg_monetary=0.0,
            segments=[],
            recency_distribution=[ScoreDistribution(score=i, customer_count=0) for i in range(1, 6)],
            frequency_distribution=[ScoreDistribution(score=i, customer_count=0) for i in range(1, 6)],
            monetary_distribution=[ScoreDistribution(score=i, customer_count=0) for i in range(1, 6)]
        )

    # Average metrics
    rfm_records = db.query(RFMScore).all()
    avg_rec = sum(r.recency_days for r in rfm_records) / len(rfm_records) if rfm_records else 0.0
    avg_freq = sum(r.frequency for r in rfm_records) / len(rfm_records) if rfm_records else 0.0
    avg_mon = sum(r.monetary_value for r in rfm_records) / len(rfm_records) if rfm_records else 0.0

    # Segments breakdown
    segment_map: Dict[str, Dict[str, Any]] = {}
    for r in rfm_records:
        seg = r.segment or "New Customers"
        if seg not in segment_map:
            segment_map[seg] = {
                "count": 0,
                "revenue": 0.0,
                "recency_sum": 0,
                "freq_sum": 0,
                "color": DEFAULT_SEGMENT_COLORS.get(seg, "#6366f1")
            }
        segment_map[seg]["count"] += 1
        segment_map[seg]["revenue"] += r.monetary_value
        segment_map[seg]["recency_sum"] += r.recency_days
        segment_map[seg]["freq_sum"] += r.frequency

    segments_out: List[RFMSegmentSummary] = []
    for seg_name, val in segment_map.items():
        cnt = val["count"]
        segments_out.append(RFMSegmentSummary(
            segment_name=seg_name,
            customer_count=cnt,
            percentage=round((cnt / total_with * 100.0), 1),
            total_revenue=round(val["revenue"], 2),
            avg_monetary=round((val["revenue"] / cnt), 2) if cnt > 0 else 0.0,
            avg_frequency=round((val["freq_sum"] / cnt), 2) if cnt > 0 else 0.0,
            avg_recency_days=round((val["recency_sum"] / cnt), 1) if cnt > 0 else 0.0,
            color_code=val["color"]
        ))
    segments_out.sort(key=lambda x: x.total_revenue, reverse=True)

    # Score distributions (1-5)
    r_counts = {i: 0 for i in range(1, 6)}
    f_counts = {i: 0 for i in range(1, 6)}
    m_counts = {i: 0 for i in range(1, 6)}

    for r in rfm_records:
        if r.r_score in r_counts:
            r_counts[r.r_score] += 1
        if r.f_score in f_counts:
            f_counts[r.f_score] += 1
        if r.m_score in m_counts:
            m_counts[r.m_score] += 1

    return RFMDashboardResponse(
        total_customers_with_rfm=total_with,
        customers_without_sufficient_data=customers_without,
        avg_recency_days=round(avg_rec, 1),
        avg_frequency=round(avg_freq, 1),
        avg_monetary=round(avg_mon, 2),
        segments=segments_out,
        recency_distribution=[ScoreDistribution(score=i, customer_count=r_counts[i]) for i in range(1, 6)],
        frequency_distribution=[ScoreDistribution(score=i, customer_count=f_counts[i]) for i in range(1, 6)],
        monetary_distribution=[ScoreDistribution(score=i, customer_count=m_counts[i]) for i in range(1, 6)]
    )

@router.post("/recalculate", response_model=MessageResponse)
def recalculate_rfm(db: Session = Depends(get_db)):
    result = RFMService.recalculate_all_rfm(db)
    return MessageResponse(
        success=True,
        message=f"RFM recalculated successfully for {result.get('total_processed', 0)} customers.",
        details=result
    )
