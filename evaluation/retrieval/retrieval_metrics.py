from typing import List, Dict

def calculate_hit_at_k(retrieved_ids: List[str], expected_ids: List[str], k: int) -> float:
    #Hit@k
    top_k_retrieved = retrieved_ids[:k]
    for expected_id in expected_ids:
        if expected_id in top_k_retrieved:
            return 1.0
    return 0.0

def calculate_precision_at_k(retrieved_ids: List[str], expected_ids: List[str], k: int) -> float:
    # precison@k
    if k <= 0:
        return 0.0
    top_k_retrieved = retrieved_ids[:k]
    relevant_retrieved = len(set(top_k_retrieved) & set(expected_ids))
    return relevant_retrieved / k

def calculate_recall_at_k(retrieved_ids: List[str], expected_ids: List[str], k: int) -> float:
    # recall@K
    if not expected_ids:
        return 0.0
    top_k_retrieved = retrieved_ids[:k]
    relevant_retrieved = len(set(top_k_retrieved) & set(expected_ids))
    return relevant_retrieved / len(expected_ids)

def calculate_reciprocal_rank(retrieved_ids: List[str], expected_ids: List[str], k: int) -> float:
    # reciprocal rank
    top_k_retrieved = retrieved_ids[:k]
    for idx, retrieved_id in enumerate(top_k_retrieved):
        if retrieved_id in expected_ids:
            return 1.0 / (idx + 1)
    return 0.0

def calculate_metrics(retrieved_ids: List[str], expected_ids: List[str], k: int) -> Dict[str, float]:
    return {
        "hit@k": calculate_hit_at_k(retrieved_ids, expected_ids, k),
        "precision@k": calculate_precision_at_k(retrieved_ids, expected_ids, k),
        "recall@k": calculate_recall_at_k(retrieved_ids, expected_ids, k),
        "reciprocal_rank": calculate_reciprocal_rank(retrieved_ids, expected_ids, k)
    }
