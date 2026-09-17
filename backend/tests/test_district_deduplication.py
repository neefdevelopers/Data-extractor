import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.models.customer import Customer
from app.models.order import Order
from app.models.district import DistrictMaster
from app.models.postal import PostalMaster
from app.models.data_quality import DataQualityIssue
from app.utils.district_normalization import (
    normalize_district_name,
    get_normalized_district_key,
    clean_district_string,
    strip_district_suffixes,
    OFFICIAL_KERALA_DISTRICTS
)
from app.services.district_service import DistrictService
from app.services.analytics_service import AnalyticsService
from app.services.customer_service import CustomerService
from app.services.location_service import LocationService
from app.services.postal_service import PostalService
from app.services.excel_import_service import ExcelImportService
from app.schemas.location import LocationCorrectionRequest, BulkLocationCorrectionRequest

# In-memory SQLite test engine
TEST_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=TEST_ENGINE)
    session = TestSession()
    DistrictService.seed_master_districts(session)
    yield session
    session.close()
    Base.metadata.drop_all(bind=TEST_ENGINE)

def test_acceptance_criteria_malappuram_variations(db):
    """
    Acceptance Test 1:
    Test these raw values:
    "Malappuram", "malappuram", "MALAPPURAM", "MaLaPpUrAm", " Malappuram ",
    "Malappuram District", "malappuram district", "മലപ്പുറം"
    All must resolve to:
    canonical_name = "Malappuram"
    normalized_key = "malappuram"
    same district_id
    """
    variations = [
        "Malappuram",
        "malappuram",
        "MALAPPURAM",
        "MaLaPpUrAm",
        " Malappuram ",
        "Malappuram District",
        "malappuram district",
        "മലപ്പുറം",
        "മലപ്പുറം ജില്ല"
    ]

    district_ids = set()
    for raw in variations:
        canon_name, canon_state = normalize_district_name(raw)
        norm_key = get_normalized_district_key(raw)
        assert canon_name == "Malappuram", f"Failed for {raw}: got {canon_name}"
        assert norm_key == "malappuram", f"Failed key for {raw}: got {norm_key}"
        assert canon_state == "Kerala"

        dist_obj, name, st = DistrictService.get_or_create_district(raw, db=db)
        assert dist_obj is not None
        assert dist_obj.canonical_name == "Malappuram"
        assert dist_obj.normalized_key == "malappuram"
        district_ids.add(dist_obj.id)

    # All must resolve to the exact same district_id
    assert len(district_ids) == 1

def test_all_14_kerala_districts_malayalam_mapping(db):
    """
    Acceptance Test 2:
    Malayalam -> English canonical mapping for all 14 official Kerala districts
    """
    kerala_test_pairs = [
        ("മലപ്പുറം", "Malappuram"),
        ("കോഴിക്കോട്", "Kozhikode"),
        ("കാലിക്കറ്റ്", "Kozhikode"),
        ("കണ്ണൂർ", "Kannur"),
        ("വയനാട്", "Wayanad"),
        ("പാലക്കാട്", "Palakkad"),
        ("തൃശൂർ", "Thrissur"),
        ("തൃശ്ശൂർ", "Thrissur"),
        ("എറണാകുളം", "Ernakulam"),
        ("കൊച്ചി", "Ernakulam"),
        ("ഇടുക്കി", "Idukki"),
        ("കോട്ടയം", "Kottayam"),
        ("ആലപ്പുഴ", "Alappuzha"),
        ("പത്തനംതിട്ട", "Pathanamthitta"),
        ("കൊല്ലം", "Kollam"),
        ("തിരുവനന്തപുരം", "Thiruvananthapuram"),
        ("കാസർഗോഡ്", "Kasaragod"),
        ("കാസർകോട്", "Kasaragod"),
    ]

    for mal_name, expected_eng in kerala_test_pairs:
        canon_name, canon_st = normalize_district_name(mal_name)
        assert canon_name == expected_eng, f"Expected {expected_eng} for {mal_name}, got {canon_name}"
        assert canon_st == "Kerala"

        dist_obj, _, _ = DistrictService.get_or_create_district(mal_name, db=db)
        assert dist_obj.canonical_name == expected_eng

