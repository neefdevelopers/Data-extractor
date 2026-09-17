import os
import json
import uuid
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.employee import Employee
from app.models.upload import UploadBatch, UploadRow
from app.models.data_quality import DataQualityIssue
from app.models.postal import PostalMaster
from app.services.postal_service import PostalService
from app.services.duplicate_detection_service import DuplicateDetectionService
from app.services.revenue_service import RevenueService
from app.services.rfm_service import RFMService
from app.services.data_quality_service import DataQualityService
from app.utils.cleaning import (
    normalize_name,
    normalize_mobile,
    normalize_pincode,
    normalize_payment_mode,
    normalize_order_status,
    clean_address
)
from app.utils.text_normalization import canonical_key, clean_display_text, ci_equals
from app.utils.district_normalization import normalize_district_name, get_normalized_district_key
from app.services.district_service import DistrictService

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "../uploads")

COLUMN_SYNONYMS = {
    "customer_name": [
        "customer name", "client name", "customer", "name", "buyer name", "full name", "client",
        "party name", "party", "cust name", "cust_name", "customer_name", "bill to", "bill to name",
        "consignee", "receiver", "receiver name", "recipient", "contact person", "person name",
        "customer / client", "customer/client", "user name", "username", "account name",
        "party_name", "buyer", "shopper", "consumer", "patient name", "student name", "member name"
    ],
    "contact_number": [
        "mobile number", "mobile", "phone number", "phone", "contact", "contact number", "cell",
        "phone no", "mobile no", "contact no", "mob", "ph", "tel", "telephone", "contact_no",
        "mobile_number", "phone_number", "cust phone", "cust mobile", "customer mobile", "customer phone",
        "whatsapp", "primary phone", "alt phone", "buyer phone", "party phone", "phone_no", "mob_no",
        "contact_no.", "mobile no.", "phone no.", "phone / mobile", "mobile/phone", "cell phone"
    ],
    "full_address": [
        "full address", "delivery address", "shipping address", "address", "customer address",
        "street address", "location", "addr", "shipping_address", "billing address", "billing_address",
        "address line 1", "address 1", "addressline1", "delivery_address", "place"
    ],
    "pincode": [
        "pincode", "pin code", "pin", "postal code", "zip code", "zip", "postal", "pin_code",
        "postal_code", "zip_code", "pincode/zip"
    ],
    "post_office": [
        "post office", "po", "post", "branch office", "postoffice", "post_office", "b.o", "s.o", "h.o", "po name"
    ],
    "district": [
        "district", "district name", "city", "town", "dist", "jilla", "district_name", "city/district"
    ],
    "state": [
        "state", "province", "region", "state name", "state_name"
    ],
    "order_number": [
        "order id", "order number", "invoice number", "order no", "order_id", "invoice no", "inv no",
        "order#", "invoice#", "bill no", "bill number", "receipt no", "transaction id", "order_no",
        "invoice_id", "voucher no", "ref no", "reference no"
    ],
    "order_date": [
        "order date", "ordered date", "ordered_date", "purchase date", "date", "created at", "order_date", "invoice date", "order time",
        "bill date", "trans date", "transaction date", "date of order", "created_date", "timestamp", "orderdate", "ordereddate",
        "ordered on", "ordered_on", "order dt", "order_dt", "booking date", "booked date"
    ],
    "payment_mode": [
        "payment mode", "payment method", "payment type", "payment", "pay mode", "pay type",
        "payment_mode", "payment_method", "mode of payment", "pay_mode"
    ],
    "order_status": [
        "order status", "status", "delivery status", "fulfillment status", "order_status", "stage",
        "shipping status", "current status"
    ],
    "total_amount": [
        "total amount", "order amount", "amount", "total", "order total", "grand total", "net amount",
        "price total", "total_amount", "order_total", "invoice amount", "bill amount", "final amount",
        "value", "order value", "sales amount"
    ],
    "employee_name": [
        "employee", "sales person", "agent", "staff", "sales rep", "employee name", "executive",
        "bde", "salesman", "assigned to", "created by", "booked by", "sales agent", "employee_name"
    ],
    "product_name": [
        "product name", "product", "item", "item name", "product description", "title", "product_name",
        "item_name", "goods", "material description", "item description", "particulars"
    ],
    "sku": [
        "sku", "product code", "item code", "sku id", "product sku", "sku_code", "item_sku", "barcode"
    ],
    "category": [
        "category", "product category", "item category", "department", "group", "product_group"
    ],
    "quantity": [
        "quantity", "qty", "units", "count", "item qty", "pieces", "nos", "pcs", "quantity_sold"
    ],
    "price": [
        "unit price", "price", "item price", "rate", "cost", "unit_price", "mrp", "selling price"
    ]
}

