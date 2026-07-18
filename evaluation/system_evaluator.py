import numpy as np
from typing import List, Dict, Any

class SystemEvaluator:
    """
    Analyzes collected performance metrics to compute aggregates:
    average, minimum, maximum, median (P50), P95, and P99 for each timing metric,
    along with average token usage and retrieved chunk count.
    """
    @staticmethod
    def evaluate(metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        successful_runs = [m for m in metrics_list if m.get("success", False)]
        total_runs = len(metrics_list)
        successful_count = len(successful_runs)

        if not successful_runs:
            return {
                "total_runs": total_runs,
                "successful_runs": 0,
                "timing_summary": {},
                "token_summary": {
                    "average_prompt_tokens": 0.0,
                    "average_completion_tokens": 0.0,
                    "average_total_tokens": 0.0
                },
                "chunk_summary": {
                    "average_retrieved_chunks": 0.0
                }
            }

        # Define fields to aggregate
        timing_fields = [
            "embedding_time",
            "retrieval_time",
            "prompt_construction_time",
            "llm_generation_time",
            "total_response_time"
        ]

        summary = {}

        for field in timing_fields:
            values = [m[field] for m in successful_runs]
            if values:
                summary[field] = {
                    "average": float(np.mean(values)),
                    "min": float(np.min(values)),
                    "max": float(np.max(values)),
                    "median": float(np.median(values)),
                    "p95": float(np.percentile(values, 95)),
                    "p99": float(np.percentile(values, 99))
                }
            else:
                summary[field] = {
                    "average": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "median": 0.0,
                    "p95": 0.0,
                    "p99": 0.0
                }

        # Token usage and chunk averages
        avg_prompt_tokens = float(np.mean([m["prompt_tokens"] for m in successful_runs]))
        avg_completion_tokens = float(np.mean([m["completion_tokens"] for m in successful_runs]))
        avg_total_tokens = float(np.mean([m["total_tokens"] for m in successful_runs]))
        avg_retrieved_chunks = float(np.mean([m["number_of_retrieved_chunks"] for m in successful_runs]))

        return {
            "total_runs": total_runs,
            "successful_runs": successful_count,
            "timing_summary": summary,
            "token_summary": {
                "average_prompt_tokens": avg_prompt_tokens,
                "average_completion_tokens": avg_completion_tokens,
                "average_total_tokens": avg_total_tokens
            },
            "chunk_summary": {
                "average_retrieved_chunks": avg_retrieved_chunks
            }
        }
