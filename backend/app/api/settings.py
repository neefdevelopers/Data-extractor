import os
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db, DATABASE_URL
from app.schemas.settings import SystemSettingsOut, RevenueSettings, RFMSettings
from app.schemas.common import MessageResponse
from app.models.settings import SystemSetting
from app.services.revenue_service import RevenueService, DEFAULT_REVENUE_RULES
from app.services.rfm_service import RFMService

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=SystemSettingsOut)
def get_system_settings(db: Session = Depends(get_db)):
    # Revenue rules
    rules = RevenueService.get_revenue_rules(db)
    rev_settings = RevenueSettings(**rules)

    # RFM Settings
    rfm_setting = db.query(SystemSetting).filter(SystemSetting.key == "rfm_settings").first()
    rfm_data = {"recency_weight": 0.33, "frequency_weight": 0.33, "monetary_weight": 0.34}
    if rfm_setting:
        try:
            rfm_data = json.loads(rfm_setting.value)
        except Exception:
            pass
    rfm_settings = RFMSettings(**rfm_data)

    postal_url = os.getenv("POSTAL_API_URL", "https://api.postalpincode.in/pincode/")
    
    # Mask database URL for safety
    masked_db = DATABASE_URL
    if "@" in DATABASE_URL:
        prefix, host = DATABASE_URL.split("@", 1)
        masked_db = f"postgresql://****:****@{host}"

    return SystemSettingsOut(
        revenue_rules=rev_settings,
        rfm_settings=rfm_settings,
        postal_api_url=postal_url,
        database_url_masked=masked_db,
        app_version="1.0.0"
    )

@router.put("/revenue-rules", response_model=MessageResponse)
def update_revenue_rules(rules: RevenueSettings, db: Session = Depends(get_db)):
    setting = db.query(SystemSetting).filter(SystemSetting.key == "revenue_rules").first()
    if not setting:
        setting = SystemSetting(key="revenue_rules", value=json.dumps(rules.model_dump()))
        db.add(setting)
    else:
        setting.value = json.dumps(rules.model_dump())
    
    db.commit()

    # Recalculate RFM and order revenues with new rules
    RFMService.recalculate_all_rfm(db)
    
    return MessageResponse(success=True, message="Revenue qualification rules updated and analytics recalculated.")

@router.post("/merge-duplicates")
def merge_database_duplicates(db: Session = Depends(get_db)):
    from app.services.deduplication_service import DeduplicationService
    result = DeduplicationService.merge_all_duplicates(db)
    return result