# Internal target aliases for matching user mappings
TARGET_FIELD_ALIASES: Dict[str, List[str]] = {
    "customer_name": ["customer_name", "customer", "name", "client_name", "party_name", "full_name", "cust_name", "buyer_name"],
    "contact_number": ["contact_number", "mobile_number", "mobile", "phone", "phone_number", "contact_no", "cell", "phone_no", "mob_no", "contact"],
    "full_address": ["full_address", "address", "shipping_address", "delivery_address", "street_address", "location"],
    "pincode": ["pincode", "pin", "postal_code", "zip_code", "zip", "postal"],
    "post_office": ["post_office", "po", "post", "branch_office", "postoffice"],
    "district": ["district", "district_name", "city", "town"],
    "state": ["state", "province", "region"],
    "order_number": ["order_number", "order_id", "order_no", "invoice_no", "invoice_number", "inv_no"],
    "order_date": ["order_date", "ordered_date", "ordered date", "date", "purchase_date", "invoice_date", "orderdate", "ordered_on"],
    "payment_mode": ["payment_mode", "payment_method", "pay_mode", "payment"],
    "order_status": ["order_status", "status", "delivery_status"],
    "total_amount": ["total_amount", "amount", "order_total", "total", "grand_total"],
    "employee_name": ["employee_name", "employee", "agent", "sales_person", "staff"],
    "product_name": ["product_name", "product", "item_name", "item", "title"],
    "sku": ["sku", "product_code", "item_code"],
    "category": ["category", "product_category", "department"],
    "quantity": ["quantity", "qty", "units", "pieces"],
    "price": ["price", "unit_price", "rate", "cost"]
}

