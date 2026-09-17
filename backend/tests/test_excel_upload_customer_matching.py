import io
import random
import uuid
import pytest
import pandas as pd
from app.database.session import SessionLocal, init_database
from app.services.excel_import_service import ExcelImportService
from app.models.customer import Customer
from app.models.upload import UploadBatch, UploadRow
from app.utils.cleaning import normalize_mobile, normalize_name

init_database()

def test_normalize_mobile_various_formats():
    # Standard 10 digit
    num, valid = normalize_mobile("9847123456")
    assert num == "9847123456" and valid is True

    # Float from excel (e.g. 9847123456.0)
    num, valid = normalize_mobile(9847123456.0)
    assert num == "9847123456" and valid is True

    # Scientific notation string (e.g. "9.847123456e+09")
    num, valid = normalize_mobile("9.847123456e+09")
    assert num == "9847123456" and valid is True

    # Country code +91 with space/dash
    num, valid = normalize_mobile("+91 98471-23456")
    assert num == "9847123456" and valid is True

    # Leading 0 (e.g. 09847123456)
    num, valid = normalize_mobile("09847123456")
    assert num == "9847123456" and valid is True

    # Multiple numbers in single cell ("9847123456 / 9447123456")
    num, valid = normalize_mobile("9847123456 / 9447123456")
    assert num == "9847123456" and valid is True

    # Text with mobile ("Mob: 9847123456 (WhatsApp)")
    num, valid = normalize_mobile("Mob: 9847123456 (WhatsApp)")
    assert num == "9847123456" and valid is True


def test_normalize_name_various_formats():
    assert normalize_name("John Doe") == "John Doe"
    assert normalize_name("മുഹമ്മദ്") == "മുഹമ്മദ്"
    assert normalize_name(101) == "101"
    assert normalize_name("  shop #42  ") == "Shop #42"
    assert normalize_name("") is None
    assert normalize_name("nan") is None


def test_preview_to_import_consistency_representative_sheet():
    """
    Section 12 requirement:
    Customer Name | Mobile Number | Pincode | District
    Fathima       | 9876543210    | 676505  | Malappuram
    Aisha         | 9876543211    | 673001  | Kozhikode
    """
    session = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:6]
        phone_fathima = f"9876{random.randint(100000, 999999)}"
        phone_aisha = f"9876{random.randint(100000, 999999)}"

        df = pd.DataFrame([
            {
                "Customer Name": f"Fathima {uid}",
                "Mobile Number": phone_fathima,
                "Pincode": "676505",
                "District": "Malappuram"
            },
            {
                "Customer Name": f"Aisha {uid}",
                "Mobile Number": phone_aisha,
                "Pincode": "673001",
                "District": "Kozhikode"
            }
        ])

        excel_buf = io.BytesIO()
        df.to_excel(excel_buf, index=False)
        excel_bytes = excel_buf.getvalue()

        # Step 1: Preview / Analysis
        analysis = ExcelImportService.analyze_file(excel_bytes, f"fathima_aisha_{uid}.xlsx")
        assert analysis["total_rows"] == 2
        assert len(analysis["sample_rows"]) == 2

        # Step 2: Confirm & Ingest with detected mappings
        batch = ExcelImportService.process_import(
            temp_file_id=analysis["temp_file_id"],
            original_filename=analysis["file_name"],
            import_type="CUSTOMER",
            column_mapping=analysis["auto_mappings"],
            db=session
        )

        assert batch.successful_rows == 2
        assert batch.failed_rows == 0
        assert batch.status in ["COMPLETED", "PARTIALLY_COMPLETED"]

        # Step 3: Verify DB records
        c1 = session.query(Customer).filter(Customer.normalized_contact == phone_fathima).first()
        assert c1 is not None
        assert c1.customer_name == normalize_name(f"Fathima {uid}")
        assert c1.district == "Malappuram"

        c2 = session.query(Customer).filter(Customer.normalized_contact == phone_aisha).first()
        assert c2 is not None
        assert c2.customer_name == normalize_name(f"Aisha {uid}")
        assert c2.district == "Kozhikode"

    finally:
        session.close()


