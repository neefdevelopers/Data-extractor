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

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "../uploads")

COLUMN_SYNONYMS = {
    "customer_name": ["customer name", "client name", "customer", "name", "buyer name", "full name", "client"],
    "contact_number": ["mobile number", "mobile", "phone number", "phone", "contact", "contact number", "cell", "phone no", "mobile no"],
    "full_address": ["full address", "delivery address", "shipping address", "address", "customer address", "street address", "location"],
    "pincode": ["pincode", "pin code", "pin", "postal code", "zip code", "zip", "postal"],
    "post_office": ["post office", "po", "post", "branch office", "postoffice"],
    "district": ["district", "district name", "city", "town"],
    "state": ["state", "province", "region"],
    "order_number": ["order id", "order number", "invoice number", "order no", "order_id", "invoice no", "inv no", "order#"],
    "order_date": ["order date", "purchase date", "date", "created at", "order_date", "invoice date", "order time"],
    "payment_mode": ["payment mode", "payment method", "payment type", "payment", "pay mode", "pay type"],
    "order_status": ["order status", "status", "delivery status", "fulfillment status"],
    "total_amount": ["total amount", "order amount", "amount", "total", "order total", "grand total", "net amount", "price total"],
    "employee_name": ["employee", "sales person", "agent", "staff", "sales rep", "employee name", "executive"],
    "product_name": ["product name", "product", "item", "item name", "product description", "title"],
    "sku": ["sku", "product code", "item code", "sku id", "product sku"],
    "category": ["category", "product category", "item category", "department"],
    "quantity": ["quantity", "qty", "units", "count", "item qty", "pieces"],
    "price": ["unit price", "price", "item price", "rate", "cost"]
}

