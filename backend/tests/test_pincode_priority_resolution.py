import io
import uuid
import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.district import DistrictMaster
from app.models.customer import Customer
from app.models.postal import PostalMaster, PostalOffice
from app.models.data_quality import DataQualityIssue
from app.services.district_resolution_service import DistrictResolutionService
from app.services.excel_import_service import ExcelImportService
from app.services.customer_service import CustomerService
from app.services.analytics_service import AnalyticsService

@pytest.fixture
def db_session():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSession()

    # Seed 14 Kerala canonical master districts
    DistrictResolutionService.seed_master_districts(session)

    # Seed mock postal master for testing without external API calls
    # 676505 -> Malappuram
    p1 = PostalMaster(pincode="676505", district="Malappuram", state="Kerala")
    po1 = PostalOffice(pincode="676505", office_name="Manjeri H.O", district="Malappuram", state="Kerala")
    po2 = PostalOffice(pincode="676505", office_name="Manjeri College B.O", district="Malappuram", state="Kerala")

    # 673001 -> Kozhikode
    p2 = PostalMaster(pincode="673001", district="Kozhikode", state="Kerala")
    po3 = PostalOffice(pincode="673001", office_name="Calicut H.O", district="Kozhikode", state="Kerala")

    # 682001 -> Ernakulam
    p3 = PostalMaster(pincode="682001", district="Ernakulam", state="Kerala")
    po4 = PostalOffice(pincode="682001", office_name="Kochi H.O", district="Ernakulam", state="Kerala")

    # 699999 -> Multi-district test pin
    p_multi = PostalMaster(pincode="699999", district="Multi", state="Kerala")
    po_multi1 = PostalOffice(pincode="699999", office_name="Office 1", district="Malappuram", state="Kerala")
    po_multi2 = PostalOffice(pincode="699999", office_name="Office 2", district="Palakkad", state="Kerala")

    session.add_all([p1, po1, po2, p2, po3, p3, po4, p_multi, po_multi1, po_multi2])
    session.commit()

    yield session
    session.close()


