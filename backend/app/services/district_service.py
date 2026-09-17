import json
import logging
from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.district import DistrictMaster
from app.models.customer import Customer
from app.utils.district_normalization import (
    OFFICIAL_KERALA_DISTRICTS,
    OTHER_MAJOR_DISTRICTS,
    normalize_district_name,
    get_normalized_district_key,
)
from app.utils.text_normalization import canonical_key, clean_display_text

logger = logging.getLogger(__name__)

class DistrictService:
    # Memory cache for fast lookups during imports & queries
    _cache_by_key: Dict[str, DistrictMaster] = {}

    @classmethod
    def seed_master_districts(cls, db: Session) -> int:
        """
        Seeds standard Kerala districts and major metropolitan districts into district_master.
        Guarantees that unique normalized keys exist in DB and populates memory cache.
        """
        seeded = 0
        all_districts = OFFICIAL_KERALA_DISTRICTS + OTHER_MAJOR_DISTRICTS

        for canonical_name, state, norm_key, aliases in all_districts:
            existing = db.query(DistrictMaster).filter(
                DistrictMaster.normalized_key == norm_key
            ).first()

            if not existing:
                master_entry = DistrictMaster(
                    canonical_name=canonical_name,
                    state=state,
                    normalized_key=norm_key,
                    aliases=json.dumps(aliases, ensure_ascii=False)
                )
                db.add(master_entry)
                seeded += 1
            else:
                # Ensure canonical name and state are accurate
                if existing.canonical_name != canonical_name:
                    existing.canonical_name = canonical_name
                if existing.state != state:
                    existing.state = state

        if seeded > 0:
            db.commit()
            logger.info(f"Seeded {seeded} standard districts into district_master.")

        # Refresh local cache
        cls.refresh_cache(db)
        return seeded

    @classmethod
    def refresh_cache(cls, db: Session):
        """Loads all districts from DB into fast lookup cache."""
        records = db.query(DistrictMaster).all()
        cls._cache_by_key = {r.normalized_key: r for r in records}

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
            OR (None, None, state_hint) if the district is missing or 'Unknown'.
        """
        if not raw_district:
            return None, None, state_hint

        canonical_name, canonical_state = normalize_district_name(raw_district, state_hint=state_hint)
        if not canonical_name:
            return None, None, state_hint

        norm_key = canonical_key(canonical_name)
        if not norm_key:
            return None, None, state_hint

        # 1. Check memory cache
        if norm_key in cls._cache_by_key:
            return cls._cache_by_key[norm_key], canonical_name, canonical_state

        if db is None:
            return None, canonical_name, canonical_state

        # 2. Query DB
        existing = db.query(DistrictMaster).filter(
            DistrictMaster.normalized_key == norm_key
        ).first()

        if existing:
            cls._cache_by_key[norm_key] = existing
            return existing, existing.canonical_name, existing.state

        # 3. Create new DistrictMaster entry safely
        try:
            new_district = DistrictMaster(
                canonical_name=canonical_name,
                state=canonical_state or "Kerala",
                normalized_key=norm_key,
                aliases=json.dumps([raw_district.strip()], ensure_ascii=False)
            )
            db.add(new_district)
            db.flush()
            cls._cache_by_key[norm_key] = new_district
            return new_district, canonical_name, canonical_state
        except Exception as e:
            db.rollback()
            # If race condition occurred, fetch the existing one
            existing = db.query(DistrictMaster).filter(
                DistrictMaster.normalized_key == norm_key
            ).first()
            if existing:
                cls._cache_by_key[norm_key] = existing
                return existing, existing.canonical_name, existing.state
            logger.error(f"Error creating district master for {raw_district}: {e}")
            return None, canonical_name, canonical_state

    @classmethod
    def migrate_existing_data(cls, db: Session) -> Dict[str, int]:
        """
        Safe Migration:
        1. Ensures master districts are seeded.
        2. Scans all Customer records.
        3. Resolves each customer's district (Malayalam, spelling variation, case differences).
        4. Updates customer.district_id and sets customer.district to canonical name.
        5. Unknown records get district_id = None.
        6. Preserves all customer and order records without deletion.
        """
        cls.seed_master_districts(db)
        cls.refresh_cache(db)

        customers = db.query(Customer).all()
        updated_count = 0
        unknown_count = 0

        for cust in customers:
            raw_dist = cust.district
            raw_state = cust.state
            
            district_obj, canonical_dist, canonical_st = cls.get_or_create_district(
                raw_dist, state_hint=raw_state, db=db
            )

            if district_obj:
                changed = False
                if cust.district_id != district_obj.id:
                    cust.district_id = district_obj.id
                    changed = True
                if cust.district != district_obj.canonical_name:
                    cust.district = district_obj.canonical_name
                    changed = True
                if canonical_st and cust.state != canonical_st:
                    cust.state = canonical_st
                    changed = True
                if changed:
                    updated_count += 1
            else:
                if cust.district_id is not None:
                    cust.district_id = None
                    updated_count += 1
                unknown_count += 1

        db.commit()
        logger.info(f"District migration complete: {updated_count} customers updated, {unknown_count} unknown location customers.")
        return {
            "total_customers": len(customers),
            "updated_count": updated_count,
            "unknown_count": unknown_count
        }
