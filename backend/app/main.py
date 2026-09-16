import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.session import init_database
from app.api import (
    customers_router,
    orders_router,
    products_router,
    employees_router,
    uploads_router,
    postal_router,
    analytics_router,
    rfm_router,
    reports_router,
    data_quality_router,
    settings_router,
    locations_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_database()
    yield

app = FastAPI(
    title="Pinlytics - Customer & Business Analytics API",
    description="Local-only analytics backend with Excel processing, Indian postal enrichment, centralized revenue rules, and RFM scoring.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers under /api
app.include_router(customers_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(employees_router, prefix="/api")
app.include_router(uploads_router, prefix="/api")
app.include_router(postal_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(rfm_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(data_quality_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(locations_router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": "Pinlytics",
        "status": "running",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health():
    return {"status": "healthy"}
