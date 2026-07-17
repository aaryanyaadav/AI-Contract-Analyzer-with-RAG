from evaluation.ragas.official_ragas_evaluator import OfficialRagasEvaluator
from evaluation.ragas.fallback_evaluator import FallbackSemanticEvaluator
from evaluation.ragas.base_evaluator import BaseEvaluator

def get_evaluator(evaluator_type: str = "auto") -> BaseEvaluator:
    if evaluator_type == "fallback":
        evaluator = FallbackSemanticEvaluator()
        evaluator.initialize()
        return evaluator
    elif evaluator_type == "official":
        evaluator = OfficialRagasEvaluator()
        evaluator.initialize()
        return evaluator

    try:
        evaluator = OfficialRagasEvaluator()
        evaluator.initialize()
    except Exception:
        evaluator = FallbackSemanticEvaluator()
        evaluator.initialize()
        
    return evaluator