def test_district_and_valid_pincode_matching(db_session):
    """Criteria 1: District + valid matching Pincode -> Resolves to Pincode verified district with no mismatch."""
    res = DistrictResolutionService.resolve_district(
        raw_district="Malappuram",
        pincode="676505",
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.is_resolved is True
    assert res.canonical_name == "Malappuram"
    assert res.resolution_source == "PINCODE"
    assert res.district_status == "RESOLVED"
    assert res.district_mismatch is False
    assert res.source_district == "Malappuram"


def test_district_and_valid_pincode_conflicting_priority(db_session):
    """Criteria 2: Uploaded District 'Kozhikode' + Pincode '676505' (Malappuram) -> MUST resolve to Malappuram and flag mismatch."""
    res = DistrictResolutionService.resolve_district(
        raw_district="Kozhikode",
        pincode="676505",
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.is_resolved is True
    assert res.canonical_name == "Malappuram"  # Priority to Pincode!
    assert res.resolution_source == "PINCODE"
    assert res.district_mismatch is True
    assert res.source_district == "Kozhikode"
    assert "Uploaded district 'Kozhikode' does not match" in res.mismatch_message


def test_missing_district_with_valid_pincode(db_session):
    """Criteria 3: Missing District + valid Pincode -> Determines canonical district from Pincode."""
    res = DistrictResolutionService.resolve_district(
        raw_district=None,
        pincode="676505",
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.is_resolved is True
    assert res.canonical_name == "Malappuram"
    assert res.resolution_source == "PINCODE"
    assert res.district_mismatch is False


def test_invalid_district_with_valid_pincode(db_session):
    """Criteria 4: Invalid District 'Gibberish District' + valid Pincode '676505' -> Resolves to Malappuram via Pincode."""
    res = DistrictResolutionService.resolve_district(
        raw_district="Some Random String",
        pincode="676505",
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.is_resolved is True
    assert res.canonical_name == "Malappuram"
    assert res.resolution_source == "PINCODE"
    assert res.district_mismatch is True


def test_valid_district_with_invalid_pincode_fallback(db_session):
    """Criteria 5: Valid District 'Malappuram' + Invalid Pincode '123' -> Falls back to district with DISTRICT_FALLBACK tag."""
    res = DistrictResolutionService.resolve_district(
        raw_district="Malappuram",
        pincode="123",
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.is_resolved is True
    assert res.canonical_name == "Malappuram"
    assert res.resolution_source == "DISTRICT_FALLBACK"
    assert res.district_mismatch is False


def test_missing_district_and_missing_pincode(db_session):
    """Criteria 6: Missing District + Missing Pincode -> UNRESOLVED."""
    res = DistrictResolutionService.resolve_district(
        raw_district=None,
        pincode=None,
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.is_resolved is False
    assert res.resolution_source == "UNRESOLVED"
    assert res.district_status == "UNRESOLVED"


def test_malayalam_district_without_pincode(db_session):
    """Criteria 7: Malayalam District 'മലപ്പുറം' + No Pincode -> Resolves to Malappuram (DISTRICT_ALIAS)."""
    res = DistrictResolutionService.resolve_district(
        raw_district="മലപ്പുറം",
        pincode=None,
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.is_resolved is True
    assert res.canonical_name == "Malappuram"
    assert res.resolution_source == "DISTRICT_ALIAS"


def test_malayalam_district_with_valid_pincode_priority(db_session):
    """Criteria 8: Malayalam District 'കോഴിക്കോട്' (Kozhikode) + Pincode '676505' (Malappuram) -> Resolves to Malappuram via PINCODE."""
    res = DistrictResolutionService.resolve_district(
        raw_district="കോഴിക്കോട്",
        pincode="676505",
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.is_resolved is True
    assert res.canonical_name == "Malappuram"
    assert res.resolution_source == "PINCODE"
    assert res.district_mismatch is True


def test_multiple_post_offices_same_district(db_session):
    """Criteria 9: Multiple post offices in same district (676505 has Manjeri H.O & College B.O in Malappuram) -> Auto-resolved."""
    res = DistrictResolutionService.resolve_district(
        raw_district=None,
        pincode="676505",
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.is_resolved is True
    assert res.canonical_name == "Malappuram"
    assert res.district_status == "RESOLVED"
    assert len(res.post_offices) == 2


def test_multiple_post_offices_different_districts(db_session):
    """Criteria 10: Multiple post offices mapping to different districts -> NEEDS_CONFIRMATION."""
    res = DistrictResolutionService.resolve_district(
        raw_district=None,
        pincode="699999",
        db=db_session,
        allow_postal_lookup=False
    )
    assert res.district_status == "NEEDS_CONFIRMATION"
    assert res.resolution_source == "PINCODE"


def test_excel_import_fathima_mismatch_case(db_session):
    """
    Section 13 & 14 requirement:
    Excel Row: Customer="Fathima", Mobile="9876543210", District="Kozhikode", Pincode="676505"
    Postal API gives 676505 -> Malappuram
    Result MUST be: canonical district = "Malappuram", source_district = "Kozhikode", mismatch = True
    """
    df = pd.DataFrame([{
        "Customer Name": "Fathima Test",
        "Mobile Number": "9876543210",
        "District": "Kozhikode",
        "Pincode": "676505"
    }])

    excel_buf = io.BytesIO()
    df.to_excel(excel_buf, index=False)
    excel_bytes = excel_buf.getvalue()

    analysis = ExcelImportService.analyze_file(excel_bytes, "fathima_mismatch.xlsx")
    batch = ExcelImportService.process_import(
        temp_file_id=analysis["temp_file_id"],
        original_filename=analysis["file_name"],
        import_type="CUSTOMER",
        column_mapping=analysis["auto_mappings"],
        db=db_session
    )

    assert batch.successful_rows == 1
    cust = db_session.query(Customer).filter(Customer.normalized_contact == "9876543210").first()
    assert cust is not None
    assert cust.district == "Malappuram"  # Canonical Pincode-verified!
    assert cust.source_district == "Kozhikode"  # Preserved original!
    assert cust.district_mismatch is True
    assert cust.district_resolution_source == "PINCODE"


def test_migrate_existing_data_re_resolves_with_pincode_priority(db_session):
    """Criteria 11: Existing legacy customer with District='Kozhikode' & Pincode='676505' gets corrected to Malappuram."""
    cust = Customer(
        customer_name="Legacy Customer",
        normalized_contact="9847111222",
        district="Kozhikode",
        pincode="676505"
    )
    db_session.add(cust)
    db_session.commit()

    stats = DistrictResolutionService.migrate_existing_data(db_session)
    assert stats["updated_count"] >= 1
    assert stats["mismatch_count"] >= 1

    db_session.refresh(cust)
    assert cust.district == "Malappuram"
    assert cust.source_district == "Kozhikode"
    assert cust.district_mismatch is True
    assert cust.district_resolution_source == "PINCODE"


def test_customer_update_edit_pincode_auto_recalculates_district(db_session):
    """Acceptance Test 8: Edit Pincode -> Automatically recalculates District."""
    from app.schemas.customer import CustomerUpdate

    cust = Customer(
        customer_name="Edit Test Customer",
        normalized_contact="9847999888",
        district="Ernakulam",
        pincode="682001"
    )
    db_session.add(cust)
    db_session.commit()

    # Customer moves / updates Pincode to 676505 (Malappuram) without specifying district
    update_data = CustomerUpdate(
        pincode="676505"
    )
    updated_cust = CustomerService.update_customer(db_session, cust.id, update_data)
    assert updated_cust.pincode == "676505"
    assert updated_cust.district == "Malappuram"
    assert updated_cust.district_resolution_source == "PINCODE"
    assert updated_cust.district_status == "RESOLVED"


def test_correct_pincode_from_unknown_location_removes_from_unknown(db_session):
    """Acceptance Test 10: Correct Pincode from Unknown Location Data -> Automatically resolved and removed from Unknown."""
    from app.schemas.location import LocationCorrectionRequest
    from app.services.location_service import LocationService

    cust = Customer(
        customer_name="Unknown Location User",
        normalized_contact="9847123999",
        district="Unknown",
        pincode=None
    )
    db_session.add(cust)
    db_session.commit()

    # Verify customer appears in unknown records
    unknown_before = LocationService.get_unknown_records(db_session, filter_type="all")
    assert unknown_before.total == 1

    # User enters Pincode '673001' (Kozhikode) in Correct Location Details without specifying district
    req = LocationCorrectionRequest(
        pincode="673001",
        source="MANUAL"
    )
    updated = LocationService.correct_customer_location(db_session, cust.id, req)
    assert updated.pincode == "673001"
    assert updated.district == "Kozhikode"  # Automatically resolved from Pincode!
    assert updated.district_status == "RESOLVED"

    # Verify customer is no longer in unknown location records
    unknown_after = LocationService.get_unknown_records(db_session, filter_type="all")
    assert unknown_after.total == 0

