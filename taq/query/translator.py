from taq.core.exceptions import QueryError
from taq.query.parser import Intent, ParsedQuery

SQL = {
    Intent.FIND_ENTITIES: """SELECT e.id, e.entity_type, e.value, e.source, e.discovered_at FROM entities e WHERE 1=1 {entity} ORDER BY e.discovered_at DESC LIMIT {limit}""",
    Intent.SCORE_LOOKUP: """SELECT s.id, s.score_type, s.value, s.factors, s.computed_at, e.entity_type, e.value as entity_value FROM scores s JOIN entities e ON s.entity_id = e.id WHERE 1=1 {entity} ORDER BY s.computed_at DESC LIMIT {limit}""",
    Intent.LIST_INVESTIGATIONS: """SELECT i.id, i.seed_type, i.seed_value, i.status, i.created_at, i.updated_at FROM investigations i ORDER BY i.created_at DESC LIMIT {limit}""",
}

CYPHER = {
    Intent.FIND_RELATIONS: """MATCH (n:{label} {{{prop}: '{value}'}}) OPTIONAL MATCH (n)-[r]-(connected) RETURN n, r, connected LIMIT {limit}""",
    Intent.FIND_ENTITIES: """MATCH (n:{label}) WHERE n.{prop} CONTAINS '{value}' RETURN n LIMIT {limit}""",
}

_LABEL = {"email": "Email", "domain": "Domain", "ip": "IP", "username": "Username", "phone": "Phone", "person": "Person", "organization": "Organization"}
_PROP = {"email": "address", "domain": "name", "ip": "address", "username": "name", "phone": "number", "person": "name", "organization": "name"}

def to_sql(q: ParsedQuery) -> str:
    intent = q.intent if q.intent != Intent.UNKNOWN or not q.entity_type else Intent.FIND_ENTITIES
    tpl = SQL.get(intent)
    if not tpl:
        raise QueryError(f"No SQL template for {intent}")
    entity = ""
    if q.entity_type and q.entity_value:
        # Escape single quotes to prevent SQL injection
        escaped_value = q.entity_value.replace("'", "''")
        entity = f"AND e.value = '{escaped_value}'"
    elif q.entity_type:
        # Escape single quotes to prevent SQL injection
        escaped_type = q.entity_type.replace("'", "''")
        entity = f"AND e.entity_type = '{escaped_type}'"
    return tpl.format(entity=entity, limit=q.limit)

def to_cypher(q: ParsedQuery) -> str:
    tpl = CYPHER.get(q.intent)
    if not tpl:
        raise QueryError(f"No Cypher template for {q.intent}")
    # Escape single quotes to prevent Cypher injection
    escaped_value = q.entity_value.replace("'", "''")
    return tpl.format(label=_LABEL.get(q.entity_type, "Entity"), prop=_PROP.get(q.entity_type, "value"), value=escaped_value, limit=q.limit)

def translate(q: ParsedQuery, target: str = "sql") -> str:
    if target == "sql":
        return to_sql(q)
    elif target == "cypher":
        return to_cypher(q)
    raise QueryError(f"Unsupported target: {target}")
