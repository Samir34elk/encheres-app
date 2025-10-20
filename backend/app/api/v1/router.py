from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    alerts,
    auth,
    favorites,
    ingestion,
    lots,
    notifications,
    sales,
    scheduler,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(sales.router, prefix="/sales", tags=["Sales"])
api_router.include_router(lots.router, prefix="/lots", tags=["Lots"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["Scheduler"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Ingestion"])
