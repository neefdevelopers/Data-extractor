import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.session import Base
from app.services.sample_data_service import SampleDataService
from app.services.excel_import_service import ExcelImportService
from app.services.analytics_service import AnalyticsService
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.employee_service import EmployeeService
from app.services.rfm_service import RFMService
from app.services.export_service import ExportService
from app.services.data_quality_service import DataQualityService

def test_full_pipeline():
    # Setup test database
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    # 1. Generate sample excel file
    excel_path = SampleDataService.generate_sample_excel_path()
    assert os.path.exists(excel_path)

    # 2. Analyze file
    with open(excel_path, "rb") as f:
        file_bytes = f.read()
    filename = os.path.basename(excel_path)
    analysis = ExcelImportService.analyze_file(file_bytes, filename)
    assert analysis["total_rows"] > 0
    assert len(analysis["detected_columns"]) >= 10
    assert analysis["suggested_import_type"] == "COMBINED"

    # 3. Confirm & Import
    batch = ExcelImportService.process_import(
        temp_file_id=analysis["temp_file_id"],
        original_filename=filename,
        import_type=analysis["suggested_import_type"],
        column_mapping=analysis["auto_mappings"],
        db=db
    )
    assert batch.successful_rows > 0
    assert batch.new_customers > 0
    assert batch.new_orders > 0

    # 4. Verify Customer Service
    customers, total_cust = CustomerService.get_customers(db)
    assert total_cust == batch.new_customers
    first_cust = customers[0]
    detail = CustomerService.get_customer_by_id(db, first_cust.id)
    assert detail is not None
    assert detail.formatted_clipboard_text is not None
    assert "Name:" in detail.formatted_clipboard_text

    # 5. Verify Orders & Centralized Revenue
    orders, total_ord = OrderService.get_orders(db)
    assert total_ord == batch.new_orders
    for o in orders:
        assert o["revenue_amount"] >= 0.0

    # 6. Verify Business Analytics & KPIs (Business Dashboard counts revenue-eligible orders per RevenueService)
    kpis = AnalyticsService.get_business_dashboard(db)
    assert kpis["total_revenue"] > 0
    assert kpis["total_orders"] <= total_ord
    assert kpis["total_orders"] > 0
    assert kpis["total_customers"] > 0
    assert len(kpis["payment_breakdown"]) == 2

    # 7. Verify RFM Recalculation
    rfm_res = RFMService.recalculate_all_rfm(db)
    assert rfm_res["total_processed"] == total_cust

    # 8. Verify Product & Employee Analytics
    products, total_prod = ProductService.get_products_analytics(db)
    assert total_prod > 0
    employees, total_emp = EmployeeService.get_employees_analytics(db)
    assert total_emp > 0

    # 9. Verify Geographic Analytics
    districts = AnalyticsService.get_district_analytics(db)
    assert len(districts) > 0

    # 10. Verify Local Exports
    cust_export = ExportService.export_customers(db, "xlsx")
    assert os.path.exists(cust_export)

    ord_export = ExportService.export_orders(db, "csv")
    assert os.path.exists(ord_export)

    # 11. Verify Data Quality
    dq_summary = DataQualityService.get_summary(db)
    assert "total_issues" in dq_summary

    db.close()
