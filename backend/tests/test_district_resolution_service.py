import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.session import Base
from app.models.district import DistrictMaster
from app.models.customer import Customer
from app.models.order import Order
from app.models.postal import PostalMaster, PostalOffice
from app.services.district_resolution_service import DistrictResolutionService
from app.services.district_service import DistrictService
from app.services.postal_service import PostalService
from app.services.analytics_service import AnalyticsService
from app.services.location_service import LocationService
from app.schemas.location import LocationCorrectionRequest
from app.utils.district_normalization import (
    KERALA_14_DISTRICTS,
    match_kerala_canonical_district,
    normalize_district_name
)


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Pre-seed master records
    DistrictResolutionService.seed_master_districts(session)
    
    # Pre-seed test postal cache for pincode lookup tests
    p_clt = PostalMaster(pincode="673001", district="Kozhikode", state="Kerala", country="India")
    session.add(p_clt)
    session.add(PostalOffice(pincode="673001", office_name="Calicut H.O", district="Kozhikode", state="Kerala"))
    session.add(PostalOffice(pincode="673001", office_name="Puthiyara S.O", district="Kozhikode", state="Kerala"))

    p_mlp = PostalMaster(pincode="673638", district="Malappuram", state="Kerala", country="India")
    session.add(p_mlp)
    session.add(PostalOffice(pincode="673638", office_name="Kondotti SO", district="Malappuram", state="Kerala"))
    session.add(PostalOffice(pincode="673638", office_name="Arimbra BO", district="Malappuram", state="Kerala"))

    p_ekm = PostalMaster(pincode="682001", district="Ernakulam", state="Kerala", country="India")
    session.add(p_ekm)
    session.add(PostalOffice(pincode="682001", office_name="Ernakulam H.O", district="Ernakulam", state="Kerala"))

    session.commit()
    yield session
    session.close()


def test_14_canonical_districts_seeded(db_session):
    """Verify exactly 14 Kerala canonical districts exist in district_master."""
    districts = db_session.query(DistrictMaster).all()
    assert len(districts) == 14
    canonical_names = {d.canonical_name for d in districts}
    expected_14 = {
        "Alappuzha", "Ernakulam", "Idukki", "Kannur", "Kasaragod", "Kollam",
        "Kottayam", "Kozhikode", "Malappuram", "Palakkad", "Pathanamthitta",
        "Thiruvananthapuram", "Thrissur", "Wayanad"
    }
    assert canonical_names == expected_14


def test_malappuram_variations(db_session):
    """1 to 5: Malappuram case, Malayalam, and suffix variations resolve to canonical Malappuram."""
    variations = [
        "Malappuram",
        "MALAPPURAM",
        "malappuram",
        "മലപ്പുറം",
        "Malappuram District",
        " മലപ്പുറം ജില്ല ",
        "malappuram dist",
        "malappuram dt"
    ]
    for v in variations:
        res = DistrictResolutionService.resolve_district(v, db=db_session, allow_postal_lookup=False)
        assert res.canonical_name == "Malappuram", f"Failed for '{v}'"
        assert res.district_status == "RESOLVED"
        assert res.resolution_source in ["DISTRICT_DIRECT_MATCH", "DISTRICT_ALIAS"]
        assert res.district_id is not None


def test_kozhikode_variations(db_session):
    """6 & 7: Kozhikode, Calicut, and Malayalam aliases resolve to canonical Kozhikode."""
    variations = [
        "Kozhikode",
        "KOZHIKODE",
        "kozhikode",
        "Calicut",
        "CALICUT",
        "calicut",
        "കോഴിക്കോട്",
        "കാലിക്കറ്റ്",
        "Kozhikode District",
        "Calicut Dist"
    ]
    for v in variations:
        res = DistrictResolutionService.resolve_district(v, db=db_session, allow_postal_lookup=False)
        assert res.canonical_name == "Kozhikode", f"Failed for '{v}'"
        assert res.district_status == "RESOLVED"
        assert res.resolution_source in ["DISTRICT_DIRECT_MATCH", "DISTRICT_ALIAS"]


