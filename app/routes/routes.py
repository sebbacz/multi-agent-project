from fastapi import APIRouter
from app.routes.analyze import router as analyze_router

# Central router aggregator
api_router = APIRouter()
api_router.include_router(analyze_router, tags=["analysis"])

# Future routes can be added here:
# api_router.include_router(reports_router, prefix="/reports", tags=["reports"])
# api_router.include_router(export_router, prefix="/export", tags=["export"])