@pytest.mark.parametrize("name_header,mobile_header", [
    ("Name", "Mobile"),
    ("Customer Name", "Mobile Number"),
    ("Customer Name", "Contact Number"),
    ("CUSTOMER NAME", "MOBILE NUMBER"),
    ("customer name", "mobile number"),
    ("Customer_Name", "Mobile_Number"),
])
def test_various_column_name_cases(name_header, mobile_header):
    session = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:6]
        phone = f"9847{random.randint(100000, 999999)}"
        name = f"Test Client {uid}"

        df = pd.DataFrame([{
            name_header: name,
            mobile_header: phone,
            "District": "Kannur",
            "Pincode": "670001"
        }])

        excel_buf = io.BytesIO()
        df.to_excel(excel_buf, index=False)
        excel_bytes = excel_buf.getvalue()

        analysis = ExcelImportService.analyze_file(excel_bytes, f"case_{uid}.xlsx")
        batch = ExcelImportService.process_import(
            temp_file_id=analysis["temp_file_id"],
            original_filename=analysis["file_name"],
            import_type="CUSTOMER",
            column_mapping=analysis["auto_mappings"],
            db=session
        )

        assert batch.successful_rows == 1
        assert batch.failed_rows == 0

        cust = session.query(Customer).filter(Customer.normalized_contact == phone).first()
        assert cust is not None
        assert cust.customer_name == normalize_name(name)
        assert cust.district == "Kannur"

    finally:
        session.close()


def test_csv_file_import():
    session = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:6]
        phone = f"9847{random.randint(100000, 999999)}"
        name = f"CSV Client {uid}"

        csv_content = f"Customer Name,Mobile Number,Pincode,District\n{name},{phone},682001,Ernakulam\n"
        csv_bytes = csv_content.encode("utf-8")

        analysis = ExcelImportService.analyze_file(csv_bytes, f"test_{uid}.csv")
        batch = ExcelImportService.process_import(
            temp_file_id=analysis["temp_file_id"],
            original_filename=analysis["file_name"],
            import_type="CUSTOMER",
            column_mapping=analysis["auto_mappings"],
            db=session
        )

        assert batch.successful_rows == 1
        assert batch.failed_rows == 0

        cust = session.query(Customer).filter(Customer.normalized_contact == phone).first()
        assert cust is not None
        assert cust.customer_name == normalize_name(name)
        assert cust.district == "Ernakulam"

    finally:
        session.close()


def test_multi_sheet_excel_import():
    session = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:6]
        phone1 = f"9847{random.randint(100000, 999999)}"
        phone2 = f"9447{random.randint(100000, 999999)}"

        df1 = pd.DataFrame([{
            "Customer Name": f"Sheet1 Cust {uid}",
            "Mobile Number": phone1,
            "District": "Thrissur",
            "Pincode": "680001"
        }])

        df2 = pd.DataFrame([{
            "Name": f"Sheet2 Cust {uid}",
            "Contact Number": phone2,
            "District": "Palakkad",
            "Pincode": "678001"
        }])

        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
            df1.to_excel(writer, sheet_name="Customers_A", index=False)
            df2.to_excel(writer, sheet_name="Customers_B", index=False)

        excel_bytes = excel_buf.getvalue()

        # Analyze Sheet2 specifically
        analysis = ExcelImportService.analyze_file(excel_bytes, f"multisheet_{uid}.xlsx", sheet_name="Customers_B")
        assert "Customers_A" in analysis["available_sheets"]
        assert "Customers_B" in analysis["available_sheets"]

        batch = ExcelImportService.process_import(
            temp_file_id=analysis["temp_file_id"],
            original_filename=analysis["file_name"],
            import_type="CUSTOMER",
            column_mapping=analysis["auto_mappings"],
            db=session,
            sheet_name="Customers_B"
        )

        assert batch.successful_rows == 1
        assert batch.failed_rows == 0

        cust = session.query(Customer).filter(Customer.normalized_contact == phone2).first()
        assert cust is not None
        assert cust.district == "Palakkad"

    finally:
        session.close()
