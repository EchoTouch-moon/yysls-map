from fastapi import APIRouter

from app.api.routes import (
    admin_content,
    ai,
    auth,
    details,
    discovery,
    graph,
    health,
    history,
    resources,
    story_arcs,
    submissions,
    timeline,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(graph.router)
api_router.include_router(resources.router)
api_router.include_router(timeline.router)
api_router.include_router(story_arcs.router)
api_router.include_router(details.router)
api_router.include_router(history.router)
api_router.include_router(discovery.router)
api_router.include_router(submissions.router)
api_router.include_router(auth.router)
api_router.include_router(admin_content.router)
api_router.include_router(ai.router)
