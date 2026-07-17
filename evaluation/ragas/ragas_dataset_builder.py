import time
from typing import List, Dict, Any
from evaluation.retrieval.benchmark_loader import BenchmarkRow
from evaluation.ragas.ragas_runner import RagasRunner
import tqdm

class RagasDatasetBuilder:
    def __init__(self, runner: RagasRunner):
        self.runner = runner

    def build_dataset(self, benchmark_rows: List[BenchmarkRow]) -> List[Dict[str, Any]]:
        dataset = []
        
        for row in tqdm.tqdm(benchmark_rows, desc="Querying backend RAG API"):
            success = False
            for attempt in range(4):
                try:
                    response = self.runner.query(
                        question=row.question,
                        document_id=row.document_id
                    )
                    
                    generated_answer = response["generated_answer"]
                    
                    # Check if the generated answer itself is a rate limit error message
                    if "rate limit reached" in generated_answer.lower() or "limit exceeded" in generated_answer.lower() or "429" in generated_answer.lower():
                        sleep_time = 20 * (attempt + 1)
                        print(f"\n[RateLimit] Backend hit rate limit (429). Sleeping {sleep_time}s before retry...")
                        time.sleep(sleep_time)
                        continue
                        
                    sources = response.get("retrieved_sources", [])
                    retrieved_context = [s.get("text", "") for s in sources]
                    retrieved_chunk_ids = [s.get("metadata", {}).get("chunk_id", "") for s in sources]
                    chunk_metadata = [s.get("metadata", {}) for s in sources]
                    rerank_scores = [s.get("rerank_score") for s in sources]

                    dataset_item = {
                        "question_id": row.question_id,
                        "document_id": row.document_id,
                        "question": row.question,
                        "expected_answer": row.expected_answer,
                        "generated_answer": generated_answer,
                        "retrieved_context": retrieved_context,
                        "retrieved_chunk_ids": retrieved_chunk_ids,
                        "chunk_metadata": chunk_metadata,
                        "rerank_scores": rerank_scores
                    }
                    dataset.append(dataset_item)
                    success = True
                    
                    # Polite sleep between successful queries to avoid hitting TPM limit on next query
                    time.sleep(5)
                    break
                    
                except Exception as e:
                    # Parse if it is an HTTP 429
                    err_msg = str(e)
                    if "429" in err_msg or "rate limit" in err_msg.lower():
                        sleep_time = 20 * (attempt + 1)
                        print(f"\n[RateLimit] Chat API query failed with rate limit (429). Sleeping {sleep_time}s before retry...")
                        time.sleep(sleep_time)
                    else:
                        print(f"\n[Error] Connection or server error on attempt {attempt + 1}: {e}")
                        time.sleep(5)
            
            if not success:
                print(f"\n[Error] Failed to execute API query for question {row.question_id} after {attempt + 1} attempts.")
                
        return dataset
