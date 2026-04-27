"""Knowledge Graph API — узлы и рёбра для визуализации."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db

router = APIRouter()


@router.get("/nodes")
async def get_graph_nodes(db: AsyncSession = Depends(get_db)) -> dict:
    """Return graph nodes: hypotheses + signals grouped by type."""
    hyp_r = await db.execute(text("""
        SELECT id, title, status, domain, overall_score, confidence_score
        FROM hypotheses ORDER BY created_at DESC LIMIT 200
    """))
    hypotheses = hyp_r.mappings().all()

    sig_r = await db.execute(text("""
        SELECT id, title, source_type, relevance_score, hypothesis_id
        FROM signals WHERE is_duplicate = false LIMIT 500
    """))
    signals = sig_r.mappings().all()

    nodes = []
    edges = []

    for h in hypotheses:
        nodes.append({
            "id": str(h["id"]),
            "label": h["title"][:60],
            "type": "hypothesis",
            "status": h["status"],
            "score": float(h["overall_score"]) if h["overall_score"] else None,
            "domain": h["domain"],
        })

    for s in signals:
        nodes.append({
            "id": str(s["id"]),
            "label": s["title"][:60],
            "type": "signal",
            "source_type": s["source_type"],
            "relevance": float(s["relevance_score"]) if s["relevance_score"] else 0,
        })
        if s["hypothesis_id"]:
            edges.append({
                "id": f"s-{s['id']}",
                "source": str(s["id"]),
                "target": str(s["hypothesis_id"]),
                "type": "generated_from",
            })

    return {"nodes": nodes, "edges": edges}