def test_all_14_malayalam_districts(db_session):
    """Verify all 14 Kerala Malayalam district names map to canonical English names."""
    malayalam_map = {
        "മലപ്പുറം": "Malappuram",
        "കോഴിക്കോട്": "Kozhikode",
        "കണ്ണൂർ": "Kannur",
        "വയനാട്": "Wayanad",
        "പാലക്കാട്": "Palakkad",
        "തൃശൂർ": "Thrissur",
        "തൃശ്ശൂർ": "Thrissur",
        "എറണാകുളം": "Ernakulam",
        "കൊച്ചി": "Ernakulam",
        "ഇടുക്കി": "Idukki",
        "കോട്ടയം": "Kottayam",
        "ആലപ്പുഴ": "Alappuzha",
        "പത്തനംതിട്ട": "Pathanamthitta",
        "കൊല്ലം": "Kollam",
        "തിരുവനന്തപുരം": "Thiruvananthapuram",
        "കാസർഗോഡ്": "Kasaragod",
        "കാസർകോട്": "Kasaragod",
    }
    for mal_name, expected_canonical in malayalam_map.items():
        res = DistrictResolutionService.resolve_district(mal_name, db=db_session, allow_postal_lookup=False)
        assert res.canonical_name == expected_canonical, f"Failed for Malayalam '{mal_name}' -> expected '{expected_canonical}'"
        assert res.resolution_source == "DISTRICT_ALIAS"


def test_invalid_district_with_valid_pincode(db_session):
    """8: Invalid district + valid Pincode resolves district using postal data."""
    res = DistrictResolutionService.resolve_district(
        raw_district="InvalidDistrictName123",
        pincode="673001",
        db=db_session,
        allow_postal_lookup=True
    )
    assert res.canonical_name == "Kozhikode"
    assert res.resolution_source == "PINCODE"
    assert res.district_status == "RESOLVED"
    assert res.district_id is not None


def test_missing_district_with_valid_pincode(db_session):
    """9: Missing district + valid Pincode resolves district using postal data."""
    res = DistrictResolutionService.resolve_district(
        raw_district=None,
        pincode="673638",
        db=db_session,
        allow_postal_lookup=True
    )
    assert res.canonical_name == "Malappuram"
    assert res.resolution_source == "PINCODE"
    assert res.district_status == "RESOLVED"
    assert len(res.post_offices) == 2


def test_invalid_district_and_invalid_pincode(db_session):
    """10: Invalid district + invalid Pincode results in UNRESOLVED status."""
    res = DistrictResolutionService.resolve_district(
        raw_district="NonExistentDistrict",
        pincode="000000",
        db=db_session,
        allow_postal_lookup=True
    )
    assert res.canonical_name is None
    assert res.district_id is None
    assert res.district_status == "UNRESOLVED"
    assert res.resolution_source == "UNRESOLVED"
    assert res.unresolved_reason is not None


def test_valid_district_and_valid_pincode_priority(db_session):
    """11: Valid district + valid pincode resolves with PINCODE priority."""
    res = DistrictResolutionService.resolve_district(
        raw_district="Ernakulam",
        pincode="682001",
        db=db_session,
        allow_postal_lookup=True
    )
    assert res.canonical_name == "Ernakulam"
    assert res.resolution_source == "PINCODE"
    assert res.district_status == "RESOLVED"


def test_multiple_post_offices_same_district(db_session):
    """12: Pincode with multiple Post Offices all under Malappuram resolves safely."""
    res = DistrictResolutionService.resolve_district(
        raw_district=None,
        pincode="673638",
        db=db_session,
        allow_postal_lookup=True
    )
    assert res.canonical_name == "Malappuram"
    assert res.resolution_source == "PINCODE"
    assert len(res.post_offices) == 2
    office_names = {po["office_name"] for po in res.post_offices}
    assert "Kondotti SO" in office_names
    assert "Arimbra BO" in office_names


