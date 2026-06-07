from fastapi import APIRouter

from app.api.routes import graph, health, resources

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(graph.router)
api_router.include_router(resources.router)