def test_district_analytics_grouping_no_duplicate_rows(db):
    """
    Acceptance Test 3:
    Analytics must group by canonical district ID and display ONLY canonical English name.
    """
    c1 = Customer(customer_name="Customer A", district="Malappuram", pincode="676505")
    c2 = Customer(customer_name="Customer B", district="malappuram", pincode="676506")
    c3 = Customer(customer_name="Customer C", district="MALAPPURAM", pincode="676507")
    c4 = Customer(customer_name="Customer D", district="മലപ്പുറം", pincode="676508")
    c5 = Customer(customer_name="Customer E", district="Malappuram District", pincode="676509")

    # Another district with casing variations
    c6 = Customer(customer_name="Customer F", district="കോഴിക്കോട്", pincode="673001")
    c7 = Customer(customer_name="Customer G", district="KOZHIKODE", pincode="673002")

    db.add_all([c1, c2, c3, c4, c5, c6, c7])
    db.commit()

    now = datetime.datetime.utcnow()
    # Add orders
    for idx, cust in enumerate([c1, c2, c3, c4, c5], 1):
        db.add(Order(order_number=f"ORD-M-{idx}", customer_id=cust.id, order_date=now, payment_mode="COD", order_status="DELIVERED", total_amount=1000.0))
    for idx, cust in enumerate([c6, c7], 1):
        db.add(Order(order_number=f"ORD-K-{idx}", customer_id=cust.id, order_date=now, payment_mode="PREPAID", order_status="DELIVERED", total_amount=500.0))
    db.commit()

    analytics = AnalyticsService.get_district_analytics(db)

    # Must contain exactly 2 rows
    assert len(analytics) == 2

    # Malappuram must aggregate all 5 customers and 5 orders
    malappuram_row = next((d for d in analytics if d["district"] == "Malappuram"), None)
    assert malappuram_row is not None
    assert malappuram_row["district"] == "Malappuram"
    assert malappuram_row["customer_count"] == 5
    assert malappuram_row["total_orders"] == 5
    assert malappuram_row["total_revenue"] == 5000.0

    # Kozhikode must aggregate both customers and orders
    kozhikode_row = next((d for d in analytics if d["district"] == "Kozhikode"), None)
    assert kozhikode_row is not None
    assert kozhikode_row["district"] == "Kozhikode"
    assert kozhikode_row["customer_count"] == 2
    assert kozhikode_row["total_orders"] == 2
    assert kozhikode_row["total_revenue"] == 1000.0

    # Assert NO Malayalam rows exist in results
    mal_rows = [d for d in analytics if d["district"] in ["മലപ്പുറം", "കോഴിക്കോട്"]]
    assert len(mal_rows) == 0

def test_existing_data_migration_safety(db):
    """
    Acceptance Test 4:
    Existing customer records with raw variations are safely migrated to canonical district ID and name.
    """
    c1 = Customer(customer_name="Cust 1", district="Malappuram", pincode="676505")
    c2 = Customer(customer_name="Cust 2", district="malappuram", pincode="676506")
    c3 = Customer(customer_name="Cust 3", district="MALAPPURAM", pincode="676507")
    c4 = Customer(customer_name="Cust 4", district="മലപ്പുറം", pincode="676508")
    c5 = Customer(customer_name="Cust 5", district="Malappuram District", pincode="676509")
    c6 = Customer(customer_name="Cust 6", district="Unknown", pincode="000000")
    c7 = Customer(customer_name="Cust 7", district=None, pincode=None)

    db.add_all([c1, c2, c3, c4, c5, c6, c7])
    db.commit()

    res = DistrictService.migrate_existing_data(db)
    assert res["total_customers"] == 7

    # Verify all Malappuram customers share the same district_id and canonical name
    db.refresh(c1)
    db.refresh(c2)
    db.refresh(c3)
    db.refresh(c4)
    db.refresh(c5)
    db.refresh(c6)
    db.refresh(c7)

    target_id = c1.district_id
    assert target_id is not None
    for c in [c1, c2, c3, c4, c5]:
        assert c.district_id == target_id
        assert c.district == "Malappuram"

    # Unknown customers must have district_id = None
    assert c6.district_id is None
    assert c7.district_id is None

def test_manual_data_entry_and_correction(db):
    """
    Acceptance Test 5:
    Manual location correction with Malayalam / uppercase resolves to canonical district.
    """
    cust = Customer(customer_name="Test User", district="Unknown", pincode="676505")
    db.add(cust)
    db.commit()
    db.refresh(cust)

    # Correct with Malayalam text
    req = LocationCorrectionRequest(district="മലപ്പുറം", pincode="676505")
    updated = LocationService.correct_customer_location(db, cust.id, req)

    assert updated.district == "Malappuram"
    assert updated.district_id is not None

    # Bulk correct with uppercase
    cust2 = Customer(customer_name="Test User 2", district="Unknown", pincode="673001")
    db.add(cust2)
    db.commit()
    db.refresh(cust2)

    bulk_req = BulkLocationCorrectionRequest(customer_ids=[cust2.id], district="  KOZHIKODE DISTRICT  ")
    LocationService.bulk_correct_locations(db, bulk_req)

    db.refresh(cust2)
    assert cust2.district == "Kozhikode"
    assert cust2.district_id is not None