def test_data_migration_deduplication(db_session):
    """13 & 14: Existing duplicate Kozhikode/Malappuram records merge into single canonical master id."""
    # Create legacy customers with mixed casing and Malayalam
    c1 = Customer(customer_name="Cust 1", district="Kozhikode")
    c2 = Customer(customer_name="Cust 2", district="KOZHIKODE")
    c3 = Customer(customer_name="Cust 3", district="കോഴിക്കോട്")
    c4 = Customer(customer_name="Cust 4", district="Calicut")
    c5 = Customer(customer_name="Cust 5", district="മലപ്പുറം")
    c6 = Customer(customer_name="Cust 6", district="Malappuram District")
    c7 = Customer(customer_name="Cust 7", district="Unknown District")

    db_session.add_all([c1, c2, c3, c4, c5, c6, c7])
    db_session.commit()

    stats = DistrictResolutionService.migrate_existing_data(db_session)
    assert stats["updated_count"] >= 6

    # Refresh records
    db_session.refresh(c1)
    db_session.refresh(c2)
    db_session.refresh(c3)
    db_session.refresh(c4)
    db_session.refresh(c5)
    db_session.refresh(c6)
    db_session.refresh(c7)

    # All Kozhikode variations share the exact same district_id
    kozhikode_master = db_session.query(DistrictMaster).filter(DistrictMaster.canonical_name == "Kozhikode").first()
    assert c1.district_id == kozhikode_master.id
    assert c2.district_id == kozhikode_master.id
    assert c3.district_id == kozhikode_master.id
    assert c4.district_id == kozhikode_master.id
    assert c1.district == "Kozhikode"
    assert c2.district == "Kozhikode"
    assert c3.district == "Kozhikode"
    assert c4.district == "Kozhikode"

    # All Malappuram variations share the exact same district_id
    malappuram_master = db_session.query(DistrictMaster).filter(DistrictMaster.canonical_name == "Malappuram").first()
    assert c5.district_id == malappuram_master.id
    assert c6.district_id == malappuram_master.id
    assert c5.district == "Malappuram"
    assert c6.district == "Malappuram"

    # Unknown record remains unresolved
    assert c7.district_id is None
    assert c7.district_status == "UNRESOLVED"


def test_district_analytics_single_row_grouping(db_session):
    """15 & 16: Analytics groups by canonical district; Kozhikode variations produce exactly ONE row."""
    # Pre-populate orders for Kozhikode variations
    km = db_session.query(DistrictMaster).filter(DistrictMaster.canonical_name == "Kozhikode").first()
    
    cust1 = Customer(customer_name="A", district_id=km.id, district="Kozhikode")
    cust2 = Customer(customer_name="B", district_id=km.id, district="Kozhikode")
    db_session.add_all([cust1, cust2])
    db_session.flush()

    o1 = Order(order_number="ORD-1", customer_id=cust1.id, total_amount=1500.0, order_status="DELIVERED", order_date=pytest.importorskip("datetime").datetime.utcnow())
    o2 = Order(order_number="ORD-2", customer_id=cust2.id, total_amount=2500.0, order_status="DELIVERED", order_date=pytest.importorskip("datetime").datetime.utcnow())
    db_session.add_all([o1, o2])
    db_session.commit()

    analytics = AnalyticsService.get_district_analytics(db_session)
    kozhikode_rows = [r for r in analytics if r["district"] == "Kozhikode"]
    assert len(kozhikode_rows) == 1
    assert kozhikode_rows[0]["customer_count"] == 2
    assert kozhikode_rows[0]["total_orders"] == 2
    assert kozhikode_rows[0]["total_revenue"] == 4000.0


def test_location_service_manual_correction(db_session):
    """18: LocationService manual edit triggers DistrictResolutionService."""
    c = Customer(customer_name="Test Customer", district=None, pincode=None)
    db_session.add(c)
    db_session.commit()

    req = LocationCorrectionRequest(district="കണ്ണൂർ", pincode="670001", source="MANUAL")
    updated = LocationService.correct_customer_location(db_session, c.id, req)

    assert updated.district_resolution_source in ["PINCODE", "DISTRICT_DIRECT_MATCH", "DISTRICT_ALIAS", "MANUAL", "MANUAL_CONFIRMATION"]
