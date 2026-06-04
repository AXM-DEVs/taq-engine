from typing import Any


def serialize_investigation(inv: Any) -> dict:
    return {
        "id": inv.id, "seed_type": inv.seed_type, "seed_value": inv.seed_value,
        "playbook_id": inv.playbook_id, "status": inv.status,
        "metadata": getattr(inv, "metadata", getattr(inv, "metadata_json", {})),
        "results": inv.results, "errors": getattr(inv, "errors", []),
        "created_at": inv.created_at.isoformat() if hasattr(inv.created_at, "isoformat") else str(inv.created_at),
        "updated_at": inv.updated_at.isoformat() if hasattr(inv.updated_at, "isoformat") else str(inv.updated_at),
    }


def serialize_entity(e: Any) -> dict:
    return {"id": e.id, "investigation_id": e.investigation_id, "entity_type": e.entity_type, "value": e.value, "source": e.source, "raw_data": e.raw_data, "discovered_at": e.discovered_at.isoformat() if hasattr(e.discovered_at, "isoformat") else str(e.discovered_at)}


def serialize_score(s: Any) -> dict:
    return {"id": s.id, "investigation_id": s.investigation_id, "entity_id": s.entity_id, "score_type": s.score_type, "value": s.value, "factors": s.factors, "computed_at": s.computed_at.isoformat() if hasattr(s.computed_at, "isoformat") else str(s.computed_at)}
