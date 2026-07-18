from typing import Dict, Any, List

class MetricsCollector:
    """
    Collects individual performance metrics for each query during system evaluation.
    """
    def __init__(self):
        self.metrics_list = []

    def collect(self, query_id: str, document_id: str, query: str, api_response: dict):
        """
        Extracts metrics from the API response and stores them.
        """
        metrics = api_response.get("metrics", {})
        
        # Ensure we capture metrics or default to zero
        self.metrics_list.append({
            "question_id": query_id,
            "document_id": document_id,
            "question": query,
            "embedding_time": metrics.get("embedding_time", 0.0),
            "retrieval_time": metrics.get("retrieval_time", 0.0),
            "prompt_construction_time": metrics.get("prompt_construction_time", 0.0),
            "llm_generation_time": metrics.get("llm_generation_time", 0.0),
            "total_response_time": metrics.get("total_response_time", 0.0),
            "number_of_retrieved_chunks": metrics.get("number_of_retrieved_chunks", 0),
            "prompt_tokens": metrics.get("prompt_tokens", 0),
            "completion_tokens": metrics.get("completion_tokens", 0),
            "total_tokens": metrics.get("total_tokens", 0),
            "success": api_response.get("success", False),
            "error": api_response.get("error", "")
        })

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        return self.metrics_list
