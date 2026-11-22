from fastapi import APIRouter
from app.api.routes import applications, documents, health, underwriting

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(underwriting.router, tags=["underwriting"])
