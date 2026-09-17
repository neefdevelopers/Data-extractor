"""
Pinlytics Development Database Reset Tool
=========================================
DEVELOPMENT USE ONLY!

Safely clears all transactional/application business data from PostgreSQL / SQLite
while strictly preserving:
  - Database schema & tables
  - District master reference data (14 Kerala Canonical Districts)
  - Postal master & offices cache
  - System settings & RFM segment configuration rules
  - User accounts

Resets primary key sequences/identity counters back to 1.
"""

import sys
import argparse
from typing import Dict, Any, Optional
from sqlalchemy import text
from app.database.session import engine, SessionLocal, DATABASE_URL
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.employee import Employee
from app.models.upload import UploadBatch, UploadRow
from app.models.rfm import RFMScore, RFMSegmentRule
from app.models.data_quality import DataQualityIssue
from app.models.location_audit import LocationCorrectionAudit
from app.models.district import DistrictMaster
from app.models.postal import PostalMaster, PostalOffice
from app.models.settings import SystemSetting
from app.models.user import User
from app.services.district_resolution_service import DistrictResolutionService

# Tables to clear in strict foreign-key dependency order (child tables first)
APPLICATION_TABLES = [
    ("order_items", "Order Items", OrderItem),
    ("orders", "Orders", Order),
    ("rfm_scores", "RFM Scores", RFMScore),
    ("location_correction_audits", "Location Correction Audits", LocationCorrectionAudit),
    ("upload_rows", "Upload Rows", UploadRow),
    ("uploads", "Upload Batches", UploadBatch),
    ("data_quality_issues", "Data Quality Issues", DataQualityIssue),
    ("customers", "Customers", Customer),
    ("products", "Products", Product),
    ("employees", "Employees", Employee),
]

PRESERVED_TABLES = [
    ("district_master", "District Master (14 Kerala Canonical Districts)", DistrictMaster),
    ("postal_master", "Postal Master Cache", PostalMaster),
    ("postal_offices", "Postal Offices Cache", PostalOffice),
    ("rfm_segments", "RFM Segment Rules", RFMSegmentRule),
    ("system_settings", "System Settings", SystemSetting),
    ("users", "Users / Admins", User),
]


def get_table_counts(session) -> Dict[str, int]:
    """Returns row counts for all application and master tables."""
    counts = {}
    for table_name, _, model_cls in APPLICATION_TABLES + PRESERVED_TABLES:
        try:
            cnt = session.query(model_cls).count()
            counts[table_name] = cnt
        except Exception:
            try:
                res = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                counts[table_name] = res or 0
            except Exception:
                counts[table_name] = -1
    return counts


def reset_database(force: bool = False, session: Optional[Any] = None, db_url: Optional[str] = None) -> bool:
    """
    Executes the safe database reset within a transaction.
    """
    effective_url = db_url or DATABASE_URL
    is_postgres = effective_url.startswith("postgresql") or effective_url.startswith("postgres")
    is_sqlite = effective_url.startswith("sqlite")

    print("\n" + "=" * 75)
    print(" [DEVELOPMENT ONLY] PINLYTICS LOCAL DATABASE RESET")
    print("=" * 75)
    print(f"Target Database Engine : {'PostgreSQL' if is_postgres else 'SQLite' if is_sqlite else effective_url.split(':')[0]}")
    print(f"Connection URL         : {effective_url}")
    print("\n--- Application Data to be CLEARED ---")
    for tbl, label, _ in APPLICATION_TABLES:
        print(f"  [X] {label:<32} (table: {tbl})")

    print("\n--- Reference/Master Data to be PRESERVED ---")
    for tbl, label, _ in PRESERVED_TABLES:
        print(f"  [v] {label:<32} (table: {tbl})")

    print("\n--- Identity / Sequence Handling ---")
    if is_postgres:
        print("  [*] PostgreSQL Sequences will be reset: RESTART IDENTITY CASCADE")
    else:
        print("  [*] SQLite Sequences will be reset via sqlite_sequence table")
    print("=" * 75)

    if not force:
        print("\nCONFIRMATION REQUIRED:")
        print("This will permanently delete all Pinlytics application transactional data.")
        user_input = input("Type 'RESET' to confirm and proceed: ").strip()
        if user_input != "RESET":
            print("\n[ABORTED] Reset cancelled. Confirmation mismatch. No data was modified.\n")
            return False

    print("\nExecuting transactional reset...")
    owns_session = False
    if session is None:
        session = SessionLocal()
        owns_session = True

    try:
        if is_postgres:
            # PostgreSQL: Truncate tables with RESTART IDENTITY CASCADE
            table_list = ", ".join([tbl for tbl, _, _ in APPLICATION_TABLES])
            session.execute(text(f"TRUNCATE TABLE {table_list} RESTART IDENTITY CASCADE;"))
            session.commit()
            print("  -> Truncated application tables and restarted sequences.")
        else:
            # SQLite: Delete rows in order of foreign key dependency
            for table_name, label, _ in APPLICATION_TABLES:
                session.execute(text(f"DELETE FROM {table_name};"))
            
            # Reset SQLite auto-increment sequences
            for table_name, _, _ in APPLICATION_TABLES:
                try:
                    session.execute(text(f"DELETE FROM sqlite_sequence WHERE name = '{table_name}';"))
                except Exception:
                    pass
            session.commit()
            print("  -> Cleared application tables and reset SQLite sequence counters.")

        # Clean up legacy non-canonical district rows and re-seed the 14 Kerala Canonical Master Districts
        from app.utils.district_normalization import KERALA_14_DISTRICTS
        canonical_keys = [item[2] for item in KERALA_14_DISTRICTS]
        session.query(DistrictMaster).filter(~DistrictMaster.normalized_key.in_(canonical_keys)).delete(synchronize_session=False)
        session.commit()
        DistrictResolutionService.seed_master_districts(session)
        print("  -> Verified & preserved Kerala 14 Canonical District Master reference records.")

        # Post-reset verification
        print("\n" + "=" * 75)
        print(" POST-RESET VERIFICATION SUMMARY")
        print("=" * 75)
        counts = get_table_counts(session)

        all_cleared = True
        print("Application Data Tables (Expected 0):")
        for tbl, label, _ in APPLICATION_TABLES:
            cnt = counts.get(tbl, 0)
            status = "[OK - CLEARED]" if cnt == 0 else f"[FAILED - {cnt} remaining]"
            if cnt != 0:
                all_cleared = False
            print(f"  {label:<32} : {cnt:>6} records  {status}")

        print("\nPreserved Master & Reference Tables:")
        for tbl, label, _ in PRESERVED_TABLES:
            cnt = counts.get(tbl, 0)
            print(f"  {label:<32} : {cnt:>6} records  [PRESERVED]")

        print("=" * 75)

        if all_cleared:
            print("\nSUCCESS: All application data has been safely cleared.")
            print("Next inserted records will start from clean initial IDs.")
            return True
        else:
            print("\nWARNING: Some application tables still contain records.")
            return False

    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Reset failed: {e}")
        print("Transaction rolled back. No partial changes were committed.")
        return False
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description="Safely reset Pinlytics development application data while preserving master references."
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive confirmation prompt (use in automated test scripts only)"
    )
    args = parser.parse_args()

    success = reset_database(force=args.yes)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
