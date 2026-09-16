from app.api.customers import router as customers_router
from app.api.orders import router as orders_router
from app.api.products import router as products_router
from app.api.employees import router as employees_router
from app.api.uploads import router as uploads_router
from app.api.postal import router as postal_router
from app.api.analytics import router as analytics_router
from app.api.rfm import router as rfm_router
from app.api.reports import router as reports_router
from app.api.data_quality import router as data_quality_router
from app.api.settings import router as settings_router
from app.api.locations import router as locations_router

__all__ = [
    "customers_router",
    "orders_router",
    "products_router",
    "employees_router",
    "uploads_router",
    "postal_router",
    "analytics_router",
    "rfm_router",
    "reports_router",
    "data_quality_router",
    "settings_router",
    "locations_router"
]

