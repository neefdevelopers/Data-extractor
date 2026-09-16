# Pinlytics 📍
> **Local-Only Customer & Business Analytics Platform**
> Complete data extraction, intelligent Excel/CSV ingestion, Indian postal PIN code enrichment, centralized revenue intelligence, and RFM customer segmentation.

---

## 🔒 100% Local Architecture

Pinlytics is built exclusively for local computer execution. All data processing, database storage, analytics calculations, and report generations run directly on your machine without cloud dependencies.

```
       Local Excel / CSV Files (.xlsx, .xls, .csv)
                           │
                           ▼
              ┌─────────────────────────┐
              │  FastAPI Import Engine  │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  PostgreSQL / SQLAlchemy│
              └────────────┬────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
  Customer CRM     Business Revenue     RFM Customer
  & Profiles         Intelligence       Segmentation
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                           ▼
             ┌───────────────────────────┐
             │ React + Vite Enterprise UI│
             │   (http://localhost:5173) │
             └───────────────────────────┘
```

---

## 🚀 Prerequisites

Ensure the following tools are installed on your system:

1. **Python** (version 3.10 or higher)
2. **Node.js** (version 18 or higher) & **npm**
3. **PostgreSQL** (version 14 or higher) running locally on port `5432` *(Or zero-config SQLite mode)*

---

## 🛠️ Complete Zero-to-Hero Local Setup

### Step 1: Database Setup (PostgreSQL)

1. Open your PostgreSQL terminal (`psql` or pgAdmin) and create a local database:
   ```sql
   CREATE DATABASE pinlytics;
   ```

2. Confirm your connection credentials (default username `postgres`, password `password` or your chosen password).

---

### Step 2: Backend Setup & Startup

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```

2. *(Optional but recommended)* Create and activate a Python virtual environment:
   ```bash
   # Windows PowerShell / CMD:
   python -m venv venv
   .\venv\Scripts\activate

   # macOS / Linux:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure local environment variables in `backend/.env`:
   ```env
   # Local PostgreSQL database URL:
   DATABASE_URL=postgresql://postgres:password@localhost:5432/pinlytics

   # (Fallback: sqlite:///./pinlytics.db for instant zero-config testing)

   POSTAL_API_URL=https://api.postalpincode.in/pincode/
   UPLOAD_DIR=../uploads
   EXPORT_DIR=../exports
   DEBUG=True
   APP_NAME=Pinlytics
   ```

5. Launch the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --host localhost --port 8000
   ```

   - **Backend API:** [http://localhost:8000](http://localhost:8000)
   - **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 3: Frontend Setup & Startup

1. Open a second terminal window and navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

4. Open your browser and navigate to:
   - **Pinlytics UI:** [http://localhost:5173](http://localhost:5173)

---

## 📊 Core System Modules

### 1. Excel / CSV Import Engine (`/uploads`)
- **Drag & Drop Ingestion:** Supports `.xlsx`, `.xls`, and `.csv` files.
- **Intelligent Column Detection:** Automatically identifies Customer Name, Mobile, Address, PIN Code, Order ID, Date, Amount, Payment Mode, Status, Product, and Sales Rep headers.
- **Pre-Import Preview:** Inspect sample rows (20–50 rows) and validation alerts before confirming database insertion.
- **Postal Enrichment:** Resolves 6-digit Indian PIN codes using official postal masters and handles multiple post offices under a single PIN.
- **Deduplication:** Prevents duplicate customers (Primary: Mobile, Secondary: Name + PIN) and duplicate orders (Order ID).

### 2. Business Analytics & Revenue (`/`)
- **Centralized `RevenueService`:** Single Source of Truth for revenue qualification.
- **Date Presets:** All Time, Today, Yesterday, 7 Days, 30 Days, This Month, Previous Month, and Custom Ranges.
- **COD vs Prepaid Intelligence:** Track cash flow, volume ratios, and fulfillment rates.

### 3. Customer CRM & Profile (`/customers`)
- **Customer Directory:** Search by Name, Mobile, District, or PIN.
- **Rich Customer Profiles:** View order timelines, lifetime spend (LTV), average order value (AOV), and R/F/M quintile scores.
- **1-Click Copy Details:** Quickly copy formatted name, phone, address, post office, district, and PIN to clipboard.

### 4. RFM Behavioral Clustering (`/rfm`)
- **Dynamic Calculation:** Computes Recency (days), Frequency (qualifying orders), and Monetary Value (spend) directly from PostgreSQL orders.
- **7 Automated Segments:** Champions, Loyal Customers, Potential Loyalists, New Customers, At Risk, Dormant Customers, and Lost Customers.
- **Recalculation Engine:** Dynamically updates customer segmentations when orders are modified or imported.

### 5. Geographic Drilldown (`/geography`)
- **4-Level Hierarchy:** District → PIN Code → Customers → Order Details.

### 6. Product & Employee Analytics (`/products`, `/employees`)
- **Product Sales Contribution %:** Track revenue share and unit velocities by SKU.
- **Sales Rep Performance:** Compare order conversions, COD vs prepaid revenue, and customer acquisition counts.

### 7. Reports & Data Quality (`/reports`, `/data-quality`)
- **Export Formats:** Generate Microsoft Excel (`.xlsx`) and CSV (`.csv`) files saved locally into `exports/`.
- **Integrity Audit:** Monitor and resolve invalid phone numbers, non-standard PINs, and postal conflicts.

---

## 🧪 Running Automated Tests

Run backend unit and integration tests:
```bash
cd backend
python -m pytest tests/test_backend.py -v
```

---

## ❓ Troubleshooting

| Issue | Solution |
|---|---|
| **Database connection error** | Ensure PostgreSQL service is running and `DATABASE_URL` in `backend/.env` has the correct username, password, and database name. Alternatively, switch to `sqlite:///./pinlytics.db`. |
| **PIN code lookup offline** | Previously fetched PINs are cached in `postal_master`. If internet is offline, new PINs will still save without crashing. |
| **Port already in use** | If port 8000 is occupied, run `uvicorn app.main:app --reload --port 8001` and update `VITE_API_URL` in `frontend/.env`. |
