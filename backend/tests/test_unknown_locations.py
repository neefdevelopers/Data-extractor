import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.models.customer import Customer
from app.models.order import Order
from app.models.location_audit import LocationCorrectionAudit
from app.models.postal import PostalMaster, PostalOffice
from app.schemas.location import (
    LocationCorrectionRequest,
    BulkLocationCorrectionRequest
)
from app.services.location_service import LocationService

# In-memory SQLite engine for tests
TEST_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=TEST_ENGINE)
    db = TestSession()
    yield db
    db.close()
    Base.metadata.drop_all(bind=TEST_ENGINE)

def test_unknown_locations_summary_and_records(db_session):
    # Customer 1: Unknown PIN only
    c1 = Customer(
        customer_name="Amina Beevi",
        contact_number="9876500001",
        pincode=None,
        district="Malappuram",
        state="Kerala"
    )
    # Customer 2: Unknown District only
    c2 = Customer(
        customer_name="Rahul Sharma",
        contact_number="9876500002",
        pincode="676505",
        district="Unknown",
        state="Kerala"
    )
    # Customer 3: Both Unknown (pincode "000000", district "Unassigned")
    c3 = Customer(
        customer_name="Sneha Paul",
        contact_number="9876500003",
        pincode="000000",
        district="Unassigned",
        state=None
    )
    # Customer 4: Valid Location
    c4 = Customer(
        customer_name="Mohammed Ali",
        contact_number="9876500004",
        pincode="673001",
        district="Kozhikode",
        state="Kerala"
    )
    db_session.add_all([c1, c2, c3, c4])
    db_session.commit()

    # Test Summary KPIs
    summary = LocationService.get_unknown_summary(db_session)
    assert summary.unknown_pincode_count == 2  # c1 (None) and c3 ("000000")
    assert summary.unknown_district_count == 2  # c2 ("Unknown") and c3 ("Unassigned")
    assert summary.both_unknown_count == 1      # c3
    assert summary.total_unresolved == 3        # c1, c2, c3 (unique, no double count)

    # Test Records Filtering
    all_res = LocationService.get_unknown_records(db_session, filter_type="all")
    assert all_res.total == 3
    names = [r.customer_name for r in all_res.items]
    assert "Amina Beevi" in names
    assert "Rahul Sharma" in names
    assert "Sneha Paul" in names
    assert "Mohammed Ali" not in names

    pin_res = LocationService.get_unknown_records(db_session, filter_type="unknown_pincode")
    assert pin_res.total == 2
    pin_names = [r.customer_name for r in pin_res.items]
    assert "Amina Beevi" in pin_names
    assert "Sneha Paul" in pin_names

    dist_res = LocationService.get_unknown_records(db_session, filter_type="unknown_district")
    assert dist_res.total == 2
    dist_names = [r.customer_name for r in dist_res.items]
    assert "Rahul Sharma" in dist_names
    assert "Sneha Paul" in dist_names

    # Test Search filter
    search_res = LocationService.get_unknown_records(db_session, filter_type="all", search="Amina")
    assert search_res.total == 1
    assert search_res.items[0].customer_name == "Amina Beevi"

def test_single_location_correction(db_session):
    c = Customer(
        customer_name="Test Customer",
        contact_number="9876500010",
        pincode=None,
        district="Unknown",
        state=None
    )
    db_session.add(c)
    db_session.commit()

    req = LocationCorrectionRequest(
        pincode="676505",
        district="Malappuram",
        state="Kerala",
        post_office="Manjeri H.O",
        source="MANUAL",
        notes="Verified via phone call"
    )

    updated_cust = LocationService.correct_customer_location(db_session, c.id, req)
    assert updated_cust.pincode == "676505"
    assert updated_cust.district == "Malappuram"
    assert updated_cust.state == "Kerala"
    assert updated_cust.post_office == "Manjeri H.O"

    # Check Audit History
    audits = LocationService.get_audit_history(db_session, customer_id=c.id)
    assert audits.total == 1
    log = audits.items[0]
    assert log.customer_id == c.id
    assert log.new_pincode == "676505"
    assert log.new_district == "Malappuram"
    assert log.correction_source == "MANUAL"
    assert log.notes == "Verified via phone call"

    # Verify summary drops to 0
    summary = LocationService.get_unknown_summary(db_session)
    assert summary.total_unresolved == 0

def test_bulk_location_correction(db_session):
    c1 = Customer(
        customer_name="Bulk User 1",
        contact_number="9876500021",
        pincode=None,
        district="Unknown",
        state=None
    )
    c2 = Customer(
        customer_name="Bulk User 2",
        contact_number="9876500022",
        pincode=None,
        district="Unknown",
        state=None
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    bulk_req = BulkLocationCorrectionRequest(
        customer_ids=[c1.id, c2.id],
        pincode="673001",
        district="Kozhikode",
        state="Kerala",
        post_office="Calicut H.O",
        notes="Bulk batch fix"
    )

    res = LocationService.bulk_correct_locations(db_session, bulk_req)
    assert res["updated_count"] == 2

    db_session.refresh(c1)
    db_session.refresh(c2)
    assert c1.pincode == "673001"
    assert c1.district == "Kozhikode"
    assert c2.pincode == "673001"
    assert c2.district == "Kozhikode"

    # Check audits
    audits = LocationService.get_audit_history(db_session)
    assert audits.total == 2
