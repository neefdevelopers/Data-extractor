import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.database.reset_db import reset_database, get_table_counts, APPLICATION_TABLES, PRESERVED_TABLES
from app.models.customer import Customer
from app.models.order import Order
from app.models.product import Product
from app.models.employee import Employee
from app.models.district import DistrictMaster
from app.services.district_resolution_service import DistrictResolutionService

def test_reset_database_safely_clears_application_data_and_preserves_master():
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSession()

    try:
        # Seed master
        DistrictResolutionService.seed_master_districts(session)

        # Insert dummy application data
        prod = Product(product_name="Test Product", price=100.0)
        emp = Employee(employee_name="Test Agent")
        cust = Customer(customer_name="Test Customer", pincode="676505", district="Malappuram")
        session.add_all([prod, emp, cust])
        session.commit()

        import uuid
        unique_ord = f"ORD-RESET-{uuid.uuid4().hex[:8]}"
        # Add order
        order = Order(order_number=unique_ord, customer_id=cust.id, order_date=cust.created_at, total_amount=100.0)
        session.add(order)
        session.commit()

        # Verify records exist before reset
        counts_before = get_table_counts(session)
        assert counts_before["customers"] >= 1
        assert counts_before["orders"] >= 1
        assert counts_before["products"] >= 1
        assert counts_before["employees"] >= 1

        # Execute reset with force=True on isolated test session
        result = reset_database(force=True, session=session, db_url="sqlite:///:memory:")
        assert result is True

        # Check counts after reset
        counts_after = get_table_counts(session)
        for tbl, _, _ in APPLICATION_TABLES:
            assert counts_after[tbl] == 0, f"Table {tbl} was expected to be 0 after reset, got {counts_after[tbl]}"

        # Master districts must remain preserved with exactly 14 records
        assert counts_after["district_master"] == 14
    finally:
        session.close()