def test_postal_enrichment_and_conflict_avoidance(db):
    """
    Acceptance Test 6:
    Postal service normalizes district, and conflict check does not flag valid aliases.
    """
    postal = PostalMaster(pincode="676505", district="Malappuram", state="Kerala")
    db.add(postal)
    db.commit()

    # Conflict check with Malayalam alias: should NOT log a conflict
    PostalService._check_conflict(postal, client_district="മലപ്പുറം", client_po=None, db=db)
    issues = db.query(DataQualityIssue).filter(DataQualityIssue.entity_id == "676505").all()
    assert len(issues) == 0

    # Conflict check with casing alias: should NOT log a conflict
    PostalService._check_conflict(postal, client_district="MALAPPURAM DISTRICT", client_po=None, db=db)
    issues = db.query(DataQualityIssue).filter(DataQualityIssue.entity_id == "676505").all()
    assert len(issues) == 0

def test_unknown_district_remains_unresolved(db):
    """
    Acceptance Test 7:
    'Unknown', 'unknown', 'Unassigned' resolve to district_id = None and do NOT create DistrictMaster records.
    """
    for unk in ["Unknown", "UNKNOWN", "unknown", "Unassigned", "n/a", "", None]:
        dist_obj, name, st = DistrictService.get_or_create_district(unk, db=db)
        assert dist_obj is None
        assert name is None

    # Check that no DistrictMaster record with name 'Unknown' exists
    unk_masters = db.query(DistrictMaster).filter(DistrictMaster.normalized_key == "unknown").all()
    assert len(unk_masters) == 0

def test_search_and_filter_by_malayalam_and_english(db):
    """
    Acceptance Test 8:
    Search and filter by Malayalam or case variation returns the canonical district records.
    """
    dist_obj, _, _ = DistrictService.get_or_create_district("Malappuram", db=db)
    c1 = Customer(customer_name="Fathima", district="Malappuram", district_id=dist_obj.id, pincode="676505")
    db.add(c1)
    db.commit()

    # Search with Malayalam filter
    res, count = CustomerService.get_customers(db, district="മലപ്പുറം")
    assert count == 1
    assert res[0].id == c1.id

    # Search with uppercase filter
    res, count = CustomerService.get_customers(db, district="MALAPPURAM")
    assert count == 1
    assert res[0].id == c1.id

    # General search query with Malayalam
    res, count = CustomerService.get_customers(db, search="മലപ്പുറം")
    assert count == 1
    assert res[0].id == c1.id

    # Pincode analytics with Malayalam district filter
    pin_analytics = AnalyticsService.get_pincode_analytics(db, district="മലപ്പുറം")
    assert len(pin_analytics) == 1
    assert pin_analytics[0]["district"] == "Malappuram"

    # Search in district analytics
    dist_analytics = AnalyticsService.get_district_analytics(db, search="മലപ്പുറം")
    assert len(dist_analytics) == 1
    assert dist_analytics[0]["district"] == "Malappuram"

def test_business_dashboard_district_filters(db):
    """
    Acceptance Test 9:
    Business Dashboard correctly filters by Malayalam and English district aliases.
    """
    dist_obj, _, _ = DistrictService.get_or_create_district("Malappuram", db=db)
    c1 = Customer(customer_name="Cust 1", district="Malappuram", district_id=dist_obj.id, pincode="676505")
    db.add(c1)
    db.commit()

    now = datetime.datetime.utcnow()
    o1 = Order(order_number="ORD-DASH-1", customer_id=c1.id, order_date=now, payment_mode="COD", order_status="DELIVERED", total_amount=2500.0)
    db.add(o1)
    db.commit()

    # Query with Malayalam district filter
    dash_mal = AnalyticsService.get_business_dashboard(db, district="മലപ്പുറം")
    assert dash_mal["total_orders"] == 1
    assert dash_mal["total_revenue"] == 2500.0

    # Query with uppercase district filter
    dash_eng = AnalyticsService.get_business_dashboard(db, district="  MALAPPURAM  ")
    assert dash_eng["total_orders"] == 1
    assert dash_eng["total_revenue"] == 2500.0

def test_export_geographic_uses_canonical_names(db):
    """
    Acceptance Test 10:
    Export geographic service exports canonical English district names.
    """
    from app.services.export_service import ExportService
    import pandas as pd

    c1 = Customer(customer_name="Cust 1", district="മലപ്പുറം", pincode="676505")
    db.add(c1)
    db.commit()

    filepath = ExportService.export_geographic(db, format_type="csv")
    df = pd.read_csv(filepath)

    assert "district" in df.columns
    # Ensure Malappuram is present in canonical English and no Malayalam text is exported
    districts = list(df["district"])
    assert "Malappuram" in districts
    assert "മലപ്പുറം" not in districts

def test_district_master_unique_constraint(db):
    """
    Acceptance Test 11:
    Duplicate district master with same normalized key cannot be inserted.
    """
    m1 = DistrictMaster(canonical_name="Malappuram", state="Kerala", normalized_key="malappuram_test_key")
    db.add(m1)
    db.commit()

    m2 = DistrictMaster(canonical_name="MALAPPURAM", state="Kerala", normalized_key="malappuram_test_key")
    db.add(m2)
    with pytest.raises(Exception):
        db.commit()
    db.rollback()
