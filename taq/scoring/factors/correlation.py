def score_correlation(entity_count: int, relationship_count: int = 0) -> float:
    if entity_count <= 1: return 0.1
    if entity_count == 2: return 0.3
    if entity_count <= 5: return 0.5
    if entity_count <= 10: return 0.7
    if entity_count <= 25: return 0.85
    return 0.95
