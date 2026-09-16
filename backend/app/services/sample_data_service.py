import random
import datetime
from typing import List, Dict, Any
import pandas as pd
from sqlalchemy.orm import Session
from app.services.excel_import_service import ExcelImportService

SAMPLE_INDIAN_DATA = [
    {"name": "Aarav Sharma", "mobile": "9820112345", "address": "Flat 402, Sea View Apts, Bandra West", "pincode": "400050", "district": "Mumbai", "state": "Maharashtra"},
    {"name": "Priya Patel", "mobile": "9879123456", "address": "12, Shanti Kunj, Navrangpura", "pincode": "380009", "district": "Ahmedabad", "state": "Gujarat"},
    {"name": "Rahul Verma", "mobile": "9811234567", "address": "B-45, Connaught Place", "pincode": "110001", "district": "New Delhi", "state": "Delhi"},
    {"name": "Sneha Reddy", "mobile": "9849012345", "address": "Plot 89, Jubilee Hills", "pincode": "500033", "district": "Hyderabad", "state": "Telangana"},
    {"name": "Vikram Iyer", "mobile": "9840123456", "address": "45, Anna Salai, T Nagar", "pincode": "600017", "district": "Chennai", "state": "Tamil Nadu"},
    {"name": "Ananya Mukherjee", "mobile": "9830123456", "address": "78, Salt Lake Sector 2", "pincode": "700091", "district": "Kolkata", "state": "West Bengal"},
    {"name": "Rohan Gupta", "mobile": "9829012345", "address": "15, MI Road, C-Scheme", "pincode": "302001", "district": "Jaipur", "state": "Rajasthan"},
    {"name": "Neha Joshi", "mobile": "9822012345", "address": "24, FC Road, Shivaji Nagar", "pincode": "411004", "district": "Pune", "state": "Maharashtra"},
    {"name": "Aditya Rao", "mobile": "9845012345", "address": "101, Indiranagar 100 Feet Rd", "pincode": "560038", "district": "Bengaluru", "state": "Karnataka"},
    {"name": "Pooja Nair", "mobile": "9847012345", "address": "56, Marine Drive", "pincode": "682011", "district": "Ernakulam", "state": "Kerala"},
    {"name": "Karan Malhotra", "mobile": "9814012345", "address": "Sector 17-C", "pincode": "160017", "district": "Chandigarh", "state": "Chandigarh"},
    {"name": "Deepika Das", "mobile": "9864012345", "address": "GS Road, Christian Basti", "pincode": "781005", "district": "Kamrup", "state": "Assam"},
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