class ExcelImportService:
    @staticmethod
    def auto_detect_columns(file_columns: List[str]) -> Dict[str, Optional[str]]:
        """Maps target schema keys to source file header names"""
        detected: Dict[str, Optional[str]] = {}
        cleaned_cols = {canonical_key(col): col for col in file_columns}

        for target_field, synonyms in COLUMN_SYNONYMS.items():
            matched_header = None
            for syn in synonyms:
                syn_key = canonical_key(syn)
                if syn_key in cleaned_cols:
                    matched_header = cleaned_cols[syn_key]
                    break
            detected[target_field] = matched_header

        return detected

    @staticmethod
    def infer_import_type(mappings: Dict[str, Optional[str]]) -> str:
        has_customer = bool(mappings.get("customer_name") or mappings.get("contact_number") or mappings.get("mobile_number"))
        has_order = bool(mappings.get("order_number") or mappings.get("total_amount"))
        has_product = bool(mappings.get("product_name") or mappings.get("sku"))

        if has_customer and has_order:
            return "COMBINED"
        elif has_order:
            return "ORDER"
        elif has_customer:
            return "CUSTOMER"
        elif has_product:
            return "PRODUCT"
        return "COMBINED"

    @staticmethod
    def analyze_file(file_bytes: bytes, filename: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """Reads file locally, detects columns, infers type, creates preview (20-50 rows)"""
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        temp_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()
        temp_filename = f"{temp_id}_{filename}"
        temp_filepath = os.path.join(UPLOAD_DIR, temp_filename)

        with open(temp_filepath, "wb") as f:
            f.write(file_bytes)

        # Read into pandas with dtype=object to preserve raw strings
        available_sheets = []
        try:
            if ext in [".xlsx", ".xls"]:
                excel_file = pd.ExcelFile(temp_filepath)
                available_sheets = excel_file.sheet_names
                target_sheet = sheet_name if (sheet_name and sheet_name in available_sheets) else available_sheets[0]
                df = pd.read_excel(excel_file, sheet_name=target_sheet, dtype=object)
            elif ext == ".csv":
                df = pd.read_csv(temp_filepath, dtype=object, encoding_errors="replace")
            else:
                raise ValueError(f"Unsupported file format: {ext}. Supported formats: .xlsx, .xls, .csv")
        except Exception as e:
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            raise ValueError(f"Failed to read spreadsheet: {str(e)}")

        # Clean column names (strip whitespace)
        df.columns = [str(c).strip() for c in df.columns]
        raw_columns = list(df.columns)
        total_rows = len(df)

        auto_maps = ExcelImportService.auto_detect_columns(raw_columns)
        import_type = ExcelImportService.infer_import_type(auto_maps)

        # Build validation warnings
        warnings = []
        if not auto_maps.get("customer_name") and not auto_maps.get("contact_number"):
            warnings.append("No customer name or phone number column could be auto-detected.")
        if not auto_maps.get("pincode"):
            warnings.append("No PIN code column detected; postal enrichment will be skipped.")
        if not auto_maps.get("order_number") and import_type in ["ORDER", "COMBINED"]:
            warnings.append("No order ID / invoice number detected. Random order IDs will be generated if unmapped.")

        # Sample rows (first 30 rows)
        sample_df = df.head(30).fillna("")
        sample_rows = sample_df.to_dict(orient="records")

        return {
            "file_name": filename,
            "temp_file_id": temp_filename,
            "total_rows": total_rows,
            "detected_columns": raw_columns,
            "suggested_import_type": import_type,
            "auto_mappings": auto_maps,
            "sample_rows": sample_rows,
            "validation_warnings": warnings,
            "available_sheets": available_sheets
        }

    @staticmethod
    def process_import(
        temp_file_id: str,
        original_filename: str,
        import_type: str,
        column_mapping: Dict[str, Optional[str]],
        db: Session,
        sheet_name: Optional[str] = None
    ) -> UploadBatch:
        temp_filepath = os.path.join(UPLOAD_DIR, temp_file_id)
        if not os.path.exists(temp_filepath):
            raise ValueError("Uploaded temporary file expired or not found.")

        ext = os.path.splitext(original_filename)[1].lower()
        if ext in [".xlsx", ".xls"]:
            excel_file = pd.ExcelFile(temp_filepath)
            target_sheet = sheet_name if (sheet_name and sheet_name in excel_file.sheet_names) else excel_file.sheet_names[0]
            df = pd.read_excel(excel_file, sheet_name=target_sheet, dtype=object)
        else:
            df = pd.read_csv(temp_filepath, dtype=object, encoding_errors="replace")

        df.columns = [str(c).strip() for c in df.columns]
        total_rows = len(df)

        # Create Upload Batch record
        batch = UploadBatch(
            file_name=original_filename,
            file_path=temp_filepath,
            upload_type=import_type,
            total_rows=total_rows,
            status="PROCESSING"
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)

        success_count = 0
        failed_count = 0
        duplicate_count = 0
        updated_count = 0
        new_cust_count = 0
        new_order_count = 0
        new_prod_count = 0

        # In-Memory Pre-fetching to eliminate per-row DB roundtrips (case-insensitive & trimmed keys)
        phone_cache: Dict[str, Customer] = {
            c.normalized_contact: c for c in db.query(Customer).filter(Customer.normalized_contact.isnot(None)).all()
        }
        name_pin_cache: Dict[Tuple[str, str], Customer] = {
            (canonical_key(c.customer_name), c.pincode.strip()): c
            for c in db.query(Customer).filter(Customer.customer_name.isnot(None), Customer.pincode.isnot(None)).all()
        }
        postal_cache: Dict[str, Optional[PostalMaster]] = {
            p.pincode.strip(): p for p in db.query(PostalMaster).all()
        }
        employee_cache: Dict[str, Employee] = {
            canonical_key(e.employee_name): e for e in db.query(Employee).all()
        }
        product_sku_cache: Dict[str, Product] = {
            canonical_key(p.sku): p for p in db.query(Product).filter(Product.sku.isnot(None)).all()
        }
        product_name_cache: Dict[str, Product] = {
            canonical_key(p.product_name): p for p in db.query(Product).all()
        }
        order_cache: Dict[str, Order] = {
            canonical_key(o.order_number): o for o in db.query(Order).all()
        }
        order_item_cache = {
            (oi.order_id, oi.product_id) for oi in db.query(OrderItem.order_id, OrderItem.product_id).all()
        }
        revenue_rules = RevenueService.get_revenue_rules(db)

        # Build case-insensitive lookup for user column mapping
        mapping_ci: Dict[str, str] = {}
        if column_mapping:
            for k, v in column_mapping.items():
                if v and str(v).strip():
                    mapping_ci[canonical_key(k)] = str(v).strip()

        for index, row in df.iterrows():
            row_num = int(index) + 2  # Excel 1-based index with header at row 1
            row_dict = row.to_dict()

            # Skip trailing / empty rows
            non_empty_values = [
                v for v in row_dict.values()
                if not pd.isna(v) and str(v).strip().lower() not in ["nan", "none", "null", "undefined", "n/a", "na", "-", ""]
            ]
            if not non_empty_values:
                continue

            # Case-insensitive map for row_dict keys
            row_ci_keys = {canonical_key(k): k for k in row_dict.keys()}

            # Resilient value extractor:
            # 1. Checks all aliases of target field in user's mapping
            # 2. Searches row_dict by exact name or case/whitespace normalized key
            # 3. Falls back to industry synonyms
            def get_val(field_key: str) -> Optional[str]:
                # 1. Check user mappings
                mapped_header = None
                aliases = TARGET_FIELD_ALIASES.get(field_key, [field_key])
                for alias in aliases:
                    alias_canon = canonical_key(alias)
                    if alias_canon in mapping_ci:
                        mapped_header = mapping_ci[alias_canon]
                        break

                if mapped_header:
                    # Direct match
                    if mapped_header in row_dict:
                        v = row_dict[mapped_header]
                        if not pd.isna(v) and str(v).strip().lower() not in ["nan", "none", "null", "undefined", "n/a", "na", "-"] and str(v).strip():
                            return str(v).strip()
                    # Case-insensitive key match
                    header_canon = canonical_key(mapped_header)
                    if header_canon in row_ci_keys:
                        actual_k = row_ci_keys[header_canon]
                        v = row_dict[actual_k]
                        if not pd.isna(v) and str(v).strip().lower() not in ["nan", "none", "null", "undefined", "n/a", "na", "-"] and str(v).strip():
                            return str(v).strip()

                # 2. Fallback to synonyms
                for syn in COLUMN_SYNONYMS.get(field_key, []):
                    syn_canon = canonical_key(syn)
                    if syn_canon in row_ci_keys:
                        actual_k = row_ci_keys[syn_canon]
                        v = row_dict[actual_k]
                        if not pd.isna(v) and str(v).strip().lower() not in ["nan", "none", "null", "undefined", "n/a", "na", "-"] and str(v).strip():
                            return str(v).strip()

                return None

            try:
                # 1. Extract Mapped Row Data
                raw_name = get_val("customer_name")
                raw_phone = get_val("contact_number")
                raw_address = get_val("full_address")
                raw_pin = get_val("pincode")
                raw_po = get_val("post_office")
                raw_district = get_val("district")
                raw_state = get_val("state")

                cust_name = normalize_name(raw_name)
                norm_phone, phone_valid = normalize_mobile(raw_phone)
                cleaned_pin, pin_valid = normalize_pincode(raw_pin)
                cleaned_addr = clean_address(raw_address)

                # Required Field Validation based on Mapped Data
                if not cust_name and not norm_phone and not raw_phone:
                    raw_ord_candidate = get_val("order_number")
                    raw_prod_candidate = get_val("product_name") or get_val("sku")
                    if (raw_ord_candidate or raw_prod_candidate or cleaned_addr or cleaned_pin) and import_type in ["ORDER", "COMBINED", "PRODUCT"]:
                        cust_name = f"Customer {raw_ord_candidate or ('Row ' + str(row_num))}"
                    else:
                        failed_count += 1
                        err_msg = "Customer name and mobile number are missing"
                        suggested = "Ensure Customer Name or Mobile Number column is mapped and contains values"
                        err_row = UploadRow(
                            upload_id=batch.id,
                            row_number=row_num,
                            status="FAILED",
                            raw_data=json.dumps({k: str(v) for k, v in row_dict.items() if not pd.isna(v)}, ensure_ascii=False),
                            error_reason=err_msg,
                            suggested_fix=suggested
                        )
                        db.add(err_row)
                        DataQualityService.log_issue(
                            db, "CUSTOMER", None, "customer_name", "MISSING_NAME",
                            raw_name, f"Row {row_num}: {err_msg}",
                            suggested_fix=suggested, row_number=row_num, batch_id=batch.id
                        )
                        continue

                if raw_phone and not phone_valid:
                    DataQualityService.log_issue(
                        db, "CUSTOMER", None, "contact_number", "INVALID_CONTACT",
                        raw_phone, f"Row {row_num}: Invalid Indian mobile '{raw_phone}'",
                        suggested_fix="Format as 10-digit number starting with 6-9", row_number=row_num, batch_id=batch.id
                    )

                if raw_pin and not pin_valid:
                    DataQualityService.log_issue(
                        db, "CUSTOMER", None, "pincode", "INVALID_PIN",
                        raw_pin, f"Row {row_num}: Invalid 6-digit PIN '{raw_pin}'",
                        suggested_fix="Enter valid 6-digit postal code", row_number=row_num, batch_id=batch.id
                    )

                # Postal Enrichment (using local cache & file data with zero network blocking)
                if cleaned_pin and pin_valid:
                    if cleaned_pin in postal_cache:
                        postal_info = postal_cache[cleaned_pin]
                        if postal_info:
                            if not raw_district and postal_info.district:
                                raw_district = postal_info.district
                            if not raw_state and postal_info.state:
                                raw_state = postal_info.state
                    else:
                        postal_info = db.query(PostalMaster).filter(PostalMaster.pincode == cleaned_pin).first()
                        if postal_info:
                            postal_cache[cleaned_pin] = postal_info
                            if not raw_district and postal_info.district:
                                raw_district = postal_info.district
                            if not raw_state and postal_info.state:
                                raw_state = postal_info.state
                        else:
                            postal_cache[cleaned_pin] = None

                # 2. Customer Deduplication & District Resolution (Priority Flow)
                matched_cust: Optional[Customer] = None
                cust_key = (canonical_key(cust_name), cleaned_pin) if (cust_name and cleaned_pin) else None

                if norm_phone and norm_phone in phone_cache:
                    matched_cust = phone_cache[norm_phone]
                elif cust_key and cust_key in name_pin_cache:
                    matched_cust = name_pin_cache[cust_key]

                # Resolve district using centralized DistrictResolutionService priority flow
                from app.services.district_resolution_service import DistrictResolutionService
                dist_res = DistrictResolutionService.resolve_district(
                    raw_district=raw_district,
                    pincode=cleaned_pin,
                    source_post_office=raw_po,
                    address_hint=cleaned_addr,
                    state_hint=raw_state,
                    db=db,
                    allow_postal_lookup=True
                )

                if dist_res.district_mismatch and raw_district:
                    DataQualityService.log_issue(
                        db, "CUSTOMER", None, "district", "DISTRICT_MISMATCH",
                        raw_district, f"Row {row_num}: {dist_res.mismatch_message}",
                        suggested_fix=f"Verified as '{dist_res.canonical_name}' via Pincode {cleaned_pin}",
                        row_number=row_num, batch_id=batch.id
                    )

                clean_state = dist_res.state or clean_display_text(raw_state, title_case=True) or "Kerala"
                clean_po_formatted = clean_display_text(raw_po, title_case=True)
                raw_row_clean_dict = {str(k): ("" if pd.isna(v) else str(v).strip()) for k, v in row_dict.items() if not pd.isna(v)}
                raw_row_json_str = json.dumps(raw_row_clean_dict, ensure_ascii=False)

                if matched_cust:
                    customer = matched_cust
                    updated_count += 1
                    if batch.file_name:
                        customer.source_file_name = batch.file_name
                    if row_num:
                        customer.source_row_number = row_num
                    if raw_row_json_str:
                        customer.raw_row_data = raw_row_json_str
                    if raw_district and not customer.source_district:
                        customer.source_district = raw_district
                    if cust_name and not customer.customer_name:
                        customer.customer_name = cust_name
                    if cleaned_addr and not customer.full_address:
                        customer.full_address = cleaned_addr
                    if cleaned_pin and not customer.pincode:
                        customer.pincode = cleaned_pin
                    if dist_res.is_resolved:
                        customer.district_id = dist_res.district_id
                        customer.district = dist_res.canonical_name
                        customer.state = dist_res.state or customer.state
                        customer.district_resolution_source = dist_res.resolution_source
                        customer.district_status = dist_res.district_status
                        customer.district_mismatch = dist_res.district_mismatch
                    elif not customer.district_id:
                        customer.district_resolution_source = dist_res.resolution_source
                        customer.district_status = dist_res.district_status
                        customer.district_mismatch = False
                    if clean_state and not customer.state:
                        customer.state = clean_state
                    if clean_po_formatted and not customer.post_office:
                        customer.post_office = clean_po_formatted
                else:
                    customer = Customer(
                        customer_name=cust_name or f"Customer {norm_phone or 'Unknown'}",
                        contact_number=raw_phone,
                        normalized_contact=norm_phone,
                        full_address=cleaned_addr,
                        pincode=cleaned_pin,
                        post_office=clean_po_formatted,
                        source_district=raw_district,
                        district_id=dist_res.district_id if dist_res.is_resolved else None,
                        district=dist_res.canonical_name if dist_res.is_resolved else None,
                        district_resolution_source=dist_res.resolution_source,
                        district_status=dist_res.district_status,
                        district_mismatch=dist_res.district_mismatch,
                        state=clean_state,
                        source_file_name=batch.file_name,
                        source_row_number=row_num,
                        raw_row_data=raw_row_json_str
                    )
                    db.add(customer)
                    new_cust_count += 1
                    if norm_phone:
                        phone_cache[norm_phone] = customer
                    if cust_key:
                        name_pin_cache[cust_key] = customer

                # 3. Employee Handling
                raw_emp = get_val("employee_name")
                employee_obj = None
                if raw_emp:
                    emp_display = clean_display_text(raw_emp, title_case=True) or raw_emp.strip()
                    emp_key = canonical_key(raw_emp)
                    if emp_key in employee_cache:
                        employee_obj = employee_cache[emp_key]
                    else:
                        employee_obj = Employee(
                            employee_name=emp_display,
                            employee_code=f"EMP-{emp_key[:3].upper()}-{len(employee_cache)+101}",
                            status="ACTIVE"
                        )
                        db.add(employee_obj)
                        employee_cache[emp_key] = employee_obj

                # 4. Product Handling
                raw_prod = get_val("product_name")
                raw_sku = get_val("sku")
                raw_cat = get_val("category")
                raw_price = get_val("price")
                raw_qty = get_val("quantity")

                product_obj = None
                if raw_prod or raw_sku:
                    sku_key = canonical_key(raw_sku) if raw_sku else None
                    prod_name = clean_display_text(raw_prod) or (f"Product {raw_sku.strip()}" if raw_sku else "Unknown Product")
                    name_key = canonical_key(prod_name)

                    if sku_key and sku_key in product_sku_cache:
                        product_obj = product_sku_cache[sku_key]
                    elif name_key in product_name_cache:
                        product_obj = product_name_cache[name_key]
                    else:
                        price_val = 0.0
                        if raw_price:
                            try:
                                price_val = float(str(raw_price).replace(",", "").replace("₹", "").strip())
                            except Exception:
                                price_val = 0.0

                        product_obj = Product(
                            product_name=prod_name,
                            sku=clean_display_text(raw_sku),
                            category=clean_display_text(raw_cat, title_case=True) or "General",
                            price=price_val
                        )
                        db.add(product_obj)
                        new_prod_count += 1
                        if sku_key:
                            product_sku_cache[sku_key] = product_obj
                        product_name_cache[name_key] = product_obj

                # 5. Order Handling (if import type is ORDER or COMBINED)
                if import_type in ["ORDER", "COMBINED"]:
                    raw_ord_num = get_val("order_number")
                    raw_ord_date = get_val("order_date")
                    raw_pay_mode = get_val("payment_mode")
                    raw_ord_status = get_val("order_status")
                    raw_total = get_val("total_amount")

                    if not raw_ord_num:
                        raw_ord_num = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                    else:
                        raw_ord_num = str(raw_ord_num).strip()

                    # Parse Date
                    ord_date = datetime.datetime.utcnow()
                    if not raw_ord_date:
                        for k, v in row_dict.items():
                            if str(k).strip().lower() in ["ordered_date", "ordered date", "order_date", "order date", "orderdate", "ordereddate", "date", "created_at", "timestamp"] and not pd.isna(v) and str(v).strip():
                                raw_ord_date = str(v).strip()
                                break
                    if raw_ord_date:
                        try:
                            ord_date = pd.to_datetime(raw_ord_date).to_pydatetime()
                        except Exception:
                            DataQualityService.log_issue(
                                db, "ORDER", raw_ord_num, "order_date", "INVALID_DATE",
                                raw_ord_date, f"Row {row_num}: Invalid order date format '{raw_ord_date}'",
                                suggested_fix="Use YYYY-MM-DD format", row_number=row_num, batch_id=batch.id
                            )

                    # Parse Total Amount
                    total_amount_val = 0.0
                    if raw_total:
                        try:
                            total_amount_val = float(str(raw_total).replace(",", "").replace("₹", "").strip())
                        except Exception:
                            total_amount_val = 0.0
                    elif product_obj and raw_qty:
                        try:
                            total_amount_val = product_obj.price * float(raw_qty)
                        except Exception:
                            total_amount_val = product_obj.price

                    norm_pay_mode = normalize_payment_mode(raw_pay_mode)
                    norm_status = normalize_order_status(raw_ord_status)

                    # Revenue calculation from cached rules
                    is_rev = RevenueService.is_revenue_eligible(norm_status, revenue_rules)
                    rev_val = total_amount_val if is_rev else 0.0

                    # Order Deduplication with in-memory order cache
                    existing_order = order_cache.get(raw_ord_num)
                    if existing_order:
                        duplicate_count += 1
                        existing_order.payment_mode = norm_pay_mode
                        existing_order.order_status = norm_status
                        existing_order.total_amount = total_amount_val
                        existing_order.revenue_amount = rev_val
                        order_record = existing_order
                    else:
                        new_order = Order(
                            order_number=raw_ord_num,
                            customer=customer,
                            order_date=ord_date,
                            employee=employee_obj,
                            payment_mode=norm_pay_mode,
                            order_status=norm_status,
                            total_amount=total_amount_val,
                            revenue_amount=rev_val
                        )
                        db.add(new_order)
                        order_cache[raw_ord_num] = new_order
                        order_record = new_order
                        new_order_count += 1

                    # Add Order Item if product information exists
                    if product_obj:
                        qty_val = 1
                        if raw_qty:
                            try:
                                qty_val = max(1, int(float(raw_qty)))
                            except Exception:
                                qty_val = 1

                        unit_price_val = product_obj.price if product_obj.price > 0 else (total_amount_val / qty_val)
                        item_total_val = unit_price_val * qty_val

                        # Check item cache key
                        prod_identifier = product_obj.sku or product_obj.product_name
                        item_key = (raw_ord_num, prod_identifier)
                        if item_key not in order_item_cache:
                            order_item = OrderItem(
                                order=order_record,
                                product=product_obj,
                                product_name=product_obj.product_name,
                                quantity=qty_val,
                                unit_price=unit_price_val,
                                discount=0.0,
                                item_total=item_total_val
                            )
                            db.add(order_item)
                            order_item_cache.add(item_key)

                success_count += 1

                # Flush in chunks of 500 rows to keep memory compact
                if index > 0 and index % 500 == 0:
                    db.flush()

            except Exception as e:
                failed_count += 1
                err_row = UploadRow(
                    upload_id=batch.id,
                    row_number=row_num,
                    status="FAILED",
                    raw_data=json.dumps({k: str(v) for k, v in row_dict.items() if not pd.isna(v)}),
                    error_reason=str(e),
                    suggested_fix="Check data types and missing values"
                )
                db.add(err_row)

        # Update batch summary
        batch.successful_rows = success_count
        batch.failed_rows = failed_count
        batch.duplicate_rows = duplicate_count
        batch.updated_rows = updated_count
        batch.new_customers = new_cust_count
        batch.new_orders = new_order_count
        batch.new_products = new_prod_count

        if failed_count == 0:
            batch.status = "COMPLETED"
        elif success_count > 0:
            batch.status = "PARTIALLY_COMPLETED"
        else:
            batch.status = "FAILED"

        db.commit()

        # Recalculate RFM and Customer LTV / AOV values
        try:
            RFMService.recalculate_all_rfm(db)
        except Exception as e:
            print(f"Warning: RFM calculation error: {e}")

        return batch
