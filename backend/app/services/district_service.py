import json
import logging
from typing import Optional, Tuple, List, Dict, Set
from sqlalchemy.orm import Session
from app.models.district import DistrictMaster
from app.models.customer import Customer
from app.services.district_resolution_service import DistrictResolutionService, DistrictResolutionResult
from app.utils.district_normalization import (
    KERALA_14_DISTRICTS,
    OFFICIAL_KERALA_DISTRICTS,
    match_kerala_canonical_district,
    normalize_district_name,
    get_normalized_district_key,
)
from app.utils.text_normalization import canonical_key, clean_display_text

logger = logging.getLogger(__name__)


class DistrictService:
    """
    DistrictService wrapper delegating to DistrictResolutionService.
    Guarantees strict 14 Kerala canonical district resolution and backwards compatibility.
    """

    @classmethod
    def cleanup_duplicates_in_master(cls, db: Session) -> int:
        return DistrictResolutionService.cleanup_duplicates_in_master(db)

    @classmethod
    def seed_master_districts(cls, db: Session) -> int:
        return DistrictResolutionService.seed_master_districts(db)

    @classmethod
    def refresh_cache(cls, db: Session):
        pass

    @classmethod
    def get_district_by_id(cls, dist_id: Optional[int], db: Optional[Session] = None) -> Optional[DistrictMaster]:
        if dist_id is None or db is None:
            return None
        return db.query(DistrictMaster).filter(DistrictMaster.id == dist_id).first()

    @classmethod
    def get_or_create_district(
        cls,
        raw_district: Optional[str],
        state_hint: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Tuple[Optional[DistrictMaster], Optional[str], Optional[str]]:
        """
        Resolves any raw district string (English, Malayalam, uppercase, with suffixes)
        to a canonical DistrictMaster record, canonical name, and state.
        
        Returns:
            (DistrictMaster_object, canonical_name, state)
            OR (None, None, state_hint) if unresolved.
        """
        if not raw_district:
            return None, None, state_hint

        res = DistrictResolutionService.resolve_district(
            raw_district=raw_district,
            pincode=None,
            state_hint=state_hint,
            db=db,
            allow_postal_lookup=False
        )

        if not res.is_resolved:
            return None, None, state_hint

        dist_master = None
        if db is not None and res.district_id:
            dist_master = cls.get_district_by_id(res.district_id, db=db)

        return dist_master, res.canonical_name, res.state

    @classmethod
    def migrate_existing_data(cls, db: Session) -> Dict[str, int]:
        return DistrictResolutionService.migrate_existing_data(db)
