from fastapi import APIRouter
from app.api.v1.routes import hypotheses, signals, sources, agents, auth, admin, counterfactual, committee, graph

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(hypotheses.router, prefix="/hypotheses", tags=["hypotheses"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(counterfactual.router, prefix="/counterfactual", tags=["counterfactual"])
api_router.include_router(committee.router, prefix="/committee", tags=["committee"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
