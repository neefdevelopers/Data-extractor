import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.employee import Employee
from app.models.postal import PostalMaster, PostalOffice
from app.utils.text_normalization import canonical_key, clean_display_text, ci_equals, ci_contains
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.analytics_service import AnalyticsService
from app.services.customer_service import CustomerService
from app.services.product_service import ProductService
from app.services.employee_service import EmployeeService
from app.services.postal_service import PostalService
from app.services.deduplication_service import DeduplicationService
from app.services.excel_import_service import ExcelImportService

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

def test_canonical_key_and_ci_helpers():
    # Whitespace and casing invariance tests
    assert canonical_key("Malappuram") == "malappuram"
    assert canonical_key("  malappuram  ") == "malappuram"
    assert canonical_key("MALAPPURAM") == "malappuram"
    assert canonical_key("MaLaPpUrAm") == "malappuram"
    assert canonical_key(" Kozhikode ") == "kozhikode"
    assert canonical_key("KOZHIKODE") == "kozhikode"

    assert ci_equals("Malappuram", "malappuram")
    assert ci_equals("MALAPPURAM", "  Malappuram  ")
    assert ci_equals("Post Office", "post office")
    assert ci_equals("POST OFFICE", "  POST  OFFICE  ")

    assert ci_contains("Kozhikode Town", "kozhikode")
    assert ci_contains("Malappuram H.O", "  MALAPPURAM  ")

    # Clean display formatting preserves casing
    assert clean_display_text("  malappuram  ", title_case=True) == "Malappuram"
    assert clean_display_text("  Hair Oil + Shampoo  ") == "Hair Oil + Shampoo"