class ExcelImportService:
    @staticmethod
    def auto_detect_columns(file_columns: List[str]) -> Dict[str, Optional[str]]:
        """Maps target schema keys to source file header names"""
        detected: Dict[str, Optional[str]] = {}
        cleaned_cols = {col.strip().lower().replace("_", " "): col for col in file_columns}

        for target_field, synonyms in COLUMN_SYNONYMS.items():
            matched_header = None
            for syn in synonyms:
                if syn in cleaned_cols:
                    matched_header = cleaned_cols[syn]
                    break
            detected[target_field] = matched_header

        return detected

    @staticmethod
    def infer_import_type(mappings: Dict[str, Optional[str]]) -> str:
        has_customer = bool(mappings.get("customer_name") or mappings.get("contact_number"))
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
    def analyze_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Reads file locally, detects columns, infers type, creates preview (20-50 rows)"""
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        temp_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()
        temp_filename = f"{temp_id}_{filename}"
        temp_filepath = os.path.join(UPLOAD_DIR, temp_filename)

        with open(temp_filepath, "wb") as f:
            f.write(file_bytes)

        # Read into pandas
        try:
            if ext in [".xlsx", ".xls"]:
                df = pd.read_excel(temp_filepath)
            elif ext == ".csv":
                df = pd.read_csv(temp_filepath, encoding_errors="replace")
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
            "validation_warnings": warnings
        }

    @staticmethod
    def process_import(
        temp_file_id: str,
        original_filename: str,
        import_type: str,
        column_mapping: Dict[str, Optional[str]],
        db: Session
    ) -> UploadBatch:
        temp_filepath = os.path.join(UPLOAD_DIR, temp_file_id)
        if not os.path.exists(temp_filepath):
            raise ValueError("Uploaded temporary file expired or not found.")

        ext = os.path.splitext(original_filename)[1].lower()
        if ext in [".xlsx", ".xls"]:
            df = pd.read_excel(temp_filepath)
        else:
            df = pd.read_csv(temp_filepath, encoding_errors="replace")

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

        # Helper mapping function
        def get_val(row_dict: dict, field_key: str) -> Optional[str]:
            header = column_mapping.get(field_key)
            if not header or header not in row_dict:
                return None
            val = row_dict[header]
            if pd.isna(val) or str(val).strip().lower() in ["nan", "none", "null", ""]:
                return None
            return str(val).strip()

        # In-Memory Pre-fetching to eliminate per-row DB roundtrips
        phone_cache: Dict[str, Customer] = {
            c.normalized_contact: c for c in db.query(Customer).filter(Customer.normalized_contact.isnot(None)).all()
        }
        name_pin_cache: Dict[Tuple[str, str], Customer] = {
            (c.customer_name.strip().lower(), c.pincode.strip()): c
            for c in db.query(Customer).filter(Customer.customer_name.isnot(None), Customer.pincode.isnot(None)).all()
        }
        postal_cache: Dict[str, Optional[PostalMaster]] = {
            p.pincode: p for p in db.query(PostalMaster).all()
        }
        employee_cache: Dict[str, Employee] = {
            e.employee_name.strip().lower(): e for e in db.query(Employee).all()
        }
        product_sku_cache: Dict[str, Product] = {
            p.sku.strip(): p for p in db.query(Product).filter(Product.sku.isnot(None)).all()
        }
        product_name_cache: Dict[str, Product] = {
            p.product_name.strip().lower(): p for p in db.query(Product).all()
        }
        order_cache: Dict[str, Order] = {
            str(o.order_number).strip(): o for o in db.query(Order).all()
        }
        order_item_cache = {
            (oi.order_id, oi.product_id) for oi in db.query(OrderItem.order_id, OrderItem.product_id).all()
        }
        revenue_rules = RevenueService.get_revenue_rules(db)

        for index, row in df.iterrows():
            row_num = int(index) + 2  # Excel 1-based index with header at row 1
            row_dict = row.to_dict()

            try:
                # 1. Extract and Clean Customer Data
                raw_name = get_val(row_dict, "customer_name")
                raw_phone = get_val(row_dict, "contact_number")
                raw_address = get_val(row_dict, "full_address")
                raw_pin = get_val(row_dict, "pincode")
                raw_po = get_val(row_dict, "post_office")
                raw_district = get_val(row_dict, "district")
                raw_state = get_val(row_dict, "state")

                cust_name = normalize_name(raw_name)
                norm_phone, phone_valid = normalize_mobile(raw_phone)
                cleaned_pin, pin_valid = normalize_pincode(raw_pin)
                cleaned_addr = clean_address(raw_address)

                # Quality checks for customer
                if not cust_name and not norm_phone:
                    failed_count += 1
                    err_row = UploadRow(
                        upload_id=batch.id,
                        row_number=row_num,
                        status="FAILED",
                        raw_data=json.dumps({k: str(v) for k, v in row_dict.items() if not pd.isna(v)}),
                        error_reason="Missing both Customer Name and Phone Number",
                        suggested_fix="Ensure customer name or mobile number is provided"
                    )
                    db.add(err_row)
                    DataQualityService.log_issue(
                        db, "CUSTOMER", None, "customer_name", "MISSING_NAME",
                        raw_name, f"Row {row_num}: Missing customer name and phone",
                        suggested_fix="Provide customer name or phone", row_number=row_num, batch_id=batch.id
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
                    elif raw_district or raw_state:
                        postal_master = PostalMaster(
                            pincode=cleaned_pin,
                            district=raw_district,
                            state=raw_state,
                            country="India"
                        )
                        db.add(postal_master)
                        postal_cache[cleaned_pin] = postal_master
                    else:
                        postal_cache[cleaned_pin] = None

                # 2. Customer Deduplication & Creation/Update
                matched_cust: Optional[Customer] = None
                if norm_phone and norm_phone in phone_cache:
                    matched_cust = phone_cache[norm_phone]
                elif cust_name and cleaned_pin and (cust_name.strip().lower(), cleaned_pin) in name_pin_cache:
                    matched_cust = name_pin_cache[(cust_name.strip().lower(), cleaned_pin)]

                if matched_cust:
                    customer = matched_cust
                    updated_count += 1
                    if cust_name and not customer.customer_name:
                        customer.customer_name = cust_name
                    if cleaned_addr and not customer.full_address:
                        customer.full_address = cleaned_addr
                    if cleaned_pin and not customer.pincode:
                        customer.pincode = cleaned_pin
                    if raw_district and not customer.district:
                        customer.district = raw_district
                    if raw_state and not customer.state:
                        customer.state = raw_state
                else:
                    customer = Customer(
                        customer_name=cust_name or f"Customer {norm_phone or 'Unknown'}",
                        contact_number=raw_phone,
                        normalized_contact=norm_phone,
                        full_address=cleaned_addr,
                        pincode=cleaned_pin,
                        post_office=raw_po,
                        district=raw_district,
                        state=raw_state
                    )
                    db.add(customer)
                    new_cust_count += 1
                    if norm_phone:
                        phone_cache[norm_phone] = customer
                    if cust_name and cleaned_pin:
                        name_pin_cache[(cust_name.strip().lower(), cleaned_pin)] = customer

                # 3. Employee Handling
                raw_emp = get_val(row_dict, "employee_name")
                employee_obj = None
                if raw_emp:
                    emp_clean = raw_emp.strip()
                    emp_key = emp_clean.lower()
                    if emp_key in employee_cache:
                        employee_obj = employee_cache[emp_key]
                    else:
                        employee_obj = Employee(
                            employee_name=emp_clean.title(),
                            employee_code=f"EMP-{emp_clean[:3].upper()}-{len(employee_cache)+101}",
                            status="ACTIVE"
                        )
                        db.add(employee_obj)
                        employee_cache[emp_key] = employee_obj

                # 4. Product Handling
                raw_prod = get_val(row_dict, "product_name")
                raw_sku = get_val(row_dict, "sku")
                raw_cat = get_val(row_dict, "category")
                raw_price = get_val(row_dict, "price")
                raw_qty = get_val(row_dict, "quantity")

                product_obj = None
                if raw_prod or raw_sku:
                    sku_key = raw_sku.strip() if raw_sku else None
                    prod_name = raw_prod.strip() if raw_prod else f"Product {raw_sku}"
                    name_key = prod_name.lower()

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
                            sku=sku_key,
                            category=raw_cat or "General",
                            price=price_val
                        )
                        db.add(product_obj)
                        new_prod_count += 1
                        if sku_key:
                            product_sku_cache[sku_key] = product_obj
                        product_name_cache[name_key] = product_obj

                # 5. Order Handling (if import type is ORDER or COMBINED)
                if import_type in ["ORDER", "COMBINED"]:
                    raw_ord_num = get_val(row_dict, "order_number")
                    raw_ord_date = get_val(row_dict, "order_date")
                    raw_pay_mode = get_val(row_dict, "payment_mode")
                    raw_ord_status = get_val(row_dict, "order_status")
                    raw_total = get_val(row_dict, "total_amount")

                    if not raw_ord_num:
                        raw_ord_num = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                    else:
                        raw_ord_num = str(raw_ord_num).strip()

                    # Parse Date
                    ord_date = datetime.datetime.utcnow()
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
