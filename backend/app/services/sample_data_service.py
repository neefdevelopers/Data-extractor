import random
import datetime
from typing import List, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from app.services.excel_import_service import ExcelImportService

SAMPLE_INDIAN_DATA = [
    {"name": "Muhammed Rashid", "mobile": "9847112345", "address": "Manjeri Road, Down Hill", "pincode": "676505", "district": "Malappuram", "state": "Kerala"},
    {"name": "Fathima Suhara", "mobile": "9847223456", "address": "Kondotty Airport Road", "pincode": "673638", "district": "മലപ്പുറം", "state": "Kerala"},
    {"name": "Anand Narayanan", "mobile": "9847334567", "address": "Mavoor Road, Near Focus Mall", "pincode": "673001", "district": "Kozhikode", "state": "Kerala"},
    {"name": "Deepa Varma", "mobile": "9847445678", "address": "Beach Road, Calicut", "pincode": "673032", "district": "Calicut", "state": "Kerala"},
    {"name": "Pooja Nair", "mobile": "9847012345", "address": "56, Marine Drive", "pincode": "682011", "district": "Ernakulam", "state": "Kerala"},
    {"name": "Rohan George", "mobile": "9847556789", "address": "MG Road, Kochi", "pincode": "682016", "district": "കൊച്ചി", "state": "Kerala"},
    {"name": "Jithin Raj", "mobile": "9847667890", "address": "Round North, Swaraj Round", "pincode": "680001", "district": "Thrissur", "state": "Kerala"},
    {"name": "Sneha Menon", "mobile": "9847778901", "address": "Payyambalam Beach Rd", "pincode": "670001", "district": "Kannur", "state": "Kerala"},
    {"name": "Vivek Krishnan", "mobile": "9847889012", "address": "TB Road, Palakkad Town", "pincode": "678001", "district": "Palakkad", "state": "Kerala"},
    {"name": "Reshma Thomas", "mobile": "9847990123", "address": "Kowdiar Avenue", "pincode": "695003", "district": "Thiruvananthapuram", "state": "Kerala"},
    {"name": "Mathew Joseph", "mobile": "9847101234", "address": "Collectorate Road", "pincode": "686001", "district": "Kottayam", "state": "Kerala"},
    {"name": "Haris K", "mobile": "9847212345", "address": "Kalpetta Main Street", "pincode": "673121", "district": "Wayanad", "state": "Kerala"},
]

SAMPLE_PRODUCTS = [
    {"name": "Wireless Noise Cancelling Headphones", "sku": "AUDIO-WNC-01", "category": "Electronics", "price": 4999.0},
    {"name": "Ergonomic Mechanical Keyboard", "sku": "TECH-KB-RGB", "category": "Electronics", "price": 3299.0},
    {"name": "Stainless Steel Thermal Water Bottle 1L", "sku": "HOME-BTL-1L", "category": "Home & Kitchen", "price": 899.0},
    {"name": "Organic Roasted Coffee Beans 500g", "sku": "FOOD-COF-500", "category": "Grocery", "price": 649.0},
    {"name": "Premium Cotton Oversized T-Shirt", "sku": "APP-TEE-OVR", "category": "Apparel", "price": 999.0},
    {"name": "Leather Slim Travel Wallet", "sku": "ACC-WLT-SLM", "category": "Accessories", "price": 1299.0},
    {"name": "Smart Fitness Band with Heart Rate", "sku": "FIT-BND-HR", "category": "Electronics", "price": 2199.0}
]

SAMPLE_EMPLOYEES = ["Rajesh Kumar", "Sunita Rao", "Amit Saxena", "Pooja Bhatt"]

class SampleDataService:
    @staticmethod
    def generate_sample_excel_path() -> str:
        """Generates a realistic test Excel file in uploads/"""
        rows = []
        now = datetime.datetime.now()
        
        order_idx = 1001
        for cust_info in SAMPLE_INDIAN_DATA:
            # Generate 1 to 4 orders per customer
            num_orders = random.randint(1, 4)
            for _ in range(num_orders):
                days_ago = random.randint(1, 90)
                order_date = now - datetime.timedelta(days=days_ago, hours=random.randint(1, 12))
                
                prod = random.choice(SAMPLE_PRODUCTS)
                qty = random.choice([1, 1, 2, 3])
                total = prod["price"] * qty
                
                pay_mode = random.choice(["COD", "PREPAID", "PREPAID", "COD"])
                status = random.choice(["DELIVERED", "DELIVERED", "DELIVERED", "COMPLETED", "RETURNED"])
                emp = random.choice(SAMPLE_EMPLOYEES)
                
                rows.append({
                    "Customer Name": cust_info["name"],
                    "Mobile Number": cust_info["mobile"],
                    "Full Address": cust_info["address"],
                    "Pincode": cust_info["pincode"],
                    "District": cust_info["district"],
                    "State": cust_info["state"],
                    "Order ID": f"ORD-2026-{order_idx}",
                    "Order Date": order_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "Payment Mode": pay_mode,
                    "Order Status": status,
                    "Product Name": prod["name"],
                    "SKU": prod["sku"],
                    "Category": prod["category"],
                    "Unit Price": prod["price"],
                    "Quantity": qty,
                    "Total Amount": total,
                    "Sales Person": emp
                })
                order_idx += 1

        df = pd.DataFrame(rows)
        sample_path = "../uploads/sample_indian_ecom_data.xlsx"
        df.to_excel(sample_path, index=False)
        return sample_path