def test_customer_search_case_insensitivity(db_session):
    c1 = Customer(
        customer_name="Fathima Nasrin",
        contact_number="9876543210",
        normalized_contact="9876543210",
        district="Malappuram",
        pincode="676505",
        post_office="Manjeri",
        total_orders=2,
        total_spend=1500.0
    )
    c2 = Customer(
        customer_name="RAHUL SHARMA",
        contact_number="9876543211",
        normalized_contact="9876543211",
        district="KOZHIKODE",
        pincode="673001",
        post_office="Calicut H.O",
        total_orders=1,
        total_spend=800.0
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    # Search customer with lowercase and extra spaces
    results, count = CustomerService.get_customers(db_session, search="  fathima  ")
    assert count == 1
    assert results[0].customer_name == "Fathima Nasrin"

    results, count = CustomerService.get_customers(db_session, search="rahul")
    assert count == 1
    assert results[0].customer_name == "RAHUL SHARMA"

    # Search by district in different casings
    results, count = CustomerService.get_customers(db_session, district="malappuram")
    assert count == 1
    results, count = CustomerService.get_customers(db_session, district="  MALAPPURAM  ")
    assert count == 1
    results, count = CustomerService.get_customers(db_session, district="kozhikode")
    assert count == 1

    # Search by post office
    results, count = CustomerService.get_customers(db_session, post_office="manjeri")
    assert count == 1
    results, count = CustomerService.get_customers(db_session, post_office="CALICUT")
    assert count == 1

def test_district_analytics_grouping_case_insensitivity(db_session):
    # Multiple customers in Malappuram with different casings and whitespace
    c1 = Customer(customer_name="Cust 1", district="Malappuram", pincode="676505")
    c2 = Customer(customer_name="Cust 2", district="malappuram", pincode="676506")
    c3 = Customer(customer_name="Cust 3", district="  MALAPPURAM  ", pincode="676507")
    c4 = Customer(customer_name="Cust 4", district="Kozhikode", pincode="673001")
    c5 = Customer(customer_name="Cust 5", district="KOZHIKODE", pincode="673002")

    db_session.add_all([c1, c2, c3, c4, c5])
    db_session.commit()

    now = datetime.datetime.utcnow()
    o1 = Order(order_number="ORD-1", customer_id=c1.id, order_date=now, payment_mode="COD", order_status="DELIVERED", total_amount=1000.0)
    o2 = Order(order_number="ORD-2", customer_id=c2.id, order_date=now, payment_mode="COD", order_status="DELIVERED", total_amount=2000.0)
    o3 = Order(order_number="ORD-3", customer_id=c3.id, order_date=now, payment_mode="PREPAID", order_status="DELIVERED", total_amount=1500.0)
    o4 = Order(order_number="ORD-4", customer_id=c4.id, order_date=now, payment_mode="COD", order_status="DELIVERED", total_amount=500.0)
    o5 = Order(order_number="ORD-5", customer_id=c5.id, order_date=now, payment_mode="PREPAID", order_status="DELIVERED", total_amount=700.0)

    db_session.add_all([o1, o2, o3, o4, o5])
    db_session.commit()

    districts = AnalyticsService.get_district_analytics(db_session)
    
    # Should consolidate into exactly 2 districts: Malappuram and Kozhikode
    assert len(districts) == 2
    
    malappuram_stat = next(d for d in districts if d["district"].lower() == "malappuram")
    assert malappuram_stat["customer_count"] == 3
    assert malappuram_stat["total_orders"] == 3
    assert malappuram_stat["total_revenue"] == 4500.0

    kozhikode_stat = next(d for d in districts if d["district"].lower() == "kozhikode")
    assert kozhikode_stat["customer_count"] == 2
    assert kozhikode_stat["total_orders"] == 2
    assert kozhikode_stat["total_revenue"] == 1200.0

def test_duplicate_detection_case_insensitivity(db_session):
    c1 = Customer(
        customer_name="Amina Beevi",
        pincode="676505",
        district="Malappuram"
    )
    db_session.add(c1)
    db_session.commit()

    # Secondary match: same name in ALL CAPS with whitespace + same PIN
    matched, rule = DuplicateDetectionService.find_matching_customer(
        db_session,
        customer_name="  AMINA BEEVI  ",
        pincode=" 676505 "
    )
    assert matched is not None
    assert matched.id == c1.id
    assert rule == "SECONDARY_NAME_PIN_MATCH"

def test_product_and_employee_search_case_insensitivity(db_session):
    p = Product(product_name="Ayurvedic Hair Oil", sku="AHO-100", category="Hair Care", price=499.0)
    e = Employee(employee_name="Nasrin C", employee_code="EMP-NAS-01", status="ACTIVE")
    db_session.add_all([p, e])
    db_session.commit()

    # Product search with mixed case
    p_res, p_cnt = ProductService.get_products_analytics(db_session, search="ayurvedic HAIR")
    assert p_cnt == 1
    assert p_res[0]["product_name"] == "Ayurvedic Hair Oil"

    # Employee search with mixed case
    e_res, e_cnt = EmployeeService.get_employees_analytics(db_session, search="nasrin")
    assert e_cnt == 1
    assert e_res[0]["employee_name"] == "Nasrin C"

def test_safe_deduplication_and_merge(db_session):
    # Create two duplicate customer records with different casings
    c1 = Customer(customer_name="John Doe", normalized_contact="9895000001", district="Malappuram", pincode="676505")
    c2 = Customer(customer_name="JOHN DOE", normalized_contact="9895000001", district="MALAPPURAM", pincode="676505", full_address="House #12, Calicut Road")
    db_session.add_all([c1, c2])
    db_session.commit()

    now = datetime.datetime.utcnow()
    o1 = Order(order_number="ORD-101", customer_id=c1.id, order_date=now, payment_mode="COD", order_status="DELIVERED", total_amount=1000.0)
    o2 = Order(order_number="ORD-102", customer_id=c2.id, order_date=now, payment_mode="COD", order_status="DELIVERED", total_amount=1500.0)
    db_session.add_all([o1, o2])
    db_session.commit()

    # Run deduplication
    result = DeduplicationService.merge_all_duplicates(db_session)
    assert result["customers"]["merged_count"] == 1

    remaining_customers = db_session.query(Customer).all()
    assert len(remaining_customers) == 1
    merged_cust = remaining_customers[0]
    
    # Verify orders were consolidated
    assert merged_cust.total_orders == 2
    assert merged_cust.total_spend == 2500.0
    assert merged_cust.full_address == "House #12, Calicut Road"
    assert merged_cust.district == "Malappuram"

def test_district_canonical_normalization(db_session):
    # Customers with various historical/spelling variations of Kozhikode & Calicut
    c1 = Customer(customer_name="Cust 1", contact_number="98765001", district="Kozhikode", pincode="673001")
    c2 = Customer(customer_name="Cust 2", contact_number="98765002", district="Calicut", pincode="673002")
    c3 = Customer(customer_name="Cust 3", contact_number="98765003", district="Kozhikkode", pincode="673003")
    c4 = Customer(customer_name="Cust 4", contact_number="98765004", district="-Kozhikode", pincode="673004")
    c5 = Customer(customer_name="Cust 5", contact_number="98765005", district="Kozhikode, Feroke kallikkudam", pincode="673631")
    db_session.add_all([c1, c2, c3, c4, c5])
    db_session.commit()

    now = datetime.datetime.utcnow()
    for idx, c in enumerate([c1, c2, c3, c4, c5], 1):
        db_session.add(Order(
            order_number=f"ORD-KOZH-{idx}",
            customer_id=c.id,
            order_date=now,
            payment_mode="COD",
            order_status="DELIVERED",
            total_amount=500.0
        ))
    db_session.commit()

    dist_analytics = AnalyticsService.get_district_analytics(db_session)
    # Ensure there is only 1 entry for Kozhikode across all variations
    kozh_entries = [d for d in dist_analytics if "kozh" in d["district"].lower() or "calicut" in d["district"].lower()]
    assert len(kozh_entries) == 1
    assert kozh_entries[0]["district"] == "Kozhikode"
    assert kozh_entries[0]["customer_count"] == 5
    assert kozh_entries[0]["total_orders"] == 5
    assert kozh_entries[0]["total_revenue"] == 2500.0

