import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Intent(str, Enum):
    FIND_ENTITIES = "find_entities"
    FIND_RELATIONS = "find_relations"
    SCORE_LOOKUP = "score_lookup"
    INVESTIGATION_STATUS = "investigation_status"
    LIST_INVESTIGATIONS = "list_investigations"
    SUMMARIZE = "summarize"
    COUNT = "count"
    UNKNOWN = "unknown"


@dataclass
class ParsedQuery:
    intent: Intent = Intent.UNKNOWN
    entity_type: str = ""
    entity_value: str = ""
    filters: dict = field(default_factory=dict)
    limit: int = 50
    raw: str = ""


_ENTITY_MAP = {
    "email": ["email", "mail", "e-mail", "correo"],
    "domain": ["domain", "dominio", "website", "site", "web", "url"],
    "ip": ["ip", "ip address", "direccion ip", "host"],
    "username": ["username", "user", "usuario", "handle", "nick", "account"],
    "phone": ["phone", "telefono", "phone number", "numero", "tel"],
    "person": ["person", "persona", "name", "nombre", "individual"],
    "organization": ["organization", "organizacion", "company", "empresa", "org"],
}

_INTENTS = [
    (re.compile(r"(find|search|lookup|buscar|show|get|list|mostrar).*(entity|entidad|entities|entidades)", re.I), Intent.FIND_ENTITIES),
    (re.compile(r"(relation|conexion|link|connect|relacion|grafo|graph|connections)", re.I), Intent.FIND_RELATIONS),
    (re.compile(r"(score|threat|puntaje|amenaza|risk|riesgo)", re.I), Intent.SCORE_LOOKUP),
    (re.compile(r"(status|estado|state).*(investigation|investigacion)", re.I), Intent.INVESTIGATION_STATUS),
    (re.compile(r"(list|show|mostrar|all|todas)\s*(investigation|investigacion)", re.I), Intent.LIST_INVESTIGATIONS),
    (re.compile(r"(summarize|summary|resumen|resumir)", re.I), Intent.SUMMARIZE),
    (re.compile(r"(count|cuantos|how many)", re.I), Intent.COUNT),
]


def parse(text: str) -> ParsedQuery:
    q = ParsedQuery(raw=text)
    for pat, intent in _INTENTS:
        if pat.search(text):
            q.intent = intent
            break
    q.entity_type = _extract_type(text)
    q.entity_value = _extract_value(text, q.entity_type)
    q.limit = _extract_limit(text)
    q.filters = _extract_filters(text)
    return q

def _extract_type(text: str) -> str:
    tl = text.lower()
    for etype, kws in _ENTITY_MAP.items():
        for kw in kws:
            if kw in tl:
                return etype
    return ""

def _extract_value(text: str, etype: str) -> str:
    patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "ip": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        "domain": r"(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,})",
        "phone": r"\+?\d{7,15}",
    }
    pat = patterns.get(etype)
    if pat:
        m = re.search(pat, text)
        if m:
            return m.group(0)
    if etype == "username":
        for w in text.split():
            w = w.strip("@#")
            if w and not re.match(r"^(find|search|show|get|list|the|for|user)$", w, re.I):
                return w
    return ""

def _extract_limit(text: str) -> int:
    m = re.search(r"(?:top|limit|max)\s*:?\s*(\d+)", text, re.I)
    return min(int(m.group(1)), 200) if m else 50

def _extract_filters(text: str) -> dict:
    f = {}
    sm = re.search(r"score\s*([>=<])\s*(\d+\.?\d*)", text)
    if sm:
        f["score"] = {"op": sm.group(1), "value": float(sm.group(2))}
    dm = re.search(r"(?:after|before|since|desde|hasta)\s*:?\s*(\d{4}[-/]\d{2}[-/]\d{2})", text, re.I)
    if dm:
        f["after" if re.search(r"(after|since|desde)", text, re.I) else "before"] = dm.group(1)
    return f
