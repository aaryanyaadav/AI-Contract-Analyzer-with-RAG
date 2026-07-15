from typing import List, Dict, Any, Optional
from evaluation.retrieval.benchmark_loader import BenchmarkRow
from evaluation.retrieval.retrieval_runner import RetrievalRunner
from evaluation.retrieval.retrieval_metrics import calculate_metrics

class RetrievalEvaluator:
    """
    Evaluator that loads benchmark queries, runs retrieval, and computes metrics.
    Designed to support multiple relevant chunks per query from day one.
    """
    def __init__(self, session_id: Optional[str] = None, chroma_path: Optional[str] = None):
        self.session_id = session_id
        self.chroma_path = chroma_path

    def evaluate(self, benchmark_rows: List[BenchmarkRow], k: int = 5) -> Dict[str, Any]:
        """
        Runs the retrieval evaluation pipeline.
        """
        runner = RetrievalRunner(session_id=self.session_id, chroma_path=self.chroma_path)
        results = []
        
        try:
            for row in benchmark_rows:
                # Query the production retriever via RetrievalRunner
                runner_output = runner.run_query(
                    question=row.question,
                    document_id=row.document_id,
                    k=k
                )
                
                retrieved_chunks = runner_output["retrieved_chunks"]
                retrieved_ids = [chunk["chunk_id"] for chunk in retrieved_chunks]
                retrieved_scores = [chunk["retrieval_score"] for chunk in retrieved_chunks]
                
                # Calculate metrics supporting multiple expected chunk IDs
                metrics = calculate_metrics(retrieved_ids, row.relevant_chunk_ids, k)
                
                # Create detailed record for this query
                row_result = {
                    "question_id": row.question_id,
                    "question": row.question,
                    "document_id": row.document_id,
                    "expected_chunk_ids": row.relevant_chunk_ids,
                    "retrieved_chunk_ids": retrieved_ids,
                    "retrieved_scores": retrieved_scores,
                    "runner_output": runner_output,  # Saved for reuse by RAGAS, DeepEval, report generator
                    **metrics
                }
                results.append(row_result)
        finally:
            runner.close()

        # Compute aggregate metrics
        total = len(results)
        if total > 0:
            avg_precision = sum(r["precision@k"] for r in results) / total
            avg_recall = sum(r["recall@k"] for r in results) / total
            avg_hit = sum(r["hit@k"] for r in results) / total
            avg_mrr = sum(r["reciprocal_rank"] for r in results) / total
        else:
            avg_precision = avg_recall = avg_hit = avg_mrr = 0.0

        summary = {
            "benchmark_size": total,
            "k": k,
            "Precision@K": avg_precision,
            "Recall@K": avg_recall,
            "Hit@K": avg_hit,
            "MRR": avg_mrr
        }

        return {
            "results": results,
            "summary": summary
        }
