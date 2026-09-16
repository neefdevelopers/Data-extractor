from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.postal import PostalMasterOut, PostalOfficeOut, PostalLookupResult
from app.models.postal import PostalMaster, PostalOffice
from app.services.postal_service import PostalService

router = APIRouter(prefix="/postal", tags=["Postal"])

@router.get("/pincode/{pincode}", response_model=PostalMasterOut)
def get_pincode_details(pincode: str, db: Session = Depends(get_db)):
    pin_clean = pincode.strip()
    postal = PostalService.get_or_enrich_pincode(pin_clean, db)
    if not postal:
        raise HTTPException(status_code=404, detail=f"No postal information found for PIN {pincode}")
    return postal

@router.get("/search-offices", response_model=List[PostalOfficeOut])
def search_offices(q: str = Query(..., min_length=2), db: Session = Depends(get_db)):
    return PostalService.search_post_offices(q, db)
