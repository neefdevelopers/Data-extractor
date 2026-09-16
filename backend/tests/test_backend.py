import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from app.models.employee import Employee
from app.models.postal import PostalMaster, PostalOffice
from app.services.revenue_service import RevenueService
from app.services.rfm_service import RFMService
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.utils.cleaning import normalize_name, normalize_mobile, normalize_pincode

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_data_cleaning():
    assert normalize_name("  aarav sharma  ") == "Aarav Sharma"
    
    phone, valid = normalize_mobile("+91 98201 12345")
    assert valid is True
    assert phone == "9820112345"

    phone2, valid2 = normalize_mobile("09820112345")
    assert valid2 is True
    assert phone2 == "9820112345"

    pin, pin_valid = normalize_pincode("400050")
    assert pin_valid is True
    assert pin == "400050"

    bad_pin, bad_pin_valid = normalize_pincode("123")
    assert bad_pin_valid is False

def test_duplicate_detection(db_session):
    cust = Customer(
        customer_name="Test Customer",
        contact_number="9876543210",
        normalized_contact="9876543210",
        pincode="400050",
        district="Mumbai"
    )
    db_session.add(cust)
    db_session.commit()

    matched, rule = DuplicateDetectionService.find_matching_customer(
        db_session, normalized_contact="9876543210"
    )
    assert matched is not None
    assert rule == "PRIMARY_PHONE_MATCH"

    matched2, rule2 = DuplicateDetectionService.find_matching_customer(
        db_session, customer_name="Test Customer", pincode="400050"
    )
    assert matched2 is not None
    assert rule2 == "SECONDARY_NAME_PIN_MATCH"

def test_revenue_and_rfm(db_session):
    import datetime
    cust = Customer(
        customer_name="RFM Tester",
        contact_number="9999988888",
        normalized_contact="9999988888"
    )
    db_session.add(cust)
    db_session.commit()

    order1 = Order(
        order_number="ORD-TEST-1",
        customer_id=cust.id,
        order_date=datetime.datetime.utcnow() - datetime.timedelta(days=10),
        total_amount=2500.0,
        order_status="DELIVERED"
    )
    order2 = Order(
        order_number="ORD-TEST-2",
        customer_id=cust.id,
        order_date=datetime.datetime.utcnow() - datetime.timedelta(days=2),
        total_amount=3500.0,
        order_status="DELIVERED"
    )
    db_session.add_all([order1, order2])
    db_session.commit()

    res = RFMService.recalculate_all_rfm(db_session)
    assert res["total_processed"] == 1

    db_session.refresh(cust)
    assert cust.total_orders == 2
    assert cust.total_spend == 6000.0
    assert cust.average_order_value == 3000.0
    assert cust.rfm_segment is not None
